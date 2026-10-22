from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, render_template, jsonify, current_app, Response
from app.models.models import db, CloudResource, AuditTrail
from app.services.token_utils import verify_action_token, mark_token_consumed, generate_action_token
from app.services.cloud_service import get_cloud_service, get_cloud_service_for_resource

webhook_bp = Blueprint('webhook', __name__)

@webhook_bp.route('/webhook/action', methods=['GET', 'POST'])
def handle_action_webhook():
    """
    Public interactive webhook endpoint for single-click remote incident response.
    Validates cryptographic HMAC signature and TTL expiration,
    then programmatically executes state transition (Stop / Extend Lease).
    """
    # Extract token and action from query params or form/JSON body
    token = request.args.get('token')
    req_action = request.args.get('action')

    if not token and request.is_json:
        data = request.get_json() or {}
        token = data.get('token')
        req_action = data.get('action', req_action)
    elif not token and request.form:
        token = request.form.get('token')
        req_action = request.form.get('action', req_action)

    secret_key = current_app.config.get('SECRET_KEY')
    is_valid, payload, error_msg = verify_action_token(token, secret_key=secret_key)

    # Prepare response helper
    def respond(success: bool, status_code: int, message: str, action: str = 'unknown', 
                instance_id: str = 'N/A', details: dict = None):
        if request.headers.get('Accept') == 'application/json' or request.is_json:
            return jsonify({
                'success': success,
                'status_code': status_code,
                'action': action,
                'instance_id': instance_id,
                'message': message,
                'details': details or {}
            }), status_code
        
        return render_template(
            'action_response.html',
            success=success,
            status_code=status_code,
            action=action,
            instance_id=instance_id,
            message=message,
            timestamp=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'),
            details=details or {}
        ), status_code

    if not is_valid:
        return respond(
            success=False,
            status_code=400,
            message=f"Action Request Rejected: {error_msg} (Workload is already safely stopped.)" if "already been executed" in str(error_msg).lower() else f"Action Request Rejected: {error_msg}",
            action=req_action or 'unknown',
            instance_id=payload.get('instance_id') if payload else 'N/A'
        )

    # Extract verified payload
    instance_id = payload['instance_id']
    action = payload['action']
    extend_minutes = payload.get('extend_minutes', 60)

    # Single-use enforcement
    mark_token_consumed(token)

    db_session = db.session
    try:
        resource = db_session.query(CloudResource).filter_by(instance_id=instance_id).first()
        if not resource:
            # Sync / fetch if not found
            cloud_svc = get_cloud_service(current_app.config)
            cloud_inst = cloud_svc.get_instance(instance_id)
            if not cloud_inst:
                if current_app.config.get('USE_MOCK_AWS', True) or instance_id.startswith('i-') or instance_id.startswith('vm-'):
                    is_azure = instance_id.startswith('vm-') or 'azure' in instance_id.lower()
                    cloud_inst = {
                        'instance_id': instance_id,
                        'instance_name': f"Workload-{instance_id}",
                        'provider': 'Azure' if is_azure else 'AWS',
                        'region': 'eastus' if is_azure else 'us-east-1',
                        'state': 'running'
                    }
                    if hasattr(cloud_svc, 'instances'):
                        cloud_svc.instances[instance_id] = cloud_inst
                else:
                    return respond(
                        success=False,
                        status_code=404,
                        message=f"Instance {instance_id} was not found in cloud inventory.",
                        action=action,
                        instance_id=instance_id
                    )

        now = datetime.now(timezone.utc)

        if action == 'stop':
            # Stop instance using provider-specific adapter (AWS or Azure)
            target_svc = get_cloud_service_for_resource(resource, current_app.config, db_session)
            cloud_res = target_svc.stop_instance(instance_id, getattr(resource, 'region', None))

            # Sync mock dictionary if mock service active
            mock_svc = get_cloud_service(current_app.config)
            if hasattr(mock_svc, 'instances') and instance_id in mock_svc.instances:
                mock_svc.instances[instance_id]['state'] = 'stopped'

            if resource:
                resource.state = 'stopped'
                resource.launch_time = None
                resource.public_ip = None
                resource.alert_sent_at = None

            prov = resource.provider if resource else ('Azure' if instance_id.startswith('vm-') else 'AWS')
            audit = AuditTrail(
                resource_id=resource.id if resource else None,
                triggered_by=f"WEBHOOK_HMAC:{instance_id}",
                action_taken='STOP',
                details=f"{prov} instance {instance_id} successfully stopped via single-click verified HMAC action webhook from mobile phone."
            )
            db_session.add(audit)
            db_session.commit()

            return respond(
                success=True,
                status_code=200,
                message=f"{prov} instance {instance_id} has been safely powered down from your phone. Cost burn stopped.",
                action='STOP',
                instance_id=instance_id,
                details={
                    'instance_name': resource.instance_name if resource else instance_id,
                    'provider': prov,
                    'region': resource.region if resource else 'us-east-1',
                    'new_state': 'STOPPED',
                    'audit_id': audit.id
                }
            )

        elif action == 'extend':
            # Extend lease
            new_expiry = now + timedelta(minutes=extend_minutes)
            if resource:
                resource.lease_expires_at = new_expiry
                resource.alert_sent_at = None  # Clear alert violation since lease was extended

            prov = resource.provider if resource else 'Cloud'
            audit = AuditTrail(
                resource_id=resource.id if resource else None,
                triggered_by=f"PHONE_1CLICK:{instance_id}",
                action_taken='EXTEND_LEASE',
                details=f"{prov} instance {instance_id} operating lease extended by {extend_minutes} minutes until {new_expiry.strftime('%Y-%m-%d %H:%M:%S UTC')}."
            )
            db_session.add(audit)
            db_session.commit()

            return respond(
                success=True,
                status_code=200,
                message=f"Runtime lease for {prov} instance {instance_id} was extended by {extend_minutes} minutes.",
                action='EXTEND',
                instance_id=instance_id,
                details={
                    'instance_name': resource.instance_name if resource else instance_id,
                    'provider': prov,
                    'region': resource.region if resource else 'us-east-1',
                    'lease_expires_at': new_expiry.strftime('%Y-%m-%d %H:%M:%S UTC'),
                    'extension_duration': f"{extend_minutes} Minutes",
                    'audit_id': audit.id
                }
            )

        else:
            return respond(
                success=False,
                status_code=400,
                message=f"Unsupported action: {action}",
                action=action,
                instance_id=instance_id
            )

    except Exception as e:
        db_session.rollback()
        return respond(
            success=False,
            status_code=500,
            message=f"Internal Server Error processing webhook: {str(e)}",
            action=action,
            instance_id=instance_id
        )
    finally:
        db_session.close()


