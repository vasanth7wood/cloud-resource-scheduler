@echo off
title Cloud Resource Scheduling & FinOps Platform - Offline & Online Host
color 0A

echo ===========================================================================
echo  Starting Cloud Resource Scheduling & Governance Platform
echo  Configured for Host Port 5000 (Local Offline & Remote Mobile Support)
echo ===========================================================================
echo.

:: Ensure python is in path
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python was not found in PATH! Please install Python 3.11+.
    pause
    exit /b 1
)

:: Launch application
echo [*] Launching Flask server on 0.0.0.0:5000...
echo [*] Local Host URL:        http://127.0.0.1:5000/quick-login
echo [*] Offline Phone Access:  Connect phone to same Wi-Fi/Hotspot
echo.
python run.py

pause
