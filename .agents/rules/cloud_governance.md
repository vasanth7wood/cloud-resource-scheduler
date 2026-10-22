---
name: cloud-governance-rules
description: Enforcement rules for Cloud Resource Scheduling, Policy Audits, and Grace Periods.
always_on: true
---

# Cloud Resource Governance & Policy Rules

## 1. Governance Audit Cycle
- The scheduler runs on a strict **60-second background cycle** powered by APScheduler.
- When evaluating schedules, compare instance running status against active schedules using **UTC timezone**:
  `datetime.now(timezone.utc)`.
- A violation occurs when:
  1. An instance is running outside its permitted operating hours (default 09:00 to 18:00 UTC).
  2. An instance is running on an unapproved day of the week (e.g., Saturday/Sunday).
  3. Continuous runtime exceeds `max_runtime_hours`.
  4. The resource lacks required compliance tags (e.g., `Environment`, `Owner`, `AutoStop`).

## 2. Grace Period & Safe Shutdown Workflow
- **Violation Detected**: Set resource state to `PENDING_SHUTDOWN`.
- **Set Grace Expiry**: `grace_period_expires_at = now + timedelta(minutes=30)`.
- **Dispatch Alert**: Immediately send push/SMS/email alert with signed HMAC-SHA256 1-click action links:
  - **Stop Immediately**: Triggers immediate cloud API shutdown.
  - **Extend / Snooze (2 hrs)**: Delays shutdown by 2 hours.
- **Auto-Termination**: If grace period expires without user action, transition instance state to `STOPPED` and record in `AuditTrail`.

## 3. Cryptographic Token Security
- All action URLs must be signed using HMAC-SHA256 with the app's `SECRET_KEY`.
- Tokens have a default TTL of 15 minutes (`ACTION_TOKEN_TTL_SECONDS=900`).
- Tokens must be verified against replay attacks by invalidating them upon consumption.

## 4. FinOps Cost Calculations
- Standard instance cost model: `$0.096 / hour` (e.g., `t3.large`).
- Currency conversion rate: `1 USD = 83.50 INR`.
- Monthly cost savings formula:
  $$\text{Savings} = (\text{Total Off-Hours Saved}) \times \text{Hourly Rate}$$
