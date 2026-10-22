import pytest
from datetime import datetime, timezone
from app.models.models import db, CloudResource, AuditTrail
from app.services.token_utils import generate_action_token

def test_webhook_successful_stop_action(client, app):
    """
    E2E test: Verifies that clicking a single-click Stop webhook with a valid HMAC
    returns status 200, renders confirmation, and powers down the instance.
    """
    secret = app.config['SECRET_KEY']
    inst_id = 'i-test001running'

    # Generate valid signed stop token
    token = generate_action_token(instance_id=inst_id, action='stop', ttl_seconds=900, secret_key=secret)

    # Perform GET request (simulating email / WhatsApp link click)
    response = client.get(f"/webhook/action?token={token}&action=stop")
    assert response.status_code == 200
    assert b"powered down" in response.data or b"successfully" in response.data

    # Verify instance state transitioned to stopped in database
    with app.app_context():
        res = db.session.query(CloudResource).filter_by(instance_id=inst_id).first()
        assert res is not None
        assert res.state == 'stopped'

        # Verify audit trail record
        audit = db.session.query(AuditTrail).filter_by(action_taken='STOP').first()
        assert audit is not None
        assert "WEBHOOK_HMAC" in audit.triggered_by

def test_webhook_successful_extend_action_json(client, app):
    """
    E2E test: Verifies JSON API execution of Extend lease webhook.
    """
    secret = app.config['SECRET_KEY']
    inst_id = 'i-test001running'

    # Generate valid extend token
    token = generate_action_token(instance_id=inst_id, action='extend', ttl_seconds=900, extend_minutes=60, secret_key=secret)

    response = client.post(
        "/webhook/action",
        json={'token': token, 'action': 'extend'},
        headers={'Accept': 'application/json'}
    )
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['success'] is True
    assert json_data['action'] == 'EXTEND'

    with app.app_context():
        res = db.session.query(CloudResource).filter_by(instance_id=inst_id).first()
        assert res.lease_expires_at is not None
        assert res.is_lease_active is True

def test_webhook_rejects_tampered_token(client, app):
    """Verifies that tampering with the token signature or payload returns 400 error."""
    secret = app.config['SECRET_KEY']
    token = generate_action_token('i-test001running', 'stop', ttl_seconds=900, secret_key=secret)
    parts = token.split('.')

    # Tamper with signature
    tampered_sig = ('X' if parts[1][0] != 'X' else 'Y') + parts[1][1:]
    bad_token = f"{parts[0]}.{tampered_sig}"

    response = client.get(f"/webhook/action?token={bad_token}&action=stop")
    assert response.status_code == 400
    assert b"Authorization Failed" in response.data or b"tampered" in response.data.lower()

    # Instance should remain running
    with app.app_context():
        res = db.session.query(CloudResource).filter_by(instance_id='i-test001running').first()
        assert res.state == 'running'

def test_webhook_rejects_expired_token(client, app):
    """Verifies that an expired token returns HTTP 400."""
    secret = app.config['SECRET_KEY']
    # Token with negative TTL (already expired)
    expired_token = generate_action_token('i-test001running', 'stop', ttl_seconds=-10, secret_key=secret)

    response = client.get(f"/webhook/action?token={expired_token}&action=stop")
    assert response.status_code == 400
    assert b"expired" in response.data.lower()

def test_webhook_prevents_replay_attack(client, app):
    """Verifies that re-executing an already consumed webhook token is rejected."""
    secret = app.config['SECRET_KEY']
    token = generate_action_token('i-test001running', 'stop', ttl_seconds=900, secret_key=secret)

    # First execution succeeds
    resp1 = client.get(f"/webhook/action?token={token}&action=stop")
    assert resp1.status_code == 200

    # Second execution of the exact same token must be rejected
    resp2 = client.get(f"/webhook/action?token={token}&action=stop")
    assert resp2.status_code == 400
    assert b"already been executed" in resp2.data.lower() or b"replay" in resp2.data.lower()
