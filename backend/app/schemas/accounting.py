from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Any
from datetime import datetime

class AccountBase(BaseModel):
    account_number: int
    name: str
    account_type: str
    vat_code: Optional[str] = None
    description: Optional[str] = None

class AccountCreate(AccountBase):
    pass

class AccountResponse(AccountBase):
    class Config:
        from_attributes = True

class TransactionLineCreate(BaseModel):
    account_number: int
    description: Optional[str] = None
    debit: float = 0.0
    credit: float = 0.0
    department_code: Optional[str] = None
    project_code: Optional[str] = None
    vat_code: Optional[str] = None

class TransactionLineResponse(TransactionLineCreate):
    id: int
    voucher_id: int

    class Config:
        from_attributes = True

class VoucherCreate(BaseModel):
    date: Optional[datetime] = None
    description: str
    source_document: Optional[str] = None
    department_code: Optional[str] = None
    project_code: Optional[str] = None
    lines: List[TransactionLineCreate]

    @field_validator("lines")
    @classmethod
    def validate_double_entry_balance(cls, lines: List[TransactionLineCreate]):
        if not lines or len(lines) < 2:
            raise ValueError("Et bilag må ha minst to linjer (dobbel bokføring).")
        
        total_debit = round(sum(line.debit for line in lines), 2)
        total_credit = round(sum(line.credit for line in lines), 2)
        
        if total_debit != total_credit:
            raise ValueError(
                f"Ubalansert bilag: Total debet ({total_debit} NOK) "
                f"må være lik total kredit ({total_credit} NOK)."
            )
        return lines

class VoucherResponse(BaseModel):
    id: int
    voucher_number: int
    date: datetime
    description: str
    source_document: Optional[str] = None
    department_code: Optional[str] = None
    project_code: Optional[str] = None
    status: str
    ai_analyzed: bool
    created_at: datetime
    lines: List[TransactionLineResponse]

    class Config:
        from_attributes = True

class FinancialSummary(BaseModel):
    total_revenue: float
    total_expenses: float
    net_income: float
    bank_balance: float
    voucher_count: int
    total_receivables: float = 0.0  # Utestående kundefordringer (1500)
    total_payables: float = 0.0     # Utestående leverandørgjeld (2400)
    pending_reconciliations: int = 0 # Uavstemte banktransaksjoner

# Leverandører
class SupplierCreate(BaseModel):
    name: str
    org_number: Optional[str] = None
    account_number: Optional[str] = None
    kid_prefix: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    default_expense_account: int = 6540
    payment_terms_days: int = 14

class SupplierResponse(SupplierCreate):
    id: int
    created_at: datetime
    outstanding_balance: float = 0.0
    invoice_count: int = 0

    class Config:
        from_attributes = True

class SupplierInvoiceCreate(BaseModel):
    supplier_id: int
    invoice_number: str
    kid: Optional[str] = None
    issue_date: Optional[datetime] = None
    due_date: datetime
    amount_ex_vat: float
    vat_amount: float = 0.0
    vat_rate_percent: int = 25
    expense_account: int = 6540
    department_code: Optional[str] = None
    project_code: Optional[str] = None
    attachment_url: Optional[str] = None

class SupplierInvoiceResponse(BaseModel):
    id: int
    supplier_id: int
    supplier_name: str
    invoice_number: str
    kid: Optional[str] = None
    issue_date: datetime
    due_date: datetime
    amount_ex_vat: float
    vat_amount: float
    vat_rate_percent: int = 25
    total_amount: float
    expense_account: int
    department_code: Optional[str] = None
    project_code: Optional[str] = None
    status: str
    voucher_id: Optional[int] = None
    attachment_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class SupplierInvoicePay(BaseModel):
    payment_date: Optional[datetime] = None
    from_account: int = 1920

# Kunder & Salgsfaktura
class CustomerCreate(BaseModel):
    name: str
    org_number: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    payment_terms_days: int = 14

class CustomerResponse(CustomerCreate):
    id: int
    created_at: datetime
    outstanding_balance: float = 0.0
    invoice_count: int = 0

    class Config:
        from_attributes = True

class InvoiceLineItem(BaseModel):
    description: str
    quantity: float = 1.0
    unit_price: float
    vat_percent: float = 25.0
    amount: float

class CustomerInvoiceCreate(BaseModel):
    customer_id: Optional[int] = None
    customer_name: str
    customer_email: Optional[str] = None
    customer_orgnr: Optional[str] = None
    due_date: datetime
    kid: Optional[str] = None
    lines: List[InvoiceLineItem]

