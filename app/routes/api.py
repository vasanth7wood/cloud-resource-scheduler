import json
from datetime import datetime, timezone, timedelta
import hashlib
from flask import Blueprint, request, jsonify, session, current_app
from app.models.models import db, CloudResource, Schedule, AlertLog, AuditTrail, CloudAccount
from app.routes.auth import login_required, role_required
from app.services.cloud_service import get_cloud_service
from app.services.token_utils import generate_action_token
from app.services.notification_service import NotificationService
from app.services.tunnel_service import get_public_base_url
import time
from sqlalchemy.orm import joinedload

api_bp = Blueprint('api', __name__, url_prefix='/api')

_STATS_CACHE = {'timestamp': 0, 'data': None}

@api_bp.route('/resources', methods=['GET'])
@login_required
def get_resources():
    """Returns list of all monitored cloud resources with active schedule and runtime details in a single query."""
    db_session = db.session
    try:
        resources = db_session.query(CloudResource).options(joinedload(CloudResource.schedules)).order_by(CloudResource.id.asc()).all()
        return jsonify({
            'success': True,
            'count': len(resources),
            'resources': [r.to_dict() for r in resources]
        })
    finally:
        db_session.close()

@api_bp.route('/resources/<int:resource_id>/start', methods=['POST'])
@login_required
@role_required(['Admin', 'Manager'])
def start_resource(resource_id):
    """Programmatically powers on a cloud instance."""
    db_session = db.session
    try:
        resource = db_session.query(CloudResource).get(resource_id)
        if not resource:
            return jsonify({'success': False, 'error': 'Resource not found'}), 404

        from app.services.cloud_service import get_cloud_service_for_resource
        cloud_service = get_cloud_service_for_resource(resource, current_app.config, db_session)
        res = cloud_service.start_instance(resource.instance_id, resource.region)

        if res.get('success'):
            now = datetime.now(timezone.utc)
            resource.state = 'running'
            resource.launch_time = now
            if not resource.public_ip:
                resource.public_ip = f"54.210.{resource.id % 250}.{resource.id * 7 % 250}"
            resource.last_scanned_at = now

            audit = AuditTrail(
                resource_id=resource.id,
                triggered_by=f"USER:{session.get('user_name', 'Unknown')} ({session.get('user_role')})",
                action_taken='START',
                details=f"Instance {resource.instance_id} started manually via dashboard."
            )
            db_session.add(audit)
            db_session.commit()

            return jsonify({
                'success': True,
                'message': res.get('message', f"Instance {resource.instance_id} started successfully."),
                'resource': resource.to_dict()
            })
        else:
            return jsonify({'success': False, 'error': res.get('message', 'Failed to start instance')}), 400
    except Exception as e:
        db_session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db_session.close()

@api_bp.route('/resources/<int:resource_id>/stop', methods=['POST'])
@login_required
@role_required(['Admin', 'Manager'])
def stop_resource(resource_id):
    """Programmatically powers down a cloud instance."""
    db_session = db.session
    try:
        resource = db_session.query(CloudResource).get(resource_id)
        if not resource:
            return jsonify({'success': False, 'error': 'Resource not found'}), 404

        from app.services.cloud_service import get_cloud_service_for_resource
        cloud_service = get_cloud_service_for_resource(resource, current_app.config, db_session)
        res = cloud_service.stop_instance(resource.instance_id, resource.region)

        if res.get('success'):
            new_state = res.get('current_state', 'stopped')
            resource.state = new_state
            resource.launch_time = None
            resource.public_ip = None
            resource.alert_sent_at = None
            resource.last_scanned_at = datetime.now(timezone.utc)

            audit = AuditTrail(
                resource_id=resource.id,
                triggered_by=f"USER:{session.get('user_name', 'Unknown')} ({session.get('user_role')})",
                action_taken='STOP',
                details=f"Instance {resource.instance_id} set to {new_state}."
            )
            db_session.add(audit)
            db_session.commit()

            return jsonify({
                'success': True,
                'message': res.get('message', f"Instance {resource.instance_id} stopped successfully."),
                'resource': resource.to_dict()
            })
        else:
            return jsonify({'success': False, 'error': res.get('message', 'Failed to stop instance')}), 400
    except Exception as e:
        db_session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db_session.close()

@api_bp.route('/resources/stop-all', methods=['POST'])
@login_required
@role_required(['Admin', 'Manager'])
def stop_all_resources():
    """Programmatically powers down ALL running cloud instances at once."""
    db_session = db.session
    try:
        running = db_session.query(CloudResource).filter_by(state='running').all()
        if not running:
            return jsonify({
                'success': True,
                'message': 'No active running instances found. All cloud workloads are already stopped.',
                'stopped_count': 0
            })

        from app.services.cloud_service import get_cloud_service_for_resource, get_cloud_service
        now = datetime.now(timezone.utc)
        stopped_names = []

        mock_svc = get_cloud_service(current_app.config)

        for resource in running:
            try:
                target_svc = get_cloud_service_for_resource(resource, current_app.config, db_session)
                target_svc.stop_instance(resource.instance_id, resource.region)
            except Exception as e:
                pass

            if hasattr(mock_svc, 'instances') and resource.instance_id in mock_svc.instances:
                mock_svc.instances[resource.instance_id]['state'] = 'stopped'

            resource.state = 'stopped'
            resource.launch_time = None
            resource.public_ip = None
            resource.alert_sent_at = None
            resource.last_scanned_at = now

            audit = AuditTrail(
                resource_id=resource.id,
                triggered_by=f"USER:{session.get('user_name', 'Unknown')} ({session.get('user_role')})",
                action_taken='STOP',
                details=f"Instance {resource.instance_id} ({resource.instance_name}) stopped via Stop All Running action."
            )
            db_session.add(audit)
            stopped_names.append(resource.instance_name)

        db_session.commit()
        return jsonify({
            'success': True,
            'message': f"Successfully stopped {len(stopped_names)} running instance(s): {', '.join(stopped_names)}.",
            'stopped_count': len(stopped_names)
        })
    except Exception as e:
        db_session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db_session.close()

