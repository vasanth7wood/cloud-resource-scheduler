# Cloud Resource Scheduling & Governance System

> **Google Antigravity IDE Project Specification**  
> An automated enterprise FinOps platform designed to identify idle, un-tagged, or off-hours cloud resources, enforce shutdown schedules, dispatch multi-channel push & SMS alerts, and process cryptographic 1-click grace extensions.

---

## 1. System Overview & Technology Stack

- **Runtime & Language**: Python 3.13 (64-bit)
- **Web Framework**: Flask 3.0+ (Application Factory pattern, Blueprints)
- **ORM & Database**: SQLAlchemy 2.0+ with dual engine:
  - SQLite fallback: `cloud_scheduler.db` (Default / Local offline)
  - MySQL enterprise: `mysql+pymysql://root:password@localhost:3306/cloud_scheduler`
- **Background Scheduler**: APScheduler (BackgroundScheduler) running 60s periodic audit loops
- **Notification Gateways**:
  - **ntfy Mobile Push**: Real-time push with audio siren/buzzer notifications to phone (`ntfy.sh/vasanth_cloud_alerts`)
  - **Twilio**: SMS & WhatsApp alerting
  - **Fast2SMS**: Indian regional SMS gateway
  - **SMTP**: Automated email alerts via Gmail TLS
- **Edge Tunnel**: Cloudflare Tunnel (`cloudflared.exe`) exposing port 5000 via HTTPS for mobile HMAC action callbacks
- **Frontend**: Bootstrap 5 dark theme, FontAwesome 6, Chart.js for FinOps cost analytics

---

## 2. Directory Layout

```
CLOUD RESOURCE SCHEDULING/
├── .agents/                        # Antigravity IDE Agentic Configuration
│   ├── rules/                      # Workspace policy & coding rules
│   │   ├── cloud_governance.md     # Governance logic, schedules & grace periods
│   │   └── coding_standards.md     # Flask, SQLAlchemy & UI standards
│   └── skills/                     # Custom Antigravity workflows
│       └── cloud-governance/       # Runbook for auditing & managing cloud resources
│           └── SKILL.md
├── .vscode/                        # Antigravity IDE Editor Configuration
│   ├── launch.json                 # Python debug profiles (Flask & Pytest)
│   ├── settings.json               # Interpreter, test discovery & formatting
│   └── tasks.json                  # IDE Tasks (Start server, tunnel, tests)
├── app/                            # Application source
│   ├── __init__.py                 # Flask App Factory & scheduler initialization
│   ├── models/
│   │   └── models.py               # Database schemas (User, CloudResource, Schedule, etc.)
│   ├── routes/
│   │   ├── auth.py                 # Authentication, auto-provisioning & /quick-login
│   │   ├── dashboard.py            # Overview dashboard, FinOps cost savings
│   │   ├── resources.py            # Resource inventory & cloud account sync
│   │   ├── schedules.py            # Schedule windows & policy enforcement
│   │   ├── alerts.py               # Alert history & notification logs
│   │   └── webhook.py              # HMAC signed 1-click action callback endpoint
│   ├── services/
│   │   ├── alert_service.py        # Multi-channel dispatcher (ntfy, SMS, email)
│   │   ├── cloud_service.py        # AWS/Azure/GCP multi-cloud adapters + Mock engine
│   │   ├── scheduler_service.py    # Policy evaluation engine & grace period manager
│   │   └── token_service.py        # Cryptographic HMAC-SHA256 action tokens
│   ├── static/                     # CSS stylesheets, JavaScript & assets
│   └── templates/                  # Jinja2 HTML templates
├── bin/
│   └── cloudflared.exe             # Official Cloudflare Tunnel binary
├── tests/                          # Automated Pytest suite
│   ├── conftest.py
│   ├── test_cloud_accounts.py
│   ├── test_scheduler.py
│   ├── test_tokens.py
│   └── test_webhook.py
├── .env                            # Environment variables & secrets
├── .env.example                    # Template environment variables
├── cloud_scheduler.db              # SQLite development database
├── GEMINI.md                       # Antigravity IDE Workspace Root Instruction
├── requirements.txt                # Python package dependencies
├── run.py                          # Flask application launcher
└── schema.sql                      # Database DDL schema script
```

---

## 3. Essential Antigravity IDE Commands

### Launching the Application
```powershell
python run.py
```
*Accessible locally at:* `http://127.0.0.1:5000`

### Launching the Cloudflare Tunnel
```powershell
.\bin\cloudflared.exe tunnel --url http://127.0.0.1:5000 --logfile scratch/tunnel.log
```

### Running the Pytest Test Suite
```powershell
python -m pytest -v tests
```

---

## 4. Authentication & Credentials

- **Primary Admin Email**: `vasanthkumar20212021@gmail.com`
- **Universal Passkey**: `password123` (or `Admin@123456`, `password`)
- **1-Click Instant Login**: Navigate to `/quick-login` in any browser to authenticate immediately without password prompts.

---

## 5. Antigravity IDE Pair-Programming Directives

1. **Header UI Cleanliness**:  
   Do **NOT** add temporary test buttons, test buzzer triggers, or intrusive widgets into the navigation header. The header must strictly retain clean brand links, navigation items, user identity, and Logout.
2. **Alert Notification Flow**:  
   Real buzzer sounds and notification sirens are broadcast to user phones via **ntfy** (`ntfy.sh/vasanth_cloud_alerts`) with `urgent` priority and audio tags (`warning`, `alarm`).
3. **Database & Models**:  
   Preserve SQLite fallback mechanism so the system works with zero friction even if a local MySQL daemon is not running.
4. **Timezone Handling**:  
   Always evaluate schedules in consistent UTC reference (`datetime.now(timezone.utc)`) to avoid local host timezone skew.
