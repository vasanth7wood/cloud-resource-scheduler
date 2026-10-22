import pytest
import os
from datetime import datetime, timezone, timedelta
from app import create_app
from app.config import TestConfig
from app.models.models import Base, db, User, CloudResource, Schedule, AlertLog, AuditTrail
from app.services.cloud_service import reset_cloud_service, MockCloudService

@pytest.fixture(scope='function')
def app():
    """Creates a fresh test application instance with in-memory SQLite."""
    reset_cloud_service()
    app = create_app(TestConfig, start_scheduler=False)
    
    with app.app_context():
        # Ensure fresh database tables
        Base.metadata.drop_all(db.engine)
        Base.metadata.create_all(db.engine)
        
        # Seed test admin user
        admin = User(
            name='Test Admin',
            email='admin@test.internal',
            phone_number='+12015550199',
            role='Admin'
        )
        admin.set_password('Admin@123456')
        db.session.add(admin)

        # Seed test running resource
        res = CloudResource(
            instance_id='i-test001running',
            instance_name='Test-Worker-Instance',
            provider='AWS',
            region='us-east-1',
            state='running',
            instance_type='t3.large',
            public_ip='54.210.1.1',
            private_ip='10.0.1.5',
            launch_time=datetime.now(timezone.utc) - timedelta(hours=6)
        )
        db.session.add(res)
        db.session.flush()

        # Seed schedule: outside working hours (e.g. 01:00 - 02:00) to guarantee policy breach
        sched = Schedule(
            resource_id=res.id,
            start_time='01:00',
            end_time='02:00',
            max_runtime_hours=2.00,
            days_of_week='MON',
            is_active=True
        )
        db.session.add(sched)
        db.session.commit()

        yield app

        db.remove()
        Base.metadata.drop_all(db.engine)

@pytest.fixture(scope='function')
def client(app):
    """Provides Flask test client."""
    return app.test_client()

@pytest.fixture(scope='function')
def authenticated_client(client, app):
    """Provides test client with authenticated Admin session."""
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['user_name'] = 'Test Admin'
        sess['user_email'] = 'admin@test.internal'
        sess['user_role'] = 'Admin'
    return client