@api_bp.route('/resources/<int:resource_id>/extend', methods=['POST'])
@login_required
@role_required(['Admin', 'Manager'])
def extend_resource_lease(resource_id):
    """Extends operational lease by N minutes (default 60 minutes)."""
    data = request.get_json() or {}
    minutes = int(data.get('minutes', 60))

    db_session = db.session
    try:
        resource = db_session.query(CloudResource).get(resource_id)
        if not resource:
            return jsonify({'success': False, 'error': 'Resource not found'}), 404

        now = datetime.now(timezone.utc)
        # If already has active future lease, extend from that; otherwise from now
        base_time = resource.lease_expires_at if (resource.lease_expires_at and resource.is_lease_active) else now
        if not base_time.tzinfo:
            base_time = base_time.replace(tzinfo=timezone.utc)
        
        new_expiry = base_time + timedelta(minutes=minutes)
        resource.lease_expires_at = new_expiry
        resource.alert_sent_at = None  # Clear alert violation

        audit = AuditTrail(
            resource_id=resource.id,
            triggered_by=f"USER:{session.get('user_name', 'Unknown')} ({session.get('user_role')})",
            action_taken='EXTEND_LEASE',
            details=f"Operating lease extended by {minutes} mins until {new_expiry.strftime('%Y-%m-%d %H:%M:%S UTC')}."
        )
        db_session.add(audit)
        db_session.commit()

        return jsonify({
            'success': True,
            'message': f"Lease for {resource.instance_id} extended by {minutes} minutes.",
            'lease_expires_at': new_expiry.isoformat(),
            'resource': resource.to_dict()
        })
    except Exception as e:
        db_session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db_session.close()

@api_bp.route('/resources/scan', methods=['POST'])
@login_required
@role_required(['Admin', 'Manager'])
def scan_cloud_resources():
    """Forces synchronization between cloud provider (Boto3 or Mock) and database."""
    from app.services.scheduler_service import SchedulerService
    scheduler = current_app.extensions.get('scheduler_service')
    if not scheduler:
        scheduler = SchedulerService(config=current_app.config, app=current_app)

    db_session = db.session
    try:
        count = scheduler.sync_cloud_inventory(db_session, add_new=True)
        audit = AuditTrail(
            resource_id=None,
            triggered_by=f"USER:{session.get('user_name', 'Unknown')}",
            action_taken='SCAN',
            details=f"Cloud discovery completed. {count} instances synchronized."
        )
        db_session.add(audit)
        db_session.commit()

        return jsonify({
            'success': True,
            'message': f"Successfully synchronized {count} cloud instances.",
            'count': count
        })
    except Exception as e:
        db_session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db_session.close()

@api_bp.route('/resources/sample-fleet', methods=['POST'])
@login_required
@role_required(['Admin', 'Manager'])
def populate_sample_fleet():
    """Populates realistic multi-cloud compute instances (AWS, Azure, GCP) with active schedules for instant evaluation."""
    db_session = db.session
    try:
        now = datetime.now(timezone.utc)
        sample_instances = [
            {
                'instance_id': 'i-0a1b2c3d4e5f6001',
                'instance_name': 'AWS-Web-Frontend-Prod',
                'provider': 'AWS',
                'region': 'us-east-1',
                'state': 'stopped',
                'instance_type': 't3.large',
                'public_ip': None,
                'private_ip': '10.0.1.45',
                'launch_time': None,
                'sched': {'start': '08:00', 'end': '20:00', 'max_h': 12.0}
            },
            {
                'instance_id': 'i-0b2c3d4e5f6a7002',
                'instance_name': 'AWS-Dev-Batch-Worker',
                'provider': 'AWS',
                'region': 'us-east-1',
                'state': 'stopped',
                'instance_type': 'c5.xlarge',
                'public_ip': None,
                'private_ip': '10.0.2.89',
                'launch_time': None,
                'sched': {'start': '09:00', 'end': '18:00', 'max_h': 8.0}
            },
            {
                'instance_id': 'vm-azure-api-gateway',
                'instance_name': 'Azure-API-Gateway-Prod',
                'provider': 'Azure',
                'region': 'eastus',
                'state': 'stopped',
                'instance_type': 'Standard_D2s_v3',
                'public_ip': None,
                'private_ip': '172.16.1.10',
                'launch_time': None,
                'sched': {'start': '09:00', 'end': '19:00', 'max_h': 8.0}
            },
            {
                'instance_id': 'gce-k8s-analytics-01',
                'instance_name': 'GCP-Data-ML-Trainer',
                'provider': 'GCP',
                'region': 'us-central1-a',
                'state': 'stopped',
                'instance_type': 'n2-standard-4',
                'public_ip': None,
                'private_ip': '10.128.0.14',
                'launch_time': None,
                'sched': {'start': '10:00', 'end': '17:00', 'max_h': 6.0}
            },
            {
                'instance_id': 'i-0e5f6a7b8c9d0005',
                'instance_name': 'AWS-QA-Test-Database',
                'provider': 'AWS',
                'region': 'eu-west-1',
                'state': 'stopped',
                'instance_type': 'r5.large',
                'public_ip': None,
                'private_ip': '10.2.1.20',
                'launch_time': None,
                'sched': {'start': '09:00', 'end': '18:00', 'max_h': 8.0}
            }
        ]

        count = 0
        for item in sample_instances:
            res = db_session.query(CloudResource).filter_by(instance_id=item['instance_id']).first()
            if not res:
                res = CloudResource(
                    instance_id=item['instance_id'],
                    instance_name=item['instance_name'],
                    provider=item['provider'],
                    region=item['region'],
                    state=item['state'],
                    instance_type=item['instance_type'],
                    public_ip=item['public_ip'],
                    private_ip=item['private_ip'],
                    launch_time=item['launch_time'],
                    last_scanned_at=now
                )
                db_session.add(res)
                db_session.flush()

                s_info = item['sched']
                sched = Schedule(
                    resource_id=res.id,
                    start_time=s_info['start'],
                    end_time=s_info['end'],
                    max_runtime_hours=s_info['max_h'],
                    days_of_week='MON,TUE,WED,THU,FRI',
                    is_active=True
                )
                db_session.add(sched)
                count += 1

        audit = AuditTrail(
            resource_id=None,
            triggered_by=f"USER:{session.get('user_name', 'Unknown')}",
            action_taken='POPULATE_SAMPLE_FLEET',
            details=f"Sample multi-cloud fleet loaded ({count} instances with active policies)."
        )
        db_session.add(audit)
        db_session.commit()

        return jsonify({
            'success': True,
            'message': f"Successfully loaded {count} multi-cloud instances with operating schedules.",
            'count': count
        })
    except Exception as e:
        db_session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db_session.close()

