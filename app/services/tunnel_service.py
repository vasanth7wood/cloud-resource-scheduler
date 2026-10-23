import os
import re
import socket
import logging
import subprocess
import requests
from typing import Optional

logger = logging.getLogger('cloud_scheduler.tunnel')

# Cache for the discovered public base URL and LAN IP
_CACHED_TUNNEL_URL: Optional[str] = None
_CACHED_LAN_IP: Optional[str] = None


def get_lan_ip() -> str:
    """Discovers and caches host LAN IP for local offline Wi-Fi / Hotspot mobile access."""
    global _CACHED_LAN_IP
    if _CACHED_LAN_IP:
        return _CACHED_LAN_IP

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.2)
        s.connect(('10.254.254.254', 1))
        ip = s.getsockname()[0]
        s.close()
        _CACHED_LAN_IP = ip
        return ip
    except Exception:
        try:
            ip = socket.gethostbyname(socket.gethostname())
            _CACHED_LAN_IP = ip
            return ip
        except Exception:
            _CACHED_LAN_IP = '127.0.0.1'
            return '127.0.0.1'


def is_url_healthy(url: str, timeout: float = 1.5) -> bool:
    """Quickly probes a URL to verify it is responsive over HTTP/HTTPS (not 530/502)."""
    if not url:
        return False
    clean = url.rstrip('/')
    try:
        # Probe lightweight health endpoint to avoid recursive application loops
        probe_url = f"{clean}/health"
        resp = requests.get(probe_url, timeout=timeout, allow_redirects=True)
        if resp.status_code in (200, 301, 302, 404, 401, 403):
            return True
        logger.debug(f"URL {url} responded with status {resp.status_code}")
        return False
    except Exception as e:
        logger.debug(f"URL probe failed for {url}: {e}")
        return False


def read_tunnel_url_from_logs() -> Optional[str]:
    """Scans scratch/tunnel.log for active trycloudflare.com URL."""
    candidates = [
        os.path.join(os.getcwd(), 'scratch', 'tunnel.log'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'scratch', 'tunnel.log')
    ]
    url_pattern = re.compile(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com')

    for log_path in candidates:
        if os.path.exists(log_path):
            try:
                with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                # Scan backwards to get the most recent tunnel URL
                for line in reversed(lines):
                    match = url_pattern.search(line)
                    if match:
                        found_url = match.group(0).rstrip('/')
                        return found_url
            except Exception as e:
                logger.warning(f"Could not read tunnel log {log_path}: {e}")

    return None


def sync_base_url_to_env(tunnel_url: str):
    """Persists active WEBHOOK_BASE_URL to .env file so restarts retain it."""
    if not tunnel_url:
        return
    env_path = os.path.join(os.getcwd(), '.env')
    if not os.path.exists(env_path):
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')

    if os.path.exists(env_path):
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if 'WEBHOOK_BASE_URL=' in content:
                content = re.sub(
                    r'WEBHOOK_BASE_URL=.*',
                    f'WEBHOOK_BASE_URL={tunnel_url}',
                    content
                )
            else:
                content = f"WEBHOOK_BASE_URL={tunnel_url}\n" + content

            with open(env_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"[TUNNEL] Synced WEBHOOK_BASE_URL={tunnel_url} into .env")
        except Exception as e:
            logger.warning(f"Failed to write tunnel URL to .env: {e}")


def is_cloudflared_running() -> bool:
    """Checks if a cloudflared process is currently alive."""
    try:
        import psutil
        for proc in psutil.process_iter(['name']):
            if 'cloudflared' in (proc.info['name'] or '').lower():
                return True
    except Exception:
        # Fallback via PowerShell / tasklist
        try:
            res = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq cloudflared.exe'],
                capture_output=True, text=True, timeout=3
            )
            return 'cloudflared.exe' in res.stdout
        except Exception:
            pass
    return False