def _process_phone_inbound_message(body: str, from_sender: str, channel: str = 'SMS') -> str:
    """
    Core engine processing inbound mobile SMS or WhatsApp text from user's phone.
    Enables remote command execution:
    - 'STOP' / 'STOP <instance_id>' / 'STOP ALL': Immediately powers down running AWS/Azure instance
    - 'EXTEND' / 'EXTEND <instance_id>': Extends operating lease by +60 minutes
    - 'STATUS' / other: Returns current running instance inventory and quick command instructions
    """
    db_session = db.session
    now = datetime.now(timezone.utc)

    # Query running resources
    running_resources = db_session.query(CloudResource).filter_by(state='running').all()

    clean_body = body.strip().lower()
    tokens = [t.strip() for t in clean_body.split() if t.strip()]
    cmd = tokens[0] if tokens else 'status'
    param = tokens[1] if len(tokens) > 1 else ''

    if 'stop' in cmd or cmd == 'stop':
        targets = []
        if param == 'all' or 'stop all' in clean_body:
            targets = running_resources
        elif param:
            for r in db_session.query(CloudResource).all():
                if param in r.instance_id.lower() or param in r.instance_name.lower():
                    targets.append(r)
        
        if not targets:
            # First check for instance with active policy breach / pending alert
            alerted = [r for r in running_resources if r.alert_sent_at is not None]
            if alerted:
                targets = [alerted[0]]
            elif running_resources:
                # Target the longest-running active instance
                sorted_by_uptime = sorted(running_resources, key=lambda x: x.uptime_hours, reverse=True)
                targets = [sorted_by_uptime[0]]

        if not targets:
            return "ℹ️ [CLOUD SCHEDULER] No active running instances found to stop. All AWS and Azure workloads are already powered down."

        stopped_names = []
        for res in targets:
            # Power down via appropriate AWS/Azure cloud adapter
            target_svc = get_cloud_service_for_resource(res, current_app.config, db_session)
            target_svc.stop_instance(res.instance_id, res.region)

            # Sync mock if mock service is used
            mock_svc = get_cloud_service(current_app.config)
            if hasattr(mock_svc, 'instances') and res.instance_id in mock_svc.instances:
                mock_svc.instances[res.instance_id]['state'] = 'stopped'

            res.state = 'stopped'
            res.launch_time = None
            res.public_ip = None
            res.alert_sent_at = None

            audit = AuditTrail(
                resource_id=res.id,
                triggered_by=f"PHONE_{channel}:{from_sender}",
                action_taken='STOP',
                details=f"{res.provider} instance {res.instance_id} ({res.instance_name}) stopped via incoming {channel} 'STOP' command from {from_sender}."
            )
            db_session.add(audit)
            stopped_names.append(f"• {res.instance_name} ({res.instance_id} - {res.provider})")

        db_session.commit()
        joined = "\n".join(stopped_names)
        return (
            f"🛑 [CLOUD SCHEDULER - PHONE STOPPED]\n"
            f"Successfully powered down from your phone:\n"
            f"{joined}\n\n"
            f"Cloud cost burn terminated immediately."
        )

    elif 'extend' in cmd or cmd == 'extend':
        targets = []
        if param:
            for r in db_session.query(CloudResource).all():
                if param in r.instance_id.lower() or param in r.instance_name.lower():
                    targets.append(r)
        if not targets:
            alerted = [r for r in running_resources if r.alert_sent_at is not None]
            targets = [alerted[0]] if alerted else (running_resources[:1] if running_resources else [])

        if not targets:
            return "ℹ️ [CLOUD SCHEDULER] No active instances found to extend lease."

        extended_names = []
        new_expiry = now + timedelta(minutes=60)
        for res in targets:
            res.lease_expires_at = new_expiry
            res.alert_sent_at = None

            audit = AuditTrail(
                resource_id=res.id,
                triggered_by=f"PHONE_{channel}:{from_sender}",
                action_taken='EXTEND_LEASE',
                details=f"{res.provider} instance {res.instance_id} operating lease extended by +60m via {channel} from {from_sender}."
            )
            db_session.add(audit)
            extended_names.append(f"• {res.instance_name} ({res.instance_id} - {res.provider})")

        db_session.commit()
        return (
            f"⏳ [CLOUD SCHEDULER - LEASE EXTENDED]\n"
            f"Operating lease extended by +60 minutes for:\n"
            f"{', '.join(extended_names)}\n"
            f"Valid until {new_expiry.strftime('%H:%M:%S UTC')}."
        )

    else:
        # Status command or unrecognized text: provide status & help
        if not running_resources:
            return (
                "ℹ️ [CLOUD SCHEDULER]\n"
                "All AWS and Azure cloud resources are currently STOPPED.\n"
                "Zero cost burn active."
            )

        lines = ["ℹ️ [CLOUD SCHEDULER - RUNNING WORKLOADS]"]
        for r in running_resources:
            lines.append(f"• {r.instance_name} ({r.instance_id})\n  Provider: {r.provider} | Uptime: {r.uptime_hours}h")
        lines.append(
            "\n⚡ Mobile Quick Commands:\n"
            "• Reply 'STOP' to stop breached instance\n"
            "• Reply 'STOP ALL' to shut down all running instances\n"
            "• Reply 'EXTEND' to add +60m lease"
        )
        return "\n".join(lines)


