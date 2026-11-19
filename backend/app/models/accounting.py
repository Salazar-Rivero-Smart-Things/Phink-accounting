from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Account(Base):
    __tablename__ = "accounts"

    account_number = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    account_type = Column(String(50), nullable=False)  # ASSET, LIABILITY, EQUITY, REVENUE, EXPENSE
    vat_code = Column(String(20), nullable=True)       # e.g., "HIGH_25", "NONE", "MED_15"
    description = Column(String(255), nullable=True)

    lines = relationship("TransactionLine", back_populates="account")

class Voucher(Base):
    """
    Bilag / Voucher i regnskapet.
    Må alltid ha balanserte poster: sum(debit) == sum(credit).
    """
    __tablename__ = "vouchers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    voucher_number = Column(Integer, unique=True, index=True)
    date = Column(DateTime, default=datetime.utcnow, nullable=False)
    description = Column(String(500), nullable=False)
    source_document = Column(String(500), nullable=True)   # Filnavn eller URL til opplastet bilde/PDF
    department_code = Column(String(50), nullable=True)    # Avdeling (f.eks. ADM, SALG, DRIFT)
    project_code = Column(String(50), nullable=True)       # Prosjekt (f.eks. PROJ-2026-01)
    status = Column(String(50), default="POSTED")          # DRAFT, POSTED, REVERSED
    ai_analyzed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    lines = relationship("TransactionLine", back_populates="voucher", cascade="all, delete-orphan")
    bank_transactions = relationship("BankTransaction", back_populates="voucher")

class TransactionLine(Base):
    __tablename__ = "transaction_lines"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    voucher_id = Column(Integer, ForeignKey("vouchers.id"), nullable=False)
    account_number = Column(Integer, ForeignKey("accounts.account_number"), nullable=False)
    description = Column(String(255), nullable=True)
    debit = Column(Float, default=0.0)
    credit = Column(Float, default=0.0)
    department_code = Column(String(50), nullable=True)
    project_code = Column(String(50), nullable=True)
    vat_code = Column(String(20), nullable=True)

    voucher = relationship("Voucher", back_populates="lines")
    account = relationship("Account", back_populates="lines")

class Supplier(Base):
    """
    Leverandørregister.
    """
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    org_number = Column(String(50), nullable=True)
    account_number = Column(String(50), nullable=True)     # Bankkontonummer for betaling
    kid_prefix = Column(String(50), nullable=True)
    email = Column(String(150), nullable=True)
    phone = Column(String(50), nullable=True)
    default_expense_account = Column(Integer, default=4300) # Standard kostnadskonto
    payment_terms_days = Column(Integer, default=14)
    created_at = Column(DateTime, default=datetime.utcnow)

    invoices = relationship("SupplierInvoice", back_populates="supplier")

class SupplierInvoice(Base):
    """
    Inngående leverandørfaktura.
    """
    __tablename__ = "supplier_invoices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    supplier_name = Column(String(200), nullable=False)
    invoice_number = Column(String(100), nullable=False)
    kid = Column(String(50), nullable=True)
    issue_date = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=False)
    amount_ex_vat = Column(Float, default=0.0)
    vat_amount = Column(Float, default=0.0)
    vat_rate_percent = Column(Integer, default=25)
    total_amount = Column(Float, default=0.0)
    expense_account = Column(Integer, default=6540)
    department_code = Column(String(50), nullable=True)
    project_code = Column(String(50), nullable=True)
    status = Column(String(50), default="UNPAID") # UNPAID, PAID, OVERDUE
    voucher_id = Column(Integer, ForeignKey("vouchers.id"), nullable=True)
    attachment_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    supplier = relationship("Supplier", back_populates="invoices")

