<#
.SYNOPSIS
    Test script for System Admin MCP
.DESCRIPTION
    This script runs tests for the System Admin MCP package,
    including both unit tests and integration tests.
#>

param (
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# Print header
Write-Host "Testing System Admin MCP" -ForegroundColor Cyan
Write-Host "-" * 80

# Run unit tests
Write-Host "Running unit tests..." -ForegroundColor Yellow
& $Python -m pytest -v tests/
if ($LASTEXITCODE -ne 0) {
    Write-Host "Unit tests failed." -ForegroundColor Red
    exit 1
}

# Run integration tests if service is running
Write-Host "`nRunning integration tests..." -ForegroundColor Yellow

# Test file owner functionality
try {
    $testFile = [System.IO.Path]::GetTempFileName()
    Write-Host "Testing file owner functionality with: $testFile"
    
    $result = & $Python -c "import system_admin_mcp; print(system_admin_mcp.get_file_owner('$testFile'))"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "File owner test passed!" -ForegroundColor Green
        Write-Host "Result: $result"
    } else {
        Write-Host "File owner test failed." -ForegroundColor Red
        exit 1
    }
} finally {
    if (Test-Path $testFile) {
        Remove-Item $testFile -Force -ErrorAction SilentlyContinue
    }
}

# Test volume listing
Write-Host "`nTesting volume listing..." -ForegroundColor Yellow
$result = & $Python -c "import system_admin_mcp; print(system_admin_mcp.list_volumes())"
if ($LASTEXITCODE -eq 0) {
    Write-Host "Volume listing test passed!" -ForegroundColor Green
    Write-Host "Result: $result"
} else {
    Write-Host "Volume listing test failed." -ForegroundColor Red
    exit 1
}

Write-Host "`nAll tests completed successfully!" -ForegroundColor Green
