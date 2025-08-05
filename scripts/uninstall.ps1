<#
.SYNOPSIS
    Uninstalls the System Admin MCP service and cleans up all related components.
    
.DESCRIPTION
    This script performs a complete uninstallation of the System Admin MCP, including:
    - Stopping and removing the Windows service
    - Removing the DXT package if installed
    - Cleaning up installation directory
    - Removing logs and temporary files
    - Cleaning up registry entries
    
.PARAMETER Force
    Suppresses all user prompts and forces uninstallation.
    
.PARAMETER KeepLogs
    Keeps log files in %LOCALAPPDATA%\SystemAdminMCP\Logs
    
.EXAMPLE
    .\uninstall.ps1
    # Interactive uninstallation with prompts
    
.EXAMPLE
    .\uninstall.ps1 -Force -KeepLogs
    # Force uninstallation without prompts, keeping log files
#>

[CmdletBinding()]
param (
    [switch]$Force,
    [switch]$KeepLogs
)

#Requires -RunAsAdministrator
#Requires -Version 5.1

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

# Configuration
$ServiceName = 'SystemAdminMCP'
$DisplayName = 'System Admin MCP Service'
$AppDataPath = "$env:LOCALAPPDATA\SystemAdminMCP"
$LogPath = "$AppDataPath\Logs"
$InstallPath = "${env:ProgramFiles}\System Admin MCP"
$DxtPackageName = 'system-admin-mcp'

function Write-ColorOutput {
    param([string]$Message, [string]$Color = 'White')
    Write-Host $Message -ForegroundColor $Color
}

function Confirm-Uninstall {
    if ($Force) { return $true }
    
    Write-ColorOutput "`n=== System Admin MCP Uninstaller ===" -Color Cyan
    Write-ColorOutput "This will completely remove $DisplayName and all its components."
    Write-ColorOutput "The following will be removed:"
    Write-ColorOutput "- $DisplayName (Windows Service)"
    Write-ColorOutput "- Installation directory: $InstallPath"
    if (-not $KeepLogs) {
        Write-ColorOutput "- Logs and temporary files: $AppDataPath"
    } else {
        Write-ColorOutput "- Logs will be kept at: $LogPath"
    }
    
    $confirmation = Read-Host "`nAre you sure you want to continue? (Y/N)"
    return $confirmation -match '^[Yy]'
}

function Stop-RemoveService {
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    
    if ($null -eq $service) {
        Write-ColorOutput "Service '$ServiceName' is not installed." -Color Yellow
        return
    }
    
    # Stop the service if running
    if ($service.Status -eq 'Running') {
        Write-ColorOutput "Stopping $DisplayName..." -Color Yellow
        try {
            Stop-Service -Name $ServiceName -Force -ErrorAction Stop
            $service.WaitForStatus('Stopped', (New-TimeSpan -Seconds 30))
            Write-ColorOutput "Service stopped successfully." -Color Green
        } catch {
            Write-ColorOutput "Warning: Failed to stop service: $_" -Color Red
            if (-not $Force) {
                $continue = Read-Host "Continue with uninstallation? (Y/N)"
                if ($continue -notmatch '^[Yy]') {
                    exit 1
                }
            }
        }
    }
    
    # Unregister the service
    Write-ColorOutput "Removing service registration..." -Color Yellow
    try {
        $service = Get-WmiObject -Class Win32_Service -Filter "Name='$ServiceName'"
        if ($null -ne $service) {
            $service.Delete()
            Write-ColorOutput "Service registration removed." -Color Green
        }
    } catch {
        Write-ColorOutput "Warning: Failed to remove service registration: $_" -Color Red
        if (-not $Force) {
            $continue = Read-Host "Continue with uninstallation? (Y/N)"
            if ($continue -notmatch '^[Yy]') {
                exit 1
            }
        }
    }
}

function Remove-InstallationFiles {
    if (Test-Path $InstallPath) {
        Write-ColorOutput "Removing installation files from $InstallPath..." -Color Yellow
        try {
            Remove-Item -Path $InstallPath -Recurse -Force -ErrorAction Stop
            Write-ColorOutput "Installation files removed." -Color Green
        } catch {
            Write-ColorOutput "Warning: Failed to remove installation files: $_" -Color Red
        }
    } else {
        Write-ColorOutput "Installation directory not found at $InstallPath" -Color Yellow
    }
}

function Remove-AppData {
    if ($KeepLogs) {
        Write-ColorOutput "Keeping log files as requested." -Color Yellow
        return
    }
    
    if (Test-Path $AppDataPath) {
        Write-ColorOutput "Removing application data from $AppDataPath..." -Color Yellow
        try {
            Remove-Item -Path $AppDataPath -Recurse -Force -ErrorAction Stop
            Write-ColorOutput "Application data removed." -Color Green
        } catch {
            Write-ColorOutput "Warning: Failed to remove application data: $_" -Color Red
        }
    }
}

function Remove-DxtPackage {
    Write-ColorOutput "Attempting to remove DXT package..." -Color Yellow
    
    try {
        # Try to remove using MCP CLI if available
        $mcpCli = Get-Command mcp -ErrorAction SilentlyContinue
        if ($null -ne $mcpCli) {
            & mcp uninstall $DxtPackageName --force
            if ($LASTEXITCODE -eq 0) {
                Write-ColorOutput "DXT package removed successfully." -Color Green
                return
            }
        }
        
        # Fallback to manual DXT package removal
        $dxtPath = "${env:USERPROFILE}\.mcp\packages\$DxtPackageName"
        if (Test-Path $dxtPath) {
            Remove-Item -Path $dxtPath -Recurse -Force -ErrorAction Stop
            Write-ColorOutput "DXT package files removed." -Color Green
        } else {
            Write-ColorOutput "DXT package not found at $dxtPath" -Color Yellow
        }
    } catch {
        Write-ColorOutput "Warning: Failed to remove DXT package: $_" -Color Red
    }
}

function Remove-RegistryEntries {
    $regPaths = @(
        "HKLM:\SYSTEM\CurrentControlSet\Services\EventLog\Application\$ServiceName",
        "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\$ServiceName"
    )
    
    foreach ($regPath in $regPaths) {
        if (Test-Path $regPath) {
            Write-ColorOutput "Removing registry key: $regPath" -Color Yellow
            try {
                Remove-Item -Path $regPath -Recurse -Force -ErrorAction Stop
            } catch {
                Write-ColorOutput "Warning: Failed to remove registry key $regPath : $_" -Color Red
            }
        }
    }
}

# Main execution
try {
    # Verify elevation
    $currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        Write-ColorOutput "This script requires administrator privileges. Please run as administrator." -Color Red
        exit 1
    }
    
    # Confirm uninstallation
    if (-not (Confirm-Uninstall)) {
        Write-ColorOutput "Uninstallation cancelled by user." -Color Yellow
        exit 0
    }
    
    # Stop and remove service
    Stop-RemoveService
    
    # Remove installation files
    Remove-InstallationFiles
    
    # Remove DXT package
    Remove-DxtPackage
    
    # Clean up registry
    Remove-RegistryEntries
    
    # Remove app data (logs, etc.)
    Remove-AppData
    
    Write-ColorOutput "`n=== Uninstallation Complete ===" -Color Green
    Write-ColorOutput "System Admin MCP has been successfully uninstalled." -Color Green
    Write-ColorOutput "You may need to restart your computer to complete the uninstallation." -Color Yellow
    
} catch {
    Write-ColorOutput "`nError during uninstallation: $_" -Color Red
    Write-ColorOutput $_.ScriptStackTrace -Color Red
    exit 1
}