class Customer(Base):
    """
    Kunderegister.
    """
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    org_number = Column(String(50), nullable=True)
    email = Column(String(150), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(String(255), nullable=True)
    payment_terms_days = Column(Integer, default=14)
    created_at = Column(DateTime, default=datetime.utcnow)

    invoices = relationship("CustomerInvoice", back_populates="customer")

class CustomerInvoice(Base):
    """
    Salgsfakturaer utstedt til kunder.
    Koblet til hovedbok ved bokføring.
    """
    __tablename__ = "customer_invoices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    invoice_number = Column(Integer, unique=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    customer_name = Column(String(200), nullable=False)
    customer_email = Column(String(150), nullable=True)
    customer_orgnr = Column(String(50), nullable=True)
    issue_date = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=False)
    kid = Column(String(50), nullable=True)
    subtotal = Column(Float, default=0.0)
    vat_amount = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    lines_json = Column(Text, nullable=True) # JSON over fakturalinjer
    status = Column(String(50), default="SENT")  # DRAFT, SENT, PAID, OVERDUE, REMINDER_SENT, COLLECTION_NOTICE, SENT_TO_KRAVIA, CREDITED
    reminder_count = Column(Integer, default=0)
    reminder_fee = Column(Float, default=0.0)
    collection_case_id = Column(String(100), nullable=True)
    collection_status = Column(String(100), nullable=True)
    is_credit_note = Column(Boolean, default=False)
    credit_for_invoice_id = Column(Integer, nullable=True)
    department_code = Column(String(50), nullable=True)
    project_code = Column(String(50), nullable=True)
    voucher_id = Column(Integer, ForeignKey("vouchers.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    customer = relationship("Customer", back_populates="invoices")

class BankTransaction(Base):
    """
    Banktransaksjoner for bankavstemning.
    Importeres via CSV/nettbank og matches mot bilag på konto 1920.
    """
    __tablename__ = "bank_transactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    transaction_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    description = Column(String(500), nullable=False)
    amount = Column(Float, nullable=False)                  # Positiv = inn, Negativ = ut
    reference = Column(String(100), nullable=True)         # KID, arkivreferanse
    reconciled = Column(Boolean, default=False)
    matched_voucher_id = Column(Integer, ForeignKey("vouchers.id"), nullable=True)
    reconciled_at = Column(DateTime, nullable=True)
    source = Column(String(100), default="BANK_IMPORT")
    created_at = Column(DateTime, default=datetime.utcnow)

    voucher = relationship("Voucher", back_populates="bank_transactions")

class UploadedDocument(Base):
    """
    Bilagsmottak / Innboks for opplastede bilag (bilde eller PDF).
    """
    __tablename__ = "uploaded_documents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)          # pdf, png, jpeg, etc.
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    extracted_data_json = Column(Text, nullable=True)       # AI-analyserte data (JSON)
    status = Column(String(50), default="PENDING")          # PENDING, BOOKED, REJECTED
    voucher_id = Column(Integer, ForeignKey("vouchers.id"), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

class CompanySetting(Base):
    """
    Bedrifts- eller privatopplysninger og innstillinger.
    Støtter PRIVATE, ENK, AS, FORENING og INSTITUSJON.
    """
    __tablename__ = "company_settings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_name = Column(String(200), default="Mitt Selskap AS")
    entity_type = Column(String(30), default="AS")             # PRIVATE | ENK | AS | FORENING | INSTITUSJON
    org_number = Column(String(50), default="999 888 777 MVA")
    national_id = Column(String(20), nullable=True)            # 11-sifret fødselsnummer (for PRIVATE/ENK)
    bank_account = Column(String(50), default="1234.56.78903")
    vat_registered = Column(Boolean, default=True)
    aga_zone = Column(Integer, default=1)                      # Arbeidsgiveravgiftssone (1-5)
    address = Column(String(200), default="Storgata 1")
    postal_code = Column(String(20), default="0182")
    city = Column(String(100), default="Oslo")
    email = Column(String(150), default="post@mittselskap.no")
    phone = Column(String(50), default="+47 22 00 00 00")
    logo_url = Column(String(500), nullable=True)
    marketing_image_url = Column(String(500), nullable=True)
    vipps_number = Column(String(50), default="")               # Vipps Bedrift nummer
    allowed_payment_methods = Column(String(100), default="VIPPS_BEDRIFT,FAKTURA")


class SubscriptionOrder(Base):
    """
    Betalings- og abonnementsordrer for Phink Accounting.
    Støtter KUN Vipps Bedrift (VIPPS_BEDRIFT) og tilsendt faktura (FAKTURA).
    """
    __tablename__ = "subscription_orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    customer_name = Column(String(200), nullable=False)
    customer_email = Column(String(150), nullable=False)
    org_number = Column(String(50), nullable=True)
    plan_id = Column(String(50), nullable=False)               # PRIVAT | ENK | AS_PRO | ENTERPRISE
    plan_name = Column(String(150), nullable=False)
    payment_method = Column(String(30), nullable=False)        # VIPPS_BEDRIFT | FAKTURA
    amount_ex_vat = Column(Float, default=0.0)
    vat_amount = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    vipps_number = Column(String(50), nullable=True)
    payment_reference = Column(String(100), nullable=False)    # Vipps-melding eller KID
    invoice_id = Column(Integer, ForeignKey("customer_invoices.id"), nullable=True)
    status = Column(String(30), default="PENDING")             # PENDING | INVOICE_SENT | PAID
    due_date = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    """
    Brukerinnlogging for både privatpersoner og bedrifter/organisasjoner
    (ENK, AS, Foreninger og Institusjoner).
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(200), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(200), nullable=False)
    role = Column(String(30), default="USER")                  # OWNER | USER | ACCOUNTANT
    entity_type = Column(String(30), default="AS")             # PRIVATE | ENK | AS | FORENING | INSTITUSJON
    company_name = Column(String(200), nullable=True)
    org_number = Column(String(30), nullable=True)             # 9 siffer for ENK, AS, FORENING, INSTITUSJON
    national_id = Column(String(20), nullable=True)            # 11 siffer fødselsnummer for PRIVATE / ENK
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(150), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    customer_name = Column(String(200), nullable=True)
    budget = Column(Float, default=0.0)
    status = Column(String(30), default="ACTIVE")              # ACTIVE | COMPLETED | ARCHIVED
    created_at = Column(DateTime, default=datetime.utcnow)


class Employee(Base):
    """
    Ansattregister for automatisk norsk lønnskjøring.
    """
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_number = Column(String(30), unique=True, index=True, nullable=False)
    full_name = Column(String(200), nullable=False)
    national_id = Column(String(20), nullable=True)            # Fødselsnummer (11 siffer)
    email = Column(String(150), nullable=True)
    bank_account = Column(String(50), nullable=True)
    position = Column(String(150), default="Ansatt")
    monthly_gross_salary = Column(Float, default=45000.0)
    tax_percent = Column(Float, default=30.0)                  # Forskuddstrekk %
    holiday_pay_percent = Column(Float, default=12.0)          # 10.2%, 12.0% eller 14.3%
    aga_zone = Column(Integer, default=1)                      # Sone 1=14.1%, 2=10.6%, 3=6.4%, 4=5.1%, 5=0%
    otp_percent = Column(Float, default=2.0)                   # Obligatorisk tjenestepensjon (min 2%)
    department_code = Column(String(50), default="ADM")
    project_code = Column(String(50), default="FELLES")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PayrollRun(Base):
    """
    Lønnskjøring som automatisk fordeler brutto, overtid, bonus, forskuddstrekk,
    nettolønn, feriepenger, AGA, AGA på feriepenger, OTP og skattetrekkskonto (1950).
    """
    __tablename__ = "payroll_runs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    period = Column(String(20), nullable=False)                # f.eks. "2026-11"
    pay_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(30), default="POSTED")
    total_gross = Column(Float, default=0.0)
    total_overtime = Column(Float, default=0.0)
    total_bonus = Column(Float, default=0.0)
    total_tax_withholding = Column(Float, default=0.0)
    total_net_pay = Column(Float, default=0.0)
    total_holiday_pay = Column(Float, default=0.0)
    total_aga = Column(Float, default=0.0)
    total_aga_holiday = Column(Float, default=0.0)
    total_otp = Column(Float, default=0.0)
    total_employer_cost = Column(Float, default=0.0)
    voucher_id = Column(Integer, ForeignKey("vouchers.id"), nullable=True)
    tax_transfer_voucher_id = Column(Integer, ForeignKey("vouchers.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    lines = relationship("PayrollLine", back_populates="payroll_run", cascade="all, delete-orphan")


class PayrollLine(Base):
    __tablename__ = "payroll_lines"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    payroll_run_id = Column(Integer, ForeignKey("payroll_runs.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    employee_name = Column(String(200), nullable=False)
    gross_salary = Column(Float, default=0.0)
    overtime_pay = Column(Float, default=0.0)
    bonus_pay = Column(Float, default=0.0)
    tax_percent = Column(Float, default=30.0)
    tax_withholding = Column(Float, default=0.0)
    net_pay = Column(Float, default=0.0)
    holiday_pay_percent = Column(Float, default=12.0)
    holiday_pay = Column(Float, default=0.0)
    aga_percent = Column(Float, default=14.1)
    aga_amount = Column(Float, default=0.0)
    aga_holiday_amount = Column(Float, default=0.0)
    otp_percent = Column(Float, default=2.0)
    otp_amount = Column(Float, default=0.0)
    total_employer_cost = Column(Float, default=0.0)
    department_code = Column(String(50), nullable=True)
    project_code = Column(String(50), nullable=True)

    payroll_run = relationship("PayrollRun", back_populates="lines")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    action = Column(String(100), nullable=False)
    details = Column(Text, nullable=True)
    ai_assisted = Column(Boolean, default=False)

class SupportTicket(Base):
    """
    Kundeservice-henvendelser.
    Kobler Llama AI som 1. linje og brukeren som ansvarlig kundeserviceoperatør.
    """
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    customer_name = Column(String(150), nullable=False)
    customer_email = Column(String(150), nullable=False)
    subject = Column(String(255), nullable=False)
    category = Column(String(50), default="SUPPORT")
    status = Column(String(50), default="ESCALATED_TO_HUMAN")
    priority = Column(String(20), default="HIGH")
    assigned_to = Column(String(100), default="Deg (Kundeserviceleder)")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("TicketMessage", back_populates="ticket", cascade="all, delete-orphan")

class TicketMessage(Base):
    __tablename__ = "ticket_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("support_tickets.id"), nullable=False)
    sender = Column(String(50), nullable=False)
    sender_name = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("SupportTicket", back_populates="messages")
