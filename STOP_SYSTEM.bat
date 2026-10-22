@echo off
title Stop Cloud Resource Scheduler
color 0C

echo ===========================================================================
echo  Stopping Cloud Resource Scheduler and Cloudflare Tunnel...
echo ===========================================================================
echo.

powershell -Command "Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }"
powershell -Command "Stop-Process -Name cloudflared -Force -ErrorAction SilentlyContinue"

echo [*] Port 5000 server stopped.
echo [*] Cloudflare tunnel stopped.
echo.
echo [DONE] The system has been cleanly terminated.
echo.
timeout /t 3
