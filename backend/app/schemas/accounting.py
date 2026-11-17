from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
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

class TransactionLineResponse(TransactionLineCreate):
    id: int
    voucher_id: int

    class Config:
        from_attributes = True

class VoucherCreate(BaseModel):
    date: Optional[datetime] = None
    description: str
    source_document: Optional[str] = None
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

# AI Schemas
class AIInvoiceParseRequest(BaseModel):
    invoice_text: str

class AIInvoiceParseResponse(BaseModel):
    supplier: Optional[str] = None
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    total_amount: Optional[float] = None
    vat_amount: Optional[float] = None
    kid_or_ref: Optional[str] = None
    suggested_expense_account: Optional[int] = None
    account_name: Optional[str] = None
    suggested_lines: List[TransactionLineCreate] = []
    explanation: Optional[str] = None

class AIChatRequest(BaseModel):
    message: str

class AIChatResponse(BaseModel):
    reply: str
    sources_considered: Optional[List[str]] = None

# Support Schemas (Kundeservice)
class TicketMessageCreate(BaseModel):
    sender: str = "OPERATOR_YOU" # "CUSTOMER", "LLAMA_AI", "OPERATOR_YOU"
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
    category: str = "REFUND" # REFUND, PAYMENT_FAILED, ACCOUNTING, TECHNICAL
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
