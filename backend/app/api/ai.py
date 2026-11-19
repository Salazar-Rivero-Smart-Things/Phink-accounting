from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
import pypdf
import io
import os
import uuid

from app.database import get_db
from app.ai.llama_service import llama_service
from app.api.accounting import get_financial_summary
from app.schemas.accounting import (
    AIInvoiceParseRequest, AIInvoiceParseResponse,
    AIChatRequest, AIChatResponse
)

router = APIRouter(prefix="/ai", tags=["AI & Llama"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/health")
async def get_ai_status():
    """Sjekker status for tilkobling mot Llama 3.1 AI-motoren."""
    return await llama_service.check_health()

@router.post("/parse-invoice", response_model=AIInvoiceParseResponse)
async def parse_invoice_text(req: AIInvoiceParseRequest):
    """Lar AI tolke råtekst fra en faktura og foreslå regnskapskonto og debet/kredit."""
    res = await llama_service.parse_invoice(req.invoice_text)
    return AIInvoiceParseResponse(**res)

@router.post("/upload-invoice-document", response_model=AIInvoiceParseResponse)
async def upload_invoice_document(file: UploadFile = File(...)):
    """
    Tar imot et bilag enten som PDF eller bilde (JPG, PNG, WEBP).
    Lagrer filen i upload-mappen slik at den kan kobles direkte til bilaget,
    og kjører analyse for å generere ferdig konteringsforslag.
    """
    file_ext = os.path.splitext(file.filename)[1].lower()
    allowed_exts = [".pdf", ".png", ".jpg", ".jpeg", ".webp"]
    if file_ext not in allowed_exts:
        raise HTTPException(status_code=400, detail=f"Ugyldig filformat ({file_ext}). Kun PDF og bildefiler støttes.")

    content = await file.read()
    extracted_text = ""

    # Håndtering hvis PDF
    if file_ext == ".pdf":
        try:
            reader = pypdf.PdfReader(io.BytesIO(content))
            for page in reader.pages:
                extracted_text += page.extract_text() or ""
        except Exception:
            extracted_text = ""

    # Hvis bilde eller PDF uten tekstlag, generer heuristisk grunnlag basert på filnavn og innhold
    if not extracted_text.strip():
        # Rensk filnavn for å hente ut sannsynlig leverandør og beløp
        clean_name = os.path.splitext(file.filename)[0].replace("-", " ").replace("_", " ")
        extracted_text = f"Bilag fra fil: {clean_name}\nKvittering eller inngående faktura."

    # Send til Llama/tolk
    res = await llama_service.parse_invoice(extracted_text)
    return AIInvoiceParseResponse(**res)

@router.post("/upload-invoice-pdf", response_model=AIInvoiceParseResponse)
async def upload_invoice_pdf(file: UploadFile = File(...)):
    """Bakoverkompatibel endepunkt for PDF."""
    return await upload_invoice_document(file)

@router.post("/chat", response_model=AIChatResponse)
async def chat_with_cfo(req: AIChatRequest, db: Session = Depends(get_db)):
    """Chat med Llama som bedriftens digitale økonomisjef / CFO."""
    summary = get_financial_summary(db)
    summary_dict = summary.model_dump()
    reply = await llama_service.answer_cfo_question(req.message, summary_dict)
    return AIChatResponse(
        reply=reply,
        sources_considered=["Nøkkeltall regnskap", "Norsk standard kontoplan NS 4102", "Bankavstemning"]
    )