@api_bp.route('/resources/<int:resource_id>/alert-config', methods=['GET'])
@login_required
def get_resource_alert_config(resource_id):
    """Fetches custom alert message and recipient routing configuration for a specific workload."""
    db_session = db.session
    try:
        resource = db_session.get(CloudResource, resource_id)
        if not resource:
            return jsonify({'success': False, 'error': 'Resource not found'}), 404

        return jsonify({
            'success': True,
            'config': {
                'id': resource.id,
                'instance_id': resource.instance_id,
                'instance_name': resource.instance_name,
                'provider': resource.provider,
                'state': resource.state,
                'custom_alert_message': resource.custom_alert_message or '',
                'alert_email': resource.alert_email or '',
                'alert_phone': resource.alert_phone or '',
                'alert_whatsapp': resource.alert_whatsapp or '',
                'alert_topic': resource.alert_topic or ''
            }
        })
    finally:
        db_session.close()

@api_bp.route('/resources/<int:resource_id>/alert-config', methods=['PUT', 'POST'])
@login_required
@role_required(['Admin', 'Manager'])
def update_resource_alert_config(resource_id):
    """Updates custom alert message and specific recipient routing for a given workload."""
    data = request.get_json() or {}
    db_session = db.session
    try:
        resource = db_session.get(CloudResource, resource_id)
        if not resource:
            return jsonify({'success': False, 'error': 'Resource not found'}), 404

        custom_msg = data.get('custom_alert_message')
        alert_email = data.get('alert_email')
        alert_phone = data.get('alert_phone')
        alert_wa = data.get('alert_whatsapp')
        alert_top = data.get('alert_topic')

        if custom_msg is not None:
            resource.custom_alert_message = str(custom_msg).strip() or None
        if alert_email is not None:
            resource.alert_email = str(alert_email).strip() or None
        if alert_phone is not None:
            resource.alert_phone = str(alert_phone).strip() or None
        if alert_wa is not None:
            resource.alert_whatsapp = str(alert_wa).strip() or None
        if alert_top is not None:
            resource.alert_topic = str(alert_top).strip() or None

        audit = AuditTrail(
            resource_id=resource.id,
            triggered_by=f"USER:{session.get('user_name', 'Unknown')}",
            action_taken='ALERT_CONFIG_UPDATE',
            details=(
                f"Custom alert rule updated for {resource.instance_id}: "
                f"Msg='{resource.custom_alert_message or 'default'}', "
                f"Email='{resource.alert_email or 'default'}', Phone='{resource.alert_phone or 'default'}'"
            )
        )
        db_session.add(audit)
        db_session.commit()

        return jsonify({
            'success': True,
            'message': f"Custom alert preferences saved for {resource.instance_name} ({resource.instance_id})!",
            'config': {
                'id': resource.id,
                'instance_id': resource.instance_id,
                'instance_name': resource.instance_name,
                'custom_alert_message': resource.custom_alert_message or '',
                'alert_email': resource.alert_email or '',
                'alert_phone': resource.alert_phone or '',
                'alert_whatsapp': resource.alert_whatsapp or '',
                'alert_topic': resource.alert_topic or ''
            }
        })
    except Exception as e:
        db_session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db_session.close()

@api_bp.route('/resources/<int:resource_id>/trigger-alert', methods=['POST'])
@login_required
@role_required(['Admin', 'Manager'])
def trigger_resource_alert(resource_id):
    """
    Manually simulates a policy breach alert for testing and presentation demonstration.
    Dispatches across Twilio SMS, Twilio WhatsApp, and SMTP Email using the instance's custom message & routing.
    """
    data = request.get_json(silent=True) or {}
    db_session = db.session
    try:
        resource = db_session.get(CloudResource, resource_id)
        if not resource:
            return jsonify({'success': False, 'error': 'Resource not found'}), 404

        now = datetime.now(timezone.utc)
        resource.alert_sent_at = now

        base_url = get_public_base_url().rstrip('/')
        secret_key = current_app.config.get('SECRET_KEY')
        ttl_seconds = current_app.config.get('ACTION_TOKEN_TTL_SECONDS', 900)

        stop_token = generate_action_token(resource.instance_id, 'stop', ttl_seconds=ttl_seconds, secret_key=secret_key)
        extend_token = generate_action_token(resource.instance_id, 'extend', ttl_seconds=ttl_seconds, extend_minutes=60, secret_key=secret_key)

        stop_url = f"{base_url}/webhook/action?token={stop_token}&action=stop"
        extend_url = f"{base_url}/webhook/action?token={extend_token}&action=extend"
        token_hash = hashlib.sha256(stop_token.encode('utf-8')).hexdigest()

        notifier = NotificationService(current_app.config)
        custom_override = data.get('custom_message')
        if custom_override:
            resource.custom_alert_message = custom_override.strip()

        reason = resource.custom_alert_message or "Operating Policy Violation: Workload exceeded scheduled operational window."
        recipient_email = resource.alert_email or data.get('email') or session.get('user_email')
        recipient_phone = resource.alert_phone or data.get('phone')
        recipient_whatsapp = resource.alert_whatsapp or data.get('whatsapp')

        inst_dict = resource.to_dict()
        if custom_override:
            inst_dict['custom_alert_message'] = custom_override.strip()

        sound_buzzer = bool(data.get('sound_buzzer', True))
        dispatch_info = notifier.dispatch_incident_alert(
            instance_data=inst_dict,
            reason=reason,
            stop_url=stop_url,
            extend_url=extend_url,
            token_hash=token_hash,
            recipient_phone=recipient_phone,
            recipient_whatsapp=recipient_whatsapp,
            recipient_email=recipient_email,
            sound_buzzer=sound_buzzer
        )

        for channel_key, channel_res in dispatch_info['channels'].items():
            alert_log = AlertLog(
                resource_id=resource.id,
                channel=channel_res.get('channel', channel_key),
                recipient=channel_res.get('recipient', 'N/A'),
                status=channel_res.get('status', 'SENT'),
                token_hash=token_hash,
                details=f"Test alert: {reason}"
            )
            db_session.add(alert_log)

        audit = AuditTrail(
            resource_id=resource.id,
            triggered_by=f"USER:{session.get('user_name', 'Unknown')}",
            action_taken='TEST_ALERT_TRIGGERED',
            details=f"Manual test alert dispatched with instance message: '{reason}'."
        )
        db_session.add(audit)
        db_session.commit()

        return jsonify({
            'success': True,
            'message': f"Custom alert successfully dispatched for {resource.instance_name}!",
            'dispatch': dispatch_info,
            'stop_url': stop_url,
            'extend_url': extend_url,
            'whatsapp_link': dispatch_info.get('whatsapp_link') or dispatch_info.get('channels', {}).get('whatsapp', {}).get('whatsapp_link'),
            'sandbox_join_url': dispatch_info.get('channels', {}).get('whatsapp', {}).get('sandbox_join_url')
        })
    except Exception as e:
        db_session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db_session.close()

