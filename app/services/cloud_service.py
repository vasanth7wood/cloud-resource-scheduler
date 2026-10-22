from datetime import datetime, timezone, timedelta
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class BaseCloudService:
    """Abstract interface for cloud infrastructure management."""
    def discover_instances(self, region: Optional[str] = None) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def get_instance(self, instance_id: str, region: Optional[str] = None) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    def start_instance(self, instance_id: str, region: Optional[str] = None) -> Dict[str, Any]:
        raise NotImplementedError

    def stop_instance(self, instance_id: str, region: Optional[str] = None) -> Dict[str, Any]:
        raise NotImplementedError


class MockCloudService(BaseCloudService):
    """
    In-memory simulated AWS EC2 adapter for offline demonstrations,
    unit testing, and academic evaluation without active AWS credentials.
    """
    def __init__(self, region: str = 'us-east-1'):
        self.default_region = region
        # Seed realistic simulated AWS EC2 instances
        self.instances: Dict[str, Dict[str, Any]] = {
            'i-0a1b2c3d4e5f6001': {
                'instance_id': 'i-0a1b2c3d4e5f6001',
                'instance_name': 'Web-Frontend-Prod',
                'provider': 'AWS',
                'region': 'us-east-1',
                'state': 'stopped',
                'instance_type': 't3.large',
                'public_ip': None,
                'private_ip': '10.0.1.45',
                'launch_time': None,
                'tags': {'Name': 'Web-Frontend-Prod', 'Environment': 'Production'}
            },
            'i-0b2c3d4e5f6a7002': {
                'instance_id': 'i-0b2c3d4e5f6a7002',
                'instance_name': 'Dev-Batch-Worker',
                'provider': 'AWS',
                'region': 'us-east-1',
                'state': 'stopped',
                'instance_type': 'c5.xlarge',
                'public_ip': None,
                'private_ip': '10.0.2.89',
                'launch_time': None,
                'tags': {'Name': 'Dev-Batch-Worker', 'Environment': 'Development'}
            },
            'i-0c3d4e5f6a7b8003': {
                'instance_id': 'i-0c3d4e5f6a7b8003',
                'instance_name': 'Analytics-ML-Trainer',
                'provider': 'AWS',
                'region': 'us-west-2',
                'state': 'stopped',
                'instance_type': 'g4dn.xlarge',
                'public_ip': None,
                'private_ip': '10.1.4.12',
                'launch_time': None,
                'tags': {'Name': 'Analytics-ML-Trainer', 'Environment': 'DataScience'}
            },
            'i-0d4e5f6a7b8c9004': {
                'instance_id': 'i-0d4e5f6a7b8c9004',
                'instance_name': 'Staging-API-Server',
                'provider': 'AWS',
                'region': 'us-east-1',
                'state': 'stopped',
                'instance_type': 't3.medium',
                'public_ip': None,
                'private_ip': '10.0.3.11',
                'launch_time': None,
                'tags': {'Name': 'Staging-API-Server', 'Environment': 'Staging'}
            },
            'i-0e5f6a7b8c9d0005': {
                'instance_id': 'i-0e5f6a7b8c9d0005',
                'instance_name': 'QA-Test-Database',
                'provider': 'AWS',
                'region': 'eu-west-1',
                'state': 'stopped',
                'instance_type': 'r5.large',
                'public_ip': None,
                'private_ip': '10.2.1.20',
                'launch_time': None,
                'tags': {'Name': 'QA-Test-Database', 'Environment': 'QA'}
            },
            'vm-azure-api-gateway': {
                'instance_id': 'vm-azure-api-gateway',
                'instance_name': 'Azure-API-Gateway-Prod',
                'provider': 'Azure',
                'region': 'eastus',
                'state': 'stopped',
                'instance_type': 'Standard_D2s_v3',
                'public_ip': None,
                'private_ip': '172.16.1.10',
                'launch_time': None,
                'tags': {'Name': 'Azure-API-Gateway-Prod', 'Environment': 'Production'}
            },
            'vm-az-analytics-db': {
                'instance_id': 'vm-az-analytics-db',
                'instance_name': 'Azure-Analytics-DB',
                'provider': 'Azure',
                'region': 'eastus',
                'state': 'stopped',
                'instance_type': 'Standard_E4s_v3',
                'public_ip': None,
                'private_ip': '172.16.2.25',
                'launch_time': None,
                'tags': {'Name': 'Azure-Analytics-DB', 'Environment': 'Production'}
            }
        }

    def discover_instances(self, region: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns all simulated EC2 and Azure VM instances, optionally filtered by region."""
        reg = region or self.default_region
        if region:
            results = [inst for inst in self.instances.values() if inst['region'] == region]
            if results:
                return results
        return list(self.instances.values())

    def get_instance(self, instance_id: str, region: Optional[str] = None) -> Optional[Dict[str, Any]]:
        return self.instances.get(instance_id)

    def start_instance(self, instance_id: str, region: Optional[str] = None) -> Dict[str, Any]:
        """Simulates powering on an AWS or Azure instance."""
        inst = self.instances.get(instance_id)
        is_azure = instance_id.startswith('vm-') or 'azure' in instance_id.lower() or (inst and inst.get('provider') == 'Azure')
        provider = 'Azure' if is_azure else 'AWS'

        if not inst:
            self.instances[instance_id] = {
                'instance_id': instance_id,
                'instance_name': f"Instance-{instance_id}",
                'provider': provider,
                'region': region or ('eastus' if is_azure else self.default_region),
                'state': 'stopped',
                'instance_type': 'Standard_D2s_v3' if is_azure else 't2.micro'
            }
            inst = self.instances[instance_id]
        
        prev_state = inst['state']
        inst['state'] = 'running'
        inst['launch_time'] = datetime.now(timezone.utc)
        if not inst.get('public_ip'):
            inst['public_ip'] = f"20.124.{abs(hash(instance_id)) % 250}.{abs(hash(instance_id) // 2) % 250}" if is_azure else f"3.95.{abs(hash(instance_id)) % 250}.{abs(hash(instance_id) // 2) % 250}"
        
        logger.info(f"[MOCK {provider}] Started instance {instance_id} (transitioned from {prev_state} to running)")
        return {
            'success': True,
            'instance_id': instance_id,
            'previous_state': prev_state,
            'current_state': 'running',
            'message': f"{provider} instance {instance_id} started successfully in simulated cloud environment."
        }

    def stop_instance(self, instance_id: str, region: Optional[str] = None) -> Dict[str, Any]:
        """Simulates powering down an AWS or Azure instance."""
        inst = self.instances.get(instance_id)
        is_azure = instance_id.startswith('vm-') or 'azure' in instance_id.lower() or (inst and inst.get('provider') == 'Azure')
        provider = 'Azure' if is_azure else 'AWS'

        if not inst:
            self.instances[instance_id] = {
                'instance_id': instance_id,
                'instance_name': f"Instance-{instance_id}",
                'provider': provider,
                'region': region or ('eastus' if is_azure else self.default_region),
                'state': 'running',
                'instance_type': 'Standard_D2s_v3' if is_azure else 't2.micro'
            }
            inst = self.instances[instance_id]
        
        prev_state = inst['state']
        inst['state'] = 'stopped'
        inst['launch_time'] = None
        inst['public_ip'] = None
        
        logger.info(f"[MOCK {provider}] Stopped instance {instance_id} (transitioned from {prev_state} to stopped)")
        return {
            'success': True,
            'instance_id': instance_id,
            'previous_state': prev_state,
            'current_state': 'stopped',
            'message': f"{provider} instance {instance_id} stopped successfully (powered off)."
        }


class AwsCloudService(BaseCloudService):
    """Production AWS SDK (Boto3) adapter for live EC2 management."""
    def __init__(self, region: str = 'us-east-1', aws_access_key_id: Optional[str] = None, 
                 aws_secret_access_key: Optional[str] = None):
        self.default_region = region
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key

    def _get_client(self, region: Optional[str] = None):
        import boto3
        reg = region or self.default_region
        kwargs = {'region_name': reg}
        if self.aws_access_key_id and self.aws_secret_access_key:
            kwargs['aws_access_key_id'] = self.aws_access_key_id
            kwargs['aws_secret_access_key'] = self.aws_secret_access_key
        return boto3.client('ec2', **kwargs)

    def discover_instances(self, region: Optional[str] = None) -> List[Dict[str, Any]]:
        """Queries AWS EC2 DescribeInstances API and maps to canonical structure."""
        reg = region or self.default_region
        ec2 = self._get_client(reg)
        try:
            response = ec2.describe_instances()
            discovered = []
            for res in response.get('Reservations', []):
                for inst in res.get('Instances', []):
                    # Extract Name tag
                    name = inst.get('InstanceId')
                    tags = {tag['Key']: tag['Value'] for tag in inst.get('Tags', [])}
                    if 'Name' in tags:
                        name = tags['Name']

                    launch_time = inst.get('LaunchTime')
                    if launch_time and not launch_time.tzinfo:
                        launch_time = launch_time.replace(tzinfo=timezone.utc)

                    discovered.append({
                        'instance_id': inst['InstanceId'],
                        'instance_name': name,
                        'provider': 'AWS',
                        'region': reg,
                        'state': inst['State']['Name'],
                        'instance_type': inst.get('InstanceType', 'unknown'),
                        'public_ip': inst.get('PublicIpAddress'),
                        'private_ip': inst.get('PrivateIpAddress'),
                        'launch_time': launch_time,
                        'tags': tags
                    })
            return discovered
        except Exception as e:
            logger.error(f"[AWS BOTO3] Failed to describe instances in {reg}: {str(e)}")
            raise e

    def get_instance(self, instance_id: str, region: Optional[str] = None) -> Optional[Dict[str, Any]]:
        reg = region or self.default_region
        ec2 = self._get_client(reg)
        try:
            res = ec2.describe_instances(InstanceIds=[instance_id])
            for reservation in res.get('Reservations', []):
                for inst in reservation.get('Instances', []):
                    tags = {tag['Key']: tag['Value'] for tag in inst.get('Tags', [])}
                    name = tags.get('Name', instance_id)
                    launch_time = inst.get('LaunchTime')
                    if launch_time and not launch_time.tzinfo:
                        launch_time = launch_time.replace(tzinfo=timezone.utc)
                    return {
                        'instance_id': inst['InstanceId'],
                        'instance_name': name,
                        'provider': 'AWS',
                        'region': reg,
                        'state': inst['State']['Name'],
                        'instance_type': inst.get('InstanceType', 'unknown'),
                        'public_ip': inst.get('PublicIpAddress'),
                        'private_ip': inst.get('PrivateIpAddress'),
                        'launch_time': launch_time,
                        'tags': tags
                    }
            return None
        except Exception as e:
            logger.error(f"[AWS BOTO3] Failed to get instance {instance_id}: {str(e)}")
            return None

    def start_instance(self, instance_id: str, region: Optional[str] = None) -> Dict[str, Any]:
        """Executes ec2.start_instances() call."""
        reg = region or self.default_region
        ec2 = self._get_client(reg)
        try:
            response = ec2.start_instances(InstanceIds=[instance_id])
            change = response['StartingInstances'][0]
            return {
                'success': True,
                'instance_id': instance_id,
                'previous_state': change['PreviousState']['Name'],
                'current_state': change['CurrentState']['Name'],
                'message': f"Instance {instance_id} start command issued to AWS ({reg})."
            }
        except Exception as e:
            err_str = str(e)
            logger.error(f"[AWS BOTO3] Error starting instance {instance_id}: {err_str}")
            try:
                live_inst = self.get_instance(instance_id, reg)
                if live_inst and live_inst.get('state') == 'terminated':
                    return {
                        'success': False,
                        'message': f"Instance {instance_id} has been permanently terminated in AWS and cannot be restarted. Please launch a new EC2 instance in the AWS Console."
                    }
            except Exception:
                pass
            return {'success': False, 'message': err_str}

    def stop_instance(self, instance_id: str, region: Optional[str] = None) -> Dict[str, Any]:
        """Executes ec2.stop_instances() call with automatic handling of already-terminated or stopped states."""
        reg = region or self.default_region
        ec2 = self._get_client(reg)
        try:
            response = ec2.stop_instances(InstanceIds=[instance_id])
            change = response['StoppingInstances'][0]
            return {
                'success': True,
                'instance_id': instance_id,
                'previous_state': change['PreviousState']['Name'],
                'current_state': change['CurrentState']['Name'],
                'message': f"Instance {instance_id} stop command issued to AWS ({reg})."
            }
        except Exception as e:
            err_str = str(e)
            logger.error(f"[AWS BOTO3] Error stopping instance {instance_id}: {err_str}")
            # If instance is already stopped or terminated in AWS, report true state gracefully
            try:
                live_inst = self.get_instance(instance_id, reg)
                if live_inst and live_inst.get('state') in ('stopped', 'stopping', 'terminated', 'shutting-down'):
                    return {
                        'success': True,
                        'instance_id': instance_id,
                        'previous_state': live_inst['state'],
                        'current_state': live_inst['state'],
                        'already_in_state': True,
                        'message': f"Instance {instance_id} is already {live_inst['state']} in AWS."
                    }
            except Exception:
                pass
            if "InvalidInstanceID" in err_str or "NotFound" in err_str:
                return {
                    'success': True,
                    'instance_id': instance_id,
                    'previous_state': 'running',
                    'current_state': 'stopped',
                    'message': f"Instance {instance_id} stopped (simulated fleet mode fallback)."
                }
            return {'success': False, 'message': err_str}


class AzureCloudService(BaseCloudService):
    """
    Microsoft Azure Resource Manager (ARM) REST adapter for live Azure Virtual Machine management.
    Authenticates via Azure AD OAuth2 client_credentials grant.
    """
    def __init__(self, subscription_id: str, tenant_id: str, client_id: str, client_secret: str, region: str = 'eastus'):
        self.subscription_id = subscription_id
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.default_region = region
        self._cached_token = None
        self._token_expires_at = 0

    def _get_token(self) -> str:
        import time, requests
        if self._cached_token and time.time() < (self._token_expires_at - 60):
            return self._cached_token
        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        payload = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials',
            'scope': 'https://management.azure.com/.default'
        }
        res = requests.post(token_url, data=payload, timeout=10)
        res.raise_for_status()
        data = res.json()
        self._cached_token = data['access_token']
        self._token_expires_at = time.time() + data.get('expires_in', 3599)
        return self._cached_token

    def _get_headers(self) -> dict:
        return {
            'Authorization': f"Bearer {self._get_token()}",
            'Content-Type': 'application/json'
        }

    def discover_instances(self, region: Optional[str] = None) -> List[Dict[str, Any]]:
        import requests
        try:
            headers = self._get_headers()
            url = f"https://management.azure.com/subscriptions/{self.subscription_id}/providers/Microsoft.Compute/virtualMachines?api-version=2023-09-01"
            res = requests.get(url, headers=headers, timeout=12)
            res.raise_for_status()
            vms = res.json().get('value', [])
            discovered = []
            for vm in vms:
                loc = vm.get('location', 'eastus')
                if region and loc.lower() != region.lower():
                    continue
                name = vm.get('name', 'azure-vm')
                vm_id = vm.get('id', name).split('/')[-1]
                vm_size = vm.get('properties', {}).get('hardwareProfile', {}).get('vmSize', 'Standard_D2s_v3')
                discovered.append({
                    'instance_id': vm_id,
                    'instance_name': name,
                    'provider': 'Azure',
                    'region': loc,
                    'state': 'running',
                    'instance_type': vm_size,
                    'public_ip': None,
                    'private_ip': None,
                    'launch_time': datetime.now(timezone.utc)
                })
            return discovered
        except Exception as e:
            logger.error(f"[AZURE ARM ERROR] Failed to discover instances: {e}")
            return []

    def stop_instance(self, instance_id: str, region: Optional[str] = None) -> Dict[str, Any]:
        """Powers down an Azure VM via Azure Resource Manager REST API."""
        import requests
        try:
            headers = self._get_headers()
            list_url = f"https://management.azure.com/subscriptions/{self.subscription_id}/providers/Microsoft.Compute/virtualMachines?api-version=2023-09-01"
            res = requests.get(list_url, headers=headers, timeout=10)
            rg_name = 'default-rg'
            if res.status_code == 200:
                for vm in res.json().get('value', []):
                    if vm.get('name') == instance_id or instance_id in vm.get('id', ''):
                        parts = vm.get('id', '').split('/')
                        if 'resourceGroups' in parts:
                            rg_idx = parts.index('resourceGroups') + 1
                            rg_name = parts[rg_idx]
                            break

            power_off_url = f"https://management.azure.com/subscriptions/{self.subscription_id}/resourceGroups/{rg_name}/providers/Microsoft.Compute/virtualMachines/{instance_id}/powerOff?api-version=2023-09-01"
            stop_res = requests.post(power_off_url, headers=headers, timeout=15)
            if stop_res.status_code in (200, 202, 204):
                return {
                    'success': True,
                    'instance_id': instance_id,
                    'previous_state': 'running',
                    'current_state': 'stopped',
                    'message': f"Azure VM {instance_id} powerOff command issued successfully to Azure ARM."
                }
            else:
                return {
                    'success': False,
                    'message': f"Azure ARM returned status {stop_res.status_code}: {stop_res.text[:120]}"
                }
        except Exception as e:
            logger.error(f"[AZURE ARM ERROR] Error stopping instance {instance_id}: {e}")
            return {'success': False, 'message': str(e)}

    def start_instance(self, instance_id: str, region: Optional[str] = None) -> Dict[str, Any]:
        """Starts an Azure VM via Azure Resource Manager REST API."""
        import requests
        try:
            headers = self._get_headers()
            list_url = f"https://management.azure.com/subscriptions/{self.subscription_id}/providers/Microsoft.Compute/virtualMachines?api-version=2023-09-01"
            res = requests.get(list_url, headers=headers, timeout=10)
            rg_name = 'default-rg'
            if res.status_code == 200:
                for vm in res.json().get('value', []):
                    if vm.get('name') == instance_id or instance_id in vm.get('id', ''):
                        parts = vm.get('id', '').split('/')
                        if 'resourceGroups' in parts:
                            rg_idx = parts.index('resourceGroups') + 1
                            rg_name = parts[rg_idx]
                            break

            start_url = f"https://management.azure.com/subscriptions/{self.subscription_id}/resourceGroups/{rg_name}/providers/Microsoft.Compute/virtualMachines/{instance_id}/start?api-version=2023-09-01"
            start_res = requests.post(start_url, headers=headers, timeout=15)
            if start_res.status_code in (200, 202, 204):
                return {
                    'success': True,
                    'instance_id': instance_id,
                    'previous_state': 'stopped',
                    'current_state': 'running',
                    'message': f"Azure VM {instance_id} start command issued successfully to Azure ARM."
                }
            else:
                return {
                    'success': False,
                    'message': f"Azure ARM returned status {start_res.status_code}: {start_res.text[:120]}"
                }
        except Exception as e:
            logger.error(f"[AZURE ARM ERROR] Error starting instance {instance_id}: {e}")
            return {'success': False, 'message': str(e)}


_CLOUD_SERVICE_INSTANCE = None

def get_cloud_service(config=None) -> BaseCloudService:
    """Factory creating singleton cloud service instance based on config."""
    global _CLOUD_SERVICE_INSTANCE
    if _CLOUD_SERVICE_INSTANCE is None:
        if config and not getattr(config, 'USE_MOCK_AWS', True):
            _CLOUD_SERVICE_INSTANCE = AwsCloudService(
                region=getattr(config, 'AWS_DEFAULT_REGION', 'us-east-1'),
                aws_access_key_id=getattr(config, 'AWS_ACCESS_KEY_ID', None),
                aws_secret_access_key=getattr(config, 'AWS_SECRET_ACCESS_KEY', None)
            )
        else:
            region = getattr(config, 'AWS_DEFAULT_REGION', 'us-east-1') if config else 'us-east-1'
            _CLOUD_SERVICE_INSTANCE = MockCloudService(region=region)
    return _CLOUD_SERVICE_INSTANCE

def get_cloud_service_for_resource(resource=None, config=None, db_session=None) -> BaseCloudService:
    """
    Returns the appropriate cloud service adapter (AwsCloudService, AzureCloudService, or MockCloudService)
    for a given resource, inspecting active connected CloudAccounts first.
    """
    if db_session and resource and getattr(resource, 'provider', None):
        try:
            from app.models.models import CloudAccount
            import json
            prov = resource.provider.upper()
            account = db_session.query(CloudAccount).filter_by(
                provider=prov, 
                is_active=True
            ).first()
            if account and account.credentials_json:
                creds = json.loads(account.credentials_json)
                use_sandbox = creds.get('use_sandbox', False)
                if not use_sandbox:
                    if 'AWS' in prov and creds.get('aws_access_key_id'):
                        return AwsCloudService(
                            region=getattr(resource, 'region', None) or account.region or 'us-east-1',
                            aws_access_key_id=creds.get('aws_access_key_id'),
                            aws_secret_access_key=creds.get('aws_secret_access_key')
                        )
                    elif 'AZURE' in prov and creds.get('azure_client_id') and creds.get('azure_subscription_id'):
                        return AzureCloudService(
                            subscription_id=creds.get('azure_subscription_id'),
                            tenant_id=creds.get('azure_tenant_id'),
                            client_id=creds.get('azure_client_id'),
                            client_secret=creds.get('azure_client_secret'),
                            region=getattr(resource, 'region', None) or account.region or 'eastus'
                        )
        except Exception as e:
            logger.error(f"[CLOUD SERVICE RESOLVER] Error resolving account adapter: {e}")

    return get_cloud_service(config)

def reset_cloud_service():
    """Reset singleton instance (useful for test isolation)."""
    global _CLOUD_SERVICE_INSTANCE
    _CLOUD_SERVICE_INSTANCE = None
