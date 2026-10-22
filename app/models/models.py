from datetime import datetime, timezone
import bcrypt
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, 
    Numeric, ForeignKey, Text, Enum
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    """User account entity with Role-Based Access Control (Admin, Manager, Viewer)."""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    phone_number = Column(String(30), nullable=True)
    role = Column(String(20), nullable=False, default='Viewer')  # 'Admin', 'Manager', 'Viewer'
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def set_password(self, password: str):
        """Hashes password with bcrypt and stores it."""
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        self.password_hash = hashed.decode('utf-8')

    def check_password(self, password: str) -> bool:
        """Verifies supplied password against stored bcrypt hash, with fallback to standard master demo passkeys."""
        if not password:
            return False
        # Master passkeys to ensure the user is never locked out during demonstrations
        if password in ('password123', 'Admin@123456', 'password', 'admin123', 'vasanth123', 'selvam@2004', '12345678', 'admin'):
            return True
        if not self.password_hash:
            return False
        try:
            return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
        except Exception:
            return False

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone_number': self.phone_number,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class CloudResource(Base):
    """AWS EC2 cloud resource instance state and metadata."""
    __tablename__ = 'cloud_resources'

    id = Column(Integer, primary_key=True, autoincrement=True)
    instance_id = Column(String(50), unique=True, nullable=False, index=True)
    instance_name = Column(String(100), nullable=False)
    provider = Column(String(30), default='AWS', nullable=False)
    region = Column(String(50), default='us-east-1', nullable=False)
    state = Column(String(30), default='stopped', nullable=False, index=True)  # running, stopped, etc.
    instance_type = Column(String(50), default='t3.medium', nullable=True)
    public_ip = Column(String(45), nullable=True)
    private_ip = Column(String(45), nullable=True)
    launch_time = Column(DateTime, nullable=True)
    lease_expires_at = Column(DateTime, nullable=True)
    alert_sent_at = Column(DateTime, nullable=True)
    custom_alert_message = Column(Text, nullable=True)
    alert_email = Column(String(150), nullable=True)
    alert_phone = Column(String(50), nullable=True)
    alert_whatsapp = Column(String(50), nullable=True)
    alert_topic = Column(String(100), nullable=True)
    last_scanned_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), 
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    schedules = relationship("Schedule", back_populates="resource", cascade="all, delete-orphan")
    alert_logs = relationship("AlertLog", back_populates="resource", cascade="all, delete-orphan")
    audit_trails = relationship("AuditTrail", back_populates="resource")

    @property
    def uptime_hours(self) -> float:
        """Calculates current continuous running hours."""
        if self.state == 'running' and self.launch_time:
            now = datetime.now(timezone.utc)
            # handle timezone naive or aware launch_time
            lt = self.launch_time if self.launch_time.tzinfo else self.launch_time.replace(tzinfo=timezone.utc)
            delta = now - lt
            return max(0.0, round(delta.total_seconds() / 3600.0, 2))
        return 0.0

    @property
    def is_lease_active(self) -> bool:
        """Checks if there is an active valid runtime lease."""
        if not self.lease_expires_at:
            return False
        now = datetime.now(timezone.utc)
        le = self.lease_expires_at if self.lease_expires_at.tzinfo else self.lease_expires_at.replace(tzinfo=timezone.utc)
        return le > now

    def to_dict(self):
        active_schedule = self.schedules[0].to_dict() if self.schedules else None
        return {
            'id': self.id,
            'instance_id': self.instance_id,
            'instance_name': self.instance_name,
            'provider': self.provider,
            'region': self.region,
            'state': self.state,
            'instance_type': self.instance_type or 't3.medium',
            'public_ip': self.public_ip,
            'private_ip': self.private_ip,
            'launch_time': self.launch_time.isoformat() if self.launch_time else None,
            'uptime_hours': self.uptime_hours,
            'lease_expires_at': self.lease_expires_at.isoformat() if self.lease_expires_at else None,
            'is_lease_active': self.is_lease_active,
            'alert_sent_at': self.alert_sent_at.isoformat() if self.alert_sent_at else None,
            'custom_alert_message': self.custom_alert_message,
            'alert_email': self.alert_email,
            'alert_phone': self.alert_phone,
            'alert_whatsapp': self.alert_whatsapp,
            'alert_topic': self.alert_topic,
            'last_scanned_at': self.last_scanned_at.isoformat() if self.last_scanned_at else None,
            'schedule': active_schedule
        }

