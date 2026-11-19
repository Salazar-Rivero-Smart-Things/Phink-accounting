from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime, timedelta
import json
import uuid

from app.database import get_db
from app.models.accounting import (
    CompanySetting, CustomerInvoice, Voucher, TransactionLine, SubscriptionOrder, AuditLog
)
from app.api.auth import is_owner_email

router = APIRouter(prefix="/billing", tags=["Billing (Vipps Bedrift & Faktura)"])

ALLOWED_METHODS = {"VIPPS_BEDRIFT", "FAKTURA"}

PLANS = [
    {
        "id": "PHINK_STANDARD",
        "name": "Phink Komplett (Ubegrenset bilag)",
        "description": "Alt inkludert: norsk regnskap (NS 4102), ubegrenset bilag, faktura med MVA & automatisk KID-føring, lønnskjøring, bilagsarkiv, varslinger, AI CFO og kundeservice. Ingen skjulte avgifter.",
        "price_ex_vat": 299.0,
        "vat_percent": 25,
    },
]

ADDONS = {
    "BANK_INTEGRATION": {
        "id": "BANK_INTEGRATION",
        "name": "Bankintegrasjon (innlogging & automatisk bank/KID-synk)",
        "price_ex_vat": 59.0,
        "billing": "monthly",
    },
    "KID_AUTOMATION": {
        "id": "KID_AUTOMATION",
        "name": "KID-automatisasjon (automatisk KID-matching & bokføring)",
        "price_ex_vat": 3.0,
        "billing": "per_invoice",
    },
    "SAFT_IMPORT": {
        "id": "SAFT_IMPORT",
        "name": "SAF-T XML filimport (fra Conta, Fiken, Tripletex m.fl.)",
        "price_ex_vat": 79.0,
        "billing": "one_time",
    },
}


class CheckoutRequest(BaseModel):
    plan_id: str = Field(default="PHINK_STANDARD", description="PHINK_STANDARD")
    payment_method: str = Field(..., description="KUN VIPPS_BEDRIFT eller FAKTURA")
    customer_name: str = Field(..., min_length=2, max_length=200)
    customer_email: str = Field(..., min_length=4, max_length=150)
    org_number: Optional[str] = None
    include_bank_integration: bool = False
    include_saft_import: bool = False


class VippsConfigUpdate(BaseModel):
    vipps_number: str = Field(..., min_length=4, max_length=50)


@router.get("/plans")
def get_plans(db: Session = Depends(get_db)):
    setting = db.query(CompanySetting).first()
    enriched = []
    for p in PLANS:
        vat = round(p["price_ex_vat"] * (p["vat_percent"] / 100.0), 2)
        enriched.append({
            **p,
            "vat_amount": vat,
            "total_inc_vat": round(p["price_ex_vat"] + vat, 2),
        })
    return {
        "currency": "NOK",
        "allowed_payment_methods": [
            {"id": "VIPPS_BEDRIFT", "label": "Vipps Bedrift", "description": "Rask og trygg betaling med Vipps Bedrift"},
            {"id": "FAKTURA", "label": "Tilsendt faktura (14 dager)", "description": "Offisiell norsk faktura med KID og 25 % MVA sendt til e-post"},
        ],
        "vipps_number": setting.vipps_number if setting else "",
        "bank_account": setting.bank_account if setting else "1234.56.78903",
        "plans": enriched,
        "addons": list(ADDONS.values()),
    }


@router.post("/vipps-config")
def update_vipps_config(req: VippsConfigUpdate, db: Session = Depends(get_db)):
    setting = db.query(CompanySetting).first()
    if not setting:
        setting = CompanySetting()
        db.add(setting)
    setting.vipps_number = req.vipps_number.strip()
    setting.allowed_payment_methods = "VIPPS_BEDRIFT,FAKTURA"
    db.commit()
    return {"ok": True, "vipps_number": setting.vipps_number}