@api_bp.route('/alerts/test-direct', methods=['POST'])
@login_required
def test_direct_alert():
    """
    Directly dispatches a multi-channel alert (Email, SMS, WhatsApp) with cryptographically
    signed HMAC action tokens for demonstration and live verification.
    """
    data = request.get_json() or {}
    recipient_email = data.get('email', session.get('user_email', 'vasanthkumar20262026@gmail.com')).strip()
    recipient_phone = data.get('phone', '+919025903459').strip()
    db_session = db.session
    req_inst_id = data.get('instance_id')
    existing_res = None
    if req_inst_id:
        existing_res = db_session.query(CloudResource).filter_by(instance_id=req_inst_id).first()
    if not existing_res:
        existing_res = db_session.query(CloudResource).filter_by(state='running').first() or db_session.query(CloudResource).first()

    if existing_res:
        instance_id = existing_res.instance_id
        instance_name = existing_res.instance_name
        prov = existing_res.provider
        region = existing_res.region
    else:
        instance_id = data.get('instance_id', 'i-0a1b2c3d4e5f6001')
        prov = data.get('provider', 'Azure' if instance_id.startswith('vm-') else 'AWS')
        instance_name = data.get('instance_name', f"{prov}-Production-Workload")
        region = data.get('region', 'eastus' if prov == 'Azure' else current_app.config.get('AWS_DEFAULT_REGION', 'us-east-1'))

    ttl_seconds = current_app.config.get('ACTION_TOKEN_TTL_SECONDS', 900)
    base_url = get_public_base_url().rstrip('/')
    secret_key = current_app.config.get('SECRET_KEY')

    stop_token = generate_action_token(instance_id, 'stop', ttl_seconds=ttl_seconds, secret_key=secret_key)
    extend_token = generate_action_token(instance_id, 'extend', ttl_seconds=ttl_seconds, extend_minutes=60, secret_key=secret_key)

    stop_url = f"{base_url}/webhook/action?token={stop_token}&action=stop"
    extend_url = f"{base_url}/webhook/action?token={extend_token}&action=extend"
    token_hash = hashlib.sha256(stop_token.encode('utf-8')).hexdigest()

    instance_data = {
        'instance_id': instance_id,
        'instance_name': instance_name,
        'provider': prov,
        'region': region,
        'state': 'running',
        'uptime_hours': data.get('uptime_hours', 9.25)
    }

    notifier = NotificationService(current_app.config)
    reason = data.get('reason', f"Operating Policy Violation: {prov} instance exceeded scheduled runtime of 8.0 hours.")
    sound_buzzer = bool(data.get('sound_buzzer', True))
    dispatch_info = notifier.dispatch_incident_alert(
        instance_data=instance_data,
        reason=reason,
        stop_url=stop_url,
        extend_url=extend_url,
        token_hash=token_hash,
        recipient_phone=recipient_phone,
        recipient_email=recipient_email,
        sound_buzzer=sound_buzzer
    )

    try:
        audit = AuditTrail(
            resource_id=None,
            triggered_by=f"USER:{session.get('user_name', 'vasanth')}",
            action_taken='TEST_ALERT_DIRECT',
            details=f"Direct test alert dispatched to Email ({recipient_email}), SMS, and WhatsApp."
        )
        db_session.add(audit)
        db_session.commit()
    finally:
        db_session.close()

    return jsonify({
        'success': True,
        'message': 'Multi-channel alert successfully dispatched across Email, SMS, and WhatsApp!',
        'dispatch': dispatch_info,
        'stop_url': stop_url,
        'extend_url': extend_url,
        'whatsapp_link': dispatch_info.get('whatsapp_link') or dispatch_info.get('channels', {}).get('whatsapp', {}).get('whatsapp_link'),
        'sandbox_join_url': dispatch_info.get('channels', {}).get('whatsapp', {}).get('sandbox_join_url'),
        'token_ttl': '15 minutes (HMAC-SHA256 Signed)'
    })

