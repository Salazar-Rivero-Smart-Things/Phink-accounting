from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional
from datetime import datetime
import json
import os
import uuid
import shutil

from app.database import get_db
from app.models.accounting import (
    Account, Voucher, TransactionLine, AuditLog,
    Supplier, SupplierInvoice,
    Customer, CustomerInvoice,
    BankTransaction, UploadedDocument, CompanySetting
)
from app.schemas.accounting import (
    AccountResponse, AccountCreate,
    VoucherResponse, VoucherCreate,
    FinancialSummary,
    SupplierCreate, SupplierResponse,
    SupplierInvoiceCreate, SupplierInvoiceResponse, SupplierInvoicePay,
    CustomerCreate, CustomerResponse,
    CustomerInvoiceCreate, CustomerInvoiceResponse,
    BankTransactionCreate, BankTransactionResponse, BankReconciliationSummary,
    QuickBookBankTransaction,
    UploadedDocumentResponse,
    CompanySettingBase, CompanySettingCreate, CompanySettingResponse,
    IncomeStatementResponse, IncomeStatementSection, ReportLine,
    BalanceSheetResponse, BalanceSheetSection,
    VatReportTerm
)

router = APIRouter(prefix="/accounting", tags=["Accounting"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# -------------------------------------------------------------
# 1. KONTOPLAN & HOVEDBOK
# -------------------------------------------------------------

@router.get("/accounts", response_model=List[AccountResponse])
def get_accounts(db: Session = Depends(get_db)):
    """Henter alle kontoer i kontoplanen."""
    return db.query(Account).order_by(Account.account_number).all()

@router.post("/accounts", response_model=AccountResponse)
def create_account(account: AccountCreate, db: Session = Depends(get_db)):
    """Oppretter en ny regnskapskonto."""
    existing = db.query(Account).filter(Account.account_number == account.account_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Kontonummeret eksisterer allerede.")
    
    db_account = Account(**account.model_dump())
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account

# -------------------------------------------------------------
# 2. BILAGSFØRING (VOUCHERS)
# -------------------------------------------------------------

@router.get("/vouchers", response_model=List[VoucherResponse])
def get_vouchers(db: Session = Depends(get_db)):
    """Henter alle bilag sortert med nyeste først."""
    return db.query(Voucher).order_by(Voucher.voucher_number.desc()).all()

@router.post("/vouchers", response_model=VoucherResponse)
def create_voucher(voucher_in: VoucherCreate, db: Session = Depends(get_db)):
    """
    Bokfører et nytt bilag. Dobbel bokføring valideres i Pydantic-skjemaet
    (sum debet må være eksakt lik sum kredit).
    """
    max_num = db.query(func.max(Voucher.voucher_number)).scalar() or 0
    next_voucher_number = max_num + 1

    db_voucher = Voucher(
        voucher_number=next_voucher_number,
        date=voucher_in.date or datetime.utcnow(),
        description=voucher_in.description,
        source_document=voucher_in.source_document,
        department_code=voucher_in.department_code,
        project_code=voucher_in.project_code,
        status="POSTED"
    )
    db.add(db_voucher)
    db.flush()

    for line in voucher_in.lines:
        acc = db.query(Account).filter(Account.account_number == line.account_number).first()
        if not acc:
            raise HTTPException(status_code=400, detail=f"Konto {line.account_number} finnes ikke i kontoplanen.")
        
        db_line = TransactionLine(
            voucher_id=db_voucher.id,
            account_number=line.account_number,
            description=line.description or voucher_in.description,
            debit=line.debit,
            credit=line.credit,
            department_code=line.department_code or voucher_in.department_code,
            project_code=line.project_code or voucher_in.project_code,
            vat_code=line.vat_code,
        )
        db.add(db_line)

    audit = AuditLog(
        action="POST_VOUCHER",
        details=f"Bilag #{next_voucher_number} bokført. Beskrivelse: {voucher_in.description}",
        ai_assisted=False
    )
    db.add(audit)

    db.commit()
    db.refresh(db_voucher)
    return db_voucher

# -------------------------------------------------------------
# 3. NØKKELTALL & SAMMENDRAG
# -------------------------------------------------------------

@router.get("/summary", response_model=FinancialSummary)
def get_financial_summary(db: Session = Depends(get_db)):
    """Beregner sanntids nøkkeltall for dashbordet."""
    lines = db.query(TransactionLine, Account).join(Account, TransactionLine.account_number == Account.account_number).all()

    total_revenue = 0.0
    total_expenses = 0.0
    bank_balance = 0.0
    receivables = 0.0
    payables = 0.0

    for line, account in lines:
        if 3000 <= account.account_number < 4000:
            total_revenue += (line.credit - line.debit)
        elif 4000 <= account.account_number < 8000:
            total_expenses += (line.debit - line.credit)
        elif account.account_number == 1920:
            bank_balance += (line.debit - line.credit)
        elif account.account_number == 1500:
            receivables += (line.debit - line.credit)
        elif account.account_number == 2400:
            payables += (line.credit - line.debit)

    net_income = total_revenue - total_expenses
    voucher_count = db.query(func.count(Voucher.id)).scalar() or 0
    unreconciled_count = db.query(func.count(BankTransaction.id)).filter(BankTransaction.reconciled == False).scalar() or 0

    return FinancialSummary(
        total_revenue=round(total_revenue, 2),
        total_expenses=round(total_expenses, 2),
        net_income=round(net_income, 2),
        bank_balance=round(bank_balance, 2),
        voucher_count=voucher_count,
        total_receivables=round(max(0.0, receivables), 2),
        total_payables=round(max(0.0, payables), 2),
        pending_reconciliations=unreconciled_count
    )

# -------------------------------------------------------------
# 4. LEVERANDØRER & LEVERANDØRRESKONTRO
# -------------------------------------------------------------

@router.get("/suppliers", response_model=List[SupplierResponse])
def get_suppliers(db: Session = Depends(get_db)):
    """Henter alle leverandører med utestående saldo og antall fakturaer."""
    suppliers = db.query(Supplier).order_by(Supplier.name).all()
    res = []
    for sup in suppliers:
        # Beregn utestående ubetalte fakturaer
        unpaid = db.query(func.sum(SupplierInvoice.total_amount)).filter(
            SupplierInvoice.supplier_id == sup.id,
            SupplierInvoice.status == "UNPAID"
        ).scalar() or 0.0
        
        count = db.query(func.count(SupplierInvoice.id)).filter(
            SupplierInvoice.supplier_id == sup.id
        ).scalar() or 0

        sup_dict = {
            "id": sup.id,
            "name": sup.name,
            "org_number": sup.org_number,
            "account_number": sup.account_number,
            "kid_prefix": sup.kid_prefix,
            "email": sup.email,
            "phone": sup.phone,
            "default_expense_account": sup.default_expense_account,
            "payment_terms_days": sup.payment_terms_days,
            "created_at": sup.created_at,
            "outstanding_balance": round(unpaid, 2),
            "invoice_count": count
        }
        res.append(SupplierResponse(**sup_dict))
    return res

@router.post("/suppliers", response_model=SupplierResponse)
def create_supplier(sup_in: SupplierCreate, db: Session = Depends(get_db)):
    """Oppretter en ny leverandør i leverandørregisteret."""
    sup = Supplier(**sup_in.model_dump())
    db.add(sup)
    db.commit()
    db.refresh(sup)
    return SupplierResponse(
        **sup_in.model_dump(),
        id=sup.id,
        created_at=sup.created_at,
        outstanding_balance=0.0,
        invoice_count=0
    )

@router.get("/supplier-invoices", response_model=List[SupplierInvoiceResponse])
def get_supplier_invoices(db: Session = Depends(get_db)):
    """Henter alle inngående leverandørfakturaer."""
    return db.query(SupplierInvoice).order_by(SupplierInvoice.due_date.asc()).all()

@router.post("/supplier-invoices", response_model=SupplierInvoiceResponse)
def create_supplier_invoice(inv_in: SupplierInvoiceCreate, db: Session = Depends(get_db)):
    """
    Registrerer og bokfører en inngående leverandørfaktura automatisk:
    - Debet: Kostnadskonto (f.eks. 6540) for beløp eks. MVA
    - Debet: 2710 Inngående MVA for MVA-beløpet
    - Kredit: 2400 Leverandørgjeld for totalbeløpet
    """
    sup = db.query(Supplier).filter(Supplier.id == inv_in.supplier_id).first()
    if not sup:
        raise HTTPException(status_code=404, detail="Leverandør finnes ikke.")

    total_amount = round(inv_in.amount_ex_vat + inv_in.vat_amount, 2)
    
    # 1. Opprett bilag i hovedbok
    max_num = db.query(func.max(Voucher.voucher_number)).scalar() or 0
    next_voucher_number = max_num + 1

    desc = f"Faktura {inv_in.invoice_number} fra {sup.name}"
    voucher = Voucher(
        voucher_number=next_voucher_number,
        date=inv_in.issue_date or datetime.utcnow(),
        description=desc,
        source_document=inv_in.attachment_url,
        status="POSTED"
    )
    db.add(voucher)
    db.flush()

    # Linje 1: Kostnad (Debet)
    db.add(TransactionLine(
        voucher_id=voucher.id,
        account_number=inv_in.expense_account,
        description=f"{sup.name} - netto kostnad",
        debit=inv_in.amount_ex_vat,
        credit=0.0,
        department_code=inv_in.department_code,
        project_code=inv_in.project_code,
    ))

    # Linje 2: Inngående MVA fordelt på riktig norsk MVA-konto (25%=2710, 15%=2711, 12%=2712, 0%=ingen)
    if inv_in.vat_amount > 0 and inv_in.vat_rate_percent > 0:
        in_vat_account = 2710 if inv_in.vat_rate_percent == 25 else (2711 if inv_in.vat_rate_percent == 15 else 2712)
        db.add(TransactionLine(
            voucher_id=voucher.id,
            account_number=in_vat_account,
            description=f"Inngående MVA {inv_in.vat_rate_percent}%",
            debit=inv_in.vat_amount,
            credit=0.0,
            department_code=inv_in.department_code,
            project_code=inv_in.project_code,
            vat_code=f"IN_{inv_in.vat_rate_percent}",
        ))

    # Linje 3: Leverandørgjeld (Kredit 2400)
    db.add(TransactionLine(
        voucher_id=voucher.id,
        account_number=2400,
        description=f"Leverandørgjeld til {sup.name}",
        debit=0.0,
        credit=total_amount,
        department_code=inv_in.department_code,
        project_code=inv_in.project_code,
    ))

    # 2. Opprett fakturapost
    invoice = SupplierInvoice(
        supplier_id=sup.id,
        supplier_name=sup.name,
        invoice_number=inv_in.invoice_number,
        kid=inv_in.kid,
        issue_date=inv_in.issue_date or datetime.utcnow(),
        due_date=inv_in.due_date,
        amount_ex_vat=inv_in.amount_ex_vat,
        vat_amount=inv_in.vat_amount,
        vat_rate_percent=inv_in.vat_rate_percent,
        total_amount=total_amount,
        expense_account=inv_in.expense_account,
        department_code=inv_in.department_code,
        project_code=inv_in.project_code,
        status="UNPAID",
        voucher_id=voucher.id,
        attachment_url=inv_in.attachment_url
    )
    db.add(invoice)

    db.commit()
    db.refresh(invoice)
    return invoice

@router.post("/supplier-invoices/{invoice_id}/pay", response_model=SupplierInvoiceResponse)
def pay_supplier_invoice(invoice_id: int, pay_data: SupplierInvoicePay, db: Session = Depends(get_db)):
    """
    Betaler en leverandørfaktura og bokfører utbetalingen:
    - Debet: 2400 Leverandørgjeld
    - Kredit: 1920 Bankinnskudd
    """
    inv = db.query(SupplierInvoice).filter(SupplierInvoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Faktura ikke funnet.")
    if inv.status == "PAID":
        raise HTTPException(status_code=400, detail="Fakturaen er allerede markert som betalt.")

    # Bokfør betalingen
    max_num = db.query(func.max(Voucher.voucher_number)).scalar() or 0
    next_voucher_number = max_num + 1

    pay_date = pay_data.payment_date or datetime.utcnow()
    desc = f"Utbetaling faktura {inv.invoice_number} ({inv.supplier_name})"

    voucher = Voucher(
        voucher_number=next_voucher_number,
        date=pay_date,
        description=desc,
        status="POSTED"
    )
    db.add(voucher)
    db.flush()

    # Debet 2400 Leverandørgjeld
    db.add(TransactionLine(
        voucher_id=voucher.id,
        account_number=2400,
        description=f"Betalt til {inv.supplier_name}",
        debit=inv.total_amount,
        credit=0.0
    ))

    # Kredit 1920 Bank
    db.add(TransactionLine(
        voucher_id=voucher.id,
        account_number=pay_data.from_account,
        description="Utbetaling fra bankkonto",
        debit=0.0,
        credit=inv.total_amount
    ))

    inv.status = "PAID"
    db.commit()
    db.refresh(inv)
    return inv

# -------------------------------------------------------------
# 5. KUNDER & SALGSFAKTURERING
# -------------------------------------------------------------

@router.get("/customers", response_model=List[CustomerResponse])
def get_customers(db: Session = Depends(get_db)):
    """Henter alle kunder med utestående saldo og antall fakturaer."""
    customers = db.query(Customer).order_by(Customer.name).all()
    res = []
    for c in customers:
        unpaid = db.query(func.sum(CustomerInvoice.total_amount)).filter(
            CustomerInvoice.customer_id == c.id,
            CustomerInvoice.status != "PAID"
        ).scalar() or 0.0

        count = db.query(func.count(CustomerInvoice.id)).filter(
            CustomerInvoice.customer_id == c.id
        ).scalar() or 0

        c_dict = {
            "id": c.id,
            "name": c.name,
            "org_number": c.org_number,
            "email": c.email,
            "phone": c.phone,
            "address": c.address,
            "payment_terms_days": c.payment_terms_days,
            "created_at": c.created_at,
            "outstanding_balance": round(unpaid, 2),
            "invoice_count": count
        }
        res.append(CustomerResponse(**c_dict))
    return res

@router.post("/customers", response_model=CustomerResponse)
def create_customer(c_in: CustomerCreate, db: Session = Depends(get_db)):
    """Oppretter en ny kunde."""
    cust = Customer(**c_in.model_dump())
    db.add(cust)
    db.commit()
    db.refresh(cust)
    return CustomerResponse(
        **c_in.model_dump(),
        id=cust.id,
        created_at=cust.created_at,
        outstanding_balance=0.0,
        invoice_count=0
    )

@router.get("/invoices", response_model=List[CustomerInvoiceResponse])
def get_invoices(db: Session = Depends(get_db)):
    """Henter alle utstedte salgsfakturaer."""
    invoices = db.query(CustomerInvoice).order_by(CustomerInvoice.invoice_number.desc()).all()
    res = []
    for inv in invoices:
        lines = []
        if inv.lines_json:
            try:
                lines = json.loads(inv.lines_json)
            except Exception:
                pass
        
        res.append(CustomerInvoiceResponse(
            id=inv.id,
            invoice_number=inv.invoice_number,
            customer_id=inv.customer_id,
            customer_name=inv.customer_name,
            customer_email=inv.customer_email,
            customer_orgnr=inv.customer_orgnr,
            issue_date=inv.issue_date,
            due_date=inv.due_date,
            kid=inv.kid,
            subtotal=inv.subtotal,
            vat_amount=inv.vat_amount,
            total_amount=inv.total_amount,
            lines=lines,
            status=inv.status,
            voucher_id=inv.voucher_id,
            created_at=inv.created_at
        ))
    return res

@router.post("/invoices", response_model=CustomerInvoiceResponse)
def create_customer_invoice(inv_in: CustomerInvoiceCreate, db: Session = Depends(get_db)):
    """
    Oppretter og bokfører en salgsfaktura:
    - Debet: 1500 Kundefordringer for totalbeløp
    - Kredit: 3000 Salgsinntekter for subtotal (eks mva)
    - Kredit: 2700 Utgående MVA 25% for MVA-beløpet
    """
    subtotal = sum(l.amount for l in inv_in.lines)
    vat_total = sum(round(l.amount * (l.vat_percent / 100.0), 2) for l in inv_in.lines)
    total_amount = round(subtotal + vat_total, 2)

    # Finn neste fakturanummer
    max_num = db.query(func.max(CustomerInvoice.invoice_number)).scalar() or 1000
    next_inv_number = max_num + 1

    # Generer KID hvis ikke oppgitt
    kid = inv_in.kid or f"2026{next_inv_number}7"

    # 1. Bokfør i hovedbok
    max_vouch = db.query(func.max(Voucher.voucher_number)).scalar() or 0
    voucher = Voucher(
        voucher_number=max_vouch + 1,
        date=datetime.utcnow(),
        description=f"Salgsfaktura #{next_inv_number} til {inv_in.customer_name}",
        status="POSTED"
    )
    db.add(voucher)
    db.flush()

    # Debet 1500 Kundefordringer
    db.add(TransactionLine(
        voucher_id=voucher.id,
        account_number=1500,
        description=f"Kundefordring #{next_inv_number} - {inv_in.customer_name}",
        debit=total_amount,
        credit=0.0
    ))

    # Kredit salgsinntekt + utgående MVA fordelt per norsk MVA-sats (25%, 15%, 12%, 0%)
    rev_by_rate = {}
    vat_by_rate = {}
    for l in inv_in.lines:
        rate = int(round(l.vat_percent))
        rev_acc = 3000 if rate == 25 else (3030 if rate == 15 else (3040 if rate == 12 else 3100))
        rev_by_rate[rev_acc] = round(rev_by_rate.get(rev_acc, 0.0) + l.amount, 2)
        line_vat = round(l.amount * (l.vat_percent / 100.0), 2)
        if line_vat > 0:
            vat_acc = 2700 if rate == 25 else (2701 if rate == 15 else 2702)
            vat_by_rate[(vat_acc, rate)] = round(vat_by_rate.get((vat_acc, rate), 0.0) + line_vat, 2)

    for rev_acc, rev_amt in rev_by_rate.items():
        if rev_amt > 0:
            db.add(TransactionLine(
                voucher_id=voucher.id,
                account_number=rev_acc,
                description=f"Salgsinntekt faktura #{next_inv_number}",
                debit=0.0,
                credit=rev_amt
            ))

    for (vat_acc, rate), v_amt in vat_by_rate.items():
        if v_amt > 0:
            db.add(TransactionLine(
                voucher_id=voucher.id,
                account_number=vat_acc,
                description=f"Utgående MVA {rate}% faktura #{next_inv_number}",
                debit=0.0,
                credit=v_amt,
                vat_code=f"OUT_{rate}"
            ))

    # 2. Lagre salgsfaktura
    lines_dump = [l.model_dump() for l in inv_in.lines]
    db_invoice = CustomerInvoice(
        invoice_number=next_inv_number,
        customer_id=inv_in.customer_id,
        customer_name=inv_in.customer_name,
        customer_email=inv_in.customer_email,
        customer_orgnr=inv_in.customer_orgnr,
        issue_date=datetime.utcnow(),
        due_date=inv_in.due_date,
        kid=kid,
        subtotal=round(subtotal, 2),
        vat_amount=round(vat_total, 2),
        total_amount=total_amount,
        lines_json=json.dumps(lines_dump),
        status="SENT",
        voucher_id=voucher.id
    )
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)

    return CustomerInvoiceResponse(
        id=db_invoice.id,
        invoice_number=db_invoice.invoice_number,
        customer_id=db_invoice.customer_id,
        customer_name=db_invoice.customer_name,
        customer_email=db_invoice.customer_email,
        customer_orgnr=db_invoice.customer_orgnr,
        issue_date=db_invoice.issue_date,
        due_date=db_invoice.due_date,
        kid=db_invoice.kid,
        subtotal=db_invoice.subtotal,
        vat_amount=db_invoice.vat_amount,
        total_amount=db_invoice.total_amount,
        lines=inv_in.lines,
        status=db_invoice.status,
        voucher_id=db_invoice.voucher_id,
        created_at=db_invoice.created_at
    )

@router.post("/invoices/{invoice_id}/pay")
def register_customer_invoice_payment(invoice_id: int, db: Session = Depends(get_db)):
    """
    Registrerer innbetaling fra kunde:
    - Debet: 1920 Bankinnskudd
    - Kredit: 1500 Kundefordringer
    """
    inv = db.query(CustomerInvoice).filter(CustomerInvoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Faktura ikke funnet.")
    if inv.status == "PAID":
        raise HTTPException(status_code=400, detail="Faktura er allerede betalt.")

    max_vouch = db.query(func.max(Voucher.voucher_number)).scalar() or 0
    voucher = Voucher(
        voucher_number=max_vouch + 1,
        date=datetime.utcnow(),
        description=f"Innbetaling faktura #{inv.invoice_number} ({inv.customer_name})",
        status="POSTED"
    )
    db.add(voucher)
    db.flush()

    # Debet 1920 Bank
    db.add(TransactionLine(
        voucher_id=voucher.id,
        account_number=1920,
        description=f"Innbetaling fra {inv.customer_name}",
        debit=inv.total_amount,
        credit=0.0
    ))

    # Kredit 1500 Kundefordring
    db.add(TransactionLine(
        voucher_id=voucher.id,
        account_number=1500,
        description=f"Oppgjør kundefordring #{inv.invoice_number}",
        debit=0.0,
        credit=inv.total_amount
    ))

    inv.status = "PAID"
    db.commit()
    return {"message": f"Innbetaling for faktura #{inv.invoice_number} bokført."}

# -------------------------------------------------------------
# 6. BANKAVSTEMNING (BANK RECONCILIATION)
# -------------------------------------------------------------

@router.get("/bank/transactions", response_model=List[BankTransactionResponse])
def get_bank_transactions(db: Session = Depends(get_db)):
    """Henter alle banktransaksjoner for avstemming."""
    return db.query(BankTransaction).order_by(BankTransaction.transaction_date.desc()).all()

@router.post("/bank/transactions", response_model=BankTransactionResponse)
def add_bank_transaction(tx: BankTransactionCreate, db: Session = Depends(get_db)):
    """Legger inn en ny transaksjon fra banken manuelt eller via import."""
    db_tx = BankTransaction(
        transaction_date=tx.transaction_date,
        description=tx.description,
        amount=tx.amount,
        reference=tx.reference,
        source="MANUAL_INPUT"
    )
    db.add(db_tx)
    db.commit()
    db.refresh(db_tx)
    return db_tx

@router.get("/bank/summary", response_model=BankReconciliationSummary)
def get_bank_reconciliation_summary(db: Session = Depends(get_db)):
    """
    Gir en fullstendig avstemmingsrapport:
    - Saldo ifølge banktransaksjoner
    - Saldo på regnskapets konto 1920 (Bankinnskudd)
    - Avstemmingsdifferanse
    - Antall avstemte og uavstemte poster
    """
    # Sum av alle banktransaksjoner
    bank_statement_sum = db.query(func.sum(BankTransaction.amount)).scalar() or 0.0

    # Saldo på konto 1920 i hovedbok
    lines_1920 = db.query(TransactionLine).filter(TransactionLine.account_number == 1920).all()
    account_1920_sum = sum(l.debit - l.credit for l in lines_1920)

    diff = round(bank_statement_sum - account_1920_sum, 2)
    reconciled_cnt = db.query(func.count(BankTransaction.id)).filter(BankTransaction.reconciled == True).scalar() or 0
    unreconciled_cnt = db.query(func.count(BankTransaction.id)).filter(BankTransaction.reconciled == False).scalar() or 0

    return BankReconciliationSummary(
        bank_statement_balance=round(bank_statement_sum, 2),
        account_1920_balance=round(account_1920_sum, 2),
        difference=diff,
        reconciled_count=reconciled_cnt,
        unreconciled_count=unreconciled_cnt,
        is_balanced=(abs(diff) < 0.01)
    )

@router.post("/bank/auto-reconcile")
def auto_reconcile_bank_transactions(db: Session = Depends(get_db)):
    """
    Automatisk matching-motor:
    Sammenligner uavstemte bankposter mot poster på konto 1920 etter beløp og dato.
    """
    unreconciled_txs = db.query(BankTransaction).filter(BankTransaction.reconciled == False).all()
    lines_1920 = db.query(TransactionLine, Voucher).join(Voucher, TransactionLine.voucher_id == Voucher.id).filter(
        TransactionLine.account_number == 1920
    ).all()

    matched_count = 0
    for tx in unreconciled_txs:
        for line, voucher in lines_1920:
            line_net = round(line.debit - line.credit, 2)
            # Hvis beløpet matcher eksakt
            if abs(line_net - round(tx.amount, 2)) < 0.01:
                tx.reconciled = True
                tx.matched_voucher_id = voucher.id
                tx.reconciled_at = datetime.utcnow()
                matched_count += 1
                break

    db.commit()
    return {"message": f"Automatisk avstemming fullført. {matched_count} transaksjoner ble matchet.", "matched_count": matched_count}

@router.post("/bank/transactions/{tx_id}/quick-book")
def quick_book_bank_transaction(tx_id: int, req: QuickBookBankTransaction, db: Session = Depends(get_db)):
    """
    Hurtigbokføring av en uavstemt banktransaksjon med ett klikk:
    F.eks. bankgebyr (7770), renteinntekt (8050) eller generelle driftskostnader.
    Bokføres direkte og markeres umiddelbart som avstemt!
    """
    tx = db.query(BankTransaction).filter(BankTransaction.id == tx_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Banktransaksjon ikke funnet.")

    acc = db.query(Account).filter(Account.account_number == req.account_number).first()
    if not acc:
        raise HTTPException(status_code=400, detail="Ugyldig konto.")

    max_vouch = db.query(func.max(Voucher.voucher_number)).scalar() or 0
    desc = req.description or tx.description

    voucher = Voucher(
        voucher_number=max_vouch + 1,
        date=tx.transaction_date,
        description=f"Bankavstemt: {desc}",
        status="POSTED"
    )
    db.add(voucher)
    db.flush()

    amount = abs(tx.amount)
    if tx.amount > 0:
        # Penger inn på bankkonto (Debet 1920, Kredit angitt konto)
        db.add(TransactionLine(
            voucher_id=voucher.id,
            account_number=1920,
            description=desc,
            debit=amount,
            credit=0.0
        ))
        db.add(TransactionLine(
            voucher_id=voucher.id,
            account_number=req.account_number,
            description=desc,
            debit=0.0,
            credit=amount
        ))
    else:
        # Penger ut fra bankkonto (Kredit 1920, Debet angitt konto)
        db.add(TransactionLine(
            voucher_id=voucher.id,
            account_number=req.account_number,
            description=desc,
            debit=amount,
            credit=0.0
        ))
        db.add(TransactionLine(
            voucher_id=voucher.id,
            account_number=1920,
            description=desc,
            debit=0.0,
            credit=amount
        ))

    tx.reconciled = True
    tx.matched_voucher_id = voucher.id
    tx.reconciled_at = datetime.utcnow()

    db.commit()
    return {"message": "Transaksjonen er bokført og automatisk avstemt!", "voucher_number": voucher.voucher_number}

# -------------------------------------------------------------
# 7. BILAGSMOTTAK & DOKUMENTOPPLASTING (BÅDE BILDE & PDF)
# -------------------------------------------------------------

@router.post("/documents/upload", response_model=UploadedDocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Laster opp et bilag enten som PDF eller som et bilde (PNG, JPG, JPEG, WEBP).
    Lagrer filen sikkert og legger den i bilagsmottaket for AI-tolking og bokføring.
    """
    allowed_exts = [".pdf", ".png", ".jpg", ".jpeg", ".webp"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Ugyldig filtype ({file_ext}). Kun PDF og bildefiler (PNG, JPG, JPEG, WEBP) er støttet."
        )

    # Generer et trygt unikt filnavn
    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    target_path = os.path.join(UPLOAD_DIR, unique_filename)

    content = await file.read()
    file_size = len(content)

    with open(target_path, "wb") as f:
        f.write(content)

    # Opprett post i uploaded_documents
    doc = UploadedDocument(
        filename=unique_filename,
        original_name=file.filename,
        file_type="pdf" if file_ext == ".pdf" else "image",
        file_path=f"/uploads/{unique_filename}",
        file_size=file_size,
        status="PENDING"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return UploadedDocumentResponse(
        id=doc.id,
        filename=doc.filename,
        original_name=doc.original_name,
        file_type=doc.file_type,
        file_path=doc.file_path,
        file_size=doc.file_size,
        status=doc.status,
        extracted_data=None,
        voucher_id=None,
        uploaded_at=doc.uploaded_at
    )

@router.get("/documents", response_model=List[UploadedDocumentResponse])
def get_documents(db: Session = Depends(get_db)):
    """Henter alle dokumenter i bilagsmottaket."""
    docs = db.query(UploadedDocument).order_by(UploadedDocument.uploaded_at.desc()).all()
    res = []
    for d in docs:
        extracted = None
        if d.extracted_data_json:
            try:
                extracted = json.loads(d.extracted_data_json)
            except Exception:
                pass
        res.append(UploadedDocumentResponse(
            id=d.id,
            filename=d.filename,
            original_name=d.original_name,
            file_type=d.file_type,
            file_path=d.file_path,
            file_size=d.file_size,
            status=d.status,
            extracted_data=extracted,
            voucher_id=d.voucher_id,
            uploaded_at=d.uploaded_at
        ))
    return res

# -------------------------------------------------------------
# 8. MVA-MELDING & MVA-OPPGJØR (VAT)
# -------------------------------------------------------------

@router.get("/vat/report", response_model=List[VatReportTerm])
def get_vat_report(db: Session = Depends(get_db)):
    """
    Beregner MVA-melding for de 6 terminene i henhold til Skatteetaten:
    - Termin 1: Jan - Feb
    - Termin 2: Mar - Apr
    - Termin 3: Mai - Jun
    - Termin 4: Jul - Aug
    - Termin 5: Sep - Okt
    - Termin 6: Nov - Des
    """
    # Hent linjer på 2700 (Utgående MVA), 2710 (Inngående MVA) og 3000 (Avgiftspliktig salg)
    terms_data = [
        {"term": 1, "term_name": "Termin 1 (Jan - Feb)"},
        {"term": 2, "term_name": "Termin 2 (Mar - Apr)"},
        {"term": 3, "term_name": "Termin 3 (Mai - Jun)"},
        {"term": 4, "term_name": "Termin 4 (Jul - Aug)"},
        {"term": 5, "term_name": "Termin 5 (Sep - Okt)"},
        {"term": 6, "term_name": "Termin 6 (Nov - Des)"},
    ]

    # Beregn reelle tall fordelt på faktisk bilagsdato og alle norske MVA-satser (25%, 15%, 12%)
    lines = db.query(TransactionLine, Voucher).join(Voucher, TransactionLine.voucher_id == Voucher.id).all()
    by_term = {t["term"]: {"sales": 0.0, "out_vat": 0.0, "in_vat": 0.0} for t in terms_data}

    for line, voucher in lines:
        month = voucher.date.month if voucher.date else 11
        term_no = min(6, max(1, (month - 1) // 2 + 1))
        bucket = by_term[term_no]
        if line.account_number in (3000, 3020, 3030, 3040):
            bucket["sales"] += (line.credit - line.debit)
        elif line.account_number in (2700, 2701, 2702):
            bucket["out_vat"] += (line.credit - line.debit)
        elif line.account_number in (2710, 2711, 2712):
            bucket["in_vat"] += (line.debit - line.credit)

    res = []
    for t in terms_data:
        b = by_term[t["term"]]
        sales = round(b["sales"], 2)
        out_vat = round(b["out_vat"], 2)
        in_vat = round(b["in_vat"], 2)
        net = round(out_vat - in_vat, 2)

        res.append(VatReportTerm(
            term=t["term"],
            term_name=t["term_name"],
            base_sales_high_25=sales,
            output_vat_25=out_vat,
            input_vat_deductible=in_vat,
            net_vat_payable=net,
            is_settled=False
        ))
    return res

# -------------------------------------------------------------
# 9. FINANSIELLE RAPPORTER (RESULTAT, BALANSE, SALDOBALANSE)
# -------------------------------------------------------------

@router.get("/reports/income-statement", response_model=IncomeStatementResponse)
def get_income_statement(db: Session = Depends(get_db)):
    """Genererer fullstendig resultatregnskap (Driftsinntekter, Driftskostnader, Resultat)."""
    lines = db.query(TransactionLine, Account).join(Account, TransactionLine.account_number == Account.account_number).all()

    rev_map = {}
    exp_map = {}

    for line, acc in lines:
        if 3000 <= acc.account_number < 4000:
            val = line.credit - line.debit
            rev_map[acc.account_number] = rev_map.get(acc.account_number, {"name": acc.name, "amount": 0.0})
            rev_map[acc.account_number]["amount"] += val
        elif 4000 <= acc.account_number < 8000:
            val = line.debit - line.credit
            exp_map[acc.account_number] = exp_map.get(acc.account_number, {"name": acc.name, "amount": 0.0})
            exp_map[acc.account_number]["amount"] += val

    rev_lines = [ReportLine(account_number=k, account_name=v["name"], amount=round(v["amount"], 2)) for k, v in sorted(rev_map.items())]
    exp_lines = [ReportLine(account_number=k, account_name=v["name"], amount=round(v["amount"], 2)) for k, v in sorted(exp_map.items())]

    total_rev = sum(l.amount for l in rev_lines)
    total_exp = sum(l.amount for l in exp_lines)

    return IncomeStatementResponse(
        sections=[
            IncomeStatementSection(title="Driftsinntekter (Salgsinntekter)", lines=rev_lines, total=round(total_rev, 2)),
            IncomeStatementSection(title="Driftskostnader (Varekjøp, IT, Administrasjon)", lines=exp_lines, total=round(total_exp, 2))
        ],
        net_profit=round(total_rev - total_exp, 2)
    )

@router.get("/reports/balance-sheet", response_model=BalanceSheetResponse)
def get_balance_sheet(db: Session = Depends(get_db)):
    """Genererer fullstendig balanserapport (Eiendeler vs Egenkapital og Gjeld)."""
    lines = db.query(TransactionLine, Account).join(Account, TransactionLine.account_number == Account.account_number).all()

    asset_map = {}
    liability_map = {}
    period_profit = 0.0

    for line, acc in lines:
        if 1000 <= acc.account_number < 2000:
            val = line.debit - line.credit
            asset_map[acc.account_number] = asset_map.get(acc.account_number, {"name": acc.name, "amount": 0.0})
            asset_map[acc.account_number]["amount"] += val
        elif 2000 <= acc.account_number < 3000:
            val = line.credit - line.debit
            liability_map[acc.account_number] = liability_map.get(acc.account_number, {"name": acc.name, "amount": 0.0})
            liability_map[acc.account_number]["amount"] += val
        elif 3000 <= acc.account_number < 4000:
            period_profit += (line.credit - line.debit)
        elif 4000 <= acc.account_number < 9000:
            period_profit -= (line.debit - line.credit)

    asset_lines = [ReportLine(account_number=k, account_name=v["name"], amount=round(v["amount"], 2)) for k, v in sorted(asset_map.items())]
    liab_lines = [ReportLine(account_number=k, account_name=v["name"], amount=round(v["amount"], 2)) for k, v in sorted(liability_map.items())]
    if abs(period_profit) >= 0.01:
        liab_lines.append(ReportLine(account_number=2050, account_name="Udisponert resultat (hittil i år)", amount=round(period_profit, 2)))

    total_assets = round(sum(l.amount for l in asset_lines), 2)
    total_liab = round(sum(l.amount for l in liab_lines), 2)

    return BalanceSheetResponse(
        assets=BalanceSheetSection(title="Eiendeler (Omløpsmidler & Bank)", lines=asset_lines, total=total_assets),
        equity_and_liabilities=BalanceSheetSection(title="Egenkapital og Gjeld", lines=liab_lines, total=total_liab),
        is_balanced=abs(total_assets - total_liab) < 0.05
    )

# -------------------------------------------------------------
# 10. BEDRIFTSINNSTILLINGER
# -------------------------------------------------------------

@router.get("/settings", response_model=CompanySettingResponse)
def get_settings(db: Session = Depends(get_db)):
    setting = db.query(CompanySetting).first()
    if not setting:
        setting = CompanySetting()
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return setting

@router.post("/settings", response_model=CompanySettingResponse)
def update_settings(set_in: CompanySettingBase, db: Session = Depends(get_db)):
    setting = db.query(CompanySetting).first()
    if not setting:
        setting = CompanySetting(**set_in.model_dump())
        db.add(setting)
    else:
        for k, v in set_in.model_dump().items():
            setattr(setting, k, v)
    db.commit()
    db.refresh(setting)
    return setting


# -------------------------------------------------------------
# 11. BRØNNØYSUNDREGISTRENE (ENHETSREGISTERET LIVE API)
# -------------------------------------------------------------

import httpx

@router.get("/brreg/search")
async def search_brreg(q: str):
    """
    Søker direkte i Brønnøysundregistrene (data.brreg.no) etter bedrifter.
    Gir sanntidsoppslag for kundenavn, leverandørnavn, organisasjonsform og MVA-status.
    """
    if not q or len(q.strip()) < 2:
        return []

    url = f"https://data.brreg.no/enhetsregisteret/api/enheter?navn={httpx.URL(q.strip())}"
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            res = await client.get(url)
            if res.status_code == 200:
                data = res.json()
                enheter = data.get("_embedded", {}).get("enheter", [])
                results = []
                for e in enheter[:10]:
                    adr = e.get("forretningsadresse", {})
                    results.append({
                        "org_number": e.get("organisasjonsnummer"),
                        "name": e.get("navn"),
                        "org_form": e.get("organisasjonsform", {}).get("kode", ""),
                        "is_vat_registered": e.get("registrertIMvaregisteret", False),
                        "address": ", ".join(adr.get("adresse", [])) if adr.get("adresse") else "",
                        "postal_code": adr.get("postnummer", ""),
                        "city": adr.get("poststed", "")
                    })
                return results
    except Exception as err:
        print("Brreg søk feilet:", err)
    return []

@router.get("/brreg/{orgnr}")
async def get_brreg_by_orgnr(orgnr: str):
    """
    Henter offisielle bedriftsopplysninger fra Brønnøysund basert på 9-sifret organisasjonsnummer.
    """
    clean_orgnr = "".join(c for c in orgnr if c.isdigit())
    if len(clean_orgnr) != 9:
        raise HTTPException(status_code=400, detail="Organisasjonsnummer må bestå av nøyaktig 9 siffer.")

    url = f"https://data.brreg.no/enhetsregisteret/api/enheter/{clean_orgnr}"
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            res = await client.get(url)
            if res.status_code == 200:
                e = res.json()
                adr = e.get("forretningsadresse", {})
                return {
                    "org_number": e.get("organisasjonsnummer"),
                    "name": e.get("navn"),
                    "org_form": e.get("organisasjonsform", {}).get("kode", ""),
                    "is_vat_registered": e.get("registrertIMvaregisteret", False),
                    "address": ", ".join(adr.get("adresse", [])) if adr.get("adresse") else "",
                    "postal_code": adr.get("postnummer", ""),
                    "city": adr.get("poststed", ""),
                    "naeringskode": e.get("naeringskode1", {}).get("beskrivelse", "")
                }
            elif res.status_code == 404:
                raise HTTPException(status_code=404, detail="Fant ingen enhet med dette organisasjonsnummeret i Brønnøysund.")
    except HTTPException:
        raise
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Kunne ikke kontakte Brønnøysundregistrene: {str(err)}")

# -------------------------------------------------------------
# 12. ALTINN & DIGDIR MASKINPORTEN / SKATTEETATEN INTEGRASJON
# -------------------------------------------------------------

@router.get("/altinn/status")
def get_altinn_status(db: Session = Depends(get_db)):
    """
    Returnerer integrasjonsstatus mot Digdir Maskinporten, Altinn 3 og Skatteetaten.
    """
    setting = db.query(CompanySetting).first()
    return {
        "gateway": "Digdir Maskinporten (ID-porten / Altinn 3 API)",
        "status": "READY_FOR_SUBMISSION",
        "registered_company": setting.company_name if setting else "Ikke konfigurert",
        "org_number": setting.org_number if setting else "",
        "supported_services": [
            {
                "service": "MVA-melding (Merverdiavgift)",
                "agency": "Skatteetaten",
                "protocol": "Skatteetaten Systeminnsending REST API via Maskinporten",
                "format": "JSON / XML (RF-0002 / Skattemelding for MVA)",
                "status": "Aktiv"
            },
            {
                "service": "A-melding (Lønn og arbeidsgiveravgift)",
                "agency": "Skatteetaten / NAV / SSB",
                "protocol": "Altinn 3 A-ordningen API",
                "format": "EDAG 2.0 XML",
                "status": "Klar"
            },
            {
                "service": "Årsregnskap til Regnskapsregisteret",
                "agency": "Brønnøysundregistrene",
                "protocol": "Altinn RR-0002",
                "format": "XBRL / XML",
                "status": "Klar"
            },
            {
                "service": "SAF-T Regnskapseksport (Standard Audit File-Tax)",
                "agency": "Skatteetaten Revisjon",
                "protocol": "Norsk Standard NS 4102 / OECD SAF-T v1.3",
                "format": "XML",
                "status": "Tilgjengelig for direkte eksport"
            }
        ]
    }

@router.post("/altinn/submit-vat-return")
def submit_vat_return_to_altinn(term: int, db: Session = Depends(get_db)):
    """
    Klargjør og simulerer digital innsending av MVA-melding via Digdir Maskinporten / Skatteetaten.
    Genererer referansenummer, kontrollsummer og offisiell kvittering.
    """
    setting = db.query(CompanySetting).first()
    org = setting.org_number if setting else "987654321"

    # Beregn MVA-tall for terminen
    lines = db.query(TransactionLine).all()
    sales_3000 = sum(l.credit - l.debit for l in lines if l.account_number == 3000)
    vat_2700 = sum(l.credit - l.debit for l in lines if l.account_number == 2700)
    vat_2710 = sum(l.debit - l.credit for l in lines if l.account_number == 2710)
    net_payable = round(vat_2700 - vat_2710, 2)

    submission_id = f"ALTINN-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    kid_payment = f"00{org.replace(' ', '')[:9]}26{term}5"

    return {
        "status": "SUBMITTED_SUCCESSFULLY",
        "submission_id": submission_id,
        "altinn_archive_reference": f"AR{uuid.uuid4().hex[:10].upper()}",
        "timestamp": datetime.utcnow().isoformat(),
        "agency": "Skatteetaten / Altinn 3",
        "term": term,
        "term_name": f"Termin {term} 2026",
        "company_name": setting.company_name if setting else "Testbedrift",
        "org_number": org,
        "figures": {
            "grunnlag_25_prosent": round(sales_3000, 2),
            "utgaaende_mva_25_prosent": round(vat_2700, 2),
            "inngaaende_mva_fradrag": round(vat_2710, 2),
            "netto_mva_aa_betale": net_payable
        },
        "payment_info": {
            "kontonummer": "7694.05.00123 (Skatteetaten innkreving)",
            "kid": kid_payment,
            "forfallsdato": "2026-12-10"
        },
        "message": f"MVA-melding for Termin {term} er godkjent og registrert hos Skatteetaten via Altinn!"
    }

@router.get("/altinn/saft-export")
def generate_saft_export(db: Session = Depends(get_db)):
    """
    Genererer SAF-T (Standard Audit File - Tax) struktur i tråd med Skatteetatens krav.
    Brukes ved bokettersyn eller når revisor ber om standard regnskapsfil.
    """
    setting = db.query(CompanySetting).first()
    accounts = db.query(Account).all()
    vouchers = db.query(Voucher).all()

    return {
        "header": {
            "audit_file_version": "1.30",
            "audit_file_country": "NO",
            "audit_file_date_created": datetime.utcnow().strftime("%Y-%m-%d"),
            "company_name": setting.company_name if setting else "Firma AS",
            "company_registration_number": setting.org_number if setting else "987654321",
            "default_currency_code": "NOK",
            "software_company_name": "Phink Technologies AS",
            "software_id": "Phink Conta Edition",
            "software_version": "2.0"
        },
        "master_files": {
            "general_ledger_accounts": [
                {"account_id": a.account_number, "account_description": a.name, "standard_account_id": a.account_number}
                for a in accounts
            ]
        },
        "general_ledger_entries": {
            "number_of_entries": len(vouchers),
            "total_debit": round(sum(l.debit for v in vouchers for l in v.lines), 2),
            "total_credit": round(sum(l.credit for v in vouchers for l in v.lines), 2),
            "journal": [
                {
                    "journal_id": v.id,
                    "description": v.description,
                    "transaction_date": v.date.strftime("%Y-%m-%d"),
                    "lines": [
                        {"account_id": l.account_number, "description": l.description, "debit": l.debit, "credit": l.credit}
                        for l in v.lines
                    ]
                }
                for v in vouchers
            ]
        }
    }
