Param([switch]$Headless)
$SkipFrontend = $Headless

# --- SOTA Headless Standard ---
if ($Headless -and ($Host.UI.RawUI.WindowTitle -notmatch 'Hidden')) {
    Start-Process pwsh -ArgumentList '-NoProfile', '-File', $PSCommandPath, '-Headless' -WindowStyle Hidden
    exit
}
$WindowStyle = if ($Headless) { 'Hidden' } else { 'Normal' }
# ------------------------------

$env:FASTMCP_LOG_LEVEL = 'WARNING'
# system-admin-mcp Start - Standards-Compliant SOTA
Write-Host 'Starting system-admin-mcp...' -ForegroundColor Cyan

Set-Location $PSScriptRoot
Write-Host 'Starting Standardized Fullstack Hybrid...' -ForegroundColor Green
# --- SOTA PORT SAFETY START ---
# NOTE: this script defines no $Port variable (ports live in fleet-start.config.ps1),
# so fleet repair sweeps that anchor on "$Port = <n>" skip this file - that is why
# the port-clear kept "regressing". Clear by literal ports instead. This block
# contains the Get-NetTCPConnection -LocalPort marker so sweeps see it as fixed.
$BackendPort = 10861
$FrontendPort = 10860
try {
    $fleetCfg = . (Join-Path $PSScriptRoot 'fleet-start.config.ps1')
    if ($fleetCfg.BackendPort) { $BackendPort = [int]$fleetCfg.BackendPort }
    if ($fleetCfg.FrontendPort) { $FrontendPort = [int]$fleetCfg.FrontendPort }
} catch { }
foreach ($portNum in @($BackendPort, $FrontendPort)) {
    Get-NetTCPConnection -LocalPort $portNum -State Listen -ErrorAction SilentlyContinue | ForEach-Object {
        if ($_.OwningProcess -ne $PID) {
            Write-Host "Clearing stale listener on port $portNum (PID $($_.OwningProcess))..." -ForegroundColor Yellow
            Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
        }
    }
}
Start-Sleep -Seconds 1
# --- SOTA PORT SAFETY END ---
# Launch backend Hidden by default to prevent console spam
Start-Process pwsh -ArgumentList '-NoProfile', '-Command', 'uv run -m system_admin_mcp --web' -WindowStyle Hidden
Set-Location web_sota
if ($SkipFrontend) { return }
npm run dev
