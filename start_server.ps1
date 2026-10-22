# PowerShell launcher for Cloud Resource Scheduling & FinOps Platform
Write-Host "===========================================================================" -ForegroundColor Cyan
Write-Host " Cloud Resource Scheduling System - Host Port 5000 Deployment" -ForegroundColor Green
Write-Host " Supports: Localhost, Offline Wi-Fi LAN / Mobile Hotspot & Cloudflare Tunnel" -ForegroundColor Yellow
Write-Host "===========================================================================" -ForegroundColor Cyan

# Check Python availability
try {
    $pythonVer = python --version 2>&1
    Write-Host "[*] Python Runtime: $pythonVer" -ForegroundColor Gray
} catch {
    Write-Error "Python is not detected. Please ensure Python is installed."
    Exit 1
}

# Run the host server
Write-Host "[*] Binding to 0.0.0.0:5000 (All IPv4 network interfaces)..." -ForegroundColor White
python run.py