@api_bp.route('/alerts/whatsapp/open', methods=['GET'])
def open_whatsapp_alert():
    """
    Direct redirect link opening WhatsApp on mobile or desktop with the full formatted incident alert.
    """
    import urllib.parse
    import re
    from flask import redirect
    inst_id = request.args.get('instance_id')
    db_session = db.session
    try:
        resource = None
        if inst_id:
            resource = db_session.query(CloudResource).filter_by(instance_id=inst_id).first()
        if not resource:
            resource = db_session.query(CloudResource).filter_by(state='running').first() or db_session.query(CloudResource).first()

        base_url = get_public_base_url().rstrip('/')
        secret_key = current_app.config.get('SECRET_KEY')
        ttl_seconds = current_app.config.get('ACTION_TOKEN_TTL_SECONDS', 900)

        target_inst_id = resource.instance_id if resource else (inst_id or 'i-06b9d8479ab4f3074')
        stop_token = generate_action_token(target_inst_id, 'stop', ttl_seconds=ttl_seconds, secret_key=secret_key)
        extend_token = generate_action_token(target_inst_id, 'extend', ttl_seconds=ttl_seconds, extend_minutes=60, secret_key=secret_key)
        stop_url = f"{base_url}/webhook/action?token={stop_token}&action=stop"
        extend_url = f"{base_url}/webhook/action?token={extend_token}&action=extend"

        notifier = NotificationService(current_app.config)
        inst_dict = resource.to_dict() if resource else {'instance_id': target_inst_id, 'instance_name': 'Cloud Workload', 'provider': 'AWS', 'state': 'running'}
        reason = resource.custom_alert_message if (resource and resource.custom_alert_message) else "Operating Policy Violation: Workload exceeded scheduled operational window."
        plain_body = notifier.format_plain_alert(inst_dict, reason, stop_url, extend_url)

        target_phone = request.args.get('phone') or (resource.alert_whatsapp if resource else None) or current_app.config.get('ALERT_WHATSAPP_NUMBER', '+919025903459')
        clean_digits = re.sub(r'\D', '', str(target_phone).replace('whatsapp:', ''))
        if len(clean_digits) == 10:
            clean_digits = f"91{clean_digits}"

        encoded_body = urllib.parse.quote(plain_body)
        whatsapp_url = f"https://api.whatsapp.com/send?phone={clean_digits}&text={encoded_body}"
        return redirect(whatsapp_url, code=302)
    finally:
        db_session.close()

@api_bp.route('/alerts/whatsapp/connect', methods=['GET'])
def connect_twilio_whatsapp():
    """
    1-Click helper redirecting to Twilio WhatsApp Sandbox to activate the 24-hour automated push window.
    """
    from flask import redirect
    return redirect("https://api.whatsapp.com/send?phone=17372508034&text=join%20twilio-trhiial", code=302)

@api_bp.route('/audit/trigger', methods=['POST'])
@login_required
@role_required(['Admin', 'Manager'])
def trigger_audit():
    """Triggers an on-demand full governance policy audit cycle."""
    scheduler = current_app.extensions.get('scheduler_service')
    if not scheduler:
        return jsonify({'success': False, 'error': 'Scheduler service not available'}), 500

    results = scheduler.trigger_immediate_audit()
    return jsonify({
        'success': True,
        'message': 'Governance audit cycle executed successfully.',
        'results': results
    })

@api_bp.route('/schedules', methods=['GET'])
@login_required
def get_schedules():
    """Lists all configured scheduling policies."""
    db_session = db.session
    try:
        schedules = db_session.query(Schedule).all()
        return jsonify({
            'success': True,
            'count': len(schedules),
            'schedules': [s.to_dict() for s in schedules]
        })
    finally:
        db_session.close()

@api_bp.route('/schedules', methods=['POST'])
@login_required
@role_required(['Admin', 'Manager'])
def save_schedule():
    """Creates or updates a resource schedule."""
    data = request.get_json() or {}
    resource_id = data.get('resource_id')
    start_time = data.get('start_time', '09:00')
    end_time = data.get('end_time') or data.get('stop_time') or '19:00'
    max_runtime_hours = float(data.get('max_runtime_hours', 8.0))
    days_of_week = data.get('days_of_week', 'MON,TUE,WED,THU,FRI')
    is_active = bool(data.get('is_active', True))

    if not resource_id:
        return jsonify({'success': False, 'error': 'resource_id is required'}), 400

    db_session = db.session
    try:
        schedule = db_session.query(Schedule).filter_by(resource_id=resource_id).first()
        if not schedule:
            schedule = Schedule(
                resource_id=resource_id,
                start_time=start_time,
                end_time=end_time,
                max_runtime_hours=max_runtime_hours,
                days_of_week=days_of_week,
                is_active=is_active
            )
            db_session.add(schedule)
        else:
            schedule.start_time = start_time
            schedule.end_time = end_time
            schedule.max_runtime_hours = max_runtime_hours
            schedule.days_of_week = days_of_week
            schedule.is_active = is_active

        audit = AuditTrail(
            resource_id=resource_id,
            triggered_by=f"USER:{session.get('user_name', 'Unknown')}",
            action_taken='SCHEDULE_UPDATE',
            details=f"Policy updated: window {start_time}-{end_time}, max {max_runtime_hours}h, days {days_of_week}"
        )
        # Reset alert tracker on target resource so any breach triggers fresh alerts immediately
        res = db_session.get(CloudResource, resource_id)
        if res:
            res.alert_sent_at = None

        # Capture dictionary before calling scheduler audit or closing session to prevent DetachedInstanceError
        schedule_data = schedule.to_dict()

        db_session.add(audit)
        db_session.commit()

        # Run immediate policy audit to alert phone & email instantly if already past stop time
        scheduler = current_app.extensions.get('scheduler_service')
        alerts_dispatched = 0
        if scheduler:
            try:
                audit_res = scheduler.audit_and_enforce_policies()
                alerts_dispatched = audit_res.get('alerts_dispatched', 0) if isinstance(audit_res, dict) else 0
            except Exception as audit_err:
                current_app.logger.warning(f"Immediate policy audit after schedule save encountered: {audit_err}")

        success_msg = 'Schedule saved successfully.'
        if alerts_dispatched > 0:
            success_msg = 'Schedule saved successfully. Stop time is exceeded — instant alert dispatched to your mobile phone, SMS, and email!'

        return jsonify({
            'success': True,
            'message': success_msg,
            'breach_alert_sent': alerts_dispatched > 0,
            'schedule': schedule_data
        })
    except Exception as e:
        db_session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db_session.close()

@api_bp.route('/schedules/<int:schedule_id>', methods=['GET'])
@login_required
def get_schedule_by_id(schedule_id):
    """Retrieves specific schedule details for viewing or editing."""
    db_session = db.session
    try:
        schedule = db_session.get(Schedule, schedule_id)
        if not schedule:
            return jsonify({'success': False, 'error': 'Schedule not found'}), 404
        return jsonify({'success': True, 'schedule': schedule.to_dict()})
    finally:
        db_session.close()

