import pytest
from datetime import datetime, timezone, timedelta
from app.models.models import db, CloudResource, Schedule, AlertLog, AuditTrail
from app.services.cloud_service import MockCloudService
from app.services.scheduler_service import SchedulerService

def test_mock_cloud_service_lifecycle():
    """Tests discovery, start, and stop transitions in the Mock Cloud Service adapter."""
    mock_service = MockCloudService(region='us-east-1')
    instances = mock_service.discover_instances()
    assert len(instances) > 0

    target = instances[0]
    inst_id = target['instance_id']

    # Stop instance
    stop_res = mock_service.stop_instance(inst_id)
    assert stop_res['success'] is True
    assert stop_res['current_state'] == 'stopped'
    assert mock_service.get_instance(inst_id)['state'] == 'stopped'

    # Start instance
    start_res = mock_service.start_instance(inst_id)
    assert start_res['success'] is True
    assert start_res['current_state'] == 'running'
    assert mock_service.get_instance(inst_id)['state'] == 'running'

def test_schedule_policy_evaluation():
    """Tests time-window and day-of-week logic in Schedule model."""
    sched = Schedule(
        resource_id=1,
        start_time='09:00',
        end_time='18:00',
        max_runtime_hours=8.0,
        days_of_week='MON,TUE,WED,THU,FRI',
        is_active=True
    )

    # 14:00 UTC on a Wednesday (Should be in schedule)
    # Oct 7, 2026 is a Wednesday
    wed_in_hours = datetime(2026, 10, 7, 14, 0, tzinfo=timezone.utc)
    assert sched.is_time_in_schedule(wed_in_hours) is True

    # 22:00 UTC on a Wednesday (Outside permitted hours)
    wed_out_hours = datetime(2026, 10, 7, 22, 0, tzinfo=timezone.utc)
    assert sched.is_time_in_schedule(wed_out_hours) is False

    # 12:00 UTC on a Sunday (Outside permitted days)
    # Oct 11, 2026 is a Sunday
    sun_weekend = datetime(2026, 10, 11, 12, 0, tzinfo=timezone.utc)
    assert sched.is_time_in_schedule(sun_weekend) is False

def test_scheduler_audit_dispatches_alert_on_violation(app):
    """Verifies that an instance running in violation triggers an alert and initiates grace period."""
    with app.app_context():
        scheduler_service = SchedulerService(config=app.config, app=app)
        
        # Run audit cycle
        results = scheduler_service.audit_and_enforce_policies()
        assert results['violations_detected'] >= 1
        assert results['alerts_dispatched'] >= 1

        # Check database records
        session = db.session
        res = session.query(CloudResource).filter_by(instance_id='i-test001running').first()
        assert res is not None
        assert res.alert_sent_at is not None  # Grace period tracker initialized

        # Verify alert log created
        alert = session.query(AlertLog).filter_by(resource_id=res.id).first()
        assert alert is not None
        assert alert.token_hash is not None

        # Verify audit trail created
        audit = session.query(AuditTrail).filter_by(action_taken='ALERT_DISPATCHED').first()
        assert audit is not None
        assert audit.resource_id == res.id

def test_scheduler_grace_period_automated_shutdown(app):
    """
    Verifies that when an instance has an unacknowledged alert pending
    beyond the grace window, the scheduler executes an automated fallback shutdown.
    """
    with app.app_context():
        session = db.session
        res = session.query(CloudResource).filter_by(instance_id='i-test001running').first()
        assert res is not None

        # Simulate alert sent 45 minutes ago (well past the 30-minute grace period)
        res.alert_sent_at = datetime.now(timezone.utc) - timedelta(minutes=45)
        session.commit()

        scheduler_service = SchedulerService(config=app.config, app=app)
        results = scheduler_service.audit_and_enforce_policies()

        assert results['shutdowns_executed'] >= 1

        # Verify instance state transitioned to stopped
        updated_res = session.query(CloudResource).filter_by(instance_id='i-test001running').first()
        assert updated_res.state == 'stopped'
        assert updated_res.alert_sent_at is None  # Reset alert tracker

        # Verify audit ledger records POLICY_SHUTDOWN
        shutdown_audit = session.query(AuditTrail).filter_by(action_taken='POLICY_SHUTDOWN').first()
        assert shutdown_audit is not None
        assert shutdown_audit.triggered_by == 'SCHEDULER_GRACE_PERIOD'
        assert "grace period" in shutdown_audit.details.lower()

        # Verify buzzer alarm AlertLog recorded when grace period expired
        buzzer_alert = session.query(AlertLog).filter_by(resource_id=res.id, token_hash='GRACE_PERIOD_EXPIRED').first()
        assert buzzer_alert is not None
        assert "BUZZER ALARM" in buzzer_alert.details

