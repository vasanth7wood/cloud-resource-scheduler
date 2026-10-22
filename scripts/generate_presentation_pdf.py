"""
Script to generate a comprehensive, executive-ready Presentation Guide PDF
for the Cloud Resource Scheduling and Governance System using Headless Edge.
"""

import os
import subprocess
import sys

def build_presentation_html() -> str:
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Cloud Resource Scheduling & FinOps Governance System - Presentation & Technical Guide</title>
<style>
  @page {
    size: A4 portrait;
    margin: 14mm 14mm 14mm 14mm;
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
    font-size: 10.5pt;
    margin: 0;
    padding: 0;
  }

  .page {
    page-break-after: always;
    position: relative;
    padding-bottom: 10px;
  }

  .page:last-child {
    page-break-after: avoid;
  }

  /* Cover Page */
  .cover {
    display: flex;
    flex-direction: column;
    justify-content: center;
    min-height: 90vh;
    padding: 40px 20px;
    background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
    color: #ffffff;
    border-radius: 16px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
  }

  .cover-badge {
    display: inline-block;
    align-self: flex-start;
    background: rgba(99, 102, 241, 0.25);
    border: 1px solid #818cf8;
    color: #c7d2fe;
    font-size: 9pt;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 6px 14px;
    border-radius: 9999px;
    margin-bottom: 24px;
  }

  .cover-title {
    font-size: 28pt;
    font-weight: 800;
    line-height: 1.2;
    margin: 0 0 12px 0;
    color: #ffffff;
  }

  .cover-subtitle {
    font-size: 14pt;
    color: #94a3b8;
    font-weight: 400;
    margin: 0 0 30px 0;
    line-height: 1.4;
  }

  .cover-divider {
    height: 3px;
    width: 80px;
    background: linear-gradient(90deg, #6366f1, #38bdf8);
    margin-bottom: 30px;
    border-radius: 2px;
  }

  .cover-meta-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
    margin-top: 20px;
  }

  .cover-meta-item {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    padding: 12px 16px;
  }

  .cover-meta-label {
    font-size: 8pt;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #94a3b8;
  }

  .cover-meta-value {
    font-size: 10.5pt;
    font-weight: 600;
    color: #f1f5f9;
    margin-top: 4px;
  }

  /* Section Styles */
  .section-header {
    border-bottom: 2px solid #e2e8f0;
    padding-bottom: 8px;
    margin-bottom: 16px;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
  }

  .section-title {
    font-size: 16pt;
    font-weight: 800;
    color: #0f172a;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .section-tag {
    font-size: 8.5pt;
    font-weight: 700;
    color: #6366f1;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  h2 {
    font-size: 12.5pt;
    color: #1e293b;
    margin: 14px 0 8px 0;
    border-left: 4px solid #6366f1;
    padding-left: 8px;
  }

  h3 {
    font-size: 11pt;
    color: #334155;
    margin: 10px 0 6px 0;
  }

  p {
    margin: 0 0 10px 0;
    color: #334155;
  }

  /* Cards and Grids */
  .grid-2 {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
    margin-bottom: 12px;
  }

  .grid-3 {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    margin-bottom: 12px;
  }

  .card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 12px 14px;
  }

  .card-highlight {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
  }

  .card-primary {
    background: #eef2ff;
    border: 1px solid #c7d2fe;
  }

  .card-warning {
    background: #fffbeb;
    border: 1px solid #fde68a;
  }

  .card-danger {
    background: #fef2f2;
    border: 1px solid #fecaca;
  }

  .card-title {
    font-size: 10pt;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  /* Tables */
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 6px 0 10px 0;
    font-size: 8pt;
  }

  th {
    background-color: #0f172a;
    color: #ffffff;
    font-weight: 600;
    text-align: left;
    padding: 5px 8px;
    font-size: 8pt;
    letter-spacing: 0.03em;
  }

  th:first-child {
    border-top-left-radius: 6px;
  }

  th:last-child {
    border-top-right-radius: 6px;
  }

  td {
    padding: 4px 8px;
    border-bottom: 1px solid #e2e8f0;
    color: #334155;
    vertical-align: top;
    line-height: 1.35;
  }

  tr:nth-child(even) td {
    background-color: #f8fafc;
  }

  /* Badges */
  .badge {
    display: inline-block;
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 7.5pt;
    font-weight: 700;
    text-transform: uppercase;
  }

  .badge-blue { background: #dbeafe; color: #1e40af; }
  .badge-green { background: #dcfce7; color: #166534; }
  .badge-purple { background: #f3e8ff; color: #6b21a8; }
  .badge-amber { background: #fef3c7; color: #92400e; }
  .badge-red { background: #fee2e2; color: #991b1b; }
  .badge-dark { background: #e2e8f0; color: #0f172a; }

  /* Speaker Script Box */
  .speaker-box {
    background: #fdf4ff;
    border: 1px solid #f0abfc;
    border-left: 5px solid #d946ef;
    border-radius: 6px;
    padding: 10px 14px;
    margin: 10px 0 12px 0;
    font-size: 9pt;
  }

  .speaker-header {
    font-weight: 800;
    color: #86198f;
    margin-bottom: 4px;
    font-size: 8.5pt;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .speaker-text {
    color: #4a044e;
    font-style: italic;
    line-height: 1.45;
  }

  /* Architecture Flow Diagram (CSS Blocks) */
  .flow-container {
    display: flex;
    justify-content: space-between;
    align-items: stretch;
    gap: 8px;
    margin: 12px 0;
  }

  .flow-step {
    flex: 1;
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-top: 4px solid #6366f1;
    border-radius: 6px;
    padding: 8px 10px;
    font-size: 8pt;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  }

  .flow-step-num {
    font-weight: 800;
    color: #6366f1;
    font-size: 7.5pt;
    text-transform: uppercase;
  }

  .flow-step-title {
    font-weight: 700;
    color: #0f172a;
    font-size: 9pt;
    margin: 2px 0 4px 0;
  }

  .flow-arrow {
    display: flex;
    align-items: center;
    font-size: 14pt;
    color: #94a3b8;
    font-weight: bold;
  }

  /* Code snippet block */
  .code-box {
    background: #0f172a;
    color: #38bdf8;
    border-radius: 6px;
    padding: 8px 12px;
    font-family: Consolas, "Courier New", monospace;
    font-size: 8pt;
    line-height: 1.35;
    margin: 6px 0 10px 0;
    overflow: hidden;
  }

  .code-comment { color: #64748b; }
  .code-keyword { color: #f43f5e; }
  .code-str { color: #a3e635; }
  .code-var { color: #f8fafc; }

  .footer-note {
    font-size: 7.5pt;
    color: #94a3b8;
    border-top: 1px solid #e2e8f0;
    padding-top: 6px;
    margin-top: 10px;
    display: flex;
    justify-content: space-between;
  }
</style>
</head>
<body>

  <!-- ==================== PAGE 1: COVER PAGE ==================== -->
  <div class="page">
    <div class="cover">
      <div class="cover-badge">Project Presentation & Technical Architecture</div>
      <h1 class="cover-title">Autonomous Cloud Resource Scheduling & FinOps Governance System</h1>
      <p class="cover-subtitle">
        An Automated FinOps Platform with Multi-Cloud Lifecycle Management, Continuous Policy Audits,
        Real-Time Siren & Multi-Channel Alerting, and Cryptographic 1-Click Action Tokens.
      </p>
      <div class="cover-divider"></div>
      
      <div class="cover-meta-grid">
        <div class="cover-meta-item">
          <div class="cover-meta-label">Primary Technology Stack</div>
          <div class="cover-meta-value">Python 3.13 • Flask 3.1 • SQLAlchemy • APScheduler</div>
        </div>
        <div class="cover-meta-item">
          <div class="cover-meta-label">Alerting Channels</div>
          <div class="cover-meta-value">ntfy Siren Push • Twilio SMS • WhatsApp • SMTP Email</div>
        </div>
        <div class="cover-meta-item">
          <div class="cover-meta-label">Security & Remote Actions</div>
          <div class="cover-meta-value">HMAC-SHA256 Signed Tokens • Cloudflare Tunnel</div>
        </div>
        <div class="cover-meta-item">
          <div class="cover-meta-label">FinOps Savings Engine</div>
          <div class="cover-meta-value">Dual-Currency (USD $ & INR ₹) • Automated 30m Fallback</div>
        </div>
      </div>
      
      <div style="margin-top: 30px; font-size: 9pt; color: #64748b;">
        Comprehensive Speaking Guide, Architecture Breakdown, and Live Demonstration Manual
      </div>
    </div>
  </div>

  <!-- ==================== PAGE 2: PROBLEM STATEMENT & MOTIVATION ==================== -->
  <div class="page">
    <div class="section-header">
      <h1 class="section-title">1. Executive Overview & Problem Statement</h1>
      <span class="section-tag">Slide 1 • Context & Value</span>
    </div>

    <h2>The Core Problem: Uncontrolled Cloud Sprawl & Cost Leakage</h2>
    <p>
      In modern enterprise cloud environments (AWS, Azure, GCP), development, testing, and staging compute resources
      frequently run <strong>24/7</strong> even though engineers only work 8 to 9 hours a day. Over <strong>65% to 70%</strong>
      of total cloud runtime occurs during idle off-hours, weekends, and holidays, wasting billions of dollars annually.
    </p>

    <div class="grid-3">
      <div class="card card-danger">
        <div class="card-title">⚠️ Blind Auto-Shutdowns <span class="badge badge-red">Disruptive</span></div>
        <p style="font-size: 8.5pt;">
          Traditional cron scripts abruptly terminate servers during active deployments or prolonged training runs,
          corrupting data and angering engineering teams.
        </p>
      </div>
      <div class="card card-warning">
        <div class="card-title">✉️ Buried Email Alerts <span class="badge badge-amber">Ignored</span></div>
        <p style="font-size: 8.5pt;">
          Standard cloud monitoring emails get lost in crowded developer inboxes. By the time someone notices,
          hundreds of dollars have already burned overnight.
        </p>
      </div>
      <div class="card card-highlight">
        <div class="card-title">🔐 VPN & Console Friction <span class="badge badge-green">Slow</span></div>
        <p style="font-size: 8.5pt;">
          To stop a resource from a mobile phone, an engineer must log into AWS Console via MFA, navigate EC2,
          and select instances—taking 5 to 10 minutes of friction.
        </p>
      </div>
    </div>

    <h2>Our Solution: Autonomous FinOps Governance Platform</h2>
    <p>
      We engineered a production-grade governance platform that harmonizes <strong>automated policy enforcement</strong>
      with <strong>frictionless human-in-the-loop controls</strong>:
    </p>
    <ul>
      <li><strong>Continuous In-Process Audits:</strong> APScheduler evaluates running workloads every 60 seconds against defined operational windows and maximum runtime caps.</li>
      <li><strong>High-Urgency Multi-Channel Alerting:</strong> Broadcasts urgent audible sirens to mobile phones via <code>ntfy</code>, alongside Twilio SMS, WhatsApp, and rich HTML emails.</li>
      <li><strong>Cryptographic 1-Click Action Tokens:</strong> Engineers can Stop the instance or Extend its lease (+60m) straight from their mobile phone lockscreen using time-bound, tamper-proof HMAC-SHA256 URLs without logging in.</li>
      <li><strong>30-Minute Grace Fallback Shutdown:</strong> If an alert goes unacknowledged for 30 minutes, the platform safely powers down the resource, guaranteeing zero overnight cost leaks.</li>
    </ul>

    <div class="speaker-box">
      <div class="speaker-header">🎤 What to Say to Examiners / Interviewers (Speaker Script)</div>
      <div class="speaker-text">
        "Good morning everyone. Today I'm presenting our Cloud Resource Scheduling and FinOps Governance Platform. 
        In enterprise cloud environments, up to 70% of compute budget is wasted on idle development servers running overnight and through weekends. 
        The existing solutions have two big flaws: they either shut down servers blindly and disrupt engineers, or they send passive emails that get ignored. 
        Our system bridges this gap: it continuously monitors workloads, sounds an instant audio siren on the operator's mobile phone, and provides a 1-click 
        tamper-proof button to either extend work or power down immediately. And if the operator is asleep, an automated 30-minute fallback takes over to protect company capital."
      </div>
    </div>

    <div class="footer-note">
      <span>Cloud Resource Scheduling System • Project Presentation Guide</span>
      <span>Page 2</span>
    </div>
  </div>

  <!-- ==================== PAGE 3: TOOLS, LANGUAGES & TECH STACK ==================== -->
  <div class="page">
    <div class="section-header">
      <h1 class="section-title">2. Tools, Languages & Technology Stack</h1>
      <span class="section-tag">Slide 2 • Technical Deep-Dive</span>
    </div>

    <h2>Comprehensive Technology Stack Breakdown</h2>
    <table>
      <thead>
        <tr>
          <th style="width: 22%;">Layer / Category</th>
          <th style="width: 28%;">Tool / Technology Used</th>
          <th style="width: 50%;">Detailed Role in the Application</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>Programming Language</strong></td>
          <td><span class="badge badge-blue">Python 3.13 (64-bit)</span></td>
          <td>Core runtime. Utilizes modern type hints, high-speed standard library (<code>hashlib</code>, <code>hmac</code>, <code>smtplib</code>), sub-process management, and thread pooling.</td>
        </tr>
        <tr>
          <td><strong>Web Framework</strong></td>
          <td><span class="badge badge-green">Flask 3.1+</span></td>
          <td>Modular Application Factory pattern with Blueprints: <code>auth</code> (RBAC), <code>dashboard</code>, <code>api</code> (RESTful endpoints), and <code>webhook</code> (HMAC action processor).</td>
        </tr>
        <tr>
          <td><strong>ORM & Database</strong></td>
          <td><span class="badge badge-purple">SQLAlchemy 2.0+ Dual-Engine</span></td>
          <td><strong>SQLite Fallback:</strong> <code>cloud_scheduler.db</code> for seamless zero-dependency local setup.<br><strong>MySQL 8.0:</strong> <code>PyMySQL</code> for production relational integrity and high concurrency.</td>
        </tr>
        <tr>
          <td><strong>Task Scheduler</strong></td>
          <td><span class="badge badge-amber">APScheduler 3.11</span></td>
          <td>In-process <code>BackgroundScheduler</code> executing non-blocking, periodic 60-second governance audit loops with thread pooling and graceful shutdown hooks.</td>
        </tr>
        <tr>
          <td><strong>Multi-Cloud SDK & Mock</strong></td>
          <td><span class="badge badge-dark">AWS Boto3 & Mock Adapter</span></td>
          <td><strong>Live Mode:</strong> Interacts with AWS EC2 API (<code>describe_instances</code>, <code>start_instances</code>, <code>stop_instances</code>).<br><strong>Mock Driver:</strong> Offline simulation for demo & testing without cloud fees.</td>
        </tr>
        <tr>
          <td><strong>Public Edge Tunnel</strong></td>
          <td><span class="badge badge-blue">Cloudflare Tunnel (cloudflared)</span></td>
          <td>Exposes local port 5000 via a secure, zero-config HTTPS URL (<code>*.trycloudflare.com</code>). Allows mobile phones worldwide to access webhook action links.</td>
        </tr>
        <tr>
          <td><strong>Push & Siren Gateway</strong></td>
          <td><span class="badge badge-red">ntfy.sh JSON API</span></td>
          <td>Dispatches instant priority-5 push notifications to mobile phones with audio siren playback (<code>buzzer.wav</code>), vibration, and interactive 1-click action buttons.</td>
        </tr>
        <tr>
          <td><strong>SMS & WhatsApp</strong></td>
          <td><span class="badge badge-green">Twilio & Fast2SMS</span></td>
          <td><strong>Twilio:</strong> Global SMS & WhatsApp API.<br><strong>Fast2SMS:</strong> Indian regional SMS gateway (+91) with direct high-delivery routing.<br><strong>CallMeBot:</strong> Direct WhatsApp API.</td>
        </tr>
        <tr>
          <td><strong>Email Alerting</strong></td>
          <td><span class="badge badge-purple">SMTP TLS (Gmail)</span></td>
          <td>Dispatches high-contrast, responsive HTML email cards with embedded metadata tables and styled action buttons over secure TLS port 587.</td>
        </tr>
        <tr>
          <td><strong>Cryptography</strong></td>
          <td><span class="badge badge-dark">HMAC-SHA256 & Secrets</span></td>
          <td>Tamper-proof digital signatures, 15-minute Time-To-Live (TTL), cryptographic nonces, and single-use replay prevention via <code>hmac.compare_digest</code>.</td>
        </tr>
        <tr>
          <td><strong>Frontend UI/UX</strong></td>
          <td><span class="badge badge-blue">Bootstrap 5 • Chart.js • FA6</span></td>
          <td>Dark-mode cloud console, real-time KPI metrics, FinOps cost charts (USD & INR), and Web Audio API synthesizer for the mobile buzzer alarm.</td>
        </tr>
        <tr>
          <td><strong>Automated Testing</strong></td>
          <td><span class="badge badge-green">Pytest 9.1+</span></td>
          <td>16 comprehensive automated test cases verifying token security, policy rules, 30m grace fallback, and end-to-end webhook execution.</td>
        </tr>
      </tbody>
    </table>

    <div class="speaker-box">
      <div class="speaker-header">🎤 What to Say to Examiners / Interviewers (Speaker Script)</div>
      <div class="speaker-text">
        "Regarding our technology stack, we chose Python 3.13 and Flask 3.1 for their lightweight modularity and rapid cryptographic execution. 
        For data persistence, we engineered a dual-engine SQLAlchemy architecture: it defaults to an embedded SQLite database for zero-friction evaluation, 
        but seamlessly connects to MySQL 8.0 for enterprise production. 
        Our task scheduling is powered by APScheduler, which runs in-process every 60 seconds without needing heavyweight external brokers like Celery or Redis. 
        To allow mobile interaction without deploying expensive cloud load balancers, we integrate Cloudflare Tunnel, which generates an end-to-end encrypted HTTPS edge URL."
      </div>
    </div>

    <div class="footer-note">
      <span>Cloud Resource Scheduling System • Project Presentation Guide</span>
      <span>Page 3</span>
    </div>
  </div>

  <!-- ==================== PAGE 4: HOW IT WORKS (ARCHITECTURE WORKFLOW) ==================== -->
  <div class="page">
    <div class="section-header">
      <h1 class="section-title">3. System Architecture & Workflow</h1>
      <span class="section-tag">Slide 3 • Operational Lifecycle</span>
    </div>

    <h2>The 4-Phase Continuous Governance Lifecycle</h2>
    <p>
      The platform operates as a continuous closed-loop feedback system. Here is the step-by-step workflow:
    </p>

    <div class="flow-container">
      <div class="flow-step">
        <div class="flow-step-num">Phase 1</div>
        <div class="flow-step-title">Discovery & Inventory</div>
        <p>Boto3 or Mock driver queries all compute instances. Database syncs status, IPs, launch times, and assigned schedules.</p>
      </div>
      <div class="flow-arrow">➔</div>
      <div class="flow-step">
        <div class="flow-step-num">Phase 2</div>
        <div class="flow-step-title">Policy Audit (60s)</div>
        <p>APScheduler checks: Is lease active? Is time within operating window? Has runtime exceeded max cap (e.g. 8.0 hrs)?</p>
      </div>
      <div class="flow-arrow">➔</div>
      <div class="flow-step">
        <div class="flow-step-num">Phase 3</div>
        <div class="flow-step-title">Multi-Channel Alert</div>
        <p>Breach generates HMAC-SHA256 tokens (15m TTL). Dispatches ntfy siren, SMS, WhatsApp, & Email. 30m grace period begins.</p>
      </div>
      <div class="flow-arrow">➔</div>
      <div class="flow-step">
        <div class="flow-step-num">Phase 4</div>
        <div class="flow-step-title">Action / Fallback</div>
        <p>Operator taps 1-Click Stop/Extend, OR 30m timer expires triggering automatic fallback shutdown to stop cost leakage.</p>
      </div>
    </div>

    <h2>Detailed Policy Evaluation Matrix</h2>
    <div class="grid-2">
      <div class="card">
        <div class="card-title">🔍 Rule 1: Operating Hours Window</div>
        <p style="font-size: 8.5pt;">
          Each workload can be assigned an operating window (e.g., <code>09:00 to 19:00</code>) and allowed days of the week (e.g., <code>Mon-Fri</code>).
          Workloads running at 20:00 or on Saturday trigger an immediate <strong>After-Hours Policy Breach</strong>.
        </p>
      </div>
      <div class="card">
        <div class="card-title">⏱️ Rule 2: Maximum Continuous Runtime</div>
        <p style="font-size: 8.5pt;">
          Even within business hours, instances cannot exceed their continuous runtime threshold (e.g., <code>8.0 hours</code>).
          This catches forgotten runaway training jobs, memory leaks, and unmonitored batch scripts.
        </p>
      </div>
    </div>

    <div class="grid-2">
      <div class="card card-highlight">
        <div class="card-title">⏳ Rule 3: Active Lease Overrides</div>
        <p style="font-size: 8.5pt;">
          If an engineer requests an extension (via 1-click webhook), the resource receives a temporary <code>lease_expires_at</code> timestamp.
          The policy engine exempts the resource until the lease window elapses, ensuring zero false alarms.
        </p>
      </div>
      <div class="card card-danger">
        <div class="card-title">🛑 Rule 4: 30-Minute Grace Fallback</div>
        <p style="font-size: 8.5pt;">
          Once the first alert is dispatched, the system timestamps <code>alert_sent_at</code>. If 30 minutes pass without human response,
          the engine invokes <code>stop_instance()</code> autonomously and writes an immutable record to the audit ledger.
        </p>
      </div>
    </div>

    <div class="speaker-box">
      <div class="speaker-header">🎤 What to Say to Examiners / Interviewers (Speaker Script)</div>
      <div class="speaker-text">
        "Let's trace how the system executes under the hood. Every 60 seconds, APScheduler fires our audit engine. 
        It pulls all running instances from our database and runs them through three governance filters: 
        First, is the instance protected by an active lease extension? If yes, it's skipped. 
        Second, is it currently inside its approved operating hours and days? 
        And third, has its continuous runtime exceeded its safety cap? 
        If a violation is detected for the first time, our system doesn't shut it down immediately. Instead, it starts a 30-minute grace period 
        and dispatches multi-channel alerts. If the operator clicks 'Extend', a 60-minute exemption is granted. 
        If no action is taken after 30 minutes, the system autonomously shuts down the instance to protect company funds."
      </div>
    </div>

    <div class="footer-note">
      <span>Cloud Resource Scheduling System • Project Presentation Guide</span>
      <span>Page 4</span>
    </div>
  </div>

  <!-- ==================== PAGE 5: SEND ALERT IN DETAIL (MULTI-CHANNEL) ==================== -->
  <div class="page">
    <div class="section-header">
      <h1 class="section-title">4. How Send Alert Works (Multi-Channel Engine)</h1>
      <span class="section-tag">Slide 4 • Notification Architecture</span>
    </div>

    <h2>The Multi-Channel Dispatch Architecture</h2>
    <p>
      When a policy violation is detected, <code>NotificationService.dispatch_incident_alert()</code> coordinates parallel
      dispatch across five distinct channels to guarantee delivery under all conditions:
    </p>

    <div class="grid-2">
      <!-- Channel 1: ntfy Push -->
      <div class="card card-primary">
        <div class="card-title">
          <span>📲 1. ntfy Mobile Push & Siren</span>
          <span class="badge badge-blue">Real-Time Audio</span>
        </div>
        <p style="font-size: 8.5pt; margin-bottom: 6px;">
          Pushes directly to the operator's smartphone via <code>ntfy.sh/vasanth_cloud_alerts</code>:
        </p>
        <ul style="font-size: 8pt; margin: 0; padding-left: 18px;">
          <li><strong>Priority 5 (Max Urgency):</strong> Wakes phone screen even in Do Not Disturb.</li>
          <li><strong>Audio Siren:</strong> Plays siren buzzer sound (<code>buzzer.wav</code>) instantly.</li>
          <li><strong>Action Buttons:</strong> Embedded buttons: <code>🔊 SOUND BUZZER</code>, <code>🛑 Stop Instance</code>, and <code>⏳ Extend (+60m)</code>.</li>
        </ul>
      </div>

      <!-- Channel 2: Twilio & Fast2SMS -->
      <div class="card card-warning">
        <div class="card-title">
          <span>💬 2. Direct Mobile SMS</span>
          <span class="badge badge-amber">Carrier Delivery</span>
        </div>
        <p style="font-size: 8.5pt; margin-bottom: 6px;">
          Dual-engine SMS routing ensures 100% deliverability:
        </p>
        <ul style="font-size: 8pt; margin: 0; padding-left: 18px;">
          <li><strong>Fast2SMS (India Gateway):</strong> Direct delivery to +91 numbers without carrier DLT blocking.</li>
          <li><strong>Twilio SMS:</strong> Global carrier routing with formatted violation text.</li>
          <li><strong>SMS Reply Control:</strong> Operator can reply <code>STOP</code> to immediately power down the instance.</li>
        </ul>
      </div>

      <!-- Channel 3: WhatsApp -->
      <div class="card card-highlight">
        <div class="card-title">
          <span>🟢 3. Twilio WhatsApp Alert</span>
          <span class="badge badge-green">Rich Text</span>
        </div>
        <p style="font-size: 8.5pt; margin-bottom: 6px;">
          Direct communication via WhatsApp messaging:
        </p>
        <ul style="font-size: 8pt; margin: 0; padding-left: 18px;">
          <li>Dispatches via Twilio WhatsApp API or CallMeBot gateway.</li>
          <li>Generates 1-Click WhatsApp Direct URL for instant operator notification.</li>
          <li>Includes full instance ID, provider, runtime, and 1-click action links.</li>
        </ul>
      </div>

      <!-- Channel 4: SMTP Email -->
      <div class="card card-danger">
        <div class="card-title">
          <span>📧 4. SMTP HTML Email & Buzzer</span>
          <span class="badge badge-red">Rich Audit Card</span>
        </div>
        <p style="font-size: 8.5pt; margin-bottom: 6px;">
          Full visual incident report via Gmail TLS:
        </p>
        <ul style="font-size: 8pt; margin: 0; padding-left: 18px;">
          <li>Responsive dark-themed HTML card with clear instance metadata table.</li>
          <li>Prominent red <strong>🛑 Stop Instance Now</strong> and blue <strong>⏳ Extend Lease</strong> buttons.</li>
          <li>Dedicated <code>/buzzer</code> route with HTML5 synthesizer and haptic vibration.</li>
        </ul>
      </div>
    </div>

    <h2>Structure of the Dispatched Incident Payload</h2>
    <div class="code-box">
<span class="code-comment"># Multi-channel alert payload dispatched simultaneously to phone & email</span>
{
  <span class="code-var">"title"</span>: <span class="code-str">"🚨 AWS Resource Exceeded Allocated Time! (i-06b9d8479ab4f3074)"</span>,
  <span class="code-var">"provider"</span>: <span class="code-str">"AWS"</span>,  <span class="code-var">"region"</span>: <span class="code-str">"us-east-1"</span>,  <span class="code-var">"uptime_hours"</span>: 10.4,
  <span class="code-var">"violation"</span>: <span class="code-str">"Continuous runtime (10.4 hrs) exceeded threshold of 8.0 hrs"</span>,
  <span class="code-var">"actions"</span>: {
    <span class="code-var">"stop_url"</span>: <span class="code-str">"https://tunnel.trycloudflare.com/webhook/action?token=&lt;HMAC_TOKEN&gt;&action=stop"</span>,
    <span class="code-var">"extend_url"</span>: <span class="code-str">"https://tunnel.trycloudflare.com/webhook/action?token=&lt;HMAC_TOKEN&gt;&action=extend"</span>
  },
  <span class="code-var">"grace_period"</span>: <span class="code-str">"30 Minutes Active (Auto-shutdown at expiry)"</span>
}
    </div>

    <div class="speaker-box">
      <div class="speaker-header">🎤 What to Say to Examiners / Interviewers (Speaker Script)</div>
      <div class="speaker-text">
        "One of the biggest innovations in our project is the Alerting Architecture. 
        Instead of relying on a single email that might sit unread, our NotificationService triggers four channels in parallel: 
        First, it fires an urgent mobile push via ntfy.sh with high priority, sounding a siren on the phone and presenting action buttons right on the lockscreen. 
        Second, it dispatches an SMS to the phone—utilizing Fast2SMS for domestic Indian routes and Twilio globally. 
        Third, it sends an interactive WhatsApp message. 
        And fourth, it sends a high-contrast HTML email card. 
        Every single notification contains cryptographically signed 1-click links that allow the engineer to take immediate action directly from their phone."
      </div>
    </div>

    <div class="footer-note">
      <span>Cloud Resource Scheduling System • Project Presentation Guide</span>
      <span>Page 5</span>
    </div>
  </div>

  <!-- ==================== PAGE 6: CRYPTOGRAPHIC 1-CLICK WEBHOOKS ==================== -->
  <div class="page">
    <div class="section-header">
      <h1 class="section-title">5. Cryptographic 1-Click Action Webhooks</h1>
      <span class="section-tag">Slide 5 • Security Architecture</span>
    </div>

    <h2>How Single-Click Mobile Actions Work Without Passwords</h2>
    <p>
      Engineers cannot afford to type 16-character passwords and MFA codes during an emergency off-hours alert.
      To solve this, we implemented a <strong>Zero-Trust Cryptographic Action Token</strong> system using HMAC-SHA256:
    </p>

    <div class="grid-2">
      <div class="card">
        <div class="card-title">🔐 Step 1: Token Generation</div>
        <p style="font-size: 8.5pt;">
          When an alert triggers, <code>token_utils.py</code> packages a JSON payload containing:
        </p>
        <div class="code-box" style="margin-bottom: 0;">
payload = {
  <span class="code-var">"instance_id"</span>: <span class="code-str">"i-06b9d8479ab4f3074"</span>,
  <span class="code-var">"action"</span>: <span class="code-str">"stop"</span>,
  <span class="code-var">"issued_at"</span>: 1775700000,
  <span class="code-var">"expires_at"</span>: 1775700900, <span class="code-comment"># 15m TTL</span>
  <span class="code-var">"nonce"</span>: <span class="code-str">"d7a1e2f9801b4c3e"</span>
}
        </div>
        <p style="font-size: 8pt; color: #64748b; margin-top: 4px;">
          The payload is base64-encoded and signed with the server's private secret key using <code>HMAC-SHA256</code>.
        </p>
      </div>

      <div class="card">
        <div class="card-title">🛡️ Step 2: Verification Pipeline</div>
        <p style="font-size: 8.5pt;">
          When the operator taps the link on their phone, <code>/webhook/action</code> executes 4 strict security checks:
        </p>
        <ol style="font-size: 8pt; margin: 0; padding-left: 18px; line-height: 1.4;">
          <li><strong>Cryptographic Signature:</strong> Verifies HMAC using <code>hmac.compare_digest</code> (prevents timing attacks).</li>
          <li><strong>Tamper Detection:</strong> If a single character in the instance ID or action is changed, signature fails.</li>
          <li><strong>Time-To-Live (TTL):</strong> If <code>current_time > expires_at</code> (15 mins), request is rejected.</li>
          <li><strong>Single-Use Replay Protection:</strong> Consumed token is blacklisted; cannot be clicked twice.</li>
        </ol>
      </div>
    </div>

    <h2>State Transitions & Immutable Audit Ledger</h2>
    <div class="grid-2">
      <div class="card card-danger">
        <div class="card-title">🛑 If Operator Clicks "STOP"</div>
        <ul style="font-size: 8.5pt; margin: 0; padding-left: 16px;">
          <li>Calls <code>cloud_service.stop_instance()</code> immediately.</li>
          <li>Instance state transitions to <code>STOPPED</code>.</li>
          <li>Hourly cost burn drops to $0.00/hr.</li>
          <li>Renders mobile confirmation: <em>"Instance safely powered down. Cost burn stopped."</em></li>
          <li>Writes entry to <code>audit_trails</code> table with timestamp and HMAC proof.</li>
        </ul>
      </div>

      <div class="card card-primary">
        <div class="card-title">⏳ If Operator Clicks "EXTEND" (+60m)</div>
        <ul style="font-size: 8.5pt; margin: 0; padding-left: 16px;">
          <li>Calculates new lease: <code>now + 60 minutes</code>.</li>
          <li>Updates <code>lease_expires_at</code> on the resource record.</li>
          <li>Clears <code>alert_sent_at</code> to reset grace period timer.</li>
          <li>Governance policy engine exempts instance from shutdowns during lease.</li>
          <li>Renders mobile confirmation: <em>"Lease extended by 60 minutes."</em></li>
        </ul>
      </div>
    </div>

    <div class="speaker-box">
      <div class="speaker-header">🎤 What to Say to Examiners / Interviewers (Speaker Script)</div>
      <div class="speaker-text">
        "Examiners frequently ask: 'How can you allow stopping cloud servers with a 1-click link without requiring a password? Isn't that dangerous?' 
        The answer is our HMAC-SHA256 Cryptographic Token Architecture. 
        Each link is uniquely signed using a server-side secret key. The token encapsulates the instance ID, the action, an expiration timestamp, and a random cryptographic nonce. 
        It has a strict 15-minute Time-To-Live, it is strictly single-use to prevent replay attacks, and we use constant-time verification to prevent timing attacks. 
        If an attacker changes even one character in the URL, the HMAC signature fails immediately. It gives operators the convenience of instant response with bank-grade security."
      </div>
    </div>

    <div class="footer-note">
      <span>Cloud Resource Scheduling System • Project Presentation Guide</span>
      <span>Page 6</span>
    </div>
  </div>

  <!-- ==================== PAGE 7: FINOPS COST SAVINGS & ROI ==================== -->
  <div class="page">
    <div class="section-header">
      <h1 class="section-title">6. FinOps Cost Modeling & ROI Analytics</h1>
      <span class="section-tag">Slide 6 • Business Impact & Metrics</span>
    </div>

    <h2>FinOps Financial Impact & Calculation Model</h2>
    <p>
      The platform features a built-in FinOps calculation engine that converts compute downtime into quantifiable dollar and rupee savings:
    </p>

    <div class="grid-3">
      <div class="card card-highlight">
        <div class="card-title">💰 Baseline Instance Burn Rate</div>
        <div style="font-size: 16pt; font-weight: 800; color: #166534; margin: 4px 0;">$0.096 / hr</div>
        <p style="font-size: 8pt; color: #64748b; margin: 0;">Standard AWS EC2 t3.medium benchmark cost.</p>
      </div>
      <div class="card card-primary">
        <div class="card-title">💵 Active Running Burn Rate</div>
        <div style="font-size: 16pt; font-weight: 800; color: #1e40af; margin: 4px 0;">Live Dynamic $/hr</div>
        <p style="font-size: 8pt; color: #64748b; margin: 0;">Sum of hourly burn across all active instances.</p>
      </div>
      <div class="card card-highlight">
        <div class="card-title">🇮🇳 Currency Conversion</div>
        <div style="font-size: 16pt; font-weight: 800; color: #166534; margin: 4px 0;">₹83.50 per USD</div>
        <p style="font-size: 8pt; color: #64748b; margin: 0;">Real-time dual-currency metrics for Indian enterprises.</p>
      </div>
    </div>

    <h2>Cost Savings Mathematical Model</h2>
    <div class="code-box">
<span class="code-comment"># FinOps Hourly Savings Calculation Formula</span>
<span class="code-keyword">def</span> <span class="code-var">calculate_savings</span>(stopped_instances, hours_stopped=16.0):
    hourly_rate = 0.096  <span class="code-comment"># USD per instance hour</span>
    usd_savings = len(stopped_instances) * hourly_rate * hours_stopped
    inr_savings = usd_savings * 83.50
    <span class="code-keyword">return</span> {<span class="code-str">"usd"</span>: usd_savings, <span class="code-str">"inr"</span>: inr_savings}

<span class="code-comment"># Example: 10 Development Instances stopped overnight (16 hours) and weekends (48 hours):</span>
<span class="code-comment"># Off-hours per week = (5 days * 16 hrs) + 48 hrs weekend = 128 idle hours / week</span>
<span class="code-comment"># Weekly Savings = 10 instances * $0.096 * 128 hrs = $122.88 / week (₹10,260 / week)</span>
<span class="code-comment"># Annual Savings = $6,389 USD / year (~ ₹5,33,500 INR / year) on just 10 small instances!</span>
    </div>

    <h2>Live Dashboard KPI Metrics Visualized</h2>
    <table>
      <thead>
        <tr>
          <th>Metric Name</th>
          <th>Definition & Purpose</th>
          <th>Typical Impact</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>Total Monitored Resources</strong></td>
          <td>Complete count of all synchronized cloud compute instances.</td>
          <td>Full visibility across AWS & Azure fleets.</td>
        </tr>
        <tr>
          <td><strong>Running Instances (Active Burn)</strong></td>
          <td>Workloads currently drawing power and incurring cloud billings.</td>
          <td>Immediately flags workloads running during off-hours.</td>
        </tr>
        <tr>
          <td><strong>Stopped Instances (Protected Capital)</strong></td>
          <td>Workloads safely powered down by schedules, webhooks, or fallback.</td>
          <td>Eliminates 100% of compute cost while preserving disk storage.</td>
        </tr>
        <tr>
          <td><strong>Projected Monthly Savings</strong></td>
          <td>Cumulative FinOps financial dividend calculated in USD ($) and INR (₹).</td>
          <td>Demonstrates tangible ROI to management and stakeholders.</td>
        </tr>
      </tbody>
    </table>

    <div class="speaker-box">
      <div class="speaker-header">🎤 What to Say to Examiners / Interviewers (Speaker Script)</div>
      <div class="speaker-text">
        "To prove the business viability of our project, we integrated a full FinOps cost accounting engine. 
        Consider a moderate development team with just 10 EC2 instances. If left running 24/7, they burn thousands of dollars in unnecessary compute. 
        By shutting them down during 16 off-hours every weekday plus 48 weekend hours, our system recovers 128 hours of wasted time every single week. 
        That translates to over $6,300 USD—or more than 5.3 Lakh Rupees—saved annually on just 10 small instances. 
        Our dashboard computes this ROI in real-time, displaying live savings in both USD and INR."
      </div>
    </div>

    <div class="footer-note">
      <span>Cloud Resource Scheduling System • Project Presentation Guide</span>
      <span>Page 7</span>
    </div>
  </div>

  <!-- ==================== PAGE 8: LIVE DEMO RUNBOOK & VIVA QUESTIONS ==================== -->
  <div class="page">
    <div class="section-header">
      <h1 class="section-title">7. Live Demonstration Runbook & Viva Q&A</h1>
      <span class="section-tag">Slide 7 • Viva Defense</span>
    </div>

    <h2>Step-by-Step Live Demonstration Script (5-Minute Demo)</h2>
    <ol style="font-size: 9pt; line-height: 1.5; padding-left: 20px;">
      <li>
        <strong>Step 1: 1-Click Authentication:</strong>
        Navigate to <code>http://localhost:5000/quick-login</code>. Explain: <em>"We implemented instant role-based authentication without tedious login friction for seamless presentations."</em>
      </li>
      <li>
        <strong>Step 2: Dashboard & FinOps Walkthrough:</strong>
        Highlight the top KPI cards: Running Instances (Active Burn), Stopped Instances (Protected Capital), and live savings in USD & INR.
      </li>
      <li>
        <strong>Step 3: Trigger Alert Simulation:</strong>
        Navigate to the Alert Simulator or trigger policy audit. Show the notification dispatching across ntfy mobile push, SMS, WhatsApp, and Email.
      </li>
      <li>
        <strong>Step 4: Demonstrate 1-Click Mobile Shutdown:</strong>
        Click the generated <code>🛑 Stop Instance</code> link. Show the mobile-optimized confirmation page: <em>"Instance safely powered down. Cost burn stopped."</em>
      </li>
      <li>
        <strong>Step 5: Verify Dashboard State & Audit Trail:</strong>
        Refresh dashboard: the instance is now <code>STOPPED</code>, burn rate decreases, and the immutable audit ledger records the action with HMAC proof.
      </li>
    </ol>

    <h2>Frequently Asked Viva / Interview Questions & Model Answers</h2>
    <div class="grid-2">
      <div class="card">
        <div class="card-title">❓ Q1: Why APScheduler instead of Celery/Redis?</div>
        <p style="font-size: 8pt;">
          <strong>Answer:</strong> Celery requires an external Redis or RabbitMQ message broker daemon, adding substantial operational overhead and failure points.
          APScheduler runs in-process with zero external dependencies, making it lightweight, self-contained, and perfectly suited for 60-second periodic audits.
        </p>
      </div>
      <div class="card">
        <div class="card-title">❓ Q2: Why HMAC tokens instead of JWT or login session?</div>
        <p style="font-size: 8pt;">
          <strong>Answer:</strong> JWT is designed for identity claims, whereas HMAC-SHA256 provides a compact, cryptographically tamper-proof proof-of-action.
          Our HMAC tokens embed an expiration timestamp and single-use nonce, enabling secure mobile 1-click execution without requiring engineers to carry active browser sessions.
        </p>
      </div>
    </div>

    <div class="grid-2">
      <div class="card">
        <div class="card-title">❓ Q3: How do mobile phones reach localhost?</div>
        <p style="font-size: 8pt;">
          <strong>Answer:</strong> We integrate Cloudflare Tunnel (<code>cloudflared.exe</code>). It creates an outbound-only, encrypted TLS tunnel from port 5000
          to a public HTTPS endpoint (<code>*.trycloudflare.com</code>). This eliminates the need for port-forwarding, static public IPs, or firewall modifications.
        </p>
      </div>
      <div class="card">
        <div class="card-title">❓ Q4: What if an engineer needs to run a job past 30 mins?</div>
        <p style="font-size: 8pt;">
          <strong>Answer:</strong> When they receive the alert, they simply click <strong>"⏳ Extend Lease (+60 Mins)"</strong>.
          The system grants a 60-minute exemption, updates the database lease timestamp, and pauses all shutdown actions until the extended window expires.
        </p>
      </div>
    </div>

    <div class="speaker-box">
      <div class="speaker-header">🎤 Concluding Pitch (Closing Words for Presentation)</div>
      <div class="speaker-text">
        "In conclusion, our Cloud Resource Scheduling and FinOps Governance Platform provides a comprehensive, production-grade solution to the multi-billion dollar cloud waste problem. 
        By combining automated policy audits, urgent multi-channel alerts with siren audio, cryptographic 1-click actions, and an automated 30-minute fallback, 
        we deliver maximum financial savings without compromising developer productivity. Thank you, and I welcome any questions!"
      </div>
    </div>

    <div class="footer-note">
      <span>Cloud Resource Scheduling System • Project Presentation Guide</span>
      <span>Page 8</span>
    </div>
  </div>

</body>
</html>
"""
    return html_content

def generate_pdf():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    scratch_dir = os.path.join(base_dir, 'scratch')
    os.makedirs(scratch_dir, exist_ok=True)

    html_file = os.path.join(scratch_dir, 'presentation_guide.html')
    output_pdf = os.path.join(base_dir, 'Cloud_Resource_Scheduling_Presentation_Guide.pdf')

    html_content = build_presentation_html()
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"[*] Wrote presentation HTML to {html_file}")

    # Microsoft Edge path
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

    print(f"[*] Executing PDF generation command...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if os.path.exists(output_pdf) and os.path.getsize(output_pdf) > 0:
        size_kb = os.path.getsize(output_pdf) / 1024
        print(f"[SUCCESS] PDF generated successfully: {output_pdf} ({size_kb:.1f} KB)")
    else:
        print(f"[ERROR] PDF generation failed. Stderr: {result.stderr}")
        sys.exit(1)

if __name__ == '__main__':
    generate_pdf()
