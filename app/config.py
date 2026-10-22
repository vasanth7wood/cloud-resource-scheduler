import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base application configuration class."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-cloud-scheduler-super-secret-key-2026')
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 't')
    PORT = int(os.environ.get('PORT', 5000))

    # Base URL for Webhook generation
    WEBHOOK_BASE_URL = os.environ.get('WEBHOOK_BASE_URL', 'http://localhost:5000').rstrip('/')

    # Database Configuration
    DATABASE_URL = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:password@localhost:3306/cloud_scheduler')
    USE_SQLITE_FALLBACK = os.environ.get('USE_SQLITE_FALLBACK', 'True').lower() in ('true', '1', 't')
    SQLITE_DB_PATH = os.environ.get('SQLITE_DB_PATH', 'sqlite:///cloud_scheduler.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # AWS Cloud Integration
    USE_MOCK_AWS = os.environ.get('USE_MOCK_AWS', 'True').lower() in ('true', '1', 't')
    AWS_DEFAULT_REGION = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', None)
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', None)

    # Task Scheduler Configuration
    SCAN_INTERVAL_SECONDS = int(os.environ.get('SCAN_INTERVAL_SECONDS', 60))
    GRACE_PERIOD_MINUTES = int(os.environ.get('GRACE_PERIOD_MINUTES', 30))
    ACTION_TOKEN_TTL_SECONDS = int(os.environ.get('ACTION_TOKEN_TTL_SECONDS', 900))  # 15 minutes

    # FinOps Cost Model
    HOURLY_COST_PER_INSTANCE_USD = float(os.environ.get('HOURLY_COST_PER_INSTANCE_USD', 0.096))
    USD_TO_INR_RATE = float(os.environ.get('USD_TO_INR_RATE', 83.50))

    # Multi-Channel Alert Gateway: Twilio (SMS & WhatsApp)
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '')
    TWILIO_WHATSAPP_NUMBER = os.environ.get('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+17372508034')
    TWILIO_WHATSAPP_CONTENT_SID = os.environ.get('TWILIO_WHATSAPP_CONTENT_SID', '')
    CALLMEBOT_APIKEY = os.environ.get('CALLMEBOT_APIKEY', '')
    NTFY_TOPIC = os.environ.get('NTFY_TOPIC', 'vasanth_cloud_alerts')

    # Alert Recipients
    ALERT_PHONE_NUMBER = os.environ.get('ALERT_PHONE_NUMBER', '+12015550199')
    ALERT_WHATSAPP_NUMBER = os.environ.get('ALERT_WHATSAPP_NUMBER', 'whatsapp:+12015550199')
    ALERT_EMAIL_RECIPIENT = os.environ.get('ALERT_EMAIL_RECIPIENT', 'cloud-admin@example.com')

    # Multi-Channel Alert Gateway: Email (SMTP)
    SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
    SMTP_USE_TLS = os.environ.get('SMTP_USE_TLS', 'True').lower() in ('true', '1', 't')
    SMTP_USER = os.environ.get('SMTP_USER', '')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
    SMTP_FROM_EMAIL = os.environ.get('SMTP_FROM_EMAIL', 'cloud-alerts@example.com')
    SMTP_FROM_NAME = os.environ.get('SMTP_FROM_NAME', 'Cloud Resource Scheduler')

class TestConfig(Config):
    """Configuration for automated test suite."""
    TESTING = True
    DEBUG = False
    USE_SQLITE_FALLBACK = True
    DATABASE_URL = 'sqlite:///:memory:'
    USE_MOCK_AWS = True
    SCAN_INTERVAL_SECONDS = 5
    GRACE_PERIOD_MINUTES = 1
    ACTION_TOKEN_TTL_SECONDS = 900
