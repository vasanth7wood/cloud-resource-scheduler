import hmac
import hashlib
import base64
import json
import time
import os
import secrets
from typing import Tuple, Dict, Any, Optional

def _get_secret_key(secret_key: Optional[str] = None) -> str:
    """Retrieves secret key from parameter, environment, or default fallback."""
    if secret_key:
        return secret_key
    return os.environ.get('SECRET_KEY', 'dev-cloud-scheduler-super-secret-key-2026')

# In-memory consumed token blacklist to guarantee single-use idempotent execution
_CONSUMED_TOKENS = set()

def generate_action_token(
    instance_id: str, 
    action: str, 
    ttl_seconds: int = 900, 
    extend_minutes: int = 60,
    secret_key: Optional[str] = None
) -> str:
    """
    Generates a cryptographically signed, tamper-proof, time-bound (TTL) action token.
    Uses HMAC-SHA256 with URL-safe base64 encoding.
    
    :param instance_id: AWS EC2 instance identifier (e.g. i-0a1b2c3d4e5f6001)
    :param action: Action to perform ('stop' or 'extend')
    :param ttl_seconds: Time to live in seconds (default: 900s = 15 minutes)
    :param extend_minutes: Lease duration extension in minutes
    :param secret_key: Optional override for signing key
    :return: URL-safe token string in format '<payload_b64>.<signature_b64>'
    """
    key = _get_secret_key(secret_key)
    now = int(time.time())
    
    payload = {
        'instance_id': instance_id.strip(),
        'action': action.strip().lower(),
        'issued_at': now,
        'expires_at': now + int(ttl_seconds),
        'extend_minutes': int(extend_minutes),
        'nonce': secrets.token_hex(8)
    }
    
    # Serialize JSON payload and base64-encode
    payload_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode('utf-8')).decode('utf-8').rstrip('=')
    
    # Compute HMAC-SHA256 signature
    sig = hmac.new(key.encode('utf-8'), payload_b64.encode('utf-8'), hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).decode('utf-8').rstrip('=')
    
    return f"{payload_b64}.{sig_b64}"

def verify_action_token(
    token: str, 
    secret_key: Optional[str] = None,
    enforce_single_use: bool = True
) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Validates token integrity, HMAC-SHA256 signature, expiration TTL, and replay status.
    
    :param token: The action token string to verify
    :param secret_key: Optional secret key override
    :param enforce_single_use: Whether to prevent reusing the same token twice
    :return: Tuple of (is_valid: bool, payload: dict | None, error_message: str | None)
    """
    if not token or not isinstance(token, str):
        return False, None, "Token missing or invalid format."
    
    parts = token.strip().split('.')
    if len(parts) != 2:
        return False, None, "Malformed token structure. Expected two segments."
    
    payload_b64, provided_sig_b64 = parts[0], parts[1]
    key = _get_secret_key(secret_key)
    
    # Verify HMAC-SHA256 signature
    expected_sig = hmac.new(key.encode('utf-8'), payload_b64.encode('utf-8'), hashlib.sha256).digest()
    expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode('utf-8').rstrip('=')
    
    if not hmac.compare_digest(expected_sig_b64, provided_sig_b64):
        return False, None, "Cryptographic signature validation failed. Token has been tampered with."
    
    # Decode and deserialize payload
    try:
        # Add padding if needed
        padding = '=' * (-len(payload_b64) % 4)
        payload_bytes = base64.urlsafe_b64decode(payload_b64 + padding)
        payload = json.loads(payload_bytes.decode('utf-8'))
    except Exception as e:
        return False, None, f"Failed to deserialize token payload: {str(e)}"
    
    # Check expiration (TTL)
    now = int(time.time())
    expires_at = payload.get('expires_at', 0)
    if now > expires_at:
        remaining_seconds = now - expires_at
        return False, payload, f"Token expired {remaining_seconds} seconds ago (TTL exceeded)."
    
    # Check action validity
    action = payload.get('action')
    if action not in ('stop', 'extend'):
        return False, payload, f"Unsupported action '{action}' in token payload."
    
    # Check single-use replay protection
    if enforce_single_use:
        token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
        if token_hash in _CONSUMED_TOKENS:
            return False, payload, "Token has already been executed. Replay attempt blocked."
    
    return True, payload, None

def mark_token_consumed(token: str):
    """Marks a token as consumed to prevent replay attacks."""
    token_hash = hashlib.sha256(token.strip().encode('utf-8')).hexdigest()
    _CONSUMED_TOKENS.add(token_hash)
