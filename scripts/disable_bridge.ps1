<#
.SYNOPSIS
    Disables the System Admin MCP bridge in Claude without modifying MCP configuration.
    
.DESCRIPTION
    This script creates a marker file that tells the bridge to disable itself.
    This is safer than directly modifying Claude's MCP configuration.
    
.PARAMETER Revert
    If specified, removes the disabled marker to re-enable the bridge.
    
.EXAMPLE
    .\disable_bridge.ps1
    # Disables the bridge
    
    .\disable_bridge.ps1 -Revert
    # Re-enables the bridge
#>

[CmdletBinding()]
param (
    [switch]$Revert
)

$ErrorActionPreference = 'Stop'

# Path to the marker file
$markerPath = "$env:LOCALAPPDATA\SystemAdminMCP\.bridge_disabled"

if ($Revert) {
    # Re-enable the bridge by removing the marker
    if (Test-Path $markerPath) {
        Remove-Item -Path $markerPath -Force
        Write-Host "Bridge has been re-enabled. Restart Claude for changes to take effect." -ForegroundColor Green
    } else {
        Write-Host "Bridge is already enabled." -ForegroundColor Yellow
    }
} else {
    # Disable the bridge by creating the marker
    $null = New-Item -Path (Split-Path $markerPath) -ItemType Directory -Force -ErrorAction SilentlyContinue
    $null = New-Item -Path $markerPath -ItemType File -Force
    Write-Host "Bridge has been disabled. Restart Claude for changes to take effect." -ForegroundColor Yellow
    Write-Host "Note: To completely remove the bridge, you'll need to uninstall it from Claude's MCP configuration." -ForegroundColor Yellow
}
