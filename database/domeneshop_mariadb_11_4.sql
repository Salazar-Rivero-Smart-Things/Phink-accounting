-- =============================================================================
-- PHINK ACCOUNTING — DOMENESHOP MARIADB 11.4 SKJEMA
-- =============================================================================
-- Database : phinkaccountin01
-- Server   : phinkaccountin01.mysql.domeneshop.no (Port 3306)
-- Versjon  : MariaDB 11.4 (InnoDB, utf8mb4_unicode_ci)
--
-- Bruk i Domeneshop phpMyAdmin:
--   1. Velg databasen `phinkaccountin01` i venstremenyen
--   2. Klikk på fanen "SQL" eller "Importer"
--   3. Last opp denne filen og klikk "Utfør"
-- =============================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 1. BRUKERINNLOGGINGER (Privatperson, ENK, AS, Forening, Institusjon)
CREATE TABLE IF NOT EXISTS `users` (
    `id`            INT          NOT NULL AUTO_INCREMENT,
    `email`         VARCHAR(200) NOT NULL,
    `password_hash` VARCHAR(255) NOT NULL,
    `full_name`     VARCHAR(200) NOT NULL,
    `role`          VARCHAR(30)  NOT NULL DEFAULT 'USER',      -- OWNER | USER | ACCOUNTANT | SUPPORT_AGENT
    `entity_type`   VARCHAR(30)  NOT NULL DEFAULT 'AS',        -- PRIVATE | ENK | AS | FORENING | INSTITUSJON
    `company_name`  VARCHAR(200) NULL,
    `org_number`    VARCHAR(30)  NULL,                         -- 9 siffer (MOD11)
    `national_id`   VARCHAR(20)  NULL,                         -- 11 siffer fødselsnummer
    `is_active`     TINYINT(1)   NOT NULL DEFAULT 1,
    `created_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_users_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. BEDRIFTS- / PRIVATPROFIL OG INNSTILLINGER
CREATE TABLE IF NOT EXISTS `company_settings` (
    `id`                      INT          NOT NULL AUTO_INCREMENT,
    `company_name`            VARCHAR(200) NOT NULL DEFAULT 'Mitt Selskap AS',
    `entity_type`             VARCHAR(30)  NOT NULL DEFAULT 'AS',
    `org_number`              VARCHAR(50)  NOT NULL DEFAULT '999 888 777 MVA',
    `national_id`             VARCHAR(20)  NULL,
    `bank_account`            VARCHAR(50)  NOT NULL DEFAULT '1234.56.78903',
    `vat_registered`          TINYINT(1)   NOT NULL DEFAULT 1,
    `aga_zone`                INT          NOT NULL DEFAULT 1,
    `address`                 VARCHAR(200) NOT NULL DEFAULT 'Storgata 1',
    `postal_code`             VARCHAR(20)  NOT NULL DEFAULT '0182',
    `city`                    VARCHAR(100) NOT NULL DEFAULT 'Oslo',
    `email`                   VARCHAR(150) NOT NULL DEFAULT 'post@phink-acounting.no',
    `phone`                   VARCHAR(50)  NOT NULL DEFAULT '+47 22 00 00 00',
    `logo_url`                VARCHAR(500) NULL,
    `marketing_image_url`     VARCHAR(500) NULL,
    `vipps_number`            VARCHAR(50)  NOT NULL DEFAULT '',
    `allowed_payment_methods` VARCHAR(100) NOT NULL DEFAULT 'VIPPS_BEDRIFT,FAKTURA',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. AVDELINGER & PROSJEKTER
CREATE TABLE IF NOT EXISTS `departments` (
    `id`         INT          NOT NULL AUTO_INCREMENT,
    `code`       VARCHAR(50)  NOT NULL,
    `name`       VARCHAR(150) NOT NULL,
    `is_active`  TINYINT(1)   NOT NULL DEFAULT 1,
    `created_at` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_departments_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `projects` (
    `id`            INT          NOT NULL AUTO_INCREMENT,
    `code`          VARCHAR(50)  NOT NULL,
    `name`          VARCHAR(200) NOT NULL,
    `customer_name` VARCHAR(200) NULL,
    `budget`        DOUBLE       NOT NULL DEFAULT 0.0,
    `status`        VARCHAR(30)  NOT NULL DEFAULT 'ACTIVE',
    `created_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_projects_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. KONTOPLAN (NS 4102)
CREATE TABLE IF NOT EXISTS `accounts` (
    `account_number` INT          NOT NULL,
    `name`           VARCHAR(255) NOT NULL,
    `account_type`   VARCHAR(50)  NOT NULL,                    -- ASSET | LIABILITY | EQUITY | REVENUE | EXPENSE
    `vat_code`       VARCHAR(20)  NULL,                        -- HIGH_25 | MED_15 | LOW_12 | NONE
    `description`    VARCHAR(255) NULL,
    PRIMARY KEY (`account_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. BILAG & TRANSAKSJONSLINJER (HOVEDBOK / DOBBEL BOKFØRING)
CREATE TABLE IF NOT EXISTS `vouchers` (
    `id`              INT          NOT NULL AUTO_INCREMENT,
    `voucher_number`  INT          NULL,
    `date`            DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `description`     VARCHAR(500) NOT NULL,
    `source_document` VARCHAR(500) NULL,
    `department_code` VARCHAR(50)  NULL,
    `project_code`    VARCHAR(50)  NULL,
    `status`          VARCHAR(50)  NOT NULL DEFAULT 'POSTED',
    `ai_analyzed`     TINYINT(1)   NOT NULL DEFAULT 0,
    `created_at`      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_vouchers_number` (`voucher_number`),
    KEY `idx_vouchers_date` (`date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `transaction_lines` (
    `id`              INT          NOT NULL AUTO_INCREMENT,
    `voucher_id`      INT          NOT NULL,
    `account_number`  INT          NOT NULL,
    `description`     VARCHAR(255) NULL,
    `debit`           DOUBLE       NOT NULL DEFAULT 0.0,
    `credit`          DOUBLE       NOT NULL DEFAULT 0.0,
    `department_code` VARCHAR(50)  NULL,
    `project_code`    VARCHAR(50)  NULL,
    `vat_code`        VARCHAR(20)  NULL,
    PRIMARY KEY (`id`),
    KEY `idx_txlines_voucher` (`voucher_id`),
    KEY `idx_txlines_account` (`account_number`),
    CONSTRAINT `fk_txlines_voucher` FOREIGN KEY (`voucher_id`) REFERENCES `vouchers` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_txlines_account` FOREIGN KEY (`account_number`) REFERENCES `accounts` (`account_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. LEVERANDØRER & INNGÅENDE FAKTURAER
CREATE TABLE IF NOT EXISTS `suppliers` (
    `id`                      INT          NOT NULL AUTO_INCREMENT,
    `name`                    VARCHAR(200) NOT NULL,
    `org_number`              VARCHAR(50)  NULL,
    `account_number`          VARCHAR(50)  NULL,
    `kid_prefix`              VARCHAR(50)  NULL,
    `email`                   VARCHAR(150) NULL,
    `phone`                   VARCHAR(50)  NULL,
    `default_expense_account` INT          NOT NULL DEFAULT 4300,
    `payment_terms_days`      INT          NOT NULL DEFAULT 14,
    `created_at`              DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `supplier_invoices` (
    `id`               INT          NOT NULL AUTO_INCREMENT,
    `supplier_id`      INT          NOT NULL,
    `supplier_name`    VARCHAR(200) NOT NULL,
    `invoice_number`   VARCHAR(100) NOT NULL,
    `kid`              VARCHAR(50)  NULL,
    `issue_date`       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `due_date`         DATETIME     NOT NULL,
    `amount_ex_vat`    DOUBLE       NOT NULL DEFAULT 0.0,
    `vat_amount`       DOUBLE       NOT NULL DEFAULT 0.0,
    `vat_rate_percent` INT          NOT NULL DEFAULT 25,
    `total_amount`     DOUBLE       NOT NULL DEFAULT 0.0,
    `expense_account`  INT          NOT NULL DEFAULT 6540,
    `department_code`  VARCHAR(50)  NULL,
    `project_code`     VARCHAR(50)  NULL,
    `status`           VARCHAR(50)  NOT NULL DEFAULT 'UNPAID',
    `voucher_id`       INT          NULL,
    `attachment_url`   VARCHAR(500) NULL,
    `created_at`       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_supinv_supplier` (`supplier_id`),
    CONSTRAINT `fk_supinv_supplier` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`),
    CONSTRAINT `fk_supinv_voucher`  FOREIGN KEY (`voucher_id`)  REFERENCES `vouchers` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. KUNDER & UTGÅENDE SALGSFAKTURAER (MED NORSK MVA)
CREATE TABLE IF NOT EXISTS `customers` (
    `id`                 INT          NOT NULL AUTO_INCREMENT,
    `name`               VARCHAR(200) NOT NULL,
    `org_number`         VARCHAR(50)  NULL,
    `email`              VARCHAR(150) NULL,
    `phone`              VARCHAR(50)  NULL,
    `address`            VARCHAR(255) NULL,
    `payment_terms_days` INT          NOT NULL DEFAULT 14,
    `created_at`         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `customer_invoices` (
    `id`                    INT          NOT NULL AUTO_INCREMENT,
    `invoice_number`        INT          NULL,
    `customer_id`           INT          NULL,
    `customer_name`         VARCHAR(200) NOT NULL,
    `customer_email`        VARCHAR(150) NULL,
    `customer_orgnr`        VARCHAR(50)  NULL,
    `issue_date`            DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `due_date`              DATETIME     NOT NULL,
    `kid`                   VARCHAR(50)  NULL,
    `subtotal`              DOUBLE       NOT NULL DEFAULT 0.0,
    `vat_amount`            DOUBLE       NOT NULL DEFAULT 0.0,
    `total_amount`          DOUBLE       NOT NULL DEFAULT 0.0,
    `lines_json`            LONGTEXT     NULL,
    `status`                VARCHAR(50)  NOT NULL DEFAULT 'SENT',
    `reminder_count`        INT          NOT NULL DEFAULT 0,
    `reminder_fee`          DOUBLE       NOT NULL DEFAULT 0.0,
    `collection_case_id`    VARCHAR(100) NULL,
    `collection_status`     VARCHAR(100) NULL,
    `is_credit_note`        TINYINT(1)   NOT NULL DEFAULT 0,
    `credit_for_invoice_id` INT          NULL,
    `department_code`       VARCHAR(50)  NULL,
    `project_code`          VARCHAR(50)  NULL,
    `voucher_id`            INT          NULL,
    `created_at`            DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_custinv_number` (`invoice_number`),
    CONSTRAINT `fk_custinv_customer` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_custinv_voucher`  FOREIGN KEY (`voucher_id`)  REFERENCES `vouchers` (`id`)  ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. BETALING & ABONNEMENT (KUN VIPPS BEDRIFT & TILSENDT FAKTURA)
CREATE TABLE IF NOT EXISTS `subscription_orders` (
    `id`                INT          NOT NULL AUTO_INCREMENT,
    `customer_name`     VARCHAR(200) NOT NULL,
    `customer_email`    VARCHAR(150) NOT NULL,
    `org_number`        VARCHAR(50)  NULL,
    `plan_id`           VARCHAR(50)  NOT NULL,
    `plan_name`         VARCHAR(150) NOT NULL,
    `payment_method`    VARCHAR(30)  NOT NULL,                 -- VIPPS_BEDRIFT | FAKTURA
    `amount_ex_vat`     DOUBLE       NOT NULL DEFAULT 0.0,
    `vat_amount`        DOUBLE       NOT NULL DEFAULT 0.0,
    `total_amount`      DOUBLE       NOT NULL DEFAULT 0.0,
    `vipps_number`      VARCHAR(50)  NULL,
    `payment_reference` VARCHAR(100) NOT NULL,
    `invoice_id`        INT          NULL,
    `status`            VARCHAR(30)  NOT NULL DEFAULT 'PENDING',
    `due_date`          DATETIME     NULL,
    `paid_at`           DATETIME     NULL,
    `created_at`        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    CONSTRAINT `chk_payment_method` CHECK (`payment_method` IN ('VIPPS_BEDRIFT', 'FAKTURA')),
    CONSTRAINT `fk_suborder_invoice` FOREIGN KEY (`invoice_id`) REFERENCES `customer_invoices` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. BANKAVSTEMNING
CREATE TABLE IF NOT EXISTS `bank_transactions` (
    `id`                 INT          NOT NULL AUTO_INCREMENT,
    `transaction_date`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `description`        VARCHAR(500) NOT NULL,
    `amount`             DOUBLE       NOT NULL,
    `reference`          VARCHAR(100) NULL,
    `reconciled`         TINYINT(1)   NOT NULL DEFAULT 0,
    `matched_voucher_id` INT          NULL,
    `reconciled_at`      DATETIME     NULL,
    `source`             VARCHAR(100) NOT NULL DEFAULT 'BANK_IMPORT',
    `created_at`         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    CONSTRAINT `fk_banktx_voucher` FOREIGN KEY (`matched_voucher_id`) REFERENCES `vouchers` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 10. BILAGSARKIV / OPPLASTEDE DOKUMENTER (PDF & BILDE)
CREATE TABLE IF NOT EXISTS `uploaded_documents` (
    `id`                  INT          NOT NULL AUTO_INCREMENT,
    `filename`            VARCHAR(255) NOT NULL,
    `original_name`       VARCHAR(255) NOT NULL,
    `file_type`           VARCHAR(50)  NOT NULL,
    `file_path`           VARCHAR(500) NOT NULL,
    `file_size`           INT          NOT NULL DEFAULT 0,
    `extracted_data_json` LONGTEXT     NULL,
    `status`              VARCHAR(50)  NOT NULL DEFAULT 'PENDING',
    `voucher_id`          INT          NULL,
    `uploaded_at`         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    CONSTRAINT `fk_updoc_voucher` FOREIGN KEY (`voucher_id`) REFERENCES `vouchers` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 11. ANSATTE & AUTOMATISK NORSK LØNNSKJØRING
CREATE TABLE IF NOT EXISTS `employees` (
    `id`                   INT          NOT NULL AUTO_INCREMENT,
    `employee_number`      VARCHAR(30)  NOT NULL,
    `full_name`            VARCHAR(200) NOT NULL,
    `national_id`          VARCHAR(20)  NULL,
    `email`                VARCHAR(150) NULL,
    `bank_account`         VARCHAR(50)  NULL,
    `position`             VARCHAR(150) NOT NULL DEFAULT 'Ansatt',
    `monthly_gross_salary` DOUBLE       NOT NULL DEFAULT 45000.0,
    `tax_percent`          DOUBLE       NOT NULL DEFAULT 30.0,
    `holiday_pay_percent`  DOUBLE       NOT NULL DEFAULT 12.0,
    `aga_zone`             INT          NOT NULL DEFAULT 1,
    `otp_percent`          DOUBLE       NOT NULL DEFAULT 2.0,
    `department_code`      VARCHAR(50)  NOT NULL DEFAULT 'ADM',
    `project_code`         VARCHAR(50)  NOT NULL DEFAULT 'FELLES',
    `is_active`            TINYINT(1)   NOT NULL DEFAULT 1,
    `created_at`           DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_employees_number` (`employee_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `payroll_runs` (
    `id`                      INT         NOT NULL AUTO_INCREMENT,
    `period`                  VARCHAR(20) NOT NULL,
    `pay_date`                DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `status`                  VARCHAR(30) NOT NULL DEFAULT 'POSTED',
    `total_gross`             DOUBLE      NOT NULL DEFAULT 0.0,
    `total_overtime`          DOUBLE      NOT NULL DEFAULT 0.0,
    `total_bonus`             DOUBLE      NOT NULL DEFAULT 0.0,
    `total_tax_withholding`   DOUBLE      NOT NULL DEFAULT 0.0,
    `total_net_pay`           DOUBLE      NOT NULL DEFAULT 0.0,
    `total_holiday_pay`       DOUBLE      NOT NULL DEFAULT 0.0,
    `total_aga`               DOUBLE      NOT NULL DEFAULT 0.0,
    `total_aga_holiday`       DOUBLE      NOT NULL DEFAULT 0.0,
    `total_otp`               DOUBLE      NOT NULL DEFAULT 0.0,
    `total_employer_cost`     DOUBLE      NOT NULL DEFAULT 0.0,
    `voucher_id`              INT         NULL,
    `tax_transfer_voucher_id` INT         NULL,
    `created_at`              DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    CONSTRAINT `fk_payroll_voucher` FOREIGN KEY (`voucher_id`)              REFERENCES `vouchers` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_payroll_taxv`    FOREIGN KEY (`tax_transfer_voucher_id`) REFERENCES `vouchers` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `payroll_lines` (
    `id`                  INT          NOT NULL AUTO_INCREMENT,
    `payroll_run_id`      INT          NOT NULL,
    `employee_id`         INT          NOT NULL,
    `employee_name`       VARCHAR(200) NOT NULL,
    `gross_salary`        DOUBLE       NOT NULL DEFAULT 0.0,
    `overtime_pay`        DOUBLE       NOT NULL DEFAULT 0.0,
    `bonus_pay`           DOUBLE       NOT NULL DEFAULT 0.0,
    `tax_percent`         DOUBLE       NOT NULL DEFAULT 30.0,
    `tax_withholding`     DOUBLE       NOT NULL DEFAULT 0.0,
    `net_pay`             DOUBLE       NOT NULL DEFAULT 0.0,
    `holiday_pay_percent` DOUBLE       NOT NULL DEFAULT 12.0,
    `holiday_pay`         DOUBLE       NOT NULL DEFAULT 0.0,
    `aga_percent`         DOUBLE       NOT NULL DEFAULT 14.1,
    `aga_amount`          DOUBLE       NOT NULL DEFAULT 0.0,
    `aga_holiday_amount`  DOUBLE       NOT NULL DEFAULT 0.0,
    `otp_percent`         DOUBLE       NOT NULL DEFAULT 2.0,
    `otp_amount`          DOUBLE       NOT NULL DEFAULT 0.0,
    `total_employer_cost` DOUBLE       NOT NULL DEFAULT 0.0,
    `department_code`     VARCHAR(50)  NULL,
    `project_code`        VARCHAR(50)  NULL,
    PRIMARY KEY (`id`),
    KEY `idx_payrolllines_run` (`payroll_run_id`),
    CONSTRAINT `fk_payrolllines_run` FOREIGN KEY (`payroll_run_id`) REFERENCES `payroll_runs` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_payrolllines_emp` FOREIGN KEY (`employee_id`)    REFERENCES `employees` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 12. REVISJONSLOGG & KUNDESERVICE
CREATE TABLE IF NOT EXISTS `audit_logs` (
    `id`          INT          NOT NULL AUTO_INCREMENT,
    `timestamp`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `action`      VARCHAR(100) NOT NULL,
    `details`     LONGTEXT     NULL,
    `ai_assisted` TINYINT(1)   NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `support_tickets` (
    `id`             INT          NOT NULL AUTO_INCREMENT,
    `customer_name`  VARCHAR(150) NOT NULL,
    `customer_email` VARCHAR(150) NOT NULL,
    `subject`        VARCHAR(255) NOT NULL,
    `category`       VARCHAR(50)  NOT NULL DEFAULT 'SUPPORT',
    `status`         VARCHAR(50)  NOT NULL DEFAULT 'ESCALATED_TO_HUMAN',
    `priority`       VARCHAR(20)  NOT NULL DEFAULT 'HIGH',
    `assigned_to`    VARCHAR(100) NOT NULL DEFAULT 'Deg (Kundeserviceleder)',
    `created_at`     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at`     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `ticket_messages` (
    `id`          INT          NOT NULL AUTO_INCREMENT,
    `ticket_id`   INT          NOT NULL,
    `sender`      VARCHAR(50)  NOT NULL,
    `sender_name` VARCHAR(100) NOT NULL,
    `message`     LONGTEXT     NOT NULL,
    `timestamp`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_ticketmsgs_ticket` (`ticket_id`),
    CONSTRAINT `fk_ticketmsgs_ticket` FOREIGN KEY (`ticket_id`) REFERENCES `support_tickets` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
