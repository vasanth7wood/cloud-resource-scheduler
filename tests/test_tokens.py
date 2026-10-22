import pytest
import time
from app.services.token_utils import (
    generate_action_token, 
    verify_action_token, 
    mark_token_consumed
)

def test_generate_and_verify_valid_stop_token():
    """Verifies that a newly generated 'stop' token validates successfully."""
    secret = "test-secret-key-12345"
    token = generate_action_token(
        instance_id="i-0a1b2c3d4e5f6001",
        action="stop",
        ttl_seconds=900,
        secret_key=secret
    )

    assert isinstance(token, str)
    assert '.' in token

    is_valid, payload, error = verify_action_token(token, secret_key=secret, enforce_single_use=False)
    assert is_valid is True
    assert error is None
    assert payload is not None
    assert payload['instance_id'] == "i-0a1b2c3d4e5f6001"
    assert payload['action'] == "stop"
    assert payload['expires_at'] > time.time()

def test_generate_and_verify_valid_extend_token():
    """Verifies that an 'extend' token carries the correct extension duration."""
    secret = "test-secret-key-12345"
    token = generate_action_token(
        instance_id="i-0b2c3d4e5f6a7002",
        action="extend",
        ttl_seconds=600,
        extend_minutes=120,
        secret_key=secret
    )

    is_valid, payload, error = verify_action_token(token, secret_key=secret, enforce_single_use=False)
    assert is_valid is True
    assert payload['action'] == "extend"
    assert payload['extend_minutes'] == 120

def test_token_tamper_detection_in_payload():
    """Verifies that modifying a single character in the payload invalidates HMAC signature."""
    secret = "test-secret-key-12345"
    token = generate_action_token("i-0a1b2c3d4e5f6001", "stop", ttl_seconds=900, secret_key=secret)
    parts = token.split('.')

    # Tamper with the first character of the payload
    tampered_payload = ('X' if parts[0][0] != 'X' else 'Y') + parts[0][1:]
    tampered_token = f"{tampered_payload}.{parts[1]}"

    is_valid, payload, error = verify_action_token(tampered_token, secret_key=secret)
    assert is_valid is False
    assert "signature validation failed" in error.lower() or "tampered" in error.lower()

def test_token_tamper_detection_in_signature():
    """Verifies that altering the signature string fails verification."""
    secret = "test-secret-key-12345"
    token = generate_action_token("i-0a1b2c3d4e5f6001", "stop", ttl_seconds=900, secret_key=secret)
    parts = token.split('.')

    # Tamper with the signature
    tampered_sig = parts[1][:-1] + ('A' if parts[1][-1] != 'A' else 'B')
    tampered_token = f"{parts[0]}.{tampered_sig}"

    is_valid, payload, error = verify_action_token(tampered_token, secret_key=secret)
    assert is_valid is False
    assert "signature validation failed" in error.lower()

def test_token_ttl_expiration():
    """Verifies that a token with 0 or negative TTL is immediately rejected as expired."""
    secret = "test-secret-key-12345"
    # Generate token with negative TTL (already expired)
    token = generate_action_token("i-0a1b2c3d4e5f6001", "stop", ttl_seconds=-10, secret_key=secret)

    is_valid, payload, error = verify_action_token(token, secret_key=secret, enforce_single_use=False)
    assert is_valid is False
    assert "expired" in error.lower()
    assert payload is not None

def test_malformed_token():
    """Verifies that garbage strings and incomplete tokens are safely rejected."""
    is_valid, payload, error = verify_action_token("not-a-valid-token-format")
    assert is_valid is False
    assert "malformed" in error.lower()

    is_valid2, payload2, error2 = verify_action_token("")
    assert is_valid2 is False

def test_replay_protection():
    """Verifies that mark_token_consumed prevents executing the token a second time."""
    secret = "test-secret-key-12345"
    token = generate_action_token("i-replay-test-01", "stop", ttl_seconds=900, secret_key=secret)

    # First check: valid
    is_valid, payload, error = verify_action_token(token, secret_key=secret, enforce_single_use=True)
    assert is_valid is True

    # Mark as consumed
    mark_token_consumed(token)

    # Second check: must fail
    is_valid2, payload2, error2 = verify_action_token(token, secret_key=secret, enforce_single_use=True)
    assert is_valid2 is False
    assert "already been executed" in error2.lower() or "replay" in error2.lower()
