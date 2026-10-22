from datetime import datetime, timezone, timedelta
import hashlib
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.models.models import db, CloudResource, Schedule, AlertLog, AuditTrail
from app.services.cloud_service import get_cloud_service, get_cloud_service_for_resource
from app.services.token_utils import generate_action_token
from app.services.notification_service import NotificationService
from app.services.tunnel_service import get_public_base_url

logger = logging.getLogger(__name__)

class SchedulerService:
    """
    In-process APScheduler orchestrator. Runs continuous cloud governance audits,
    evaluates policy constraints, and triggers multi-channel alerts or automated shutdowns.
    """
    def __init__(self, config=None, app=None):
        self.config = config
        self.app = app
        self.scheduler = BackgroundScheduler(daemon=True)
        self.notification_service = NotificationService(config=config)
        self.job_id = 'cloud_resource_audit_job'

    def start(self):
        """Starts the background scheduler."""
        if not self.scheduler.running:
            interval = getattr(self.config, 'SCAN_INTERVAL_SECONDS', 60) if self.config else 60
            self.scheduler.add_job(
                func=self.audit_and_enforce_policies,
                trigger=IntervalTrigger(seconds=interval),
                id=self.job_id,
                name="Periodic Cloud Resource Policy Audit",
                replace_existing=True
            )
            self.scheduler.start()
            logger.info(f"[SCHEDULER] APScheduler started. Running audits every {interval}s.")

    def shutdown(self):
        """Stops the scheduler safely."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("[SCHEDULER] APScheduler stopped.")

    def sync_cloud_inventory(self, session, add_new: bool = True) -> int:
        """Discovers instances from Cloud Service and syncs with database records."""
        cloud_service = get_cloud_service(self.config)
        instances = cloud_service.discover_instances()
        now = datetime.now(timezone.utc)
        count = 0

        is_mock = getattr(self.config, 'USE_MOCK_AWS', True)
        for inst in instances:
            res = session.query(CloudResource).filter_by(instance_id=inst['instance_id']).first()
            if not res and add_new:
                init_state = inst.get('state', 'stopped')
                res = CloudResource(
                    instance_id=inst['instance_id'],
                    instance_name=inst.get('instance_name', inst['instance_id']),
                    provider=inst.get('provider', 'AWS'),
                    region=inst.get('region', 'us-east-1'),
                    state=init_state,
                    instance_type=inst.get('instance_type', 't3.medium'),
                    public_ip=inst.get('public_ip') if init_state == 'running' else None,
                    private_ip=inst.get('private_ip'),
                    launch_time=inst.get('launch_time') if init_state == 'running' else None,
                    last_scanned_at=now
                )
                session.add(res)
                session.flush()
                count += 1
            elif res:
                # Update existing instance state
                res.instance_name = inst.get('instance_name', res.instance_name)
                res.instance_type = inst.get('instance_type', res.instance_type)
                res.private_ip = inst.get('private_ip', res.private_ip)
                
                if not is_mock:
                    # In live cloud mode, sync state from actual cloud provider API
                    res.state = inst.get('state', res.state)
                    res.public_ip = inst.get('public_ip')
                    if inst.get('launch_time'):
                        res.launch_time = inst.get('launch_time')
                    elif res.state == 'stopped':
                        res.launch_time = None
                else:
                    # In simulated mode, user explicitly starts or stops instances!
                    # Sync mock in-memory state from the database
                    inst['state'] = res.state
                    inst['launch_time'] = res.launch_time
                    inst['public_ip'] = res.public_ip
                    if res.state == 'stopped':
                        res.launch_time = None
                        res.public_ip = None

                res.last_scanned_at = now
                count += 1

        session.commit()
        return count

    def audit_and_enforce_policies(self) -> dict:
        """
        Executes complete governance audit cycle:
        1. Synchronizes inventory with cloud provider.
        2. Inspects all running instances against defined schedules.
        3. Dispatches multi-channel alerts if violations are detected.
        4. Triggers automated shutdowns if grace period has elapsed.
        """
        logger.info("[AUDIT] Beginning cloud governance audit cycle...")
        now = datetime.now(timezone.utc)
        results = {
            'audited_at': now.isoformat(),
            'violations_detected': 0,
            'alerts_dispatched': 0,
            'shutdowns_executed': 0,
            'details': []
        }

        # Handle Flask application context if available and not already within an active context
        from flask import has_app_context
        pushed_context = None
        if not has_app_context() and self.app:
            pushed_context = self.app.app_context()
            pushed_context.push()

        session = db.session
        try:
            # Step 1: Synchronize existing inventory state (do not auto-add until user discovers)
            self.sync_cloud_inventory(session, add_new=False)

            # Step 2: Query running instances
            running_resources = session.query(CloudResource).filter_by(state='running').all()
            cloud_service = get_cloud_service(self.config)

            grace_period_mins = getattr(self.config, 'GRACE_PERIOD_MINUTES', 30) if self.config else 30
            ttl_seconds = getattr(self.config, 'ACTION_TOKEN_TTL_SECONDS', 900) if self.config else 900
            base_url = get_public_base_url(app=self.app).rstrip('/')

            for res in running_resources:
                # Check for active lease override
                if res.is_lease_active:
                    logger.debug(f"[AUDIT] Resource {res.instance_id} has active lease until {res.lease_expires_at}. Exemption active.")
                    continue

                # Fetch active schedule
                sched = session.query(Schedule).filter_by(resource_id=res.id, is_active=True).first()
                
                # Policy checks
                violation_reasons = []

                if sched:
                    # Check 1: Allowed operating window and days
                    if not sched.is_time_in_schedule(now):
                        violation_reasons.append(
                            f"Running outside authorized operating window ({sched.start_time} - {sched.end_time}) or outside allowed days ({sched.days_of_week})"
                        )

                    # Check 2: Max continuous runtime
                    uptime = res.uptime_hours
                    max_runtime = float(sched.max_runtime_hours) if sched.max_runtime_hours else 8.0
                    if uptime > max_runtime:
                        violation_reasons.append(
                            f"Continuous runtime ({uptime:.1f} hrs) exceeded policy threshold of {max_runtime:.1f} hrs"
                        )
                else:
                    # Unscheduled workload: check against enterprise baseline (default 8.0 hrs)
                    default_max_hours = float(getattr(self.config, 'DEFAULT_MAX_RUNTIME_HOURS', 8.0) if self.config else 8.0)
                    if res.uptime_hours > default_max_hours:
                        violation_reasons.append(
                            f"Unscheduled {res.provider} workload continuous runtime ({res.uptime_hours:.1f} hrs) exceeded enterprise cap of {default_max_hours:.1f} hrs"
                        )
                    else:
                        continue

                # If violation found
                if violation_reasons:
                    results['violations_detected'] += 1
                    reason_str = " | ".join(violation_reasons)

                    # Check grace period status
                    if res.alert_sent_at is None:
                        # First time violation detected -> Dispatch alerts
                        res.alert_sent_at = now
                        session.commit()

                        # Generate signed HMAC action tokens
                        stop_token = generate_action_token(
                            res.instance_id, 'stop', ttl_seconds=ttl_seconds, 
                            secret_key=getattr(self.config, 'SECRET_KEY', None)
                        )
                        extend_token = generate_action_token(
                            res.instance_id, 'extend', ttl_seconds=ttl_seconds, 
                            extend_minutes=60, secret_key=getattr(self.config, 'SECRET_KEY', None)
                        )

                        stop_url = f"{base_url}/webhook/action?token={stop_token}&action=stop"
                        extend_url = f"{base_url}/webhook/action?token={extend_token}&action=extend"
                        token_hash = hashlib.sha256(stop_token.encode('utf-8')).hexdigest()

                        inst_payload = res.to_dict()
                        if sched:
                            inst_payload['schedule'] = sched.to_dict()
                            inst_payload['start_time'] = sched.start_time
                            inst_payload['end_time'] = sched.end_time
                            inst_payload['stop_time'] = sched.end_time
                            inst_payload['max_runtime_hours'] = float(sched.max_runtime_hours) if sched.max_runtime_hours else 8.0

                        # Dispatch multi-channel notification (Buzzer sound delivered directly to phone; PC silent)
                        dispatch_info = self.notification_service.dispatch_incident_alert(
                            instance_data=inst_payload,
                            reason=reason_str,
                            stop_url=stop_url,
                            extend_url=extend_url,
                            token_hash=token_hash,
                            recipient_phone=res.alert_phone,
                            recipient_whatsapp=res.alert_whatsapp,
                            recipient_email=res.alert_email,
                            sound_buzzer=True
                        )

                        # Record alert logs in database
                        for channel_key, channel_res in dispatch_info['channels'].items():
                            alert_log = AlertLog(
                                resource_id=res.id,
                                channel=channel_res.get('channel', channel_key),
                                recipient=channel_res.get('recipient', 'N/A'),
                                status=channel_res.get('status', 'SENT'),
                                token_hash=token_hash,
                                details=f"Violation: {reason_str}"
                            )
                            session.add(alert_log)

                        # Record audit trail
                        audit = AuditTrail(
                            resource_id=res.id,
                            triggered_by='SCHEDULER',
                            action_taken='ALERT_DISPATCHED',
                            details=f"Multi-channel breach alert dispatched. Violation: {reason_str}. Grace period {grace_period_mins} mins initiated."
                        )
                        session.add(audit)
                        session.commit()

                        results['alerts_dispatched'] += 1
                        results['details'].append({
                            'instance_id': res.instance_id,
                            'action': 'ALERT_DISPATCHED',
                            'reason': reason_str
                        })
                    else:
                        # Alert already sent. Check if grace window has expired.
                        alert_time = res.alert_sent_at if res.alert_sent_at.tzinfo else res.alert_sent_at.replace(tzinfo=timezone.utc)
                        elapsed_minutes = (now - alert_time).total_seconds() / 60.0

                        if elapsed_minutes >= grace_period_mins:
                            # Automated fallback: shutdown instance!
                            logger.warning(
                                f"[AUTO-SHUTDOWN] Grace period of {grace_period_mins}m expired for {res.instance_id} "
                                f"(elapsed: {elapsed_minutes:.1f}m). Executing automated shutdown and sounding buzzer alarm!"
                            )
                            target_svc = get_cloud_service_for_resource(res, self.config, session)
                            target_svc.stop_instance(res.instance_id, res.region)

                            mock_svc = get_cloud_service(self.config)
                            if hasattr(mock_svc, 'instances') and res.instance_id in mock_svc.instances:
                                mock_svc.instances[res.instance_id]['state'] = 'stopped'

                            # Grace period ended: Dispatch loud buzzer alarm to ntfy / phone channels
                            inst_dict = res.to_dict()
                            expiry_dispatch = self.notification_service.dispatch_grace_expiry_alert(
                                instance_data=inst_dict,
                                grace_period_mins=grace_period_mins,
                                reason=reason_str,
                                recipient_phone=res.alert_phone,
                                recipient_whatsapp=res.alert_whatsapp,
                                recipient_email=res.alert_email,
                                sound_buzzer=True
                            )

                            for ch_key, ch_res in expiry_dispatch.get('channels', {}).items():
                                expiry_alert_log = AlertLog(
                                    resource_id=res.id,
                                    channel=ch_res.get('channel', ch_key),
                                    recipient=ch_res.get('recipient', 'N/A'),
                                    status=ch_res.get('status', 'SENT'),
                                    token_hash='GRACE_PERIOD_EXPIRED',
                                    details=f"🚨 BUZZER ALARM: Grace period {grace_period_mins}m ended. Auto-shutdown executed. Violation: {reason_str}"
                                )
                                session.add(expiry_alert_log)

                            res.state = 'stopped'
                            res.launch_time = None
                            res.public_ip = None
                            res.alert_sent_at = None  # Reset alert tracker
                            session.commit()

                            audit = AuditTrail(
                                resource_id=res.id,
                                triggered_by='SCHEDULER_GRACE_PERIOD',
                                action_taken='POLICY_SHUTDOWN',
                                details=(
                                    f"Automated fallback shutdown executed after {grace_period_mins}-minute grace period "
                                    f"elapsed without user acknowledgment. Loud buzzer alarm dispatched. Reason: {reason_str}"
                                )
                            )
                            session.add(audit)
                            session.commit()

                            results['shutdowns_executed'] += 1
                            results['details'].append({
                                'instance_id': res.instance_id,
                                'action': 'POLICY_SHUTDOWN',
                                'reason': f"Grace period of {grace_period_mins}m expired without action. Buzzer alarm dispatched."
                            })
                else:
                    # Resource compliant; reset alert state if previously marked
                    if res.alert_sent_at is not None:
                        res.alert_sent_at = None
                        session.commit()

        except Exception as e:
            session.rollback()
            logger.error(f"[AUDIT ERROR] Exception during policy audit: {str(e)}", exc_info=True)
            results['error'] = str(e)
        finally:
            if pushed_context:
                session.close()
                pushed_context.pop()

        return results

    def trigger_immediate_audit(self) -> dict:
        """On-demand policy evaluation trigger for immediate dashboard or API execution."""
        return self.audit_and_enforce_policies()
