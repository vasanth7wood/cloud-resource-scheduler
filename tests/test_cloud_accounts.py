import pytest
import json
from app import create_app
from app.config import Config
from app.models.models import db, User, CloudResource, CloudAccount
from app.services.cloud_account_service import CloudAccountService

class TestConfig(Config):
    TESTING = True
    USE_SQLITE_FALLBACK = True
    SQLITE_DB_PATH = 'sqlite:///:memory:'
    USE_MOCK_AWS = True
    SECRET_KEY = 'test-secret-cloud-account-suite'

@pytest.fixture
def app():
    app = create_app(config_class=TestConfig, start_scheduler=False)
    with app.app_context():
        # Create test admin user
        admin = User(name='Admin', email='admin@test.local', role='Admin')
        admin.set_password('Admin@123456')
        db.session.add(admin)
        db.session.commit()
        yield app
        db.session.rollback()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_client(client):
    client.post('/login', json={'email': 'admin@test.local', 'password': 'Admin@123456'})
    return client

def test_aws_sandbox_connection():
    creds = {
        'aws_access_key_id': 'AKIA-SANDBOX-DEMO-KEY',
        'aws_secret_access_key': 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
        'aws_region': 'us-east-1',
        'use_sandbox': True
    }
    result = CloudAccountService.test_aws_connection(creds)
    assert result['success'] is True
    assert result['provider'] == 'AWS'
    assert result['account_id'] == '987654321012'
    assert 'permissions_verified' in result
    assert 'sts:GetCallerIdentity' in result['permissions_verified']

def test_aws_missing_credentials():
    creds = {'aws_access_key_id': '', 'aws_secret_access_key': ''}
    result = CloudAccountService.test_aws_connection(creds)
    assert result['success'] is False
    assert 'required' in result['error']

def test_azure_sandbox_connection():
    creds = {
        'azure_subscription_id': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
        'azure_tenant_id': '72f988bf-86f1-41af-91ab-2d7cd011db47',
        'azure_client_id': 'a4b8c9d0-1122-3344-5566-778899aabbcc',
        'azure_client_secret': 'SecretValue123!',
        'azure_region': 'eastus',
        'use_sandbox': True
    }
    result = CloudAccountService.test_azure_connection(creds)
    assert result['success'] is True
    assert result['provider'] == 'Azure'
    assert result['subscription_id'] == creds['azure_subscription_id']
    assert 'permissions_verified' in result

def test_azure_missing_credentials():
    creds = {'azure_subscription_id': '123'}
    result = CloudAccountService.test_azure_connection(creds)
    assert result['success'] is False
    assert 'required' in result['error']

def test_gcp_sandbox_connection():
    creds = {
        'gcp_project_id': 'demo-scheduler-project',
        'gcp_client_email': 'sa@demo.iam.gserviceaccount.com',
        'gcp_zone': 'us-central1-a',
        'use_sandbox': True
    }
    result = CloudAccountService.test_gcp_connection(creds)
    assert result['success'] is True
    assert result['provider'] == 'GCP'
    assert result['project_id'] == 'demo-scheduler-project'
    assert 'permissions_verified' in result

def test_api_cloud_account_lifecycle(auth_client):
    # 1. Test connection via API
    test_payload = {
        'provider': 'AWS',
        'credentials': {
            'aws_access_key_id': 'AKIA-MOCK-TEST-KEY',
            'aws_secret_access_key': 'mocksecretkey999',
            'aws_region': 'us-east-1'
        },
        'use_sandbox': True
    }
    res = auth_client.post('/api/cloud-accounts/test', json=test_payload)
    assert res.status_code == 200
    assert res.json['success'] is True

    # 2. Save account via API
    save_payload = {
        'provider': 'AWS',
        'account_name': 'Production AWS East',
        'credentials': {
            'aws_access_key_id': 'AKIA-MOCK-TEST-KEY',
            'aws_secret_access_key': 'mocksecretkey999',
            'aws_region': 'us-east-1'
        },
        'use_sandbox': True
    }
    save_res = auth_client.post('/api/cloud-accounts', json=save_payload)
    assert save_res.status_code == 200
    assert save_res.json['success'] is True
    account_id = save_res.json['account']['id']

    # 3. List accounts
    list_res = auth_client.get('/api/cloud-accounts')
    assert list_res.status_code == 200
    assert list_res.json['count'] >= 1

    # 4. Discover from account
    disc_res = auth_client.post(f'/api/cloud-accounts/{account_id}/discover')
    assert disc_res.status_code == 200
    assert disc_res.json['success'] is True
    assert disc_res.json['count'] > 0

    # 5. Verify resources populated
    res_list = auth_client.get('/api/resources')
    assert res_list.json['count'] > 0

    # 6. Clear inventory (User requested: remove discovered content)
    clear_res = auth_client.post('/api/resources/clear')
    assert clear_res.status_code == 200
    assert clear_res.json['success'] is True

    # 7. Verify inventory is back to 0
    after_clear = auth_client.get('/api/resources')
    assert after_clear.json['count'] == 0

    # 8. Delete account
    del_res = auth_client.delete(f'/api/cloud-accounts/{account_id}')
    assert del_res.status_code == 200
    assert del_res.json['success'] is True

def test_direct_alert_dispatch(auth_client):
    res = auth_client.post('/api/alerts/test-direct', json={
        'email': 'vasanthkumar23212921@gmail.com',
        'phone': '+15551234567'
    })
    assert res.status_code == 200
    assert res.json['success'] is True
    assert 'stop_url' in res.json
    assert 'extend_url' in res.json
    assert 'token=' in res.json['stop_url']
    assert 'action=stop' in res.json['stop_url']

def test_trigger_resource_alert_endpoint(auth_client, app):
    with app.app_context():
        res = CloudResource(
            instance_id='i-alert-test-99',
            instance_name='Alert-Test-VM',
            provider='AWS',
            region='us-east-1',
            state='running'
        )
        db.session.add(res)
        db.session.commit()
        res_id = res.id

    resp = auth_client.post(f'/api/resources/{res_id}/trigger-alert')
    assert resp.status_code == 200
    assert resp.json['success'] is True
    assert 'stop_url' in resp.json
    assert 'extend_url' in resp.json
    assert 'token=' in resp.json['stop_url']