def kill_stale_cloudflared():
    """Terminates any existing cloudflared processes."""
    try:
        if os.name == 'nt':
            subprocess.run(['taskkill', '/F', '/IM', 'cloudflared.exe'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run(['pkill', '-f', 'cloudflared'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def ensure_tunnel_process(port: int = 5000) -> Optional[str]:
    """
    Ensures Cloudflare Tunnel is running and healthy. If disconnected or stale,
    terminates it and spawns a fresh bin/cloudflared.exe tunnel session.
    """
    global _CACHED_TUNNEL_URL
    os.makedirs('scratch', exist_ok=True)
    tunnel_log = os.path.join('scratch', 'tunnel.log')

    # If already running and URL found in logs, keep using it for maximum stability
    if is_cloudflared_running():
        logged_url = read_tunnel_url_from_logs()
        if logged_url:
            _CACHED_TUNNEL_URL = logged_url
            os.environ['WEBHOOK_BASE_URL'] = logged_url
            sync_base_url_to_env(logged_url)
            return logged_url

    # Cloudflared executable path
    bin_candidates = [
        os.path.join(os.getcwd(), 'bin', 'cloudflared.exe'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'bin', 'cloudflared.exe')
    ]
    cloudflared_bin = None
    for b in bin_candidates:
        if os.path.exists(b):
            cloudflared_bin = b
            break

    if not cloudflared_bin:
        logger.warning("[TUNNEL] cloudflared.exe binary not found in bin/ directory.")
        return None

    try:
        # Clear old tunnel log so we don't accidentally read an expired URL
        try:
            with open(tunnel_log, 'w', encoding='utf-8') as f:
                f.write('')
        except Exception:
            pass

        logger.info(f"[TUNNEL] Launching Cloudflare Tunnel on port {port}...")
        cmd = [
            cloudflared_bin,
            'tunnel',
            '--protocol', 'http2',
            '--url', f'http://127.0.0.1:{port}',
            '--logfile', tunnel_log
        ]
        # Start in background detached
        creationflags = 0
        if os.name == 'nt':
            creationflags = subprocess.CREATE_NO_WINDOW | getattr(subprocess, 'DETACHED_PROCESS', 0x00000008)

        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags
        )

        # Wait for the tunnel log to output the live URL (up to 12 seconds)
        import time
        start_t = time.time()
        while time.time() - start_t < 12.0:
            time.sleep(1.0)
            url = read_tunnel_url_from_logs()
            if url:
                _CACHED_TUNNEL_URL = url
                os.environ['WEBHOOK_BASE_URL'] = url
                sync_base_url_to_env(url)
                logger.info(f"[TUNNEL READY] Live Phone Action Link: {url}")
                return url

    except Exception as e:
        logger.error(f"[TUNNEL ERROR] Failed to start cloudflared: {e}")

    return None


def get_public_base_url(app=None) -> str:
    """
    Returns the most reachable base URL for mobile devices immediately (sub-millisecond):
    1. Live active tunnel URL discovered from scratch/tunnel.log when cloudflared is running
    2. WEBHOOK_BASE_URL from app.config, current_app, or os.environ
    3. Host LAN IP (http://<lan_ip>:5000) for local Wi-Fi / Hotspot mobile access
    4. http://127.0.0.1:5000 fallback
    """
    global _CACHED_TUNNEL_URL

    # 1. Check live tunnel log first if cloudflared is running or log has fresh URL
    if is_cloudflared_running():
        logged_url = read_tunnel_url_from_logs()
        if logged_url and 'remember-refused-date-exercises' not in logged_url:
            _CACHED_TUNNEL_URL = logged_url
            os.environ['WEBHOOK_BASE_URL'] = logged_url
            sync_base_url_to_env(logged_url)
            if app and hasattr(app, 'config'):
                app.config['WEBHOOK_BASE_URL'] = logged_url
            return logged_url

    # 2. In-memory cached URL if already set and healthy
    if _CACHED_TUNNEL_URL:
        return _CACHED_TUNNEL_URL

    # 3. Check environment / app config URL
    configured = None
    if app and hasattr(app, 'config'):
        configured = app.config.get('WEBHOOK_BASE_URL')
    if not configured:
        try:
            from flask import current_app
            if current_app:
                configured = current_app.config.get('WEBHOOK_BASE_URL')
        except Exception:
            pass
    if not configured:
        configured = os.environ.get('WEBHOOK_BASE_URL')

    if not configured or 'localhost' in configured or '127.0.0.1' in configured:
        render_ext = os.environ.get('RENDER_EXTERNAL_URL')
        if render_ext:
            configured = render_ext.rstrip('/')

    if configured:
        clean = configured.strip().rstrip('/')
        if 'localhost' not in clean and '127.0.0.1' not in clean and 'remember-refused-date-exercises' not in clean:
            _CACHED_TUNNEL_URL = clean
            return clean

    # 4. Fallback to LAN IP so phone on local Wi-Fi / Hotspot still works
    lan_ip = get_lan_ip()
    port = int(os.environ.get('PORT', 5000))
    if lan_ip and lan_ip != '127.0.0.1':
        return f"http://{lan_ip}:{port}"

    return f"http://127.0.0.1:{port}"