class CustomerInvoiceResponse(BaseModel):
    id: int
    invoice_number: int
    customer_id: Optional[int] = None
    customer_name: str
    customer_email: Optional[str] = None
    customer_orgnr: Optional[str] = None
    issue_date: datetime
    due_date: datetime
    kid: Optional[str] = None
    subtotal: float
    vat_amount: float
    total_amount: float
    lines: List[InvoiceLineItem] = []
    status: str
    voucher_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Bankavstemning
class BankTransactionCreate(BaseModel):
    transaction_date: datetime
    description: str
    amount: float
    reference: Optional[str] = None

class BankTransactionResponse(BaseModel):
    id: int
    transaction_date: datetime
    description: str
    amount: float
    reference: Optional[str] = None
    reconciled: bool
    matched_voucher_id: Optional[int] = None
    reconciled_at: Optional[datetime] = None
    source: str
    created_at: datetime

    class Config:
        from_attributes = True

class BankReconciliationSummary(BaseModel):
    bank_statement_balance: float
    account_1920_balance: float
    difference: float
    reconciled_count: int
    unreconciled_count: int
    is_balanced: bool

class QuickBookBankTransaction(BaseModel):
    account_number: int
    description: Optional[str] = None

# Bilagsmottak / Dokumenter
class UploadedDocumentResponse(BaseModel):
    id: int
    filename: str
    original_name: str
    file_type: str
    file_path: str
    file_size: int
    status: str
    extracted_data: Optional[Any] = None
    voucher_id: Optional[int] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True

# Bedriftsprofil
class CompanySettingBase(BaseModel):
    company_name: str
    entity_type: str = "AS"
    org_number: str
    national_id: Optional[str] = None
    bank_account: str
    vat_registered: bool = True
    aga_zone: int = 1
    address: str
    postal_code: str
    city: str
    email: str
    phone: str
    logo_url: Optional[str] = None
    marketing_image_url: Optional[str] = None

class CompanySettingCreate(CompanySettingBase):
    pass

class CompanySettingResponse(CompanySettingBase):
    id: int

    class Config:
        from_attributes = True

# Rapporter
class ReportLine(BaseModel):
    account_number: Optional[int] = None
    account_name: str
    amount: float

class IncomeStatementSection(BaseModel):
    title: str
    lines: List[ReportLine]
    total: float

class IncomeStatementResponse(BaseModel):
    sections: List[IncomeStatementSection]
    net_profit: float

class BalanceSheetSection(BaseModel):
    title: str
    lines: List[ReportLine]
    total: float

class BalanceSheetResponse(BaseModel):
    assets: BalanceSheetSection
    equity_and_liabilities: BalanceSheetSection
    is_balanced: bool

class VatReportTerm(BaseModel):
    term: int # 1 til 6
    term_name: str
    base_sales_high_25: float
    output_vat_25: float
    input_vat_deductible: float
    net_vat_payable: float
    is_settled: bool

# AI Schemas
class AIInvoiceParseRequest(BaseModel):
    invoice_text: str

class AIInvoiceParseResponse(BaseModel):
    supplier: Optional[str] = None
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    total_amount: Optional[float] = None
    vat_amount: Optional[float] = None
    vat_rate_percent: Optional[int] = 25
    kid_or_ref: Optional[str] = None
    department_code: Optional[str] = "ADM"
    department_name: Optional[str] = "Administrasjon"
    project_code: Optional[str] = "FELLES"
    project_name: Optional[str] = "Felleskostnad / Drift"
    suggested_expense_account: Optional[int] = None
    account_name: Optional[str] = None
    suggested_lines: List[TransactionLineCreate] = []
    explanation: Optional[str] = None
    is_duplicate: Optional[bool] = False
    duplicate_warning: Optional[str] = None

class AIChatRequest(BaseModel):
    message: str

class AIChatResponse(BaseModel):
    reply: str
    sources_considered: Optional[List[str]] = None

# Support Schemas (Kundeservice)
class TicketMessageCreate(BaseModel):
    sender: str = "OPERATOR_YOU"
    sender_name: str = "Deg (Kundeservice)"
    message: str

class TicketMessageResponse(BaseModel):
    id: int
    ticket_id: int
    sender: str
    sender_name: str
    message: str
    timestamp: datetime

    class Config:
        from_attributes = True

class SupportTicketCreate(BaseModel):
    customer_name: str
    customer_email: str
    subject: str
    category: str = "REFUND"
    initial_message: str

class SupportTicketResponse(BaseModel):
    id: int
    customer_name: str
    customer_email: str
    subject: str
    category: str
    status: str
    priority: str
    assigned_to: str
    created_at: datetime
    updated_at: datetime
    messages: List[TicketMessageResponse] = []

    class Config:
        from_attributes = True
