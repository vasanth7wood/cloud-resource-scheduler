import os
import sys
from app import create_app
from app.config import Config
from app.services.tunnel_service import ensure_tunnel_process, get_public_base_url, get_lan_ip

app = create_app(Config)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 't')
    lan_ip = get_lan_ip()

    # Automatically ensure Cloudflare Tunnel is running and discover the live HTTPS URL
    live_tunnel = ensure_tunnel_process(port=port)
    base_url = get_public_base_url(app=app).rstrip('/')
    app.config['WEBHOOK_BASE_URL'] = base_url
    os.environ['WEBHOOK_BASE_URL'] = base_url

    print("\n" + "="*75)
    print("[*] [CLOUD RESOURCE SCHEDULER & FINOPS GOVERNANCE SYSTEM]")
    print("="*75)
    print(f"[*] Local Host (Laptop):     http://127.0.0.1:{port}/quick-login")
    print(f"[*] Offline LAN / Wi-Fi:     http://{lan_ip}:{port}/quick-login (Same Wi-Fi/Hotspot)")
    if 'localhost' not in base_url and '127.0.0.1' not in base_url:
        print(f"[*] Online Phone Link:       {base_url}/quick-login (Anywhere on 4G/5G Mobile)")
        print(f"[*] Mobile Buzzer Link:      {base_url}/buzzer (Touch from lockscreen or notification)")
    print(f"[*] API & Webhook Root:      {base_url}/webhook/action")
    print(f"[*] Cloud Engine:            {'Simulated AWS EC2 & Azure (Mock Driver)' if Config.USE_MOCK_AWS else 'Live Cloud SDK'}")
    print(f"[*] APScheduler Audit:       Every {Config.SCAN_INTERVAL_SECONDS} seconds")
    print(f"[*] Grace Period:            {Config.GRACE_PERIOD_MINUTES} minutes fallback auto-shutdown")
    print(f"[*] Action Token TTL:        {Config.ACTION_TOKEN_TTL_SECONDS} seconds (HMAC-SHA256)")
    print("-" * 75)
    print("[*] INSTANT ACCESS CREDENTIALS:")
    print("    - 1-Click Login:         Navigate directly to /quick-login")
    print("    - Admin Email:           vasanthkumar20212021@gmail.com / password123")
    print("="*75 + "\n")

    # use_reloader=False prevents duplicate APScheduler background instances; threaded=True enables high-concurrency response
    app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False, threaded=True)
