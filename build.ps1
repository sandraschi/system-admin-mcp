<#
.SYNOPSIS
    Build script for System Admin MCP
.DESCRIPTION
    This script builds the System Admin MCP package, including DXT packaging.
    It handles dependency installation, testing, and creating the final DXT package.
#>

param (
    [switch]$NoTest,
    [switch]$NoClean,
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# Project information
$ProjectName = "system-admin-mcp"
$Version = "0.1.0"
$BuildDir = "dist"
$DxtDir = "$BuildDir\$ProjectName.dxt"

# Print header
Write-Host "Building $ProjectName v$Version" -ForegroundColor Cyan
Write-Host "-" * 80

# Clean previous builds
if (-not $NoClean) {
    Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
    Remove-Item -Path $BuildDir -Recurse -ErrorAction SilentlyContinue
    Remove-Item -Path "*.egg-info" -Recurse -ErrorAction SilentlyContinue
    Remove-Item -Path "build" -Recurse -ErrorAction SilentlyContinue
}

# Create build directories
$null = New-Item -Path $DxtDir -ItemType Directory -Force
$null = New-Item -Path "$DxtDir\server" -ItemType Directory -Force

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
& $Python -m pip install --upgrade pip
& $Python -m pip install -e .[dev]

# Run tests if not skipped
if (-not $NoTest) {
    Write-Host "Running tests..." -ForegroundColor Yellow
    & $Python -m pytest -v --cov=system_admin_mcp --cov-report=term-missing
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Tests failed. Aborting build." -ForegroundColor Red
        exit 1
    }
}

# Build the package
Write-Host "Building package..." -ForegroundColor Yellow
& $Python -m build --outdir $BuildDir
if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed." -ForegroundColor Red
    exit 1
}

# Prepare DXT package
Write-Host "Preparing DXT package..." -ForegroundColor Yellow

# Copy required files to DXT directory
$filesToCopy = @(
    "manifest.json",
    "README.md",
    "LICENSE"
)

foreach ($file in $filesToCopy) {
    if (Test-Path $file) {
        Copy-Item -Path $file -Destination $DxtDir\ -Force
    }
}

# Copy built package to DXT server directory
$whlFile = Get-ChildItem -Path "$BuildDir\*.whl" | Select-Object -First 1
if ($whlFile) {
    Copy-Item -Path $whlFile.FullName -Destination "$DxtDir\server\" -Force
}

# Create requirements.txt
@"
# System Admin MCP requirements
pywin32>=300
pywin32-ctypes>=0.2.0
"@ | Out-File -FilePath "$DxtDir\requirements.txt" -Encoding utf8

# Create a simple launcher script
@"
@echo off
python -m system_admin_mcp.elevated_service.service %*
"@ | Out-File -FilePath "$DxtDir\server\start_elevated_service.cmd" -Encoding ascii

# Create ZIP archive
$zipPath = "$BuildDir\$ProjectName-$Version.dxt"
if (Test-Path $zipPath) {
    Remove-Item -Path $zipPath -Force
}

Write-Host "Creating DXT package: $zipPath" -ForegroundColor Yellow
Add-Type -Assembly "System.IO.Compression.FileSystem"
[IO.Compression.ZipFile]::CreateFromDirectory($DxtDir, $zipPath)

# Clean up temp DXT directory
Remove-Item -Path $DxtDir -Recurse -Force

Write-Host "\nBuild completed successfully!" -ForegroundColor Green
Write-Host "DXT package created: $((Get-Item $zipPath).FullName)" -ForegroundColor Green
