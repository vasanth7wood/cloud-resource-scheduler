@echo off
title Cloud Resource Scheduler - Enterprise FinOps Platform
color 0A

echo ===========================================================================
echo  Starting Cloud Resource Scheduling & FinOps Governance Platform
echo  Configured to run INDEPENDENT of IDE (Keeps running after IDE is closed)
echo ===========================================================================
echo.

cd /d "%~dp0"

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3 was not found in PATH!
    pause
    exit /b 1
)

echo [*] Launching Python Flask Server and Cloudflare Tunnel...
echo [*] Local Host URL:   http://127.0.0.1:5000/quick-login
echo [*] The live public mobile URL will be displayed below in a few seconds...
echo.

:: Launch the main application
python run.py

pause
