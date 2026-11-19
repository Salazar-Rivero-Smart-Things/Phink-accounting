from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.config import settings
from app.database import engine, Base, SessionLocal, ensure_schema_migrations
from app.accounting.chart_of_accounts import seed_default_accounts
from app.accounting.seed_data import seed_enterprise_demo_data
from app.api.accounting import router as accounting_router
from app.api.auth import router as auth_router, seed_default_owner
from app.api.payroll import router as payroll_router, seed_demo_employees
from app.api.saft_compliance import router as saft_compliance_router, seed_default_dimensions
from app.api.billing import router as billing_router
from app.api.ai import router as ai_router
from app.api.support import router as support_router, seed_demo_support_cases

# Sørg for at mappen uploads eksisterer
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Opprett alle databasetabeller og migrer eventuelle nye kolonner
    Base.metadata.create_all(bind=engine)
    ensure_schema_migrations()
    
    # Kjøring av seeder (sett SEED_DEMO_DATA=false i produksjon for helt blankt regnskap klart til SAF-T import)
    db = SessionLocal()
    try:
        seed_default_accounts(db)
        seed_default_dimensions(db)
        seed_default_owner(db)
        if os.getenv("SEED_DEMO_DATA", "false").lower() == "true":
            seed_demo_employees(db)
            seed_enterprise_demo_data(db)
            seed_demo_support_cases(db)
    finally:
        db.close()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Fullverdig regnskapssystem med leverandørreskontro, bankavstemning, salgsfaktura, bilagsmottak og AI",
    lifespan=lifespan
)

# Tillat kall fra Next.js (port 3000) og produksjonsdomenet www.phink-acounting.no
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://www.phink-acounting.no",
        "https://phink-acounting.no",
        "https://www.phink-accounting.no",
        "https://phink-accounting.no",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Server opplastede filer (bilder og PDF-er) statisk for visning i frontend
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(accounting_router, prefix=settings.API_V1_STR)
app.include_router(payroll_router, prefix=settings.API_V1_STR)
app.include_router(saft_compliance_router, prefix=settings.API_V1_STR)
app.include_router(billing_router, prefix=settings.API_V1_STR)
app.include_router(ai_router, prefix=settings.API_V1_STR)
app.include_router(support_router, prefix=settings.API_V1_STR)

@app.get("/health")
def health():
    return {"status": "ok", "service": settings.PROJECT_NAME, "version": settings.VERSION}


@app.get("/")
def root():
    return {
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs_url": "/docs",
        "uploads_url": "/uploads",
        "modules": [
            "Bilagsmottak (PDF & Bilde)",
            "Bankavstemning",
            "Leverandører & Leverandørreskontro",
            "Kunder & Salgsfaktura",
            "MVA-oppgave & Skatt",
            "Finansielle Rapporter (Resultat, Balanse, Saldobalanse)",
            "NS 4102 Kontoplan",
            "Llama 3.1 AI CFO",
            "Kundeservicedesk & Operatørdriver"
        ]
    }
