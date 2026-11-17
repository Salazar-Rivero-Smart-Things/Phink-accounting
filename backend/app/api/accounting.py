from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app.database import get_db
from app.models.accounting import Account, Voucher, TransactionLine, AuditLog
from app.schemas.accounting import (
    AccountResponse, AccountCreate,
    VoucherResponse, VoucherCreate,
    FinancialSummary
)

router = APIRouter(prefix="/accounting", tags=["Accounting"])

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
    # Finn neste bilagsnummer
    max_num = db.query(func.max(Voucher.voucher_number)).scalar() or 0
    next_voucher_number = max_num + 1

    db_voucher = Voucher(
        voucher_number=next_voucher_number,
        date=voucher_in.date,
        description=voucher_in.description,
        source_document=voucher_in.source_document,
        status="POSTED"
    )
    db.add(db_voucher)
    db.flush()  # Få ID til bilaget

    for line in voucher_in.lines:
        # Sjekk om konto finnes
        acc = db.query(Account).filter(Account.account_number == line.account_number).first()
        if not acc:
            raise HTTPException(status_code=400, detail=f"Konto {line.account_number} finnes ikke i kontoplanen.")
        
        db_line = TransactionLine(
            voucher_id=db_voucher.id,
            account_number=line.account_number,
            description=line.description or voucher_in.description,
            debit=line.debit,
            credit=line.credit
        )
        db.add(db_line)

    # Revisjonsspor
    audit = AuditLog(
        action="POST_VOUCHER",
        details=f"Bilag #{next_voucher_number} bokført. Beskrivelse: {voucher_in.description}",
        ai_assisted=False
    )
    db.add(audit)

    db.commit()
    db.refresh(db_voucher)
    return db_voucher

@router.get("/summary", response_model=FinancialSummary)
def get_financial_summary(db: Session = Depends(get_db)):
    """
    Beregner sanntids nøkkeltall for dashbordet:
    - Inntekt (Konto 3000-3999)
    - Kostnader (Konto 4000-7999)
    - Driftsresultat (Inntekt - Kostnader)
    - Bankinnskudd (Konto 1920)
    """
    # Hent alle linjer koblet til kontoer
    lines = db.query(TransactionLine, Account).join(Account, TransactionLine.account_number == Account.account_number).all()

    total_revenue = 0.0
    total_expenses = 0.0
    bank_balance = 0.0

    for line, account in lines:
        if 3000 <= account.account_number < 4000:
            # Inntekter krediteres normalt
            total_revenue += (line.credit - line.debit)
        elif 4000 <= account.account_number < 8000:
            # Kostnader debiteres normalt
            total_expenses += (line.debit - line.credit)
        elif account.account_number == 1920:
            # Bankkonto (Debet øker, kredit reduserer)
            bank_balance += (line.debit - line.credit)

    net_income = total_revenue - total_expenses
    voucher_count = db.query(func.count(Voucher.id)).scalar() or 0

    return FinancialSummary(
        total_revenue=round(total_revenue, 2),
        total_expenses=round(total_expenses, 2),
        net_income=round(net_income, 2),
        bank_balance=round(bank_balance, 2),
        voucher_count=voucher_count
    )
