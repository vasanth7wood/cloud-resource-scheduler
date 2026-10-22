---
name: cloud-governance
description: Manage and audit cloud resources, enforce off-hours shutdown schedules, dispatch ntfy sirens/SMS alerts, and monitor tunnel status in the Cloud Resource Scheduling system.
---

# Cloud Governance & Resource Scheduling Runbook

This skill equips the Antigravity agent to audit, govern, and control cloud resources (EC2 instances) within the FinOps automation platform.

## Common Operations

### 1. Manual Policy Audit
Run an immediate audit cycle outside the 60-second periodic scheduler loop:
```powershell
python -c "from app import create_app; app = create_app(); from app.services.scheduler_service import SchedulerService; print(SchedulerService(app.config, app).audit_and_enforce_policies())"
```

### 2. Check Database State
Inspect registered cloud resources and schedules in SQLite:
```powershell
python -c "from app import create_app; from app.models.models import CloudResource, Schedule; app = create_app(); [print(r.instance_id, r.state, r.is_idle) for r in CloudResource.query.all()]"
```

### 3. Test Mobile Push Alert (ntfy siren)
Broadcast an urgent mobile push notification with alarm siren sound to the phone:
```powershell
python -c "import requests; requests.post('https://ntfy.sh/vasanth_cloud_alerts', data='[TEST] Governance Alert: Cloud resource audit active.', headers={'Title': 'Cloud Alert Test', 'Priority': 'urgent', 'Tags': 'warning,alarm'})"
```

### 4. Cloudflare Tunnel Health Check
Inspect the live status of the public HTTPS tunnel:
```powershell
Get-Content scratch/tunnel.log -Tail 20
```
Restart tunnel if necessary:
```powershell
.\bin\cloudflared.exe tunnel --protocol http2 --url http://127.0.0.1:5000 --logfile scratch/tunnel.log
```
