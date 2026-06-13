param(
    [switch]$Headless,
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [switch]$NoBrowser
)

$WebPort = 10860
$BackendPort = 10861
$ProjectRoot = Split-Path -Parent $PSScriptRoot

$FleetStartPath = Join-Path $ProjectRoot "scripts\FleetStartMode.ps1"
if (-not (Test-Path -LiteralPath $FleetStartPath)) {
    Write-Host "ERROR: Missing vendored launcher helper: $FleetStartPath" -ForegroundColor Red
    exit 1
}
. $FleetStartPath
$FleetStart = Initialize-FleetStartMode @PSBoundParameters
Enter-FleetHeadlessConsole -Headless:$Headless -BackendOnly:$BackendOnly
Stop-FleetPortSquatters -Ports @($WebPort, $BackendPort) -Label "system-admin-mcp"

if (-not (Assert-FleetPortsAvailable -Ports @($WebPort, $BackendPort) -Label "system-admin-mcp")) { exit 1 }

# 2. Setup
Set-Location $PSScriptRoot
if (-not (Test-Path "node_modules")) { npm install }

# 3. Start the Python backend (Background)
Write-Host "Starting Python backend on port $BackendPort ..." -ForegroundColor Cyan

# Use TRIPLE backtick to ensure $env:PYTHONPATH reaches the REAL shell
$backendCmd = "`$env:PYTHONPATH = '$ProjectRoot\src'; Set-Location '$ProjectRoot'; uv run uvicorn system_admin_mcp.server:app --host 127.0.0.1 --port $BackendPort --log-level info"

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd -WindowStyle Normal

# 4. Run server (Vite dev)
if (-not $FleetStart.RunFrontend) { return }

Write-Host "Starting Vite frontend on port $WebPort ..." -ForegroundColor Green

# 4b. Launch background task to open browser once frontend is ready (Auto-opened by Antigravity)
$frontendUrl = "http://127.0.0.1:$WebPort/"
$pollAndOpen = "for (`$i = 0; `$i -lt 60; `$i++) { try { `$null = Invoke-WebRequest -Uri '$frontendUrl' -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop; Start-Process '$frontendUrl'; exit } catch { Start-Sleep -Seconds 1 } }"
Start-Process powershell -ArgumentList "-NoProfile", "-WindowStyle", "Hidden", "-Command", $pollAndOpen

Write-Host "Browser will open automatically when Vite is ready." -ForegroundColor Gray
if (-not $FleetStart.RunFrontend) { return }
npm run dev -- --port $WebPort --host







