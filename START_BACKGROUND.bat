@echo off
title Launch Cloud Resource Scheduler (Silent Background Host)
color 0B

echo ===========================================================================
echo  Launching Cloud Resource Scheduler in Permanent Background Mode
echo ===========================================================================
echo.

cd /d "%~dp0"

:: Start python process detached in background
echo [*] Spawning detached server process...
powershell -Command "Start-Process python -ArgumentList 'run.py' -WindowStyle Hidden"

:: Wait 4 seconds for server & tunnel to start
echo [*] Initializing Cloudflare Tunnel and discovery service...
timeout /t 4 /nobreak >nul

:: Automatically open default browser to 1-Click Login
echo [*] Opening Web Dashboard in your browser...
start http://127.0.0.1:5000/quick-login

echo.
echo ===========================================================================
echo  [SUCCESS] Server and Cloudflare Tunnel are now running in the background!
echo  You can safely CLOSE this window and CLOSE Antigravity IDE.
echo  The scheduler, alerts, and phone links will continue running 24/7!
echo.
echo  To STOP the system anytime, double-click STOP_SYSTEM.bat
echo ===========================================================================
echo.
pause
