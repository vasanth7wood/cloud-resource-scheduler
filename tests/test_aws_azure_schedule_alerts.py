import pytest
from datetime import datetime, timezone, timedelta
from app.models.models import db, CloudResource, Schedule, AlertLog, AuditTrail
from app.services.scheduler_service import SchedulerService
from app.services.token_utils import generate_action_token

def test_azure_and_aws_schedule_breach_and_phone_stop_webhook(app, client):
    """
    Tests both AWS and Azure resources:
    1. Running beyond allocated time window or max runtime.
    2. Scheduler audit detects breach and dispatches multi-channel alerts (SMS & Email).
    3. User clicks the Stop link on phone (webhook/action) -> stops the instance.
    """
    with app.app_context():
        session = db.session

        # Add an Azure Virtual Machine running for 5 hours with a 2-hour max runtime
        azure_res = CloudResource(
            instance_id='vm-azure-api-gateway',
            instance_name='Azure-API-Gateway-Prod',
            provider='Azure',
            region='eastus',
            state='running',
            instance_type='Standard_D2s_v3',
            public_ip='20.124.65.110',
            private_ip='172.16.1.10',
            launch_time=datetime.now(timezone.utc) - timedelta(hours=5)
        )
        session.add(azure_res)
        session.flush()

        # Schedule: Max runtime 2.0 hours (exceeded by 3 hours)
        azure_sched = Schedule(
            resource_id=azure_res.id,
            start_time='09:00',
            end_time='18:00',
            max_runtime_hours=2.0,
            days_of_week='MON,TUE,WED,THU,FRI,SAT,SUN',
            is_active=True
        )
        session.add(azure_sched)
        session.commit()

        # Run scheduler audit
        scheduler = SchedulerService(config=app.config, app=app)
        results = scheduler.audit_and_enforce_policies()

        assert results['violations_detected'] >= 1
        assert results['alerts_dispatched'] >= 1

        # Verify Azure instance has alert timestamp set
        refreshed_azure = session.query(CloudResource).filter_by(instance_id='vm-azure-api-gateway').first()
        assert refreshed_azure.alert_sent_at is not None

        # Verify AlertLog created for Azure resource
        alert_logs = session.query(AlertLog).filter_by(resource_id=azure_res.id).all()
        assert len(alert_logs) > 0

    # User clicks STOP link on phone
    secret = app.config['SECRET_KEY']
    stop_token = generate_action_token('vm-azure-api-gateway', 'stop', ttl_seconds=900, secret_key=secret)
    
    resp = client.get(f"/webhook/action?token={stop_token}&action=stop")
    assert resp.status_code == 200
    assert b"powered down" in resp.data.lower() or b"stopped" in resp.data.lower()

    # Verify Azure instance is now STOPPED in database
    with app.app_context():
        res = db.session.query(CloudResource).filter_by(instance_id='vm-azure-api-gateway').first()
        assert res.state == 'stopped'
        assert res.launch_time is None
        assert res.alert_sent_at is None

        # Verify audit trail
        audit = db.session.query(AuditTrail).filter_by(resource_id=res.id, action_taken='STOP').first()
        assert audit is not None
        assert "Azure" in audit.details


def test_inbound_sms_reply_stop_powers_down_resource(app, client):
    """
    Tests mobile phone SMS control:
    When user receives SMS alert on their phone and replies 'STOP' to Twilio SMS,
    the server receives the webhook and powers down the instance immediately.
    """
    with app.app_context():
        session = db.session

        # Seed running Azure VM
        azure_res = CloudResource(
            instance_id='vm-az-worker-1',
            instance_name='Azure-Worker-Batch',
            provider='Azure',
            region='eastus',
            state='running',
            launch_time=datetime.now(timezone.utc) - timedelta(hours=4),
            alert_sent_at=datetime.now(timezone.utc) - timedelta(minutes=5)
        )
        session.add(azure_res)
        session.commit()

    # User replies "STOP" via SMS from phone
    resp = client.post(
        '/webhook/twilio/sms',
        data={'Body': 'STOP', 'From': '+919025903459'}
    )
    assert resp.status_code == 200
    assert b"STOPPED" in resp.data
    assert b"Azure-Worker-Batch" in resp.data

    with app.app_context():
        res = db.session.query(CloudResource).filter_by(instance_id='vm-az-worker-1').first()
        assert res.state == 'stopped'

        audit = db.session.query(AuditTrail).filter_by(resource_id=res.id, action_taken='STOP').first()
        assert audit is not None
        assert "PHONE_SMS" in audit.triggered_by


def test_inbound_sms_reply_stop_specific_instance(app, client):
    """
    Tests mobile phone SMS replying 'STOP vm-azure-api-gateway':
    Only the specified instance is powered down.
    """
    with app.app_context():
        session = db.session
        r1 = CloudResource(
            instance_id='i-aws-app1',
            instance_name='AWS-App-1',
            provider='AWS',
            region='us-east-1',
            state='running',
            launch_time=datetime.now(timezone.utc) - timedelta(hours=2)
        )
        r2 = CloudResource(
            instance_id='vm-azure-app2',
            instance_name='Azure-App-2',
            provider='Azure',
            region='eastus',
            state='running',
            launch_time=datetime.now(timezone.utc) - timedelta(hours=3)
        )
        session.add_all([r1, r2])
        session.commit()

    # User replies "STOP vm-azure-app2" from phone
    resp = client.post(
        '/webhook/sms',
        data={'Body': 'STOP vm-azure-app2', 'From': '+919025903459'}
    )
    assert resp.status_code == 200
    assert b"Azure-App-2" in resp.data

    with app.app_context():
        az = db.session.query(CloudResource).filter_by(instance_id='vm-azure-app2').first()
        assert az.state == 'stopped'
        aws = db.session.query(CloudResource).filter_by(instance_id='i-aws-app1').first()
        assert aws.state == 'running'


