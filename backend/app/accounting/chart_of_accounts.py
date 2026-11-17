from sqlalchemy.orm import Session
from app.models.accounting import Account

# Norsk Standard Kontoplan (NS 4102) - Standard utvalg for SMB / AS / ENK
DEFAULT_ACCOUNTS = [
    # 1xxx: Eiendeler
    {"account_number": 1920, "name": "Bankinnskudd drift", "account_type": "ASSET", "vat_code": "NONE", "description": "Hovedkonto bank"},
    {"account_number": 1500, "name": "Kundefordringer", "account_type": "ASSET", "vat_code": "NONE", "description": "Utestående fakturaer til kunder"},
    {"account_number": 1200, "name": "Maskiner og inventar", "account_type": "ASSET", "vat_code": "HIGH_25", "description": "Varige driftsmidler"},
    
    # 2xxx: Egenkapital og gjeld
    {"account_number": 2000, "name": "Egenkapital", "account_type": "EQUITY", "vat_code": "NONE", "description": "Selskapets egenkapital"},
    {"account_number": 2400, "name": "Leverandørgjeld", "account_type": "LIABILITY", "vat_code": "NONE", "description": "Ubetalte regninger til leverandører"},
    {"account_number": 2710, "name": "Utgående merverdiavgift (25%)", "account_type": "LIABILITY", "vat_code": "HIGH_25", "description": "MVA krevd inn fra kunder"},
    {"account_number": 2740, "name": "Oppgjørskonto merverdiavgift", "account_type": "LIABILITY", "vat_code": "NONE", "description": "MVA-oppgjør mot Skatteetaten"},
    
    # 3xxx: Inntekter
    {"account_number": 3000, "name": "Salgsinntekt (25% mva)", "account_type": "REVENUE", "vat_code": "HIGH_25", "description": "Salg av varer og tjenester med høy sats"},
    {"account_number": 3100, "name": "Salgsinntekt (avgiftsfri)", "account_type": "REVENUE", "vat_code": "NONE", "description": "Avgiftsfritt salg / eksport"},
    {"account_number": 3200, "name": "Salgsinntekt (15% mva)", "account_type": "REVENUE", "vat_code": "MED_15", "description": "Næringsmidler og mat"},
    
    # 4xxx: Varekostnad
    {"account_number": 4300, "name": "Innkjøp av varer for videresalg", "account_type": "EXPENSE", "vat_code": "HIGH_25", "description": "Varekjøp"},
    
    # 6xxx: Driftskostnader (IT, lokaler, kontor)
    {"account_number": 6300, "name": "Leie lokaler", "account_type": "EXPENSE", "vat_code": "NONE", "description": "Husleie for kontor/lager"},
    {"account_number": 6540, "name": "IT-drift, programvare og skylisenser", "account_type": "EXPENSE", "vat_code": "HIGH_25", "description": "SaaS, servere, programvare"},
    {"account_number": 6800, "name": "Kontorrekvisita og trykksaker", "account_type": "EXPENSE", "vat_code": "HIGH_25", "description": "Småanskaffelser til kontor"},
    {"account_number": 6900, "name": "Telefon og internett", "account_type": "EXPENSE", "vat_code": "HIGH_25", "description": "Bredbånd og mobilabonnement"},
    
    # 7xxx: Salg, reise og andre kostnader
    {"account_number": 7140, "name": "Reisekostnad / diett", "account_type": "EXPENSE", "vat_code": "NONE", "description": "Tjenestereiser og transport"},
    {"account_number": 7320, "name": "Reklame og annonsering", "account_type": "EXPENSE", "vat_code": "HIGH_25", "description": "Google Ads, sosiale medier, markedsføring"},
    {"account_number": 7770, "name": "Bank- og kortgebyrer", "account_type": "EXPENSE", "vat_code": "NONE", "description": "Transaksjonsgebyrer bank"},
    
    # 8xxx: Finansposter
    {"account_number": 8050, "name": "Renteinntekter", "account_type": "REVENUE", "vat_code": "NONE", "description": "Renter på bankinnskudd"},
    {"account_number": 8150, "name": "Rentekostnader", "account_type": "EXPENSE", "vat_code": "NONE", "description": "Lånerenter og forsinkelsesrenter"}
]

def seed_default_accounts(db: Session):
    """Sikrer at standard kontoplan er opprettet i databasen ved oppstart."""
    for item in DEFAULT_ACCOUNTS:
        existing = db.query(Account).filter(Account.account_number == item["account_number"]).first()
        if not existing:
            account = Account(**item)
            db.add(account)
    db.commit()