@router.post("/checkout")
def create_payment_order(req: CheckoutRequest, db: Session = Depends(get_db)):
    """
    Oppretter betaling KUN via Vipps Bedrift eller tilsendt norsk faktura (25 % MVA).
    """
    method = (req.payment_method or "").strip().upper()
    if method not in ALLOWED_METHODS:
        raise HTTPException(
            status_code=400,
            detail="Ugyldig betalingsmetode. Phink Accounting tar kun imot Vipps Bedrift (VIPPS_BEDRIFT) eller tilsendt faktura (FAKTURA).",
        )

    plan = next((p for p in PLANS if p["id"] == req.plan_id.strip().upper()), PLANS[0])

    # Eier / Administrator har alltid gratis ubegrenset tilgang uten betaling
    if is_owner_email(req.customer_email):
        return {
            "ok": True,
            "order_id": None,
            "payment_method": "ADMIN_FREE",
            "plan_name": f"{plan['name']} (Gratis Administrator-konto)",
            "amount_ex_vat": 0.0,
            "vat_amount": 0.0,
            "total_amount": 0.0,
            "payment_reference": "ADMIN-EXEMPT",
            "status": "PAID",
            "billing_exempt": True,
            "instructions": "Du er registrert som Administrator & Eier — kontoen din har ubegrenset tilgang helt gratis (0 kr).",
        }

    setting = db.query(CompanySetting).first()
    vipps_no = (setting.vipps_number if setting and setting.vipps_number else "Oppgis i Innstillinger")

    addon_labels = []
    subtotal = round(plan["price_ex_vat"], 2)
    if req.include_bank_integration:
        subtotal = round(subtotal + ADDONS["BANK_INTEGRATION"]["price_ex_vat"], 2)
        addon_labels.append("Bankintegrasjon (+59 kr)")
    if req.include_saft_import:
        subtotal = round(subtotal + ADDONS["SAFT_IMPORT"]["price_ex_vat"], 2)
        addon_labels.append("SAF-T import (+79 kr)")
    plan_label = plan["name"] + (f" + {', '.join(addon_labels)}" if addon_labels else "")
    vat_amount = round(subtotal * (plan["vat_percent"] / 100.0), 2)
    total = round(subtotal + vat_amount, 2)
    now = datetime.utcnow()
    due_date = now + timedelta(days=14)

    invoice_id = None
    invoice_number = None

    if method == "FAKTURA":
        max_inv = db.query(func.max(CustomerInvoice.invoice_number)).scalar() or 1000
        invoice_number = max_inv + 1
        payment_ref = f"2026{invoice_number}7"

        # Bokfør utgående salgsfaktura i hovedbok (Debet 1500, Kredit 3000 + 2700)
        max_vouch = db.query(func.max(Voucher.voucher_number)).scalar() or 0
        voucher = Voucher(
            voucher_number=max_vouch + 1,
            date=now,
            description=f"Abonnementsfaktura #{invoice_number} ({plan['name']}) til {req.customer_name}",
            department_code="SALG",
            project_code="FELLES",
            status="POSTED",
        )
        db.add(voucher)
        db.flush()
        db.add(TransactionLine(voucher_id=voucher.id, account_number=1500, description=f"Kundefordring #{invoice_number}", debit=total, credit=0.0))
        db.add(TransactionLine(voucher_id=voucher.id, account_number=3000, description=f"Abonnement {plan['name']}", debit=0.0, credit=subtotal))
        db.add(TransactionLine(voucher_id=voucher.id, account_number=2700, description="Utgående MVA 25%", debit=0.0, credit=vat_amount, vat_code="OUT_25"))

        inv = CustomerInvoice(
            invoice_number=invoice_number,
            customer_name=req.customer_name.strip(),
            customer_email=req.customer_email.strip(),
            customer_orgnr=req.org_number,
            issue_date=now,
            due_date=due_date,
            kid=payment_ref,
            subtotal=subtotal,
            vat_amount=vat_amount,
            total_amount=total,
            lines_json=json.dumps([{
                "description": f"{plan['name']} (månedlig abonnement)",
                "quantity": 1,
                "unit_price": subtotal,
                "vat_percent": 25,
                "amount": subtotal,
            }]),
            status="SENT",
            voucher_id=voucher.id,
        )
        db.add(inv)
        db.flush()
        invoice_id = inv.id
        status = "INVOICE_SENT"
    else:
        payment_ref = f"PHINK-{uuid.uuid4().hex[:8].upper()}"
        status = "PENDING"

    order = SubscriptionOrder(
        customer_name=req.customer_name.strip(),
        customer_email=req.customer_email.strip(),
        org_number=req.org_number,
        plan_id=plan["id"],
        plan_name=plan_label,
        payment_method=method,
        amount_ex_vat=subtotal,
        vat_amount=vat_amount,
        total_amount=total,
        vipps_number=vipps_no if method == "VIPPS_BEDRIFT" else None,
        payment_reference=payment_ref,
        invoice_id=invoice_id,
        status=status,
        due_date=due_date,
    )
    db.add(order)
    db.add(AuditLog(
        action="BILLING_ORDER",
        details=f"Ordre opprettet via {method}: {plan['name']} ({total} NOK inkl. MVA) for {req.customer_name} (Ref: {payment_ref})",
        ai_assisted=False,
    ))
    db.commit()
    db.refresh(order)

    return {
        "ok": True,
        "order_id": order.id,
        "payment_method": method,
        "plan_name": plan["name"],
        "amount_ex_vat": subtotal,
        "vat_amount": vat_amount,
        "total_amount": total,
        "vipps_number": order.vipps_number,
        "bank_account": setting.bank_account if setting else "1234.56.78903",
        "payment_reference": payment_ref,
        "invoice_number": invoice_number,
        "due_date": due_date.strftime("%Y-%m-%d"),
        "status": order.status,
        "instructions": (
            f"Betal {total:,.2f} kr til Vipps Bedrift nr. {vipps_no} og merk betalingen med '{payment_ref}'."
            if method == "VIPPS_BEDRIFT"
            else f"Faktura #{invoice_number} på {total:,.2f} kr (inkl. 25 % MVA) er opprettet og bokført. KID: {payment_ref}, forfall: {due_date.strftime('%Y-%m-%d')}."
        ),
    }


