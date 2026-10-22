import os
import logging
from flask import Flask
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session

from app.config import Config
from app.models.models import Base, db, User, CloudResource, Schedule, AuditTrail
from app.routes.auth import auth_bp
from app.routes.dashboard import dashboard_bp
from app.routes.api import api_bp
from app.routes.webhook import webhook_bp
from app.services.scheduler_service import SchedulerService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
)
logger = logging.getLogger('cloud_scheduler')

def create_app(config_class=Config, start_scheduler=True):
    """
    Application factory for Cloud Resource Scheduling & Alert System.
    Configures database engine (MySQL with SQLite automatic fallback),
    registers blueprints, and launches background APScheduler.
    """
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(config_class)

    # --------------------------------------------------------------------------
    # Database Engine Initialization
    # --------------------------------------------------------------------------
    db_url = app.config.get('DATABASE_URL')
    engine = None
    connected = False

    # Attempt Primary Database Connection (MySQL)
    if db_url and not db_url.startswith('sqlite'):
        try:
            logger.info(f"Attempting connection to MySQL: {db_url.split('@')[-1] if '@' in db_url else db_url}")
            engine = create_engine(
                db_url,
                pool_pre_ping=True,
                pool_recycle=3600,
                connect_args={'connect_timeout': 1}
            )
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            connected = True
            logger.info("Successfully connected to MySQL database.")
        except Exception as e:
            logger.warning(f"MySQL connection failed: {str(e)}")
            if app.config.get('USE_SQLITE_FALLBACK', True):
                logger.info("Falling back to local SQLite engine...")
            else:
                raise e

    # Fallback to SQLite if primary connection not established
    if not connected:
        sqlite_uri = app.config.get('SQLITE_DB_PATH', 'sqlite:///cloud_scheduler.db')
        if app.config.get('TESTING'):
            sqlite_uri = 'sqlite:///:memory:'
        logger.info(f"Using SQLite database: {sqlite_uri}")
        engine = create_engine(
            sqlite_uri,
            connect_args={'check_same_thread': False} if sqlite_uri.startswith('sqlite') else {}
        )
        if sqlite_uri.startswith('sqlite') and not app.config.get('TESTING'):
            from sqlalchemy import event
            @event.listens_for(engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                try:
                    cursor = dbapi_connection.cursor()
                    cursor.execute("PRAGMA journal_mode=WAL")
                    cursor.execute("PRAGMA synchronous=NORMAL")
                    cursor.execute("PRAGMA cache_size=10000")
                    cursor.close()
                except Exception:
                    pass

    # Bind Session Factory
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    ScopedSession = scoped_session(session_factory)
    db.init_app(engine, ScopedSession)

    # Create tables
    Base.metadata.create_all(engine)
    _ensure_schema_columns(engine)

    # Seed initial system accounts and data if database is empty
    _seed_initial_data(db.session)

    # --------------------------------------------------------------------------
    # Register Route Blueprints
    # --------------------------------------------------------------------------
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(webhook_bp)

    # --------------------------------------------------------------------------
    # Task Scheduler Initialization (APScheduler)
    # --------------------------------------------------------------------------
    scheduler_service = SchedulerService(config=app.config, app=app)
    app.extensions['scheduler_service'] = scheduler_service

    if start_scheduler and not app.config.get('TESTING'):
        scheduler_service.start()

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        ScopedSession.remove()

    try:
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    except Exception:
        pass

    return app

def _seed_initial_data(session):
    """Seeds only the default authenticated operator account if empty. No pre-stored resources or schedules."""
    try:
        # Seed user account if none exists
        if session.query(User).count() == 0:
            logger.info("Initializing fresh user accounts...")
            vasanth = User(
                name='vasanth',
                email='vasanthkumar23212921@gmail.com',
                phone_number='+15551234567',
                role='Admin'
            )
            vasanth.set_password('Admin@123456')

            admin = User(
                name='Lead Cloud Architect',
                email='admin@cloudops.internal',
                phone_number='+12015550199',
                role='Admin'
            )
            admin.set_password('Admin@123456')

            session.add_all([vasanth, admin])
            session.commit()
            logger.info("Fresh database initialized with user account: vasanth (vasanthkumar23212921@gmail.com).")
    except Exception as e:
        session.rollback()
        logger.error(f"Error seeding user accounts: {str(e)}")
    finally:
        session.close()

def _ensure_schema_columns(engine):
    """Ensures dynamic columns for per-instance alerts exist in cloud_resources table."""
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(engine)
        if 'cloud_resources' not in inspector.get_table_names():
            return
        columns = [c['name'] for c in inspector.get_columns('cloud_resources')]
        new_cols = {
            'custom_alert_message': 'TEXT',
            'alert_email': 'VARCHAR(150)',
            'alert_phone': 'VARCHAR(50)',
            'alert_whatsapp': 'VARCHAR(50)',
            'alert_topic': 'VARCHAR(100)',
        }
        with engine.begin() as conn:
            for col_name, col_type in new_cols.items():
                if col_name not in columns:
                    conn.execute(text(f"ALTER TABLE cloud_resources ADD COLUMN {col_name} {col_type}"))
                    logger.info(f"[DB SCHEMA] Added column {col_name} to cloud_resources table.")
    except Exception as e:
        logger.warning(f"[DB SCHEMA] Column check notice: {e}")