def test_inbound_sms_extend_lease(app, client):
    """
    Tests mobile phone SMS replying 'EXTEND':
    Operating lease is extended by 60 minutes.
    """
    with app.app_context():
        session = db.session
        res = CloudResource(
            instance_id='i-aws-extendable',
            instance_name='AWS-Extendable-Job',
            provider='AWS',
            region='us-east-1',
            state='running',
            alert_sent_at=datetime.now(timezone.utc) - timedelta(minutes=5)
        )
        session.add(res)
        session.commit()

    # User replies "EXTEND"
    resp = client.post(
        '/webhook/twilio/sms',
        data={'Body': 'EXTEND', 'From': '+919025903459'}
    )
    assert resp.status_code == 200
    assert b"LEASE EXTENDED" in resp.data or b"extended" in resp.data.lower()

    with app.app_context():
        refreshed = db.session.query(CloudResource).filter_by(instance_id='i-aws-extendable').first()
        assert refreshed.is_lease_active is True
        assert refreshed.alert_sent_at is None


def test_custom_per_instance_alert_message_and_recipient_routing(app, client):
    """
    Tests:
    1. Saving a tailored alert message and separate recipient phone/email for a specific instance.
    2. Reading back the custom alert configuration.
    3. Triggering alert dispatches the custom instance note and routes to the dedicated recipient.
    """
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_email'] = 'admin@cloudops.internal'
        sess['user_role'] = 'Admin'

    with app.app_context():
        res = CloudResource(
            instance_id='i-tailored-msg-test',
            instance_name='Tailored-Worker-1',
            provider='AWS',
            region='us-east-1',
            state='running'
        )
        db.session.add(res)
        db.session.commit()
        res_id = res.id

    # 1. Update alert config
    payload = {
        'custom_alert_message': 'URGENT: Tailored message for QA worker - stop immediately!',
        'alert_email': 'custom-qa@company.com',
        'alert_phone': '+919876543210',
        'alert_whatsapp': 'whatsapp:+919876543210',
        'alert_topic': 'qa_team_alerts'
    }
    put_res = client.put(f'/api/resources/{res_id}/alert-config', json=payload)
    assert put_res.status_code == 200
    data = put_res.get_json()
    assert data['success'] is True
    assert data['config']['custom_alert_message'] == payload['custom_alert_message']

    # 2. Get alert config
    get_res = client.get(f'/api/resources/{res_id}/alert-config')
    assert get_res.status_code == 200
    cfg = get_res.get_json()['config']
    assert cfg['alert_email'] == 'custom-qa@company.com'
    assert cfg['alert_phone'] == '+919876543210'

    # 3. Trigger alert with custom message
    trigger_res = client.post(f'/api/resources/{res_id}/trigger-alert', json={})
    assert trigger_res.status_code == 200
    trig_data = trigger_res.get_json()
    assert trig_data['success'] is True
    assert 'whatsapp_link' in trig_data
    assert 'api.whatsapp.com/send' in trig_data['whatsapp_link']

    # 4. Verify AlertLog contains custom message and recipient
    with app.app_context():
        logs = db.session.query(AlertLog).filter_by(resource_id=res_id).all()
        assert len(logs) > 0
        recipients = [l.recipient for l in logs]
        assert any('custom-qa@company.com' in r for r in recipients)
        assert any('+919876543210' in r for r in recipients)


def test_whatsapp_alert_dispatch_and_redirect_endpoint(client, app):
    """
    Verifies WhatsApp alert link generation, direct redirect endpoint, and Twilio sandbox connect helper.
    """
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_email'] = 'admin@cloudops.internal'
        sess['user_role'] = 'Admin'

    with app.app_context():
        res = CloudResource(
            instance_id='i-whatsapp-test-01',
            instance_name='WhatsApp-Monitored-EC2',
            provider='AWS',
            region='us-east-1',
            state='running',
            alert_whatsapp='whatsapp:+919025903459'
        )
        db.session.add(res)
        db.session.commit()
        res_id = res.id

    # 1. Trigger alert
    trig_res = client.post(f'/api/resources/{res_id}/trigger-alert', json={})
    assert trig_res.status_code == 200
    data = trig_res.get_json()
    assert data['success'] is True
    assert 'whatsapp_link' in data
    assert 'api.whatsapp.com/send' in data['whatsapp_link']
    assert '919025903459' in data['whatsapp_link']

    # 2. Test direct WhatsApp redirect endpoint (/api/alerts/whatsapp/open)
    open_res = client.get(f'/api/alerts/whatsapp/open?instance_id=i-whatsapp-test-01')
    assert open_res.status_code == 302
    redirect_target = open_res.headers.get('Location', '')
    assert 'api.whatsapp.com/send' in redirect_target
    assert '919025903459' in redirect_target

    # 3. Test sandbox connect helper
    connect_res = client.get('/api/alerts/whatsapp/connect')
    assert connect_res.status_code == 302
    assert '17372508034' in connect_res.headers.get('Location', '')