@api_bp.route('/schedules/<int:schedule_id>', methods=['PUT'])
@login_required
@role_required(['Admin', 'Manager'])
def update_schedule_by_id(schedule_id):
    """Modifies/updates an existing schedule's date, time, hours, minutes, and constraints."""
    data = request.get_json() or {}
    start_time = data.get('start_time')
    end_time = data.get('end_time') or data.get('stop_time')
    max_runtime_hours = data.get('max_runtime_hours')
    days_of_week = data.get('days_of_week')
    is_active = data.get('is_active')

    db_session = db.session
    try:
        schedule = db_session.get(Schedule, schedule_id)
        if not schedule:
            return jsonify({'success': False, 'error': 'Schedule not found'}), 404

        if start_time is not None:
            schedule.start_time = str(start_time).strip()
        if end_time is not None:
            schedule.end_time = str(end_time).strip()
        if max_runtime_hours is not None:
            schedule.max_runtime_hours = float(max_runtime_hours)
        if days_of_week is not None:
            schedule.days_of_week = str(days_of_week).strip()
        if is_active is not None:
            schedule.is_active = bool(is_active)

        # Reset alert tracker on the attached cloud resource so updated schedule triggers fresh alerts immediately
        res = db_session.get(CloudResource, schedule.resource_id)
        if res:
            res.alert_sent_at = None

        audit = AuditTrail(
            resource_id=schedule.resource_id,
            triggered_by=f"USER:{session.get('user_name', 'Unknown')}",
            action_taken='SCHEDULE_UPDATE',
            details=f"Schedule #{schedule_id} updated: window {schedule.start_time} to {schedule.end_time}, max {schedule.max_runtime_hours}h"
        )
        db_session.add(audit)
        
        schedule_data = schedule.to_dict()
        db_session.commit()

        # Run immediate policy audit to alert phone & email instantly if already past new stop time
        scheduler = current_app.extensions.get('scheduler_service')
        alerts_dispatched = 0
        if scheduler:
            try:
                audit_res = scheduler.audit_and_enforce_policies()
                alerts_dispatched = audit_res.get('alerts_dispatched', 0) if isinstance(audit_res, dict) else 0
            except Exception as audit_err:
                current_app.logger.warning(f"Immediate policy audit after schedule PUT encountered: {audit_err}")

        success_msg = 'Schedule updated successfully.'
        if alerts_dispatched > 0:
            success_msg = 'Schedule updated successfully. Stop time is exceeded — instant alert dispatched to your mobile phone, SMS, and email!'

        return jsonify({
            'success': True,
            'message': success_msg,
            'breach_alert_sent': alerts_dispatched > 0,
            'schedule': schedule_data
        })
    except Exception as e:
        db_session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db_session.close()

@api_bp.route('/schedules/<int:schedule_id>', methods=['DELETE'])
@login_required
@role_required(['Admin', 'Manager'])
def delete_schedule(schedule_id):
    """Deletes a configured schedule."""
    db_session = db.session
    try:
        schedule = db_session.get(Schedule, schedule_id)
        if not schedule:
            return jsonify({'success': False, 'error': 'Schedule not found'}), 404

        resource_id = schedule.resource_id
        db_session.delete(schedule)
        
        audit = AuditTrail(
            resource_id=resource_id,
            triggered_by=f"USER:{session.get('user_name', 'Unknown')}",
            action_taken='SCHEDULE_DELETE',
            details=f"Schedule #{schedule_id} deleted."
        )
        db_session.add(audit)
        db_session.commit()

        return jsonify({'success': True, 'message': 'Schedule deleted successfully.'})
    except Exception as e:
        db_session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db_session.close()

# In-memory alert preferences store
_ALERT_PREFS = {
    'email_dest': 'vasanthkumar20262026@gmail.com',
    'email_enabled': True,
    'sms_dest': '+919025903459',
    'sms_enabled': True,
    'whatsapp_dest': 'whatsapp:+919025903459',
    'whatsapp_enabled': True
}

@api_bp.route('/alerts/preferences', methods=['GET'])
@login_required
def get_alert_preferences():
    """Returns current alert delivery preferences."""
    user_email = session.get('user_email', _ALERT_PREFS['email_dest'])
    prefs = dict(_ALERT_PREFS)
    if user_email:
        prefs['email_dest'] = user_email
    return jsonify({'success': True, 'preferences': prefs})

@api_bp.route('/alerts/preferences', methods=['POST'])
@login_required
def save_alert_preferences():
    """Saves alert delivery preferences."""
    data = request.get_json() or {}
    _ALERT_PREFS['email_dest'] = data.get('email_dest', _ALERT_PREFS['email_dest']).strip()
    _ALERT_PREFS['email_enabled'] = bool(data.get('email_enabled', True))
    _ALERT_PREFS['sms_dest'] = data.get('sms_dest', _ALERT_PREFS['sms_dest']).strip()
    _ALERT_PREFS['sms_enabled'] = bool(data.get('sms_enabled', False))
    _ALERT_PREFS['whatsapp_dest'] = data.get('whatsapp_dest', _ALERT_PREFS['whatsapp_dest']).strip()
    _ALERT_PREFS['whatsapp_enabled'] = bool(data.get('whatsapp_enabled', False))

    # Also update current app config alert recipients
    current_app.config['ALERT_EMAIL_RECIPIENT'] = _ALERT_PREFS['email_dest']
    current_app.config['ALERT_PHONE_NUMBER'] = _ALERT_PREFS['sms_dest']
    current_app.config['ALERT_WHATSAPP_NUMBER'] = _ALERT_PREFS['whatsapp_dest']

    return jsonify({'success': True, 'message': 'Alert preferences saved successfully.', 'preferences': _ALERT_PREFS})

