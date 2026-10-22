-- ==============================================================================
-- Cloud Resource Scheduling and Interactive Multi-Channel Alert System
-- Database Schema DDL Definition (MySQL 8.0+)
-- ==============================================================================

CREATE DATABASE IF NOT EXISTS `cloud_scheduler` 
  DEFAULT CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci;

USE `cloud_scheduler`;

-- Drop existing tables in reverse dependency order
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS `audit_trails`;
DROP TABLE IF EXISTS `alert_logs`;
DROP TABLE IF EXISTS `schedules`;
DROP TABLE IF EXISTS `cloud_resources`;
DROP TABLE IF EXISTS `users`;
SET FOREIGN_KEY_CHECKS = 1;

-- ------------------------------------------------------------------------------
-- 1. Table: users
-- Manages user authentication and Role-Based Access Control (RBAC)
-- ------------------------------------------------------------------------------
CREATE TABLE `users` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(100) NOT NULL,
  `email` VARCHAR(120) NOT NULL UNIQUE,
  `password_hash` VARCHAR(255) NOT NULL,
  `phone_number` VARCHAR(30) NULL,
  `role` ENUM('Admin', 'Manager', 'Viewer') NOT NULL DEFAULT 'Viewer',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_users_email` (`email`),
  INDEX `idx_users_role` (`role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 1b. Table: cloud_accounts
-- Multi-Cloud account integrations and connection credentials (AWS, Azure, GCP)
-- ------------------------------------------------------------------------------
CREATE TABLE `cloud_accounts` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `provider` VARCHAR(20) NOT NULL COMMENT 'AWS, AZURE, GCP',
  `account_name` VARCHAR(100) NOT NULL,
  `account_identifier` VARCHAR(120) NULL,
  `region` VARCHAR(50) NULL DEFAULT 'us-east-1',
  `credentials_json` TEXT NOT NULL,
  `status` VARCHAR(30) NOT NULL DEFAULT 'UNTESTED' COMMENT 'CONNECTED, FAILED, UNTESTED',
  `last_tested_at` DATETIME NULL,
  `last_error` TEXT NULL,
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_accounts_provider` (`provider`),
  INDEX `idx_accounts_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 2. Table: cloud_resources
-- Maintains discovered cloud instances and their operational state
-- ------------------------------------------------------------------------------
CREATE TABLE `cloud_resources` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `instance_id` VARCHAR(50) NOT NULL UNIQUE,
  `instance_name` VARCHAR(100) NOT NULL,
  `provider` VARCHAR(30) NOT NULL DEFAULT 'AWS',
  `region` VARCHAR(50) NOT NULL DEFAULT 'us-east-1',
  `state` VARCHAR(30) NOT NULL DEFAULT 'stopped',
  `instance_type` VARCHAR(50) NULL DEFAULT 't3.medium',
  `public_ip` VARCHAR(45) NULL,
  `private_ip` VARCHAR(45) NULL,
  `launch_time` DATETIME NULL,
  `lease_expires_at` DATETIME NULL,
  `alert_sent_at` DATETIME NULL,
  `last_scanned_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX `idx_res_instance_id` (`instance_id`),
  INDEX `idx_res_state` (`state`),
  INDEX `idx_res_region` (`region`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 3. Table: schedules
-- Operating policies and automated run-window constraints per resource
-- ------------------------------------------------------------------------------
CREATE TABLE `schedules` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `resource_id` INT NOT NULL,
  `start_time` VARCHAR(10) NOT NULL DEFAULT '09:00',
  `end_time` VARCHAR(10) NOT NULL DEFAULT '19:00',
  `max_runtime_hours` DECIMAL(4, 2) NOT NULL DEFAULT 8.00,
  `days_of_week` VARCHAR(50) NOT NULL DEFAULT 'MON,TUE,WED,THU,FRI',
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT `fk_schedules_resource` 
    FOREIGN KEY (`resource_id`) 
    REFERENCES `cloud_resources` (`id`) 
    ON DELETE CASCADE ON UPDATE CASCADE,
  INDEX `idx_schedules_active` (`is_active`),
  INDEX `idx_schedules_resource_id` (`resource_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 4. Table: alert_logs
-- Records all outbound alerts dispatched across SMS, WhatsApp, and Email
-- ------------------------------------------------------------------------------
CREATE TABLE `alert_logs` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `resource_id` INT NOT NULL,
  `channel` VARCHAR(30) NOT NULL COMMENT 'Twilio SMS, Twilio WhatsApp, SMTP Email',
  `recipient` VARCHAR(150) NOT NULL,
  `status` VARCHAR(30) NOT NULL DEFAULT 'SENT' COMMENT 'SENT, FAILED, SIMULATED',
  `token_hash` VARCHAR(128) NULL,
  `details` TEXT NULL,
  `sent_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT `fk_alert_logs_resource` 
    FOREIGN KEY (`resource_id`) 
    REFERENCES `cloud_resources` (`id`) 
    ON DELETE CASCADE ON UPDATE CASCADE,
  INDEX `idx_alert_logs_sent_at` (`sent_at`),
  INDEX `idx_alert_logs_resource_id` (`resource_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 5. Table: audit_trails
