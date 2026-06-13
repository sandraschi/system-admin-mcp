@echo off
REM Hard restart system-admin-mcp
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0web_sota\stop.ps1"
if errorlevel 1 (
    echo stop failed
    pause
    exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0web_sota\start.ps1"
pause

