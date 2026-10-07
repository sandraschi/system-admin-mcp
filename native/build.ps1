$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$RepoName = Split-Path -Leaf $Root
$Triple = "x86_64-pc-windows-msvc"
$ResourceDir = "$PSScriptRoot\resources"
$DevDir = "$PSScriptRoot\binaries"
New-Item -ItemType Directory -Force -Path $ResourceDir, $DevDir | Out-Null

Write-Host "=== ${RepoName} Tauri Release Build ===" -ForegroundColor Cyan

# Step 1: TypeScript lint gate + frontend build (bun per BUN_STANDARDS.md; Node stays for Vite/Tauri CLIs)
$bunExe = "$env:USERPROFILE\.bun\bin\bun.exe"
if (-not (Test-Path -LiteralPath $bunExe)) { $bunExe = "bun" }
$bunxExe = "$env:USERPROFILE\.bun\bin\bunx.exe"
if (-not (Test-Path -LiteralPath $bunxExe)) { $bunxExe = "bunx" }
$frontendDirs = @("web_sota", "webapp/frontend", "webapp")
foreach ($dir in $frontendDirs) {
    $frontend = Join-Path $Root $dir
    if (Test-Path "$frontend\package.json") {
        Write-Host "-> [1/4] Building frontend ($dir)..." -ForegroundColor Yellow
        Push-Location $frontend
        & $bunExe install --silent 2>$null

        Write-Host "  tsc --noEmit..." -ForegroundColor Gray
        $tscOut = & $bunxExe tsc --noEmit 2>&1
        $tscExit = $LASTEXITCODE
        if ($tscExit -ne 0) {
            Write-Host "  TypeScript compilation FAILED - fix errors before building NSIS" -ForegroundColor Red
            Write-Host $tscOut
            throw "TypeScript compilation failed - fix all errors before building NSIS installer"
        }

        & $bunExe run build
        if ($LASTEXITCODE -ne 0) { throw "Frontend build failed" }
        Pop-Location
        break
    }
}

# Step 2: PyInstaller backend (onefile)
Write-Host "-> [2/4] PyInstaller backend..." -ForegroundColor Yellow
$specFile = "$Root\${RepoName}-backend.spec"
if (Test-Path $specFile) {
    Push-Location $Root
    # Patch fastmcp to not crash on missing metadata (dist-info stripped below)
    $fm = "$Root\.venv\Lib\site-packages\fastmcp\__init__.py"
    if (Test-Path $fm) {
        $c = Get-Content $fm -Raw
        if ($c -match 'except PackageNotFoundError:\s+    __version__ = _version\("fastmcp"\)') {
            $c = $c -replace 'except PackageNotFoundError:\s+    __version__ = _version\("fastmcp"\)', 'except PackageNotFoundError:
    try:
        __version__ = _version("fastmcp")
    except PackageNotFoundError:
        __version__ = "0.0.0"'
            Set-Content $fm -Value $c -Encoding utf8
            Write-Host "  Patched fastmcp metadata fallback" -ForegroundColor Yellow
        }
    }
    uv run pyinstaller "$specFile" --clean --noconfirm
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed with exit code $LASTEXITCODE" }
    Pop-Location
} else {
    Write-Host "  WARNING: spec file not found at $specFile - using existing backend exe if present" -ForegroundColor DarkYellow
}

# Step 3: Embed in Tauri resources (+ dev fallback)
Write-Host "-> [3/4] Embedding backend..." -ForegroundColor Yellow
$src = "$Root\dist\${RepoName}-backend.exe"
if (-not (Test-Path $src)) { throw "Backend exe not found at $src - PyInstaller step failed" }
Copy-Item $src "$ResourceDir\${RepoName}-backend.exe" -Force
Copy-Item $src "$DevDir\${RepoName}-backend-$Triple.exe" -Force
$backendMB = (Get-Item $src).Length / 1MB
Write-Host "  Backend exe: $([math]::Round($backendMB, 1)) MB"
# Gate 0 (tauri_nsis_building.md): a runt backend means PyInstaller silently dropped imports.
if ((Get-Item $src).Length -lt 5MB) { throw "Backend exe is only $([math]::Round($backendMB, 2)) MB (< 5 MB) - PyInstaller dropped imports, refusing to bundle" }

# Frozen smoke test: boot the exe on a scratch port and probe /api/health.
$smokePort = 11999
$env:SYSTEMADMIN_TAURI = "1"
$env:PORT = "$smokePort"
$smokeLog = "$Root\dist\pyi-smoke.log"
$smokeProc = Start-Process -FilePath $src -NoNewWindow -PassThru -RedirectStandardError $smokeLog
try {
    $smoked = $false
    for ($i = 0; $i -lt 12; $i++) {
        Start-Sleep -Seconds 5
        if ($smokeProc.HasExited) { break }
        try {
            $r = Invoke-WebRequest "http://127.0.0.1:$smokePort/api/health" -UseBasicParsing -TimeoutSec 5
            if ($r.StatusCode -eq 200) { $smoked = $true; break }
        } catch { }
    }
    if (-not $smoked) {
        $tail = if (Test-Path $smokeLog) { Get-Content $smokeLog -Raw } else { "(no log)" }
        throw "Frozen backend smoke test failed on :$smokePort (exited=$($smokeProc.HasExited)). stderr: $tail"
    }
    Write-Host "  Frozen smoke test PASSED (:$smokePort /api/health 200)" -ForegroundColor Green
} finally {
    if (-not $smokeProc.HasExited) { $smokeProc.Kill() }
    Remove-Item Env:\SYSTEMADMIN_TAURI -ErrorAction SilentlyContinue
    Remove-Item Env:\PORT -ErrorAction SilentlyContinue
}

# Bundle .env.example (NOT .env - dev .env has personal API keys)
$envExample = "$Root\.env.example"
if (Test-Path $envExample) {
    Copy-Item $envExample "$ResourceDir\.env.example" -Force
    Write-Host "  Bundled .env.example OK" -ForegroundColor Green
} else {
    Write-Host "  WARNING: .env.example not found at repo root" -ForegroundColor DarkYellow
}

# Step 4: Single NSIS installer
Write-Host "-> [4/4] Tauri NSIS bundle..." -ForegroundColor Yellow
Push-Location $PSScriptRoot
$env:Path = "$env:USERPROFILE\.cargo\bin;$env:Path"
npx @tauri-apps/cli build --bundles nsis
if ($LASTEXITCODE -ne 0) { throw "Tauri build failed with exit code $LASTEXITCODE" }
Pop-Location

# Stage to repo dist/
$distDir = Join-Path $Root "dist"
New-Item -ItemType Directory -Force -Path $distDir | Out-Null
$nsisDir = "$PSScriptRoot\target\release\bundle\nsis"
if (Test-Path $nsisDir) { Copy-Item "$nsisDir\*-setup.exe" "$distDir\" -Force }
$strayExe = "$PSScriptRoot\target\release\system-admin-mcp-backend.exe"
if (Test-Path $strayExe) { Remove-Item $strayExe -Force; Write-Host "  Cleaned stray: $strayExe" -ForegroundColor DarkGray }

Write-Host "=== Build complete ===" -ForegroundColor Green
Write-Host "Ship: $nsisDir\*.exe"