@webhook_bp.route('/webhook/twilio/sms', methods=['GET', 'POST'])
@webhook_bp.route('/webhook/sms', methods=['GET', 'POST'])
def handle_twilio_sms():
    """
    Handles incoming SMS webhooks from Twilio when user replies 'STOP' or 'EXTEND' from their phone.
    Executes immediate remote instance shutdown and replies with TwiML XML confirmation.
    """
    body = (request.values.get('Body') or request.args.get('Body') or '').strip()
    from_number = request.values.get('From') or request.args.get('From') or 'Mobile'

    reply_text = _process_phone_inbound_message(body, from_number, channel='SMS')

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{reply_text}</Message>
</Response>"""
    return Response(twiml, mimetype='application/xml')


@webhook_bp.route('/webhook/twilio/whatsapp', methods=['GET', 'POST'])
@webhook_bp.route('/webhook/whatsapp', methods=['GET', 'POST'])
def handle_twilio_whatsapp():
    """
    Handles incoming WhatsApp messages from Twilio WhatsApp Sandbox.
    Executes immediate remote instance shutdown and replies with TwiML XML confirmation.
    """
    body = (request.values.get('Body') or request.args.get('Body') or '').strip()
    from_number = request.values.get('From') or request.args.get('From') or 'WhatsApp'

    reply_text = _process_phone_inbound_message(body, from_number, channel='WhatsApp')

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{reply_text}</Message>
</Response>"""
    return Response(twiml, mimetype='application/xml')
