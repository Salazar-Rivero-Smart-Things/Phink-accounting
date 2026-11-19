-- =============================================================================
-- PHINK ACCOUNTING — SAMLET SQL-SKJEMA FOR WEBDOMENET (www.phink-acounting.no)
-- =============================================================================
-- Samler alle tabeller i ett konsistent skjema (kompatibelt med SQLite & PostgreSQL):
--   1. Brukerinnlogginger (Privatperson, ENK, AS, Forening, Institusjon)
--   2. Bedriftsprofil & innstillinger (inkl. orgnr, fødselsnummer, AGA-sone, logo)
--   3. Avdelinger & Prosjekter (dimensjoner)
--   4. Norsk Standard Kontoplan (NS 4102)
--   5. Hovedbok, Bilag & Transaksjonslinjer (Dobbel bokføring)
--   6. Leverandører & Inngående fakturaer (25%, 15%, 12%, 0% MVA)
--   7. Kunder & Utgående salgsfakturaer (25%, 15%, 12%, 0% MVA, purring, kreditnota)
--   8. Banktransaksjoner & Bankavstemning
--   9. Bilagsarkiv & Opplastede dokumenter (PDF / Bilde — 5-års oppbevaring)
--  10. Ansatte & Automatisk Norsk Lønnskjøring (5000, 5180, 5400, 5420, 1950, 2600, 2930, 2940, 2770, 2780, 2960)
--  11. Revisjonslogg (Audit Trail) & Kundeservice-desk
-- =============================================================================

-- 1. BRUKERINNLOGGINGER (Privat & Firma: PRIVATE, ENK, AS, FORENING, INSTITUSJON)
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT, -- PostgreSQL: SERIAL PRIMARY KEY
    email           VARCHAR(200) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    full_name       VARCHAR(200) NOT NULL,
    role            VARCHAR(30)  NOT NULL DEFAULT 'USER',      -- OWNER | USER | ACCOUNTANT
    entity_type     VARCHAR(30)  NOT NULL DEFAULT 'AS',        -- PRIVATE | ENK | AS | FORENING | INSTITUSJON
    company_name    VARCHAR(200),
    org_number      VARCHAR(30),                               -- 9 siffer (MOD11) for ENK, AS, FORENING, INSTITUSJON
    national_id     VARCHAR(20),                               -- 11 siffer fødselsnummer for PRIVATE / ENK
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- 2. BEDRIFTS- / PRIVATPROFIL OG INNSTILLINGER
CREATE TABLE IF NOT EXISTS company_settings (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name        VARCHAR(200) DEFAULT 'Mitt Selskap AS',
    entity_type         VARCHAR(30)  DEFAULT 'AS',             -- PRIVATE | ENK | AS | FORENING | INSTITUSJON
    org_number          VARCHAR(50)  DEFAULT '999 888 777 MVA',
    national_id         VARCHAR(20),
    bank_account        VARCHAR(50)  DEFAULT '1234.56.78903',
    vat_registered      BOOLEAN      DEFAULT TRUE,
    aga_zone            INTEGER      DEFAULT 1,                -- 1=14.1%, 2=10.6%, 3=6.4%, 4=5.1%, 5=0.0%
    address             VARCHAR(200) DEFAULT 'Storgata 1',
    postal_code         VARCHAR(20)  DEFAULT '0182',
    city                VARCHAR(100) DEFAULT 'Oslo',
    email               VARCHAR(150) DEFAULT 'post@phink-acounting.no',
    phone               VARCHAR(50)  DEFAULT '+47 22 00 00 00',
    logo_url            VARCHAR(500),
    marketing_image_url VARCHAR(500),
    vipps_number        VARCHAR(50)  DEFAULT '',
    allowed_payment_methods VARCHAR(100) DEFAULT 'VIPPS_BEDRIFT,FAKTURA'
);

