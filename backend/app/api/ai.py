from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
import pypdf
import io

from app.database import get_db
from app.ai.llama_service import llama_service
from app.api.accounting import get_financial_summary
from app.schemas.accounting import (
    AIInvoiceParseRequest, AIInvoiceParseResponse,
    AIChatRequest, AIChatResponse
)

router = APIRouter(prefix="/ai", tags=["AI & Llama"])

@router.get("/health")
async def get_ai_status():
    """Sjekker status for tilkobling mot Llama 3.1 AI-motoren."""
    return await llama_service.check_health()

@router.post("/parse-invoice", response_model=AIInvoiceParseResponse)
async def parse_invoice_text(req: AIInvoiceParseRequest):
    """Lar AI tolke råtekst fra en faktura og foreslå regnskapskonto og debet/kredit."""
    res = await llama_service.parse_invoice(req.invoice_text)
    return AIInvoiceParseResponse(**res)

@router.post("/upload-invoice-pdf", response_model=AIInvoiceParseResponse)
async def upload_invoice_pdf(file: UploadFile = File(...)):
    """Leser en opplastet faktura-PDF og sender innholdet til Llama for tolkning."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Vennligst last opp en gyldig PDF-fil.")

    content = await file.read()
    try:
        reader = pypdf.PdfReader(io.BytesIO(content))
        extracted_text = ""
        for page in reader.pages:
            extracted_text += page.extract_text() or ""
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Kunne ikke lese PDF: {str(e)}")

    if not extracted_text.strip():
        extracted_text = f"Faktura fra {file.filename} med ukjent beløp"

    res = await llama_service.parse_invoice(extracted_text)
    return AIInvoiceParseResponse(**res)

@router.post("/chat", response_model=AIChatResponse)
async def chat_with_cfo(req: AIChatRequest, db: Session = Depends(get_db)):
    """Chat med Llama som bedriftens digitale økonomisjef / CFO."""
    summary = get_financial_summary(db)
    summary_dict = summary.model_dump()
    reply = await llama_service.answer_cfo_question(req.message, summary_dict)
    return AIChatResponse(
        reply=reply,
        sources_considered=["Nøkkeltall regnskap", "Norsk standard kontoplan NS 4102"]
    )