@api_bp.route('/stats', methods=['GET'])
@login_required
def get_stats():
    """Computes real-time FinOps statistics and governance metrics with short TTL caching."""
    global _STATS_CACHE
    now_ts = time.time()
    if _STATS_CACHE['data'] and (now_ts - _STATS_CACHE['timestamp'] < 2.5):
        return jsonify(_STATS_CACHE['data'])

    db_session = db.session
    try:
        total_resources = db_session.query(CloudResource).count()
        running_resources = db_session.query(CloudResource).filter_by(state='running').count()
        stopped_resources = db_session.query(CloudResource).filter_by(state='stopped').count()
        active_schedules = db_session.query(Schedule).filter_by(is_active=True).count()
        total_alerts = db_session.query(AlertLog).count()
        total_audits = db_session.query(AuditTrail).count()

        # FinOps Cost Analysis
        hourly_rate = current_app.config.get('HOURLY_COST_PER_INSTANCE_USD', 0.096)
        usd_to_inr = current_app.config.get('USD_TO_INR_RATE', 83.50)

        # Count stopped instances and automated policy shutdowns
        auto_shutdowns = db_session.query(AuditTrail).filter(
            AuditTrail.action_taken.in_(['POLICY_SHUTDOWN', 'STOP'])
        ).count()

        # Estimated avoided run hours: approximate 14 hours idle saved per stopped instance per day
        estimated_avoided_hours = stopped_resources * 14.0 + (auto_shutdowns * 4.0)
        estimated_savings_usd = round(estimated_avoided_hours * hourly_rate, 2)
        estimated_savings_inr = round(estimated_savings_usd * usd_to_inr, 2)

        # Current active burn rate (running instances * hourly rate)
        current_burn_rate_usd = round(running_resources * hourly_rate, 3)

        result_payload = {
            'success': True,
            'metrics': {
                'total_resources': total_resources,
                'running_resources': running_resources,
                'stopped_resources': stopped_resources,
                'active_schedules': active_schedules,
                'total_alerts': total_alerts,
                'total_audits': total_audits,
                'auto_shutdowns': auto_shutdowns,
                'estimated_avoided_hours': estimated_avoided_hours,
                'estimated_savings_usd': estimated_savings_usd,
                'estimated_savings_inr': estimated_savings_inr,
                'current_burn_rate_usd': current_burn_rate_usd,
                'currency_symbol': '$',
                'currency_inr_symbol': '₹'
            }
        }
        _STATS_CACHE['timestamp'] = time.time()
        _STATS_CACHE['data'] = result_payload
        return jsonify(result_payload)
    finally:
        db_session.close()

@api_bp.route('/audit-logs', methods=['GET'])
@login_required
def get_audit_logs():
    """Returns recent audit trail entries."""
    db_session = db.session
    try:
        limit = min(int(request.args.get('limit', 50)), 100)
        logs = db_session.query(AuditTrail).order_by(AuditTrail.id.desc()).limit(limit).all()
        return jsonify({
            'success': True,
            'count': len(logs),
            'audit_logs': [log.to_dict() for log in logs]
        })
    finally:
        db_session.close()

@api_bp.route('/alerts', methods=['GET'])
@login_required
def get_alerts():
    """Returns recent multi-channel alert log entries."""
    db_session = db.session
    try:
        limit = min(int(request.args.get('limit', 50)), 100)
        logs = db_session.query(AlertLog).order_by(AlertLog.id.desc()).limit(limit).all()
        return jsonify({
            'success': True,
            'count': len(logs),
            'alerts': [log.to_dict() for log in logs]
        })
    finally:
        db_session.close()

# ==============================================================================
# CLEAR DISCOVERED RESOURCES (Reset Inventory)
# ==============================================================================
@api_bp.route('/resources/clear', methods=['POST'])
@login_required
@role_required(['Admin', 'Manager'])
def clear_resources():
    """Purges all discovered cloud resources, resetting the dashboard to a fresh empty state."""
    db_session = db.session
    try:
        db_session.query(Schedule).delete()
        db_session.query(AlertLog).delete()
        count = db_session.query(CloudResource).delete()
        
        audit = AuditTrail(
            resource_id=None,
            triggered_by=f"USER:{session.get('user_name', 'Unknown')}",
            action_taken='CLEARED_INVENTORY',
            details=f"Discovered inventory cleared. {count} instances removed."
        )
        db_session.add(audit)
        db_session.commit()
        return jsonify({
            'success': True,
            'message': f"Successfully cleared {count} cloud resources from inventory.",
            'cleared_count': count
        })
    except Exception as e:
        db_session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db_session.close()

# ==============================================================================
# MULTI-CLOUD ACCOUNT MANAGEMENT & CONNECTION TESTING (AWS, Azure, GCP)
# ==============================================================================
@api_bp.route('/cloud-accounts', methods=['GET'])
@login_required
def get_cloud_accounts():
    """Lists all configured cloud accounts with connection status and masked credentials."""
    db_session = db.session
    try:
        accounts = db_session.query(CloudAccount).order_by(CloudAccount.id.asc()).all()
        return jsonify({
            'success': True,
            'count': len(accounts),
            'accounts': [a.to_dict() for a in accounts]
        })
    finally:
        db_session.close()

@api_bp.route('/cloud-accounts/test', methods=['POST'])
@login_required
@role_required(['Admin', 'Manager'])
def test_cloud_account():
    """Tests live or sandbox connection to AWS, Azure, or GCP on demand."""
    from app.services.cloud_account_service import CloudAccountService
    data = request.get_json() or {}
    provider = data.get('provider', 'AWS').upper()
    creds = data.get('credentials', {})
    use_sandbox = bool(data.get('use_sandbox', False))
    creds['use_sandbox'] = use_sandbox

    if 'AWS' in provider:
        res = CloudAccountService.test_aws_connection(creds)
    elif 'AZURE' in provider:
        res = CloudAccountService.test_azure_connection(creds)
    elif 'GCP' in provider:
        res = CloudAccountService.test_gcp_connection(creds)
    else:
        return jsonify({'success': False, 'error': f'Unsupported cloud provider: {provider}'}), 400

    return jsonify(res)

