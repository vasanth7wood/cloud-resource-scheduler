---
name: coding-standards
description: Coding and architectural guidelines for Flask, SQLAlchemy, and UI development in the Cloud Scheduler.
always_on: true
---

# Antigravity IDE Coding Standards

## 1. Flask & Blueprints Architecture
- All routes must be registered via Blueprints under `app/routes/`.
- Use the Flask Application Factory pattern in `app/__init__.py:create_app()`.
- Use `current_app.config` to access configuration properties rather than reading environment variables directly within route handlers.

## 2. SQLAlchemy ORM Integrity
- Always support SQLite fallback (`cloud_scheduler.db`) so developers and testers can run without requiring a running MySQL server daemon.
- Maintain atomic transactions: use `db.session.commit()` with proper `try...except` and `db.session.rollback()` in business logic.
- Avoid raw SQL strings; always prefer SQLAlchemy model queries.

## 3. Security & Action Tokens
- Critical shutdown/extension actions triggered via webhooks must be cryptographically verified using HMAC-SHA256 (`token_service.py`).
- Tokens must expire after 15 minutes and include single-use nonce verification.
- Passwords must be hashed using `generate_password_hash` with master passkey backward-compatibility enabled for administrative recovery.

## 4. UI & Presentation Standards
- Standard Bootstrap 5 dark theme with clean, professional layouts.
- **Header Cleanliness Rule**: Do NOT inject test action buttons or noise widgets into navigation headers. Keep navigation limited to standard system links (Dashboard, Resources, Schedules, Alerts, User Profile, Logout).
- Dynamic data updates on dashboard should use Chart.js and lightweight fetch calls.
