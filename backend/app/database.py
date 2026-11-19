from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# SQLite needs check_same_thread=False for multithreaded FastAPI requests
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_schema_migrations():
    """
    Sikrer at eksisterende SQLite/PostgreSQL-databaser får nye kolonner
    uten å slette eksisterende bilag eller kundedata.
    """
    insp = inspect(engine)
    existing_tables = set(insp.get_table_names())

    migrations = {
        "vouchers": [
            ("department_code", "VARCHAR(50)"),
            ("project_code", "VARCHAR(50)"),
        ],
        "transaction_lines": [
            ("department_code", "VARCHAR(50)"),
            ("project_code", "VARCHAR(50)"),
            ("vat_code", "VARCHAR(20)"),
        ],
        "supplier_invoices": [
            ("vat_rate_percent", "INTEGER DEFAULT 25"),
            ("department_code", "VARCHAR(50)"),
            ("project_code", "VARCHAR(50)"),
        ],
        "customer_invoices": [
            ("department_code", "VARCHAR(50)"),
            ("project_code", "VARCHAR(50)"),
        ],
        "company_settings": [
            ("entity_type", "VARCHAR(30) DEFAULT 'AS'"),
            ("national_id", "VARCHAR(20)"),
            ("aga_zone", "INTEGER DEFAULT 1"),
            ("logo_url", "VARCHAR(500)"),
            ("marketing_image_url", "VARCHAR(500)"),
            ("vipps_number", "VARCHAR(50) DEFAULT ''"),
            ("allowed_payment_methods", "VARCHAR(100) DEFAULT 'VIPPS_BEDRIFT,FAKTURA'"),
        ],
    }

    with engine.begin() as conn:
        for table, cols in migrations.items():
            if table not in existing_tables:
                continue
            existing_cols = {c["name"] for c in insp.get_columns(table)}
            for col_name, col_type in cols:
                if col_name not in existing_cols:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}"))
