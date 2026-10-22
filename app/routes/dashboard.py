from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, session, current_app, jsonify
from app.routes.auth import login_required
from app.models.models import db, CloudResource, Schedule, AlertLog, AuditTrail
from app.services.tunnel_service import get_public_base_url

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/health', methods=['GET'])
def health_check():
    """Lightweight sub-millisecond health check endpoint."""
    return jsonify({'status': 'ok'}), 200

def _get_context():
    webhook_url = current_app.config.get('WEBHOOK_BASE_URL') or get_public_base_url().rstrip('/')
    return {
        'user': {
            'id': session.get('user_id'),
            'name': session.get('user_name', 'vasanth'),
            'email': session.get('user_email', 'vasanthkumar20212021@gmail.com'),
            'role': session.get('user_role', 'Admin')
        },
        'app_meta': {
            'use_mock_aws': current_app.config.get('USE_MOCK_AWS', True),
            'region': current_app.config.get('AWS_DEFAULT_REGION', 'us-east-1'),
            'scan_interval': current_app.config.get('SCAN_INTERVAL_SECONDS', 60),
            'grace_period': current_app.config.get('GRACE_PERIOD_MINUTES', 30),
            'webhook_url': webhook_url
        }
    }

@dashboard_bp.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard.view_dashboard'))
    return redirect(url_for('auth.login'))

@dashboard_bp.route('/dashboard')
@login_required
def view_dashboard():
    """Renders main dashboard overview."""
    ctx = _get_context()
    return render_template('dashboard.html', active_tab='dashboard', **ctx)

@dashboard_bp.route('/schedules')
@login_required
def view_schedules():
    """Renders dedicated Schedules page matching user screenshot."""
    ctx = _get_context()
    return render_template('schedules.html', active_tab='schedules', **ctx)

@dashboard_bp.route('/alerts')
@login_required
def view_alerts():
    """Renders dedicated Alerts & notifications page matching user screenshot."""
    ctx = _get_context()
    return render_template('alerts.html', active_tab='alerts', **ctx)

@dashboard_bp.route('/resources')
@login_required
def view_resources():
    """Renders dedicated Cloud Resources page."""
    ctx = _get_context()
    return render_template('resources.html', active_tab='resources', **ctx)

@dashboard_bp.route('/audit-logs')
@login_required
def view_audit_logs():
    """Renders dedicated Audit logs page."""
    ctx = _get_context()
    return render_template('audit_logs.html', active_tab='audit-logs', **ctx)

@dashboard_bp.route('/cloud-accounts')
@dashboard_bp.route('/accounts')
@login_required
def view_cloud_accounts():
    """Renders dedicated Cloud Accounts integration & connection testing page."""
    ctx = _get_context()
    return render_template('cloud_accounts.html', active_tab='cloud-accounts', **ctx)

@dashboard_bp.route('/buzzer')
def mobile_buzzer():
    """Renders dedicated mobile buzzer alarm page with audio and vibration."""
    ctx = _get_context()
    return render_template('buzzer.html', **ctx)


@dashboard_bp.route('/api/public/buzzer-status', methods=['GET'])
def public_buzzer_status():
    """
    Public telemetry endpoint for mobile alarm page.
    Returns real-time policy breach status without requiring session authentication.
    """
    from datetime import datetime, timezone
    from app.services.token_utils import generate_action_token
    now = datetime.now(timezone.utc)
    base_url = (current_app.config.get('WEBHOOK_BASE_URL') or (request.host_url.rstrip('/') if request else '') or get_public_base_url()).rstrip('/')
    secret_key = current_app.config.get('SECRET_KEY')
    ttl_seconds = current_app.config.get('ACTION_TOKEN_TTL_SECONDS', 900)

    db_session = db.session
    try:
        running_resources = db_session.query(CloudResource).filter_by(state='running').all()
        breaches = []

        for res in running_resources:
            sched = db_session.query(Schedule).filter_by(resource_id=res.id, is_active=True).first()
            if not sched:
                continue

            # Check if running outside schedule
            is_compliant = sched.is_time_in_schedule(now)
            uptime = res.uptime_hours
            max_runtime = float(sched.max_runtime_hours) if sched.max_runtime_hours else 8.0
            exceeded_runtime = uptime > max_runtime

            if (not is_compliant) or exceeded_runtime or (res.alert_sent_at is not None):
                # Generate action tokens
                stop_token = generate_action_token(res.instance_id, 'stop', ttl_seconds=ttl_seconds, secret_key=secret_key)
                extend_token = generate_action_token(res.instance_id, 'extend', ttl_seconds=ttl_seconds, extend_minutes=60, secret_key=secret_key)

                reason = []
                if not is_compliant:
                    reason.append(f"Operating outside allowed window ({sched.start_time} - {sched.end_time})")
                if exceeded_runtime:
                    reason.append(f"Uptime ({uptime:.1f}h) exceeded threshold ({max_runtime:.1f}h)")
                if not reason:
                    reason.append("Active policy breach alert dispatched")

                elapsed_mins = 0.0
                if res.alert_sent_at:
                    alert_time = res.alert_sent_at if res.alert_sent_at.tzinfo else res.alert_sent_at.replace(tzinfo=timezone.utc)
                    elapsed_mins = (now - alert_time).total_seconds() / 60.0

                grace_period_mins = current_app.config.get('GRACE_PERIOD_MINUTES', 30)
                grace_expired = elapsed_mins >= grace_period_mins if res.alert_sent_at else False
                remaining_mins = max(0.0, round(grace_period_mins - elapsed_mins, 1)) if res.alert_sent_at else float(grace_period_mins)

                breaches.append({
                    'id': res.id,
                    'instance_id': res.instance_id,
                    'instance_name': res.instance_name,
                    'region': res.region,
                    'uptime_hours': round(uptime, 2),
                    'reason': " | ".join(reason),
                    'alert_sent_at': res.alert_sent_at.isoformat() if res.alert_sent_at else None,
                    'grace_period_mins': grace_period_mins,
                    'grace_remaining_mins': remaining_mins,
                    'grace_expired': grace_expired,
                    'stop_url': f"{base_url}/webhook/action?token={stop_token}&action=stop",
                    'extend_url': f"{base_url}/webhook/action?token={extend_token}&action=extend"
                })

        return {
            'success': True,
            'has_breach': len(breaches) > 0,
            'breach_count': len(breaches),
            'breaches': breaches,
            'server_time': now.isoformat()
        }
    finally:
        db_session.close()


@dashboard_bp.route('/api/public/reset-and-test-alarm', methods=['POST'])
def reset_and_test_alarm():
    """
    Resets alert timestamps on all running violating instances and triggers an immediate audit
    so notifications (Buzzer, Push, SMS, WhatsApp, Email) fire right away.
    """
    from app.services.scheduler_service import SchedulerService
    db_session = db.session
    try:
        # Clear alert_sent_at so scheduler immediately treats breaches as fresh
        running_resources = db_session.query(CloudResource).filter_by(state='running').all()
        for r in running_resources:
            r.alert_sent_at = None
        db_session.commit()

        # Trigger immediate audit
        scheduler = SchedulerService(config=current_app.config, app=current_app)
        audit_res = scheduler.audit_and_enforce_policies()

        return {
            'success': True,
            'message': 'Alert cycle reset and re-dispatched to all channels!',
            'audit_results': audit_res
        }
    except Exception as e:
        db_session.rollback()
        return {'success': False, 'error': str(e)}, 500
    finally:
        db_session.close()