-- Tamper-evident ledger of all user commands, webhooks, and scheduler actions
-- ------------------------------------------------------------------------------
CREATE TABLE `audit_trails` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `resource_id` INT NULL,
  `triggered_by` VARCHAR(100) NOT NULL COMMENT 'USER:<name>, SCHEDULER, WEBHOOK:<action>',
  `action_taken` VARCHAR(50) NOT NULL COMMENT 'START, STOP, EXTEND_LEASE, SCAN, POLICY_SHUTDOWN',
  `details` TEXT NULL,
  `timestamp` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT `fk_audit_resource` 
    FOREIGN KEY (`resource_id`) 
    REFERENCES `cloud_resources` (`id`) 
    ON DELETE SET NULL ON UPDATE CASCADE,
  INDEX `idx_audit_timestamp` (`timestamp`),
  INDEX `idx_audit_action` (`action_taken`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==============================================================================
-- INITIAL SEED DATA
-- Default system accounts: Admin, Manager, Viewer
-- Default password for all seeded accounts: Admin@123456
-- ==============================================================================

INSERT INTO `users` (`name`, `email`, `password_hash`, `phone_number`, `role`, `created_at`) VALUES
('Lead Cloud Architect', 'admin@cloudops.internal', '$2b$12$.UzwgGxkRv9rCou73dEzb.VAlHpB1UCdoVZ.Bqfg9sT9fI2dfnjY2', '+12015550199', 'Admin', NOW()),
('DevOps Manager', 'manager@cloudops.internal', '$2b$12$.UzwgGxkRv9rCou73dEzb.VAlHpB1UCdoVZ.Bqfg9sT9fI2dfnjY2', '+12015550198', 'Manager', NOW()),
('Security Auditor', 'viewer@cloudops.internal', '$2b$12$.UzwgGxkRv9rCou73dEzb.VAlHpB1UCdoVZ.Bqfg9sT9fI2dfnjY2', '+12015550197', 'Viewer', NOW());

-- Seed Simulated Cloud Resources
INSERT INTO `cloud_resources` (`instance_id`, `instance_name`, `provider`, `region`, `state`, `instance_type`, `public_ip`, `private_ip`, `launch_time`, `lease_expires_at`, `alert_sent_at`, `last_scanned_at`) VALUES
('i-0a1b2c3d4e5f6001', 'Web-Frontend-Prod', 'AWS', 'us-east-1', 'running', 't3.large', '54.210.12.34', '10.0.1.45', DATE_SUB(NOW(), INTERVAL 5 HOUR), NULL, NULL, NOW()),
('i-0b2c3d4e5f6a7002', 'Dev-Batch-Worker', 'AWS', 'us-east-1', 'running', 'c5.xlarge', '52.90.87.12', '10.0.2.89', DATE_SUB(NOW(), INTERVAL 12 HOUR), NULL, NULL, NOW()),
('i-0c3d4e5f6a7b8003', 'Analytics-ML-Trainer', 'AWS', 'us-west-2', 'stopped', 'g4dn.xlarge', NULL, '10.1.4.12', NULL, NULL, NULL, NOW()),
('i-0d4e5f6a7b8c9004', 'Staging-API-Server', 'AWS', 'us-east-1', 'running', 't3.medium', '3.88.19.45', '10.0.3.11', DATE_SUB(NOW(), INTERVAL 9 HOUR), NULL, NULL, NOW()),
('i-0e5f6a7b8c9d0005', 'QA-Test-Database', 'AWS', 'eu-west-1', 'stopped', 'r5.large', NULL, '10.2.1.20', NULL, NULL, NULL, NOW());

-- Seed Schedules (Operating window: 09:00 - 19:00 Mon-Fri, max 8 continuous hours)
INSERT INTO `schedules` (`resource_id`, `start_time`, `end_time`, `max_runtime_hours`, `days_of_week`, `is_active`, `created_at`) VALUES
(1, '08:00', '20:00', 12.00, 'MON,TUE,WED,THU,FRI,SAT,SUN', TRUE, NOW()),
(2, '09:00', '18:00', 8.00, 'MON,TUE,WED,THU,FRI', TRUE, NOW()),
(3, '10:00', '17:00', 6.00, 'MON,TUE,WED,THU,FRI', TRUE, NOW()),
(4, '09:00', '19:00', 8.00, 'MON,TUE,WED,THU,FRI', TRUE, NOW()),
(5, '09:00', '18:00', 8.00, 'MON,TUE,WED,THU,FRI', TRUE, NOW());

-- Initial Audit Trail
INSERT INTO `audit_trails` (`resource_id`, `triggered_by`, `action_taken`, `details`, `timestamp`) VALUES
(1, 'SYSTEM', 'SCAN', 'Initial cloud discovery synchronized 5 EC2 instances.', NOW()),
(2, 'SYSTEM', 'POLICY_CHECK', 'Operating policy applied to Dev-Batch-Worker.', NOW());