@router.get("/orders")
def list_orders(db: Session = Depends(get_db)):
    rows = db.query(SubscriptionOrder).order_by(SubscriptionOrder.created_at.desc()).all()
    return [
        {
            "id": o.id,
            "customer_name": o.customer_name,
            "customer_email": o.customer_email,
            "org_number": o.org_number,
            "plan_id": o.plan_id,
            "plan_name": o.plan_name,
            "payment_method": o.payment_method,
            "amount_ex_vat": o.amount_ex_vat,
            "vat_amount": o.vat_amount,
            "total_amount": o.total_amount,
            "vipps_number": o.vipps_number,
            "payment_reference": o.payment_reference,
            "invoice_id": o.invoice_id,
            "status": o.status,
            "due_date": o.due_date.isoformat() if o.due_date else None,
            "paid_at": o.paid_at.isoformat() if o.paid_at else None,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }
        for o in rows
    ]


@router.post("/orders/{order_id}/mark-paid")
def mark_order_paid(order_id: int, db: Session = Depends(get_db)):
    order = db.query(SubscriptionOrder).filter(SubscriptionOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Ordre ikke funnet.")
    if order.status == "PAID":
        raise HTTPException(status_code=400, detail="Ordren er allerede betalt.")

    now = datetime.utcnow()
    max_vouch = db.query(func.max(Voucher.voucher_number)).scalar() or 0
    voucher = Voucher(
        voucher_number=max_vouch + 1,
        date=now,
        description=f"Betaling mottatt ({order.payment_method}) - {order.plan_name} ({order.customer_name}, ref {order.payment_reference})",
        department_code="SALG",
        project_code="FELLES",
        status="POSTED",
    )
    db.add(voucher)
    db.flush()

    if order.invoice_id:
        # Oppgjør av kundefordring: Debet 1920 Bank, Kredit 1500 Kundefordringer
        db.add(TransactionLine(voucher_id=voucher.id, account_number=1920, description=f"Innbetaling faktura {order.payment_reference}", debit=order.total_amount, credit=0.0))
        db.add(TransactionLine(voucher_id=voucher.id, account_number=1500, description=f"Oppgjør {order.customer_name}", debit=0.0, credit=order.total_amount))
        inv = db.query(CustomerInvoice).filter(CustomerInvoice.id == order.invoice_id).first()
        if inv:
            inv.status = "PAID"
    else:
        # Direkte Vipps Bedrift innbetaling: Debet 1920 Bank, Kredit 3000 Salg + 2700 Utgående MVA 25%
        db.add(TransactionLine(voucher_id=voucher.id, account_number=1920, description=f"Vipps Bedrift {order.payment_reference}", debit=order.total_amount, credit=0.0))
        db.add(TransactionLine(voucher_id=voucher.id, account_number=3000, description=f"Abonnement {order.plan_name}", debit=0.0, credit=order.amount_ex_vat))
        db.add(TransactionLine(voucher_id=voucher.id, account_number=2700, description="Utgående MVA 25% (Vipps)", debit=0.0, credit=order.vat_amount, vat_code="OUT_25"))

    order.status = "PAID"
    order.paid_at = now
    db.commit()
    return {"ok": True, "voucher_number": voucher.voucher_number, "status": "PAID"}


@router.get("/monthly-reminders")
def get_monthly_invoice_reminders(db: Session = Depends(get_db)):
    """
    Sjekker hvilke månedlige faktura-kunder som mangler faktura for inneværende måned (YYYY-MM),
    slik at programmet minner deg på å sende faktura hver måned!
    """
    now = datetime.utcnow()
    current_month = now.strftime("%Y-%m")
    all_orders = db.query(SubscriptionOrder).order_by(SubscriptionOrder.created_at.desc()).all()

    latest_by_email = {}
    billed_this_month = set()
    for o in all_orders:
        key = (o.customer_email or "").strip().lower()
        if not key or is_owner_email(key):
            continue
        if o.created_at and o.created_at.strftime("%Y-%m") == current_month:
            billed_this_month.add(key)
        if key not in latest_by_email:
            latest_by_email[key] = o

    due_customers = []
    for email, last_order in latest_by_email.items():
        if email not in billed_this_month:
            due_customers.append({
                "customer_name": last_order.customer_name,
                "customer_email": last_order.customer_email,
                "org_number": last_order.org_number,
                "plan_id": last_order.plan_id,
                "plan_name": last_order.plan_name,
                "payment_method": last_order.payment_method,
                "total_amount": last_order.total_amount,
                "last_billed_at": last_order.created_at.strftime("%Y-%m-%d") if last_order.created_at else None,
            })

    return {
        "month": current_month,
        "billed_this_month_count": len(billed_this_month),
        "due_count": len(due_customers),
        "due_customers": due_customers,
        "needs_monthly_action": len(due_customers) > 0 or len(billed_this_month) == 0,
    }


@router.post("/send-monthly-invoices")
def send_due_monthly_invoices(db: Session = Depends(get_db)):
    """
    Oppretter og bokfører månedens fakturaer med 1 klikk for alle abonnementskunder
    som ikke har fått faktura denne måneden ennå.
    """
    reminder_info = get_monthly_invoice_reminders(db)
    created = []
    for cust in reminder_info["due_customers"]:
        res = create_payment_order(
            CheckoutRequest(
                plan_id=cust["plan_id"],
                payment_method="FAKTURA",
                customer_name=cust["customer_name"],
                customer_email=cust["customer_email"],
                org_number=cust["org_number"],
            ),
            db=db,
        )
        created.append(res)
    return {
        "ok": True,
        "month": reminder_info["month"],
        "created_count": len(created),
        "invoices": created,
    }
