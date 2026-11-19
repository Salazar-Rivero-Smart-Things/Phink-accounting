import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.accounting import (
    Account, Voucher, TransactionLine,
    Supplier, SupplierInvoice,
    Customer, CustomerInvoice,
    BankTransaction, CompanySetting
)

def seed_enterprise_demo_data(db: Session):
    """
    Fyller databasen med et realistisk utvalg leverandører, kunder,
    fakturaer og banktransaksjoner for bankavstemning.
    """
    # 1. Bedriftsinnstillinger
    existing_setting = db.query(CompanySetting).first()
    if not existing_setting:
        setting = CompanySetting(
            company_name="Nordic Tech Solutions AS",
            org_number="987 654 321 MVA",
            bank_account="1503.22.88991",
            vat_registered=True,
            address="Dronning Eufemias gate 16",
            postal_code="0191",
            city="Oslo",
            email="okonomi@nordictech.no",
            phone="+47 21 55 40 00"
        )
        db.add(setting)

    # 2. Leverandører
    if db.query(Supplier).count() == 0:
        suppliers = [
            Supplier(
                name="Google Cloud EMEA Ltd",
                org_number="IE6388047V",
                account_number="1503.01.99281",
                kid_prefix="9910",
                email="billing@google.com",
                phone="+353 1 436 1000",
                default_expense_account=6540,
                payment_terms_days=30
            ),
            Supplier(
                name="Telenor Norge AS",
                org_number="988 568 288",
                account_number="7050.05.01015",
                kid_prefix="1002",
                email="bedrift@telenor.no",
                phone="09000",
                default_expense_account=6900,
                payment_terms_days=14
            ),
            Supplier(
                name="Elkjøp Bedrift AS",
                org_number="947 186 648",
                account_number="1503.44.11223",
                kid_prefix="5540",
                email="bedrift@elkjop.no",
                phone="+47 21 00 21 21",
                default_expense_account=6800,
                payment_terms_days=14
            ),
            Supplier(
                name="DNB Bank ASA",
                org_number="984 851 006",
                account_number="1503.00.00001",
                kid_prefix="7770",
                email="kundeservice@dnb.no",
                phone="915 04800",
                default_expense_account=7770,
                payment_terms_days=0
            )
        ]
        db.add_all(suppliers)
        db.flush()

        # Eksempel leverandørfaktura
        sup1 = suppliers[0] # Google
        inv1 = SupplierInvoice(
            supplier_id=sup1.id,
            supplier_name=sup1.name,
            invoice_number="INV-2026-9012",
            kid="9910202601",
            issue_date=datetime.utcnow() - timedelta(days=12),
            due_date=datetime.utcnow() + timedelta(days=18),
            amount_ex_vat=1160.0,
            vat_amount=290.0,
            total_amount=1450.0,
            expense_account=6540,
            status="PAID"
        )
        db.add(inv1)

        sup2 = suppliers[1] # Telenor
        inv2 = SupplierInvoice(
            supplier_id=sup2.id,
            supplier_name=sup2.name,
            invoice_number="TEL-889102",
            kid="1002889102",
            issue_date=datetime.utcnow() - timedelta(days=5),
            due_date=datetime.utcnow() + timedelta(days=9),
            amount_ex_vat=719.2,
            vat_amount=179.8,
            total_amount=899.0,
            expense_account=6900,
            status="UNPAID"
        )
        db.add(inv2)

    # 3. Kunder
    if db.query(Customer).count() == 0:
        customers = [
            Customer(
                name="Fjord Design Studio AS",
                org_number="912 345 678",
                email="faktura@fjorddesign.no",
                phone="+47 55 12 34 56",
                address="Bryggen 15, 5003 Bergen",
                payment_terms_days=14
            ),
            Customer(
                name="Bergen Konsulentgruppe AS",
                org_number="923 456 789",
                email="regnskap@bergen-kg.no",
                phone="+47 55 99 88 77",
                address="Strandgaten 88, 5004 Bergen",
                payment_terms_days=14
            ),
            Customer(
                name="Oslo Håndverksservice AS",
                org_number="934 567 890",
                email="post@oslohandverk.no",
                phone="+47 22 11 22 33",
                address="Grensen 12, 0159 Oslo",
                payment_terms_days=14
            )
        ]
        db.add_all(customers)
        db.flush()

        # Eksempel kundefaktura
        c1 = customers[0]
        cinv1 = CustomerInvoice(
            invoice_number=1001,
            customer_id=c1.id,
            customer_name=c1.name,
            customer_email=c1.email,
            customer_orgnr=c1.org_number,
            issue_date=datetime.utcnow() - timedelta(days=10),
            due_date=datetime.utcnow() + timedelta(days=4),
            kid="202610019",
            subtotal=15000.0,
            vat_amount=3750.0,
            total_amount=18750.0,
            status="PAID",
            lines_json=json.dumps([
                {"description": "Konsulentbistand systemarkitektur (15 timer)", "quantity": 15, "unit_price": 1000.0, "vat_percent": 25.0, "amount": 15000.0}
            ])
        )
        db.add(cinv1)

        c2 = customers[1]
        cinv2 = CustomerInvoice(
            invoice_number=1002,
            customer_id=c2.id,
            customer_name=c2.name,
            customer_email=c2.email,
            customer_orgnr=c2.org_number,
            issue_date=datetime.utcnow() - timedelta(days=2),
            due_date=datetime.utcnow() + timedelta(days=12),
            kid="202610027",
            subtotal=24000.0,
            vat_amount=6000.0,
            total_amount=30000.0,
            status="SENT",
            lines_json=json.dumps([
                {"description": "Utvikling av integrasjonsmodul", "quantity": 1, "unit_price": 24000.0, "vat_percent": 25.0, "amount": 24000.0}
            ])
        )
        db.add(cinv2)

    # 4. Banktransaksjoner for Bankavstemning
    if db.query(BankTransaction).count() == 0:
        bank_txs = [
            BankTransaction(
                transaction_date=datetime.utcnow() - timedelta(days=3),
                description="Innbetaling fra Fjord Design Studio AS",
                amount=18750.0,
                reference="KID 202610019",
                reconciled=False,
                source="DNB Bedriftsnettbank (CSV)"
            ),
            BankTransaction(
                transaction_date=datetime.utcnow() - timedelta(days=5),
                description="Google Ireland Ltd - Skylisenser",
                amount=-1450.0,
                reference="INV-2026-9012",
                reconciled=False,
                source="DNB Bedriftsnettbank (CSV)"
            ),
            BankTransaction(
                transaction_date=datetime.utcnow() - timedelta(days=6),
                description="DNB Bank ASA - Månedlig gebyr bedriftsavtale",
                amount=-125.0,
                reference="GEBYR-NOV",
                reconciled=False,
                source="DNB Bedriftsnettbank (CSV)"
            ),
            BankTransaction(
                transaction_date=datetime.utcnow() - timedelta(days=8),
                description="Renter godskrevet driftskonto",
                amount=385.50,
                reference="RENTER-Q4",
                reconciled=False,
                source="DNB Bedriftsnettbank (CSV)"
            )
        ]
        db.add_all(bank_txs)

    db.commit()