-- 2B. BETALING & ABONNEMENT (KUN VIPPS BEDRIFT OG TILSENDT FAKTURA)
CREATE TABLE IF NOT EXISTS subscription_orders (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name     VARCHAR(200) NOT NULL,
    customer_email    VARCHAR(150) NOT NULL,
    org_number        VARCHAR(50),
    plan_id           VARCHAR(50)  NOT NULL,
    plan_name         VARCHAR(150) NOT NULL,
    payment_method    VARCHAR(30)  NOT NULL CHECK (payment_method IN ('VIPPS_BEDRIFT', 'FAKTURA')),
    amount_ex_vat     REAL         DEFAULT 0.0,
    vat_amount        REAL         DEFAULT 0.0,
    total_amount      REAL         DEFAULT 0.0,
    vipps_number      VARCHAR(50),
    payment_reference VARCHAR(100) NOT NULL,
    invoice_id        INTEGER      REFERENCES customer_invoices(id),
    status            VARCHAR(30)  DEFAULT 'PENDING',
    due_date          TIMESTAMP,
    paid_at           TIMESTAMP,
    created_at        TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- 3. AVDELINGER & PROSJEKTER
CREATE TABLE IF NOT EXISTS departments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    code        VARCHAR(50)  NOT NULL UNIQUE,
    name        VARCHAR(150) NOT NULL,
    is_active   BOOLEAN      DEFAULT TRUE,
    created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS projects (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    code          VARCHAR(50)  NOT NULL UNIQUE,
    name          VARCHAR(200) NOT NULL,
    customer_name VARCHAR(200),
    budget        REAL         DEFAULT 0.0,
    status        VARCHAR(30)  DEFAULT 'ACTIVE',
    created_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- 4. KONTOPLAN (NS 4102)
CREATE TABLE IF NOT EXISTS accounts (
    account_number INTEGER      PRIMARY KEY,
    name           VARCHAR(255) NOT NULL,
    account_type   VARCHAR(50)  NOT NULL,                      -- ASSET | LIABILITY | EQUITY | REVENUE | EXPENSE
    vat_code       VARCHAR(20),                                -- HIGH_25 | MED_15 | LOW_12 | NONE
    description    VARCHAR(255)
);

-- 5. BILAG & TRANSAKSJONSLINJER (HOVEDBOK / DOBBEL BOKFØRING)
CREATE TABLE IF NOT EXISTS vouchers (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    voucher_number  INTEGER      UNIQUE,
    date            TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    description     VARCHAR(500) NOT NULL,
    source_document VARCHAR(500),
    department_code VARCHAR(50),
    project_code    VARCHAR(50),
    status          VARCHAR(50)  DEFAULT 'POSTED',             -- DRAFT | POSTED | REVERSED
    ai_analyzed     BOOLEAN      DEFAULT FALSE,
    created_at      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_vouchers_number ON vouchers(voucher_number);
CREATE INDEX IF NOT EXISTS idx_vouchers_date   ON vouchers(date);

CREATE TABLE IF NOT EXISTS transaction_lines (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    voucher_id      INTEGER      NOT NULL REFERENCES vouchers(id) ON DELETE CASCADE,
    account_number  INTEGER      NOT NULL REFERENCES accounts(account_number),
    description     VARCHAR(255),
    debit           REAL         NOT NULL DEFAULT 0.0,
    credit          REAL         NOT NULL DEFAULT 0.0,
    department_code VARCHAR(50),
    project_code    VARCHAR(50),
    vat_code        VARCHAR(20)
);
CREATE INDEX IF NOT EXISTS idx_txlines_voucher ON transaction_lines(voucher_id);
CREATE INDEX IF NOT EXISTS idx_txlines_account ON transaction_lines(account_number);

-- 6. LEVERANDØRER & INNGÅENDE LEVERANDØRFAKTURAER
CREATE TABLE IF NOT EXISTS suppliers (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    name                    VARCHAR(200) NOT NULL,
    org_number              VARCHAR(50),
    account_number          VARCHAR(50),
    kid_prefix              VARCHAR(50),
    email                   VARCHAR(150),
    phone                   VARCHAR(50),
    default_expense_account INTEGER      DEFAULT 4300,
    payment_terms_days      INTEGER      DEFAULT 14,
    created_at              TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS supplier_invoices (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id      INTEGER      NOT NULL REFERENCES suppliers(id),
    supplier_name    VARCHAR(200) NOT NULL,
    invoice_number   VARCHAR(100) NOT NULL,
    kid              VARCHAR(50),
    issue_date       TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    due_date         TIMESTAMP    NOT NULL,
    amount_ex_vat    REAL         DEFAULT 0.0,
    vat_amount       REAL         DEFAULT 0.0,
    vat_rate_percent INTEGER      DEFAULT 25,                  -- 25 | 15 | 12 | 0
    total_amount     REAL         DEFAULT 0.0,
    expense_account  INTEGER      DEFAULT 6540,
    department_code  VARCHAR(50),
    project_code     VARCHAR(50),
    status           VARCHAR(50)  DEFAULT 'UNPAID',            -- UNPAID | PAID | OVERDUE
    voucher_id       INTEGER      REFERENCES vouchers(id),
    attachment_url   VARCHAR(500),
    created_at       TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- 7. KUNDER & UTGÅENDE SALGSFAKTURAER (MED NORSK MVA)
CREATE TABLE IF NOT EXISTS customers (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    name               VARCHAR(200) NOT NULL,
    org_number         VARCHAR(50),
    email              VARCHAR(150),
    phone              VARCHAR(50),
    address            VARCHAR(255),
    payment_terms_days INTEGER      DEFAULT 14,
    created_at         TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS customer_invoices (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_number        INTEGER      UNIQUE,
    customer_id           INTEGER      REFERENCES customers(id),
    customer_name         VARCHAR(200) NOT NULL,
    customer_email        VARCHAR(150),
    customer_orgnr        VARCHAR(50),
    issue_date            TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    due_date              TIMESTAMP    NOT NULL,
    kid                   VARCHAR(50),
    subtotal              REAL         DEFAULT 0.0,
    vat_amount            REAL         DEFAULT 0.0,
    total_amount          REAL         DEFAULT 0.0,
    lines_json            TEXT,
    status                VARCHAR(50)  DEFAULT 'SENT',
    reminder_count        INTEGER      DEFAULT 0,
    reminder_fee          REAL         DEFAULT 0.0,
    collection_case_id    VARCHAR(100),
    collection_status     VARCHAR(100),
    is_credit_note        BOOLEAN      DEFAULT FALSE,
    credit_for_invoice_id INTEGER,
    department_code       VARCHAR(50),
    project_code          VARCHAR(50),
    voucher_id            INTEGER      REFERENCES vouchers(id),
    created_at            TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- 8. BANKAVSTEMNING
CREATE TABLE IF NOT EXISTS bank_transactions (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_date   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    description        VARCHAR(500) NOT NULL,
    amount             REAL         NOT NULL,
    reference          VARCHAR(100),
    reconciled         BOOLEAN      DEFAULT FALSE,
    matched_voucher_id INTEGER      REFERENCES vouchers(id),
    reconciled_at      TIMESTAMP,
    source             VARCHAR(100) DEFAULT 'BANK_IMPORT',
    created_at         TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- 9. BILAGSARKIV / OPPLASTEDE DOKUMENTER (PDF & BILDE)
CREATE TABLE IF NOT EXISTS uploaded_documents (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    filename            VARCHAR(255) NOT NULL,
    original_name       VARCHAR(255) NOT NULL,
    file_type           VARCHAR(50)  NOT NULL,
    file_path           VARCHAR(500) NOT NULL,
    file_size           INTEGER      DEFAULT 0,
    extracted_data_json TEXT,
    status              VARCHAR(50)  DEFAULT 'PENDING',        -- PENDING | BOOKED | REJECTED
    voucher_id          INTEGER      REFERENCES vouchers(id),
    uploaded_at         TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- 10. ANSATTE & AUTOMATISK NORSK LØNNSKJØRING
CREATE TABLE IF NOT EXISTS employees (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_number      VARCHAR(30)  NOT NULL UNIQUE,
    full_name            VARCHAR(200) NOT NULL,
    national_id          VARCHAR(20),
    email                VARCHAR(150),
    bank_account         VARCHAR(50),
    position             VARCHAR(150) DEFAULT 'Ansatt',
    monthly_gross_salary REAL         DEFAULT 45000.0,
    tax_percent          REAL         DEFAULT 30.0,
    holiday_pay_percent  REAL         DEFAULT 12.0,
    aga_zone             INTEGER      DEFAULT 1,
    otp_percent          REAL         DEFAULT 2.0,
    department_code      VARCHAR(50)  DEFAULT 'ADM',
    project_code         VARCHAR(50)  DEFAULT 'FELLES',
    is_active            BOOLEAN      DEFAULT TRUE,
    created_at           TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS payroll_runs (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    period                  VARCHAR(20) NOT NULL,
    pay_date                TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status                  VARCHAR(30) DEFAULT 'POSTED',
    total_gross             REAL        DEFAULT 0.0,
    total_overtime          REAL        DEFAULT 0.0,
    total_bonus             REAL        DEFAULT 0.0,
    total_tax_withholding   REAL        DEFAULT 0.0,
    total_net_pay           REAL        DEFAULT 0.0,
    total_holiday_pay       REAL        DEFAULT 0.0,
    total_aga               REAL        DEFAULT 0.0,
    total_aga_holiday       REAL        DEFAULT 0.0,
    total_otp               REAL        DEFAULT 0.0,
    total_employer_cost     REAL        DEFAULT 0.0,
    voucher_id              INTEGER     REFERENCES vouchers(id),
    tax_transfer_voucher_id INTEGER     REFERENCES vouchers(id),
    created_at              TIMESTAMP   DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS payroll_lines (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    payroll_run_id      INTEGER      NOT NULL REFERENCES payroll_runs(id) ON DELETE CASCADE,
    employee_id         INTEGER      NOT NULL REFERENCES employees(id),
    employee_name       VARCHAR(200) NOT NULL,
    gross_salary        REAL         DEFAULT 0.0,
    overtime_pay        REAL         DEFAULT 0.0,
    bonus_pay           REAL         DEFAULT 0.0,
    tax_percent         REAL         DEFAULT 30.0,
    tax_withholding     REAL         DEFAULT 0.0,
    net_pay             REAL         DEFAULT 0.0,
    holiday_pay_percent REAL         DEFAULT 12.0,
    holiday_pay         REAL         DEFAULT 0.0,
    aga_percent         REAL         DEFAULT 14.1,
    aga_amount          REAL         DEFAULT 0.0,
    aga_holiday_amount  REAL         DEFAULT 0.0,
    otp_percent         REAL         DEFAULT 2.0,
    otp_amount          REAL         DEFAULT 0.0,
    total_employer_cost REAL         DEFAULT 0.0,
    department_code     VARCHAR(50),
    project_code        VARCHAR(50)
);

-- 11. REVISJONSLOGG & KUNDESERVICE
CREATE TABLE IF NOT EXISTS audit_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    action      VARCHAR(100) NOT NULL,
    details     TEXT,
    ai_assisted BOOLEAN      DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS support_tickets (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_name  VARCHAR(150) NOT NULL,
    customer_email VARCHAR(150) NOT NULL,
    subject        VARCHAR(255) NOT NULL,
    category       VARCHAR(50)  DEFAULT 'SUPPORT',
    status         VARCHAR(50)  DEFAULT 'ESCALATED_TO_HUMAN',
    priority       VARCHAR(20)  DEFAULT 'HIGH',
    assigned_to    VARCHAR(100) DEFAULT 'Deg (Kundeserviceleder)',
    created_at     TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ticket_messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id   INTEGER      NOT NULL REFERENCES support_tickets(id) ON DELETE CASCADE,
    sender      VARCHAR(50)  NOT NULL,
    sender_name VARCHAR(100) NOT NULL,
    message     TEXT         NOT NULL,
    timestamp   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);