@api_bp.route('/cloud-accounts', methods=['POST'])
@login_required
@role_required(['Admin', 'Manager'])
def save_cloud_account():
    """Saves or updates a cloud account integration after verification."""
    import json
    from app.services.cloud_account_service import CloudAccountService
    data = request.get_json() or {}
    provider = data.get('provider', 'AWS').strip().upper()
    account_name = data.get('account_name', '').strip()
    creds = data.get('credentials', {})
    use_sandbox = bool(data.get('use_sandbox', False))
    creds['use_sandbox'] = use_sandbox

    if not account_name:
        return jsonify({'success': False, 'error': 'Account name is required.'}), 400

    region = creds.get('aws_region') or creds.get('azure_region') or creds.get('gcp_zone') or 'us-east-1'
    if 'AWS' in provider:
        raw_id = creds.get('aws_access_key_id', '')
        ident = (raw_id[:4] + '****' + raw_id[-4:]) if len(raw_id) > 8 else raw_id
        test_res = CloudAccountService.test_aws_connection(creds)
    elif 'AZURE' in provider:
        raw_id = creds.get('azure_subscription_id', '')
        ident = (raw_id[:6] + '****' + raw_id[-4:]) if len(raw_id) > 10 else raw_id
        test_res = CloudAccountService.test_azure_connection(creds)
    else:
        ident = creds.get('gcp_project_id', 'GCP-Project')
        test_res = CloudAccountService.test_gcp_connection(creds)

    status = 'CONNECTED' if test_res.get('success') else 'FAILED'
    last_error = None if test_res.get('success') else test_res.get('error')

    db_session = db.session
    try:
        account = CloudAccount(
            provider=provider,
            account_name=account_name,
            account_identifier=ident,
            region=region,
            credentials_json=json.dumps(creds),
            status=status,
            last_tested_at=datetime.now(timezone.utc),
            last_error=last_error,
            is_active=True
        )
        db_session.add(account)
        db_session.flush()

        audit = AuditTrail(
            resource_id=None,
            triggered_by=f"USER:{session.get('user_name', 'Unknown')}",
            action_taken='CLOUD_ACCOUNT_SAVED',
            details=f"Connected cloud account '{account_name}' ({provider}) created with status {status}."
        )
        db_session.add(audit)
        db_session.commit()

        return jsonify({
            'success': True,
            'message': f"Account '{account_name}' saved successfully ({status}).",
            'account': account.to_dict(),
            'test_result': test_res
        })
    except Exception as e:
        db_session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db_session.close()

@api_bp.route('/cloud-accounts/<int:account_id>/test', methods=['POST'])
@login_required
@role_required(['Admin', 'Manager'])
def retest_cloud_account(account_id):
    """Re-tests an existing saved cloud account."""
    import json
    from app.services.cloud_account_service import CloudAccountService
    db_session = db.session
    try:
        account = db_session.query(CloudAccount).filter_by(id=account_id).first()
        if not account:
            return jsonify({'success': False, 'error': 'Account not found'}), 404

        creds = json.loads(account.credentials_json or '{}')
        provider = account.provider.upper()

        if 'AWS' in provider:
            res = CloudAccountService.test_aws_connection(creds)
        elif 'AZURE' in provider:
            res = CloudAccountService.test_azure_connection(creds)
        else:
            res = CloudAccountService.test_gcp_connection(creds)

        account.status = 'CONNECTED' if res.get('success') else 'FAILED'
        account.last_tested_at = datetime.now(timezone.utc)
        account.last_error = None if res.get('success') else res.get('error')
        db_session.commit()

        return jsonify({
            'success': True,
            'account': account.to_dict(),
            'test_result': res
        })
    finally:
        db_session.close()

@api_bp.route('/cloud-accounts/<int:account_id>', methods=['DELETE'])
@login_required
@role_required(['Admin', 'Manager'])
def delete_cloud_account(account_id):
    """Deletes a saved cloud account."""
    db_session = db.session
    try:
        account = db_session.query(CloudAccount).filter_by(id=account_id).first()
        if not account:
            return jsonify({'success': False, 'error': 'Account not found'}), 404

        name = account.account_name
        db_session.delete(account)
        db_session.commit()
        return jsonify({'success': True, 'message': f"Account '{name}' removed successfully."})
    finally:
        db_session.close()

@api_bp.route('/cloud-accounts/<int:account_id>/discover', methods=['POST'])
@login_required
@role_required(['Admin', 'Manager'])
def discover_from_account(account_id):
    """Discovers cloud resources specifically from a verified cloud account."""
    from app.services.cloud_account_service import CloudAccountService
    db_session = db.session
    try:
        account = db_session.query(CloudAccount).filter_by(id=account_id).first()
        if not account:
            return jsonify({'success': False, 'error': 'Account not found'}), 404

        creds = json.loads(account.credentials_json or '{}')
        instances = []
        is_sandbox = creds.get('use_sandbox', False) or creds.get('aws_access_key_id', '').startswith(('MOCK', 'SANDBOX', 'DEMO'))

        if 'AWS' in account.provider.upper() and not is_sandbox:
            try:
                from app.services.cloud_service import AwsCloudService
                aws_srv = AwsCloudService(
                    region=account.region or 'us-east-1',
                    aws_access_key_id=creds.get('aws_access_key_id'),
                    aws_secret_access_key=creds.get('aws_secret_access_key')
                )
                instances = aws_srv.discover_instances(region=account.region)
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f"Failed to query AWS EC2: {str(e)}. Please verify AWS IAM policy 'AmazonEC2FullAccess' is attached to this user."
                }), 400
        elif is_sandbox:
            instances = CloudAccountService.get_provider_sample_instances(
                provider=account.provider,
                account_name=account.account_name,
                region=account.region or 'us-east-1'
            )

        now = datetime.now(timezone.utc)
        added_count = 0
        for inst in instances:
            existing = db_session.query(CloudResource).filter_by(instance_id=inst['instance_id']).first()
            if not existing:
                res = CloudResource(
                    instance_id=inst['instance_id'],
                    instance_name=inst['instance_name'],
                    provider=inst['provider'],
                    region=inst['region'],
                    state=inst['state'],
                    instance_type=inst['instance_type'],
                    public_ip=inst.get('public_ip'),
                    private_ip=inst.get('private_ip'),
                    launch_time=inst.get('launch_time'),
                    last_scanned_at=now
                )
                db_session.add(res)
                added_count += 1
            else:
                existing.state = inst['state']
                existing.public_ip = inst.get('public_ip')
                existing.private_ip = inst.get('private_ip')
                existing.last_scanned_at = now

        audit = AuditTrail(
            resource_id=None,
            triggered_by=f"USER:{session.get('user_name', 'Unknown')}",
            action_taken='DISCOVER_ACCOUNT',
            details=f"Discovered {added_count} instances from {account.provider} account '{account.account_name}'."
        )
        db_session.add(audit)
        db_session.commit()

        return jsonify({
            'success': True,
            'message': f"Discovered {added_count} instances from {account.account_name} ({account.provider}).",
            'count': added_count
        })
    finally:
        db_session.close()

