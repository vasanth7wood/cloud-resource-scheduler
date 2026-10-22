# Cloud Resource Scheduling and Interactive Multi-Channel Alert System

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://python.org)
[![Framework](https://img.shields.io/badge/Framework-Flask%203.1-emerald.svg)](https://flask.palletsprojects.com/)
[![Database](https://img.shields.io/badge/Database-MySQL%20%2F%20SQLAlchemy-orange.svg)](https://www.mysql.com/)
[![Scheduler](https://img.shields.io/badge/Task%20Scheduler-APScheduler-purple.svg)](https://apscheduler.readthedocs.io/)
[![Cloud SDK](https://img.shields.io/badge/Cloud%20SDK-AWS%20Boto3%20%26%20Mock%20Driver-yellow.svg)](https://boto3.amazonaws.com/)
[![Tests](https://img.shields.io/badge/Tests-16%20Passing%20(Pytest)-brightgreen.svg)](https://pytest.org/)

A production-grade, enterprise-ready cloud governance, scheduling, and FinOps cost optimization web application. Built for academic demonstration and real-world infrastructure management, this system continuously audits cloud compute resources (AWS EC2), enforces operating hours and continuous runtime limits, dispatches simultaneous multi-channel alerts (**Twilio SMS**, **Twilio WhatsApp**, and **SMTP Email**), and allows operators to take single-click emergency actions (**Stop** or **Extend Lease**) via time-bound, cryptographically signed HMAC-SHA256 webhooks without logging into the cloud console.

---

## 🏛️ System Architecture & Workflow

```mermaid
flowchart TD
    subgraph Discovery ["1. Cloud Discovery & Inventory"]
        AWS[AWS EC2 / Mock Engine] -->|Boto3 / Mock API| Sync[Cloud Inventory Sync]
        Sync --> DB[(MySQL / SQLAlchemy)]
    end

    subgraph Governance ["2. Continuous Governance Engine"]
        AP[APScheduler In-Process Job] -->|Every 60s| Audit[Policy Evaluation Engine]
        DB -->|Operating Hours & Max Runtime| Audit
        Audit -->|Compliant| OK[Keep Active State]
        Audit -->|Breach Detected| Breach[Policy Violation Trigger]
    end

    subgraph Dispatch ["3. Multi-Channel Alert Gateway"]
        Breach --> TokenGen[HMAC-SHA256 Token Signer<br/>TTL: 15 Mins]
        TokenGen --> SMS[Twilio SMS]
        TokenGen --> WA[Twilio WhatsApp]
        TokenGen --> Mail[SMTP Email]
        Breach --> GraceStart[Start 30-Min Grace Period]
    end

    subgraph Execution ["4. Remote Action & Auto-Shutdown"]
        UserClick[Operator Webhook Click<br/>Stop / Extend Lease] --> HookHandler[Webhook Action Handler]
        HookHandler -->|Verify HMAC & TTL| ExecAction[AWS State Transition]
        ExecAction -->|Stop / Extend| AWS
        ExecAction --> ConfPage[Mobile Confirmation Page]
        
        GraceStart -->|No Action within 30 Mins| AutoStop[Automated Fallback Shutdown]
        AutoStop -->|Curtailed Cost Leakage| AWS
        AutoStop --> Ledger[(Audit Trails & FinOps Ledger)]
    end
```

---

## 🚀 Key Features & Capabilities

1. **Enterprise Cloud Management UI:**
   - Dark/light cloud operations console inspired by CloudResource Scheduler and AWS Management Console.
   - Real-time KPI cards: Total Monitored Resources, Running Instances (Active Burn), Stopped Instances (Protected Capital), FinOps Cost Savings (both in **USD $** and **INR ₹**), and Dispatched Alerts.
   - Interactive table with live state indicators, continuous uptime counter, IP addresses, and lease expiry timers.

2. **Dual-Mode Cloud Adapter (AWS Boto3 + Offline Mock Engine):**
   - **Mock Mode (`USE_MOCK_AWS=True`)**: Pre-seeded with simulated EC2 instances (`Web-Frontend-Prod`, `Dev-Batch-Worker`, `Analytics-ML-Trainer`, etc.), enabling offline unit testing, evaluation, and presentations without AWS credentials or incurring charges.
   - **Production AWS Mode (`USE_MOCK_AWS=False`)**: Leverages `boto3.client('ec2')` to interact with live AWS infrastructure (`describe_instances`, `start_instances`, `stop_instances`).

3. **In-Process Policy & Task Scheduler (APScheduler):**
   - Periodic audit job (default: every 60 seconds) inspecting running instances against custom operating windows (e.g., `09:00 - 19:00 Mon-Fri`) and maximum continuous runtime caps (e.g., `8.0 hours`).
   - **Grace-Period Automated Fallback**: When a violation alert is dispatched and unacknowledged for **30 minutes**, the system automatically executes a fallback shutdown to eliminate cost leakage.

4. **Multi-Channel Dispatch Gateway:**
   - Formats incident alerts with detailed metadata (Instance ID, Name, Region, Uptime, Violation Reason).
   - Generates single-click direct URLs:
     * `Stop`: `http://localhost:5000/webhook/action?token=<HMAC_TOKEN>&action=stop`
     * `Extend (+60m)`: `http://localhost:5000/webhook/action?token=<HMAC_TOKEN>&action=extend`
   - Simultaneously dispatches across **Twilio SMS**, **Twilio WhatsApp** (`whatsapp:+14155238886`), and **SMTP Email** (HTML button card + Plain Text). Includes graceful console fallback when credentials are left as demo placeholders.

5. **Cryptographic Single-Click Action Webhooks:**
   - Signs tokens with **HMAC-SHA256**, base64 URL-safe encoding, and an embedded timestamp.
   - Strict **15-minute Time-To-Live (TTL)**.
   - Tamper-detection: modifying even a single byte invalidates the signature.
   - Replay protection: tokens are strictly single-use.
   - Mobile-optimized HTML response page confirming the state change.

6. **Role-Based Access Control (RBAC):**
   - `Admin`: Full governance control (Start/Stop, modify policies, trigger audits, scan cloud).
   - `Manager`: Operational access (Start/Stop, lease extensions, view schedules).
   - `Viewer`: Read-only telemetry and log viewer.

---

## 📂 Project Directory Structure

```
CLOUD RESOURCE SCHEDULING/
├── app/
│   ├── __init__.py                # Flask application factory, DB setup & scheduler init
│   ├── config.py                  # Environment configurations & FinOps constants
│   ├── models/
│   │   ├── __init__.py
│   │   └── models.py              # SQLAlchemy ORM models (User, CloudResource, Schedule, etc.)
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py                # Login, registration, session, and RBAC decorators
│   │   ├── dashboard.py           # Dashboard view route
│   │   ├── api.py                 # RESTful APIs (resources, schedules, stats, audits)
│   │   └── webhook.py             # Public HMAC-authenticated single-click webhook handler
│   ├── services/
│   │   ├── __init__.py
│   │   ├── cloud_service.py       # AWS Boto3 SDK & Mock Cloud Adapter
│   │   ├── scheduler_service.py   # APScheduler background runner & grace period engine
│   │   ├── notification_service.py# Multi-channel gateway (Twilio SMS/WhatsApp + SMTP)
│   │   └── token_utils.py         # Cryptographic HMAC-SHA256 token generator & validator
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css          # Modern dark cloud theme & mobile webhook UI
│   │   └── js/
│   │       ├── auth.js            # Demo credential auto-fill helper
│   │       └── dashboard.js       # Asynchronous fetch, dynamic DOM & auto-refresh
│   └── templates/
│       ├── base.html              # Base layout with typography and toasts
│       ├── login.html             # Login view with one-click demo credentials
│       ├── register.html          # User registration view
│       ├── dashboard.html         # Main operations dashboard & KPI metrics
│       └── action_response.html   # Mobile-optimized webhook confirmation page
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Pytest fixtures & in-memory test DB
│   ├── test_tokens.py             # HMAC signing, tamper detection, and TTL tests
│   ├── test_scheduler.py          # Policy evaluation, breach alerts, and 30m grace fallback
│   └── test_webhook.py            # E2E single-click stop/extend webhook tests
├── schema.sql                     # Complete MySQL DDL schema and seed queries
├── run.py                         # Application server startup script
├── requirements.txt               # Dependencies list
├── .env.example                   # Environment configuration template
├── .env                           # Local working environment file
└── README.md                      # Documentation & execution guide
```

---

## 🗄️ Database Schema (MySQL 8.0+)

The relational schema is defined in [`schema.sql`](schema.sql) with full foreign key constraints, indexes, and initial seed records:

| Table | Primary Columns | Purpose |
| :--- | :--- | :--- |
| `users` | `id`, `name`, `email`, `password_hash`, `phone_number`, `role`, `created_at` | RBAC accounts with bcrypt password hashes (`Admin`, `Manager`, `Viewer`) |
| `cloud_resources` | `id`, `instance_id`, `instance_name`, `provider`, `region`, `state`, `public_ip`, `private_ip`, `launch_time`, `lease_expires_at`, `alert_sent_at`, `last_scanned_at` | Monitored compute instances, runtime metadata, and grace period timestamps |
| `schedules` | `id`, `resource_id`, `start_time`, `end_time`, `max_runtime_hours`, `days_of_week`, `is_active` | Allowable operating hours and continuous runtime limits per resource |
| `alert_logs` | `id`, `resource_id`, `channel`, `recipient`, `status`, `token_hash`, `details`, `sent_at` | Multi-channel dispatch records (`Twilio SMS`, `Twilio WhatsApp`, `SMTP Email`) |
| `audit_trails` | `id`, `resource_id`, `triggered_by`, `action_taken`, `details`, `timestamp` | Immutable audit log of all human actions, webhooks, and automated shutdowns |

### Importing into MySQL

```bash
# 1. Log in to MySQL CLI or MySQL Workbench
mysql -u root -p

# 2. Run the DDL script to create the database and seed tables
source /path/to/schema.sql;
```

> **Note on Automatic SQLite Fallback:**
> If MySQL is not running or credentials are not configured, the application automatically falls back to an embedded SQLite database (`sqlite:///cloud_scheduler.db`) with zero manual setup required!

---

## ⚙️ Environment Configuration (`.env`)

Copy `.env.example` to `.env` or customize existing parameters:

```ini
# Application Secret Key
SECRET_KEY=dev-cloud-scheduler-super-secret-key-change-in-production-2026
PORT=5000
WEBHOOK_BASE_URL=http://localhost:5000

# Database URI (MySQL with PyMySQL)
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/cloud_scheduler
USE_SQLITE_FALLBACK=True
SQLITE_DB_PATH=sqlite:///cloud_scheduler.db

# Cloud Adapter Toggle (True = Mock for offline testing; False = Live AWS)
USE_MOCK_AWS=True
AWS_DEFAULT_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here

# Scheduler & Policy Timers
SCAN_INTERVAL_SECONDS=60
GRACE_PERIOD_MINUTES=30
ACTION_TOKEN_TTL_SECONDS=900

# FinOps Cost Modeling
HOURLY_COST_PER_INSTANCE_USD=0.096
USD_TO_INR_RATE=83.50

# Twilio SMS & WhatsApp Gateway
TWILIO_ACCOUNT_SID=AC_your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+12015550123
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# Admin Alert Recipients
ALERT_PHONE_NUMBER=+12015550199
ALERT_WHATSAPP_NUMBER=whatsapp:+12015550199
ALERT_EMAIL_RECIPIENT=cloud-admin@example.com

# SMTP Email Gateway
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=True
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=cloud-alerts@example.com
```

---

## 🚀 Setup & Execution Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch the Application
```bash
python run.py
```

Console output will display:
```
===========================================================================
[CLOUD RESOURCE SCHEDULER & MULTI-CHANNEL ALERT SYSTEM]
===========================================================================
[*] Web Interface:      http://localhost:5000
[*] API & Webhook Root: http://localhost:5000/webhook/action
[*] Cloud Engine:       Simulated AWS EC2 (Mock Driver)
[*] APScheduler Audit:  Every 60 seconds
[*] Grace Period:       30 minutes fallback auto-shutdown
[*] Action Token TTL:   900 seconds (HMAC-SHA256)
---------------------------------------------------------------------------
[*] SEEDED DEMO CREDENTIALS:
    - Admin:   admin@cloudops.internal   / Admin@123456
    - Manager: manager@cloudops.internal / Admin@123456
    - Viewer:  viewer@cloudops.internal  / Admin@123456
===========================================================================
```

### 3. Open the Web Dashboard
Navigate to `http://localhost:5000` in your web browser. You can click the **Demo One-Click Credentials** buttons on the sign-in screen to instantly authenticate as **Admin**, **Manager**, or **Viewer**.

---

## 🧪 Comprehensive Automated Testing

The project includes 16 thorough Pytest tests covering all security and scheduling modules.

Run the test suite:
```bash
python -m pytest -v
```

### Test Coverage Highlights:
- **`tests/test_tokens.py`**:
  * Cryptographic token signing and signature verification.
  * Tamper detection: modifying characters in payload or signature fails verification.
  * Time-To-Live (TTL) expiration enforcement.
  * Replay protection (preventing token reuse).
- **`tests/test_scheduler.py`**:
  * Simulated AWS EC2 discovery, start, and stop transitions.
  * Schedule operating window and active days calculation.
  * Audit violation detection and multi-channel alert dispatching.
  * **30-minute grace period automated fallback shutdown**.
- **`tests/test_webhook.py`**:
  * End-to-end `GET /webhook/action?token=...&action=stop` modifying instance state to `stopped` (HTTP 200).
  * End-to-end `POST /webhook/action` extending instance operating lease.
  * Rejection of tampered, expired, or replayed tokens.

---

## 🎯 Academic Project Demonstration Workflow

Follow these steps during project evaluations or live demonstrations:

1. **Log in as Admin:**
   - Go to `http://localhost:5000` and click the **Admin** quick-login button.
2. **Review Dashboard & FinOps KPIs:**
   - Observe the live metrics: Running instances, active burn rate ($/hr), and estimated cost savings in USD and INR.
3. **Simulate an After-Hours Breach:**
   - Navigate to the **"FinOps & Alert Simulator"** tab.
   - Select a running instance and click **"Dispatch Multi-Channel Alert"**.
   - Notice the simulated alert recorded in the **"Multi-Channel Alert Logs"** tab and the structured terminal banner.
4. **Test Single-Click Webhook Execution:**
   - Click the generated **"Test Single-Click STOP Action"** link.
   - A mobile-optimized confirmation page will load: *"Instance has been safely powered down. Cost burn stopped."*
   - Return to the dashboard: the instance is now `STOPPED`, and cost savings have increased.
5. **Inspect the Immutable Audit Trail:**
   - Switch to the **"Audit Ledger"** tab to verify that the webhook execution was recorded with timestamp, action (`STOP`), and HMAC verification proof.
6. **Demonstrate Role-Based Access Control:**
   - Log out and log in as **Viewer**.
   - Observe that destructive action buttons (Start, Stop, Extend, Edit Policy) are disabled or hidden, adhering to strict least-privilege security principles.