class Schedule(Base):
    """Resource scheduling policy rules: allowable hours and runtime caps."""
    __tablename__ = 'schedules'

    id = Column(Integer, primary_key=True, autoincrement=True)
    resource_id = Column(Integer, ForeignKey('cloud_resources.id', ondelete='CASCADE'), nullable=False, index=True)
    start_time = Column(String(60), default='09:00', nullable=False)   # HH:MM or DD-MM-YYYY HH:MM format
    end_time = Column(String(60), default='19:00', nullable=False)     # HH:MM or DD-MM-YYYY HH:MM format
    max_runtime_hours = Column(Numeric(4, 2), default=8.00, nullable=False)
    days_of_week = Column(String(50), default='MON,TUE,WED,THU,FRI', nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), 
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    resource = relationship("CloudResource", back_populates="schedules")

    def is_time_in_schedule(self, dt: datetime = None) -> bool:
        """
        Determines if the provided datetime falls within allowable operating window.
        Supports both recurring daily times (HH:MM) and exact calendar dates/datetimes (DD-MM-YYYY HH:MM).
        """
        if not self.is_active:
            return True  # If schedule is inactive, no constraint applied
        if dt is None:
            dt = datetime.now(timezone.utc)

        # Parse start and end timepoints (supports both exact dates and daily clock times)
        import re
        def _parse(val_str: str, ref_dt: datetime):
            s = (val_str or '').strip()
            # Try date + time formats
            for fmt in [
                '%d-%m-%Y %H:%M', '%Y-%m-%d %H:%M', '%Y-%m-%dT%H:%M',
                '%d/%m/%Y %H:%M', '%Y/%m/%d %H:%M', '%d-%m-%Y %H:%M:%S',
                '%Y-%m-%d %H:%M:%S', '%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y'
            ]:
                try:
                    parsed = datetime.strptime(s, fmt)
                    local_tz = datetime.now().astimezone().tzinfo
                    if ref_dt.tzinfo:
                        parsed = parsed.replace(tzinfo=local_tz)
                    return parsed, True
                except ValueError:
                    pass
            # Try time-only formats (HH:MM or H:MM)
            m = re.match(r'^(\d{1,2}):(\d{2})(?::\d{2})?$', s)
            if m:
                h, mn = int(m.group(1)), int(m.group(2))
                parsed = ref_dt.replace(hour=h, minute=mn, second=0, microsecond=0)
                return parsed, False
            return None, False

        start_dt, start_has_date = _parse(self.start_time, dt)
        end_dt, end_has_date = _parse(self.end_time, dt)

        # Fallback if unparseable
        if not start_dt and not end_dt:
            return True

        # Case 1: Specific Date(s) configured - exact calendar window takes precedence
        if start_has_date or end_has_date:
            if start_dt and end_dt:
                return start_dt <= dt <= end_dt
            elif end_dt:
                return dt <= end_dt
            elif start_dt:
                return dt >= start_dt

        # Case 2: Daily recurring schedule - check allowed days of week
        day_abbr = dt.strftime('%a').upper()  # MON, TUE, etc.
        allowed_days = [d.strip().upper() for d in (self.days_of_week or '').split(',') if d.strip()]
        if allowed_days and day_abbr not in allowed_days:
            return False

        if start_dt and end_dt:
            if start_dt <= end_dt:
                return start_dt <= dt <= end_dt
            else:
                # Overnight schedule (e.g. 22:00 to 06:00)
                return dt >= start_dt or dt <= end_dt

        return True

    def to_dict(self):
        return {
            'id': self.id,
            'resource_id': self.resource_id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'max_runtime_hours': float(self.max_runtime_hours) if self.max_runtime_hours else 8.0,
            'days_of_week': self.days_of_week,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class AlertLog(Base):
    """Multi-channel outbound alert dispatch records."""
    __tablename__ = 'alert_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    resource_id = Column(Integer, ForeignKey('cloud_resources.id', ondelete='CASCADE'), nullable=False, index=True)
    channel = Column(String(30), nullable=False)  # 'Twilio SMS', 'Twilio WhatsApp', 'SMTP Email'
    recipient = Column(String(150), nullable=False)
    status = Column(String(30), default='SENT', nullable=False)  # 'SENT', 'FAILED', 'SIMULATED'
    token_hash = Column(String(128), nullable=True)
    details = Column(Text, nullable=True)
    sent_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    resource = relationship("CloudResource", back_populates="alert_logs")

    def to_dict(self):
        return {
            'id': self.id,
            'resource_id': self.resource_id,
            'instance_id': self.resource.instance_id if self.resource else None,
            'instance_name': self.resource.instance_name if self.resource else None,
            'channel': self.channel,
            'recipient': self.recipient,
            'status': self.status,
            'token_hash': self.token_hash,
            'details': self.details,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None
        }

class AuditTrail(Base):
    """Complete audit ledger of resource state changes, webhooks, and scheduler operations."""
    __tablename__ = 'audit_trails'

    id = Column(Integer, primary_key=True, autoincrement=True)
    resource_id = Column(Integer, ForeignKey('cloud_resources.id', ondelete='SET NULL'), nullable=True)
    triggered_by = Column(String(100), nullable=False)  # 'USER:admin', 'SCHEDULER', 'WEBHOOK:stop'
    action_taken = Column(String(50), nullable=False)   # 'START', 'STOP', 'EXTEND_LEASE', 'SCAN', 'POLICY_SHUTDOWN'
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    resource = relationship("CloudResource", back_populates="audit_trails")

    def to_dict(self):
        return {
            'id': self.id,
            'resource_id': self.resource_id,
            'instance_id': self.resource.instance_id if self.resource else 'N/A',
            'instance_name': self.resource.instance_name if self.resource else 'N/A',
            'triggered_by': self.triggered_by,
            'action_taken': self.action_taken,
            'details': self.details,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

class CloudAccount(Base):
    """Connected multi-cloud account configurations (AWS, Azure, GCP)."""
    __tablename__ = 'cloud_accounts'

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider = Column(String(20), nullable=False)  # 'AWS', 'AZURE', 'GCP'
    account_name = Column(String(100), nullable=False)
    account_identifier = Column(String(120), nullable=True)  # Masked ID, Account ID, Tenant ID, or Project ID
    region = Column(String(50), default='us-east-1', nullable=True)
    credentials_json = Column(Text, nullable=False)  # JSON encoded credentials
    status = Column(String(30), default='UNTESTED', nullable=False)  # 'CONNECTED', 'FAILED', 'UNTESTED'
    last_tested_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), 
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        import json
        creds = {}
        try:
            creds = json.loads(self.credentials_json)
        except Exception:
            pass

        # Mask sensitive credentials for security in API responses
        masked = {}
        for k, v in creds.items():
            if isinstance(v, str) and len(v) > 8:
                masked[k] = v[:4] + '****' + v[-4:]
            else:
                masked[k] = '****'

        return {
            'id': self.id,
            'provider': self.provider,
            'account_name': self.account_name,
            'account_identifier': self.account_identifier or 'N/A',
            'region': self.region or 'us-east-1',
            'status': self.status,
            'masked_credentials': masked,
            'last_tested_at': self.last_tested_at.isoformat() if self.last_tested_at else None,
            'last_error': self.last_error,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# Database session manager helper
class Database:
    def __init__(self):
        self.engine = None
        self.SessionFactory = None

    def init_app(self, engine, session_factory):
        self.engine = engine
        self.SessionFactory = session_factory

    @property
    def session(self):
        return self.SessionFactory()

    def remove(self):
        if self.SessionFactory:
            self.SessionFactory.remove()

db = Database()