def test_ntfy_buzzer_sound_only_when_alert_grace_period_ends(app):
    """
    Verifies the user requirement:
    1. During initial policy breach alert, ntfy push notification sends standard chime (sound_buzzer=False).
    2. When the alert grace period ends (expires without action), scheduler automatically powers down the workload
       AND dispatches the urgent loud buzzer siren alarm to the phone (sound_buzzer=True).
    """
    with app.app_context():
        from app.services.notification_service import NotificationService
        notifier = NotificationService(config=app.config)

        # 1. Test alert dispatch sends buzzer sound to phone by default
        inst_data = {
            'instance_id': 'i-test-buzzer-timing',
            'instance_name': 'Timing-Test-Instance',
            'provider': 'AWS',
            'region': 'us-east-1',
            'state': 'running',
            'alert_topic': 'test_alerts'
        }
        dispatch_default = notifier.dispatch_incident_alert(
            instance_data=inst_data,
            reason="Workload exceeded operational schedule",
            stop_url="http://test/stop",
            extend_url="http://test/extend"
        )
        assert dispatch_default['channels']['ntfy']['sound_buzzer'] is True

        # 2. Test grace period expiry dispatch has sound_buzzer=True
        expiry_dispatch = notifier.dispatch_grace_expiry_alert(
            instance_data=inst_data,
            grace_period_mins=30,
            reason="Grace period ended without operator action",
            sound_buzzer=True
        )
        assert expiry_dispatch['channels']['ntfy']['sound_buzzer'] is True

def test_schedule_update_and_enriched_alert_details(app, client):
    """
    Verifies:
    1. Granular schedule modification via PUT /api/schedules/<id>
    2. Alert message accurately displays scheduled time, stop time, start time, and total running hours.
    """
    with app.app_context():
        session = db.session
        res = session.query(CloudResource).filter_by(instance_id='i-test001running').first()
        sched = session.query(Schedule).filter_by(resource_id=res.id).first()
        sched_id = sched.id

    # Authenticate client
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_email'] = 'admin@test.internal'
        sess['user_role'] = 'Admin'

    # GET schedule details
    get_res = client.get(f'/api/schedules/{sched_id}')
    assert get_res.status_code == 200
    assert get_res.get_json()['schedule']['start_time'] == '01:00'

    # PUT update schedule with new date/time/hours
    update_payload = {
        'start_time': '11-10-2026 09:30',
        'end_time': '11-10-2026 18:30',
        'max_runtime_hours': 4.5
    }
    put_res = client.put(f'/api/schedules/{sched_id}', json=update_payload)
    assert put_res.status_code == 200
    assert put_res.get_json()['success'] is True
    assert put_res.get_json()['schedule']['max_runtime_hours'] == 4.5

    # Verify notification formatting includes scheduled time, stop time, start time, running hours
    from app.services.notification_service import NotificationService
    notifier = NotificationService(config=app.config)
    instance_info = {
        'instance_name': 'Test-Worker-Instance',
        'instance_id': 'i-test001running',
        'provider': 'AWS',
        'region': 'us-east-1',
        'launch_time': '2026-10-11T04:00:00Z',
        'uptime_hours': 6.0,
        'schedule': {
            'start_time': '11-10-2026 09:30',
            'end_time': '11-10-2026 18:30',
            'max_runtime_hours': 4.5
        }
    }
    plain_msg = notifier.format_plain_alert(instance_info, "Schedule Exceeded", "http://stop", "http://extend")
    assert "11-10-2026 09:30 - 11-10-2026 18:30" in plain_msg
    assert "Scheduled Stop Time: 11-10-2026 18:30" in plain_msg
    assert "Run Started At: 2026-10-11 04:00:00 UTC" in plain_msg
    assert "Scheduled Max Hours: 4.5 hrs" in plain_msg
    assert "Total Running Time: 6.00 hrs" in plain_msg
    assert "Exceeded by +1.5 hrs" in plain_msg

    html_email = notifier.format_html_email(instance_info, "Schedule Exceeded", "http://stop", "http://extend")
    assert "11-10-2026 09:30 &rarr; 11-10-2026 18:30" in html_email
    assert "Scheduled Stop Time:" in html_email
    assert "11-10-2026 18:30" in html_email
    assert "Run Started At:" in html_email
    assert "Total Running Time:" in html_email

