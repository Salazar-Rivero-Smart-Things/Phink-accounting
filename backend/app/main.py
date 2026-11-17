from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.accounting.chart_of_accounts import seed_default_accounts
from app.api.accounting import router as accounting_router
from app.api.ai import router as ai_router
from app.api.support import router as support_router, seed_demo_support_cases

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Opprett databasetabeller hvis de ikke finnes
    Base.metadata.create_all(bind=engine)
    # Legg inn Norsk Standard Kontoplan (NS 4102) & support-demo
    db = SessionLocal()
    try:
        seed_default_accounts(db)
        seed_demo_support_cases(db)
    finally:
        db.close()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Regnskapssystem med dobbel bokføring, Llama 3.1 AI og Live Kundeservicedesk",
    lifespan=lifespan
)

# Tillat kall fra Next.js (port 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(accounting_router, prefix=settings.API_V1_STR)
app.include_router(ai_router, prefix=settings.API_V1_STR)
app.include_router(support_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs_url": "/docs",
        "operator": "Pepito Liindo (Kundeservice & Driftsansvarlig)",
        "license_notice": "Llama 3.1 is licensed under the Llama 3.1 Community License, Copyright © Meta Platforms, Inc. All Rights Reserved."
    }
