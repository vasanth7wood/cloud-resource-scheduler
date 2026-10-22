"""
Script to generate the complete, comprehensive project documentation PDF:
'Cloud_Resource_Scheduling_Full_Project_Documentation.pdf'
using Headless Microsoft Edge.
"""

import os
import subprocess
import sys

def build_full_doc_html() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Cloud Resource Scheduling & FinOps Governance System - Comprehensive Technical & Deployment Documentation</title>
<style>
  @page {
    size: A4 portrait;
    margin: 12mm 12mm 12mm 12mm;
    @bottom-right {
      content: counter(page);
    }
  }

  *, *:before, *:after {
    box-sizing: border-box;
  }

  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: #1e293b;
    background-color: #ffffff;
    line-height: 1.5;
    font-size: 10pt;
    margin: 0;
    padding: 0;
  }

  .page {
    page-break-after: always;
    position: relative;
    padding-bottom: 8px;
  }

  .page:last-child {
    page-break-after: avoid;
  }

  /* Cover Page */
  .cover {
    display: flex;
    flex-direction: column;
    justify-content: center;
    min-height: 92vh;
    padding: 40px 28px;
    background: linear-gradient(135deg, #090d16 0%, #1e1b4b 50%, #0f172a 100%);
    color: #ffffff;
    border-radius: 14px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.25);
  }

  .cover-badge {
    display: inline-block;
    align-self: flex-start;
    background: rgba(99, 102, 241, 0.25);
    border: 1px solid #818cf8;
    color: #c7d2fe;
    font-size: 8.5pt;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 5px 12px;
    border-radius: 9999px;
    margin-bottom: 20px;
  }

  .cover-title {
    font-size: 26pt;
    font-weight: 800;
    line-height: 1.2;
    margin: 0 0 12px 0;
    color: #ffffff;
  }

  .cover-subtitle {
    font-size: 13pt;
    color: #94a3b8;
    font-weight: 400;
    margin: 0 0 24px 0;
    line-height: 1.45;
  }

  .cover-divider {
    height: 3px;
    width: 80px;
    background: linear-gradient(90deg, #6366f1, #38bdf8);
    margin-bottom: 24px;
    border-radius: 2px;
  }

  .cover-meta-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 14px;
    margin-top: 15px;
  }

  .cover-meta-item {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 10px 14px;
  }

  .cover-meta-label {
    font-size: 7.5pt;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #94a3b8;
  }

  .cover-meta-value {
    font-size: 9.5pt;
    font-weight: 700;
    color: #f1f5f9;
    margin-top: 3px;
  }

  /* Section Headers */
  .section-header {
    border-bottom: 2px solid #e2e8f0;
    padding-bottom: 6px;
    margin-bottom: 14px;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
  }

  .section-title {
    font-size: 15pt;
    font-weight: 800;
    color: #0f172a;
    margin: 0;
  }

  .section-tag {
    font-size: 7.5pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #6366f1;
    background: #e0e7ff;
    padding: 3px 8px;
    border-radius: 4px;
  }

  h2 {
    font-size: 11pt;
    font-weight: 700;
    color: #1e293b;
    margin: 12px 0 6px 0;
  }

  h3 {
    font-size: 9.5pt;
    font-weight: 700;
    color: #334155;
    margin: 8px 0 4px 0;
  }

  p {
    margin: 0 0 8px 0;
    line-height: 1.45;
    font-size: 9pt;
  }

  ul, ol {
    margin: 0 0 8px 0;
    padding-left: 18px;
    font-size: 8.5pt;
  }

  li {
    margin-bottom: 3px;
    line-height: 1.4;
  }

  /* Grid Layouts */
  .grid-2 {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
    margin-bottom: 10px;
  }

  .grid-3 {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
    margin-bottom: 10px;
  }

  .grid-4 {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
    margin-bottom: 10px;
  }

  /* Card Components */
  .card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 10px 12px;
  }

  .card-title {
    font-weight: 700;
    font-size: 9pt;
    color: #0f172a;
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    gap: 5px;
  }

  .card-highlight {
    border-left: 3px solid #6366f1;
    background: #f5f3ff;
  }

  .card-success {
    border-left: 3px solid #10b981;
    background: #ecfdf5;
  }

  .card-warning {
    border-left: 3px solid #f59e0b;
    background: #fffbeb;
  }

  .card-danger {
    border-left: 3px solid #ef4444;
    background: #fef2f2;
  }

  .card-blue {
    border-left: 3px solid #0284c7;
    background: #f0f9ff;
  }

  /* Badges */
  .badge {
    display: inline-block;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 7pt;
    font-weight: 700;
    text-transform: uppercase;
  }

  .badge-blue { background: #dbeafe; color: #1e40af; }
  .badge-green { background: #d1fae5; color: #065f46; }
  .badge-amber { background: #fef3c7; color: #92400e; }
  .badge-red { background: #fee2e2; color: #991b1b; }
  .badge-purple { background: #ede9fe; color: #5b21b6; }
  .badge-dark { background: #1e293b; color: #f8fafc; }

  /* Tables */
  table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 10px;
    font-size: 8pt;
  }

  th {
    background: #0f172a;
    color: #ffffff;
    font-weight: 700;
    text-align: left;
    padding: 6px 8px;
    font-size: 8pt;
  }

  td {
    padding: 5px 8px;
    border-bottom: 1px solid #e2e8f0;
    vertical-align: top;
    line-height: 1.35;
  }

  tr:nth-child(even) td {
    background-color: #f8fafc;
  }

  /* Code Block */
  .code-box {
    background: #090d16;
    color: #38bdf8;
    border-radius: 5px;
    padding: 8px 10px;
    font-family: Consolas, "Courier New", monospace;
    font-size: 7.5pt;
    line-height: 1.35;
    margin: 4px 0 8px 0;
    border: 1px solid #1e293b;
    white-space: pre-wrap;
    word-break: break-all;
  }

  .code-box.terminal {
    background: #000000;
    color: #4ade80;
  }

  .footer-note {
    font-size: 7.5pt;
    color: #94a3b8;
    border-top: 1px solid #e2e8f0;
    padding-top: 5px;
    margin-top: 8px;
    display: flex;
    justify-content: space-between;
  }

  .diagram-flow {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 6px;
    margin: 8px 0;
  }

  .diagram-step {
    flex: 1;
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-top: 3px solid #6366f1;
    border-radius: 5px;
    padding: 6px 8px;
    font-size: 7.5pt;
    text-align: center;
  }

  .diagram-step-title {
    font-weight: 700;
    font-size: 8pt;
    color: #0f172a;
    margin-bottom: 2px;
  }

  .diagram-arrow {
    color: #94a3b8;
    font-size: 11pt;
    font-weight: bold;
  }
</style>
</head>
<body>

  <!-- ==================== PAGE 1: COVER PAGE ==================== -->
  <div class="page">
    <div class="cover">
      <div class="cover-badge">System Specification & Technical Architecture</div>
      <h1 class="cover-title">Autonomous Cloud Resource Scheduling & FinOps Governance System</h1>
      <p class="cover-subtitle">
        An enterprise automated FinOps platform featuring continuous policy audits, off-hours shutdown enforcement,
        multi-channel push siren alerts, cryptographic HMAC-SHA256 1-click grace extensions, and dual-engine data persistence.
      </p>
      <div class="cover-divider"></div>

      <div class="cover-meta-grid">
        <div class="cover-meta-item">
          <div class="cover-meta-label">Frontend Stack</div>
          <div class="cover-meta-value">HTML5 • CSS3 Custom Tokens • Vanilla JS ES6+ • Bootstrap 5 • Jinja2</div>
        </div>
        <div class="cover-meta-item">
          <div class="cover-meta-label">Backend Stack</div>
          <div class="cover-meta-value">Python 3.13 • Flask 3.1+ • APScheduler • Boto3 AWS SDK • Cryptography</div>
        </div>
        <div class="cover-meta-item">
          <div class="cover-meta-label">Database Dual-Engine</div>
          <div class="cover-meta-value">SQLAlchemy 2.0+ • MySQL 8.0 Enterprise • SQLite 3 WAL Fallback</div>
        </div>
        <div class="cover-meta-item">
          <div class="cover-meta-label">Multi-Channel Alerts & Networking</div>
          <div class="cover-meta-value">ntfy Siren Push • Twilio SMS/WhatsApp • SMTP Email • Cloudflare Tunnel</div>
        </div>
      </div>

      <div style="margin-top: 28px; font-size: 8.5pt; color: #64748b; line-height: 1.4;">
        <strong>Document Contents:</strong> Complete Architecture Overview, Technology Stack (Frontend, Backend, Database),
        Data Model & Schema DDL, Production Deployment (Render, Local Background, Docker, VPS), Governance Policies,
        Cryptographic Action Security, REST APIs, and Automated Test Protocols.
      </div>
    </div>
  </div>

  <!-- ==================== PAGE 2: EXECUTIVE OVERVIEW & ARCHITECTURE ==================== -->
  <div class="page">
    <div class="section-header">
      <h1 class="section-title">1. System Overview & Architecture</h1>
      <span class="section-tag">Section 1 • Architecture</span>
    </div>

    <h2>1.1 Executive Summary & FinOps Challenge</h2>
    <p>
      In modern multi-cloud infrastructure (AWS, Azure, GCP), development, testing, and staging compute instances frequently run
      <strong>24 hours a day, 7 days a week</strong>, even though teams only operate during business hours (8 to 9 hours/day).
      Over <strong>65% to 70%</strong> of total compute spend is incurred during off-hours, weekends, and holidays.
      This system solves this challenge by autonomously monitoring compute inventory, validating running instances against allowable schedules,
      broadcasting urgent multi-channel alerts, providing 1-click mobile cryptographic extensions, and executing safe automated fallback shutdowns.
    </p>

    <h2>1.2 End-to-End System Workflow</h2>
    <div class="diagram-flow">
      <div class="diagram-step">
        <div class="diagram-step-title">1. Discovery</div>
        <div>AWS Boto3 & Mock Adapter discovers instances into DB</div>
      </div>
      <div class="diagram-arrow">➔</div>
      <div class="diagram-step">
        <div class="diagram-step-title">2. Policy Audit</div>
        <div>APScheduler 60s background cycle detects off-hour breaches</div>
      </div>
      <div class="diagram-arrow">➔</div>
      <div class="diagram-step">
        <div class="diagram-step-title">3. Multi-Channel Alert</div>
        <div>Dispatches ntfy siren push, Twilio SMS/WA, and SMTP email</div>
      </div>
      <div class="diagram-arrow">➔</div>
      <div class="diagram-step">
        <div class="diagram-step-title">4. 1-Click Action</div>
        <div>HMAC token: Stop instance or Extend lease by 2 hours</div>
      </div>
      <div class="diagram-arrow">➔</div>
      <div class="diagram-step">
        <div class="diagram-step-title">5. Auto-Shutdown</div>
        <div>If unacknowledged for 30m, safe fallback shutdown executes</div>
      </div>
    </div>

    <h2>1.3 Key Architectural Modules</h2>
    <div class="grid-2">
      <div class="card card-highlight">
        <div class="card-title">🛡️ Policy & Scheduler Engine (APScheduler)</div>
        <p>
          Continuously evaluates schedules using UTC timestamps. Identifies un-tagged, idle, or after-hours instances.
          Manages automated 30-minute fallback shutdown countdowns to eliminate cost leakage.
        </p>
      </div>
      <div class="card card-blue">
        <div class="card-title">🔐 Cryptographic Action Gateway (HMAC-SHA256)</div>
        <p>
          Generates time-limited (15-min TTL) cryptographically signed URLs for Stop and Extend actions.
          Eliminates the need for engineers to log into the AWS Console; supports single-click execution from lockscreen notifications.
        </p>
      </div>
      <div class="card card-warning">
        <div class="card-title">📢 Real-Time Multi-Channel Dispatcher</div>
        <p>
          Dispatches alerts simultaneously via <strong>ntfy Mobile Push</strong> (with audible emergency buzzer sirens),
          <strong>Twilio SMS & WhatsApp</strong>, and <strong>Gmail SMTP</strong> with styled HTML action buttons.
        </p>
      </div>
      <div class="card card-success">
        <div class="card-title">🌐 Cloudflare Edge Ingress Tunnel</div>
        <p>
          Integrates <code>cloudflared.exe</code> to expose the local host on a secure HTTPS domain
          (<code>https://*.trycloudflare.com</code>), enabling remote smartphone access over 4G/5G mobile networks.
        </p>
      </div>
    </div>

    <div class="footer-note">
      <span>Cloud Resource Scheduling System • Technical Specification</span>
      <span>Page 2</span>
    </div>
  </div>

  <!-- ==================== PAGE 3: TECHNOLOGY STACK BREAKDOWN ==================== -->
  <div class="page">
    <div class="section-header">
      <h1 class="section-title">2. Complete Technology Stack</h1>
      <span class="section-tag">Section 2 • Technologies</span>
    </div>

    <h2>2.1 Frontend Technologies (Client-Side)</h2>
    <table>
      <thead>
        <tr>
          <th style="width: 25%;">Technology</th>
          <th style="width: 25%;">Version / Type</th>
          <th style="width: 50%;">Role & Functional Implementation</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>HTML5</strong></td>
          <td>Semantic Web Standard</td>
          <td>Structures all operational dashboards, KPI cards, resource tables, schedule dialogs, and mobile confirmation views.</td>
        </tr>
        <tr>
          <td><strong>CSS3 & Custom Tokens</strong></td>
          <td>Custom Design System</td>
          <td>CSS variables, glassmorphism, responsive flex/grid layouts, card border accents, and micro-animations in <code>style.css</code>.</td>
        </tr>
        <tr>
          <td><strong>JavaScript (ES6+)</strong></td>
          <td>Vanilla Asynchronous JS</td>
          <td>Dynamic client-side controller in <code>dashboard.js</code>; manages 20s telemetry auto-refresh, fetch API calls, and DOM updates.</td>
        </tr>
        <tr>
          <td><strong>Bootstrap 5</strong></td>
          <td>v5.3+ (Dark/Light Console)</td>
          <td>Executive UI components, responsive layout grid, form controls, tables, and modal dialogs.</td>
        </tr>
        <tr>
          <td><strong>Jinja2</strong></td>
          <td>Flask Templating Engine</td>
          <td>Server-side HTML template inheritance (<code>base.html</code>), conditional RBAC rendering, and session token injection.</td>
        </tr>
        <tr>
          <td><strong>FontAwesome 6</strong></td>
          <td>v6.5+ (CDN)</td>
          <td>Vector iconography for cloud providers (AWS, Azure, GCP), status badges, and action triggers.</td>
        </tr>
        <tr>
          <td><strong>Google Fonts</strong></td>
          <td>Web Fonts Stack</td>
          <td><strong>Plus Jakarta Sans</strong> (Headings/UI), <strong>Inter</strong> (Body text), and <strong>JetBrains Mono</strong> (Telemetry/IPs).</td>
        </tr>
      </tbody>
    </table>

    <h2>2.2 Backend Technologies (Server-Side)</h2>
    <table>
      <thead>
        <tr>
          <th style="width: 25%;">Component</th>
          <th style="width: 25%;">Technology & Version</th>
          <th style="width: 50%;">Role & Functional Implementation</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>Language</strong></td>
          <td>Python 3.13 / 3.11+</td>
          <td>High-performance, type-hinted core server runtime executing web requests and asynchronous scheduler threads.</td>
        </tr>
        <tr>
          <td><strong>Web Framework</strong></td>
          <td>Flask 3.1+</td>
          <td>Application Factory pattern with Blueprints: <code>auth_bp</code>, <code>dashboard_bp</code>, <code>api_bp</code>, and <code>webhook_bp</code>.</td>
        </tr>
        <tr>
          <td><strong>Background Scheduler</strong></td>
          <td>APScheduler 3.10+</td>
          <td>In-process multi-threaded <code>BackgroundScheduler</code> running 60-second periodic policy audit loops and auto-shutdown timers.</td>
        </tr>
        <tr>
          <td><strong>Cloud SDK</strong></td>
          <td>AWS Boto3 1.34+</td>
          <td>Interacts with live AWS EC2 APIs (<code>describe_instances</code>, <code>start_instances</code>, <code>stop_instances</code>).</td>
        </tr>
        <tr>
          <td><strong>Simulation Engine</strong></td>
          <td>Mock Cloud Adapter</td>
          <td>Pre-seeded with realistic EC2 instances for high-fidelity offline demonstrations without incurring cloud billing.</td>
        </tr>
        <tr>
          <td><strong>Security & Hashing</strong></td>
          <td>Bcrypt 4.1+ & HMAC-SHA256</td>
          <td>Bcrypt for password hashing (12 rounds) and HMAC-SHA256 for signing tamper-proof single-click action tokens.</td>
        </tr>
        <tr>
          <td><strong>Notification Gateways</strong></td>
          <td>ntfy.sh / Twilio / SMTP</td>
          <td>Multi-channel alert dispatching across mobile push sirens (ntfy), SMS/WhatsApp (Twilio), and HTML email (Gmail TLS).</td>
        </tr>
        <tr>
          <td><strong>Edge Tunnel</strong></td>
          <td>Cloudflare Tunnel</td>
          <td>Embedded <code>cloudflared.exe</code> mapping port 5000 to public HTTPS for mobile webhook callbacks over cell networks.</td>
        </tr>
        <tr>
          <td><strong>Production Server</strong></td>
          <td>Gunicorn 21.2+</td>
          <td>Production WSGI HTTP server supporting multi-worker execution on Linux and cloud platforms.</td>
        </tr>
      </tbody>
    </table>

    <div class="footer-note">
      <span>Cloud Resource Scheduling System • Technical Specification</span>
      <span>Page 3</span>
    </div>
  </div>

  <!-- ==================== PAGE 4: DATABASE & ORM ARCHITECTURE ==================== -->
  <div class="page">
    <div class="section-header">
      <h1 class="section-title">3. Database & Data Model Architecture</h1>
      <span class="section-tag">Section 3 • Database</span>
    </div>

    <h2>3.1 Dual-Engine Database Architecture</h2>
    <p>
      The system employs a <strong>Dual-Engine Architecture</strong> managed through <strong>SQLAlchemy 2.0+ ORM</strong> with thread-safe
      <code>scoped_session</code> management. It connects to MySQL in production, and automatically falls back to SQLite if MySQL is offline:
    </p>
    <div class="grid-2">
      <div class="card card-highlight">
        <div class="card-title">🐬 Primary: MySQL 8.0+ Enterprise</div>
        <p style="font-size: 8pt;">
          • Driver: <code>pymysql 1.1+</code><br>
          • Connection pool: <code>pool_pre_ping=True</code>, <code>pool_recycle=3600</code><br>
          • Complete DDL script provided in <code>schema.sql</code> with foreign key cascades and indexes.
        </p>
      </div>
      <div class="card card-success">
        <div class="card-title">🗃️ Automatic Fallback: SQLite 3</div>
        <p style="font-size: 8pt;">
          • Database file: <code>cloud_scheduler.db</code> (zero manual configuration)<br>
          • Optimized with high-concurrency <strong>WAL (Write-Ahead Logging)</strong> mode<br>
          • Pragma: <code>synchronous=NORMAL</code>, <code>cache_size=10000</code>.
        </p>
      </div>
    </div>

    <h2>3.2 Database Entity-Relationship (ER) Schema</h2>
    <table>
      <thead>
        <tr>
          <th style="width: 20%;">Table</th>
          <th style="width: 35%;">Key Columns</th>
          <th style="width: 45%;">Functional Role & Relationships</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>users</strong></td>
          <td><code>id, name, email, password_hash, phone_number, role, created_at</code></td>
          <td>RBAC user accounts. Roles: <code>Admin</code>, <code>Manager</code>, <code>Viewer</code>. Passwords hashed with Bcrypt.</td>
        </tr>
        <tr>
          <td><strong>cloud_resources</strong></td>
          <td><code>id, instance_id, instance_name, provider, region, state, public_ip, private_ip, launch_time, lease_expires_at, alert_sent_at</code></td>
          <td>Discovered compute instances. Tracks operational state (running/stopped), continuous uptime hours, and active lease expirations.</td>
        </tr>
        <tr>
          <td><strong>schedules</strong></td>
          <td><code>id, resource_id, start_time, end_time, max_runtime_hours, days_of_week, is_active</code></td>
          <td>Permitted execution policies per resource. Supports both daily recurring windows (HH:MM) and calendar timestamps (DD-MM-YYYY HH:MM).</td>
        </tr>
        <tr>
          <td><strong>alert_logs</strong></td>
          <td><code>id, resource_id, channel, recipient, status, token_hash, details, sent_at</code></td>
          <td>Audit log of outbound alerts dispatched across ntfy, Twilio SMS, WhatsApp, and SMTP Email with delivery statuses.</td>
        </tr>
        <tr>
          <td><strong>audit_trails</strong></td>
          <td><code>id, resource_id, triggered_by, action_taken, details, timestamp</code></td>
          <td>Immutable ledger of state changes: START, STOP, EXTEND_LEASE, SCAN, POLICY_SHUTDOWN, and operator actions.</td>
        </tr>
        <tr>
          <td><strong>cloud_accounts</strong></td>
          <td><code>id, provider, account_name, account_identifier, region, credentials_json, status, is_active</code></td>
          <td>Encrypted multi-cloud credentials for connecting live AWS, Azure, and Google Cloud Platform environments.</td>
        </tr>
      </tbody>
    </table>

    <h2>3.3 FinOps Cost Calculation Formulas</h2>
    <div class="grid-2">
      <div class="card card-blue">
        <div class="card-title">💵 Active Cost Burn Calculation</div>
        <div class="code-box">Active Hourly Burn ($) = Total Running Instances × Hourly Rate ($0.096)
Active Hourly Burn (₹) = Active Hourly Burn ($) × USD_TO_INR_RATE (83.50)</div>
      </div>
      <div class="card card-success">
        <div class="card-title">🛡️ Protected Capital / Total Savings</div>
        <div class="code-box">Cumulative Savings ($) = Stopped Instances × Off-Hours Saved × Hourly Rate
Cumulative Savings (₹) = Cumulative Savings ($) × 83.50</div>
      </div>
    </div>

    <div class="footer-note">
      <span>Cloud Resource Scheduling System • Technical Specification</span>
      <span>Page 4</span>
    </div>
  </div>

  <!-- ==================== PAGE 5: STEP-BY-STEP DEPLOYMENT GUIDE ==================== -->
  <div class="page">
    <div class="section-header">
      <h1 class="section-title">4. Comprehensive Deployment Guide</h1>
      <span class="section-tag">Section 4 • Deployment</span>
    </div>

    <h2>4.1 Method 1: Cloud Deployment on Render (Free Hosting Pre-Configured)</h2>
    <p>
      The repository includes a ready-to-use <code>render.yaml</code> blueprint and <code>Procfile</code> for one-click deployment:
    </p>
    <ol>
      <li><strong>Push to GitHub:</strong> Initialize git and push the repository to GitHub:
        <div class="code-box terminal">git init && git add . && git commit -m "Deploy Cloud Scheduler"
git remote add origin https://github.com/&lt;user&gt;/&lt;repo&gt;.git
git push -u origin main</div>
      </li>
      <li><strong>Connect to Render:</strong> Log in to <a href="https://render.com">render.com</a>, click <strong>New +</strong> &gt; <strong>Blueprint</strong>, and select the repository.</li>
      <li><strong>Configure Environment Variables:</strong> Set the following required variables in the Render Dashboard:
        <ul>
          <li><code>WEBHOOK_BASE_URL</code>: <code>https://&lt;your-app-name&gt;.onrender.com</code> (enables remote mobile action clicks)</li>
          <li><code>USE_SQLITE_FALLBACK</code>: <code>True</code></li>
          <li><code>USE_MOCK_AWS</code>: <code>True</code> (or <code>False</code> if passing live AWS keys)</li>
          <li><code>NTFY_TOPIC</code>: <code>vasanth_cloud_alerts</code></li>
        </ul>
      </li>
      <li><strong>Deploy:</strong> Render runs <code>pip install -r requirements.txt</code> and executes <code>python run.py</code>.</li>
    </ol>

    <h2>4.2 Method 2: Local 24/7 Deployment with Cloudflare Tunnel (Windows)</h2>
    <p>
      For running the system continuously on a host machine with zero cloud costs while allowing remote mobile access:
    </p>
    <div class="grid-2">
      <div class="card card-highlight">
        <div class="card-title">🚀 1-Click Silent Background Host</div>
        <p style="font-size: 8pt;">
          Double-click <code>START_BACKGROUND.bat</code>. It spawns the server as a background process and launches the Cloudflare Tunnel.
          The scheduler and phone push alerts continue running 24/7 even after Antigravity IDE is closed.
        </p>
      </div>
      <div class="card card-blue">
        <div class="card-title">🛑 Stopping the System</div>
        <p style="font-size: 8pt;">
          Double-click <code>STOP_SYSTEM.bat</code>. It cleanly terminates any process bound to port 5000 and kills running <code>cloudflared</code> tunnel processes.
        </p>
      </div>
    </div>

    <h2>4.3 Method 3: Containerized Deployment (Docker)</h2>
    <p>The included <code>Dockerfile</code> provides a production container based on <code>python:3.13-slim</code>:</p>
    <div class="code-box terminal"># 1. Build the Docker container image
docker build -t cloud-resource-scheduler .

# 2. Run container in detached mode with persistent database volume
docker run -d --name cloud-scheduler -p 5000:5000 --env-file .env -v scheduler-db:/app/instance --restart unless-stopped cloud-resource-scheduler</div>

    <h2>4.4 Method 4: Production Linux Server (Ubuntu / AWS EC2)</h2>
    <div class="code-box terminal"># 1. Install system runtime & virtual environment
sudo apt update && sudo apt install -y python3 python3-pip python3-venv git
git clone &lt;repo-url&gt; /opt/cloud-scheduler && cd /opt/cloud-scheduler
python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt

# 2. Run with Gunicorn production server
gunicorn --workers 3 --bind 0.0.0.0:5000 "run:app"</div>

    <div class="footer-note">
      <span>Cloud Resource Scheduling System • Technical Specification</span>
      <span>Page 5</span>
    </div>
  </div>

  <!-- ==================== PAGE 6: SECURITY, APIS & TESTING ==================== -->
  <div class="page">
    <div class="section-header">
      <h1 class="section-title">5. Security, Webhooks & Automated Testing</h1>
      <span class="section-tag">Section 5 • Security & Quality</span>
    </div>

    <h2>5.1 Cryptographic Action Tokens (HMAC-SHA256)</h2>
    <p>
      Single-click remote governance actions (Stop and Extend) operate without requiring engineers to enter passwords or log into the cloud console:
    </p>
    <ul>
      <li><strong>Token Structure:</strong> Base64 URL-safe encoded payload containing <code>instance_id</code>, <code>action</code>, <code>nonce</code>, and <code>exp</code> timestamp.</li>
      <li><strong>Cryptographic Signature:</strong> Signed using HMAC-SHA256 with the server's <code>SECRET_KEY</code>.</li>
      <li><strong>Time-To-Live (TTL):</strong> Strict 15-minute validity window (<code>ACTION_TOKEN_TTL_SECONDS=900</code>). Expired tokens are immediately rejected.</li>
      <li><strong>Replay & Tamper Protection:</strong> Altering any single byte invalidates the signature; tokens are consumed on execution to prevent replay attacks.</li>
    </ul>

    <h2>5.2 Core REST API Endpoints</h2>
    <table>
      <thead>
        <tr>
          <th style="width: 25%;">Endpoint</th>
          <th style="width: 15%;">Method</th>
          <th style="width: 20%;">Auth Level</th>
          <th style="width: 40%;">Description</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><code>/quick-login</code></td>
          <td>GET</td>
          <td>Public</td>
          <td>1-Click instant administrator authentication for fast access during demonstrations.</td>
        </tr>
        <tr>
          <td><code>/api/resources</code></td>
          <td>GET / POST</td>
          <td>Session (Admin/Manager)</td>
          <td>Retrieves discovered cloud compute instances or initiates manual cloud inventory sync.</td>
        </tr>
        <tr>
          <td><code>/api/resources/&lt;id&gt;/action</code></td>
          <td>POST</td>
          <td>Session (Admin/Manager)</td>
          <td>Triggers manual START, STOP, or EXTEND action on an EC2 instance.</td>
        </tr>
        <tr>
          <td><code>/api/schedules</code></td>
          <td>GET / POST</td>
          <td>Session (Admin)</td>
          <td>Reads or configures operating hours, runtime caps, and active days per resource.</td>
        </tr>
        <tr>
          <td><code>/api/audit-policies</code></td>
          <td>POST</td>
          <td>Session (Admin)</td>
          <td>Manually triggers an immediate policy audit cycle outside the 60s background loop.</td>
        </tr>
        <tr>
          <td><code>/webhook/action</code></td>
          <td>GET / POST</td>
          <td>HMAC Token</td>
          <td>Validates cryptographic token and executes remote 1-click Stop or 2-Hour Lease Extension.</td>
        </tr>
      </tbody>
    </table>

    <h2>5.3 Automated Pytest Test Suite</h2>
    <p>The project includes <strong>16 passing automated tests</strong> covering all critical policy and security paths:</p>
    <div class="code-box terminal"># Run the full automated test suite with verbose output
python -m pytest -v tests</div>
    <div class="grid-3">
      <div class="card card-highlight">
        <div class="card-title">test_tokens.py</div>
        <p style="font-size: 7.5pt;">
          • HMAC signature generation<br>
          • Tamper detection rejection<br>
          • 15-minute TTL expiration<br>
          • Replay prevention verification
        </p>
      </div>
      <div class="card card-blue">
        <div class="card-title">test_scheduler.py</div>
        <p style="font-size: 7.5pt;">
          • EC2 discovery & state transition<br>
          • Schedule window compliance<br>
          • Policy breach alert dispatch<br>
          • 30m fallback auto-shutdown
        </p>
      </div>
      <div class="card card-success">
        <div class="card-title">test_webhook.py</div>
        <p style="font-size: 7.5pt;">
          • GET 1-click STOP execution<br>
          • POST 2-hour lease extension<br>
          • Mobile HTML response confirmation<br>
          • Invalid token error rejection
        </p>
      </div>
    </div>

    <h2>5.4 Default System Credentials</h2>
    <div class="grid-2">
      <div class="card card-highlight">
        <div class="card-title">👤 Primary Admin Account</div>
        <p style="font-size: 8pt;">
          • <strong>Email:</strong> <code>vasanthkumar20212021@gmail.com</code><br>
          • <strong>Passkey:</strong> <code>password123</code> (or <code>Admin@123456</code>)<br>
          • <strong>1-Click Instant Login:</strong> Navigate directly to <code>/quick-login</code>
        </p>
      </div>
      <div class="card card-warning">
        <div class="card-title">📱 Emergency Alert Dispatch Configuration</div>
        <p style="font-size: 8pt;">
          • <strong>ntfy Push Channel:</strong> <code>https://ntfy.sh/vasanth_cloud_alerts</code><br>
          • <strong>Alert Phone / WhatsApp:</strong> <code>+919025903459</code><br>
          • <strong>Recipient Email:</strong> <code>vasanthkumar20262026@gmail.com</code>
        </p>
      </div>
    </div>

    <div class="footer-note">
      <span>Cloud Resource Scheduling System • Technical Specification</span>
      <span>Page 6</span>
    </div>
  </div>

</body>
</html>
"""

def generate_pdf():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    scratch_dir = os.path.join(base_dir, 'scratch')
    os.makedirs(scratch_dir, exist_ok=True)

    html_file = os.path.join(scratch_dir, 'full_project_documentation.html')
    output_pdf = os.path.join(base_dir, 'Cloud_Resource_Scheduling_Full_Project_Documentation.pdf')

    html_content = build_full_doc_html()
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"[*] Wrote documentation HTML to {html_file}")

    # Microsoft Edge path candidates
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expanduser(r"~\AppData\Local\Microsoft\Edge\Application\msedge.exe")
    ]
    edge_exe = next((p for p in edge_paths if os.path.exists(p)), None)

    if not edge_exe:
        print("[!] Microsoft Edge executable not found. Unable to render PDF via Edge.")
        sys.exit(1)

    print(f"[*] Utilizing Microsoft Edge at: {edge_exe}")
    cmd = [
        edge_exe,
        '--headless',
        '--disable-gpu',
        '--no-pdf-header-footer',
        f'--print-to-pdf={output_pdf}',
        html_file
    ]

    print("[*] Executing PDF rendering command...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if os.path.exists(output_pdf) and os.path.getsize(output_pdf) > 0:
        size_kb = os.path.getsize(output_pdf) / 1024
        print(f"[SUCCESS] PDF generated successfully: {output_pdf} ({size_kb:.1f} KB)")
        return output_pdf
    else:
        print(f"[ERROR] PDF generation failed. Stderr: {result.stderr}")
        sys.exit(1)

if __name__ == '__main__':
    generate_pdf()
