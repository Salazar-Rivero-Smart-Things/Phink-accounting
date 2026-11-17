import json
import re
import httpx
from typing import Dict, Any, Optional
from app.config import settings

class LlamaService:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model_name = settings.LLAMA_MODEL_NAME

    async def check_health(self) -> Dict[str, Any]:
        """Sjekker om lokal Llama-tjeneste (f.eks. Ollama) er tilgjengelig."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    models = [m.get("name") for m in res.json().get("models", [])]
                    has_llama = any(self.model_name in m for m in models)
                    return {
                        "status": "connected",
                        "engine": "Ollama (Local Llama 3.1)",
                        "installed_models": models,
                        "model_ready": has_llama
                    }
        except Exception:
            pass
        
        return {
            "status": "offline_mode",
            "engine": "Built-in Rule-Assisted AI Engine",
            "message": "Lokal Llama 3.1 (Ollama) kjører ikke enda på port 11434. Systemet bruker innebygd regelassistert tolk inntil modellen startes."
        }

    async def parse_invoice(self, text: str) -> Dict[str, Any]:
        """
        Parser tekst fra en faktura eller kvittering og strukturerer den
        i henhold til Norsk Standard Kontoplan (NS 4102).
        """
        prompt = f"""Du er en autorisert regnskapsfører og bilagsleser i Norge.
Analyser følgende faktura/kvittering og returner KUN gyldig JSON i dette formatet:
{{
  "supplier": "Navn på leverandør",
  "invoice_date": "YYYY-MM-DD",
  "due_date": "YYYY-MM-DD",
  "total_amount": 1250.00,
  "vat_amount": 250.00,
  "kid_or_ref": "KID eller fakturanummer",
  "suggested_expense_account": 6540,
  "account_name": "IT-drift, programvare og skylisenser",
  "explanation": "Kort begrunnelse for valg av konto"
}}

Bruk disse vanlige reglene for kontovalg:
- IT, programvare, skylisenser, hosting -> 6540
- Varekjøp for videresalg -> 4300
- Kontorrekvisita -> 6800
- Husleie -> 6300
- Reklame, annonser -> 7320
- Telefon / bredbånd -> 6900
- Reise og diett -> 7140

Tekst fra bilag:
\"\"\"{text}\"\"\"
"""
        # Forsøk å kalle Llama 3.1 via Ollama hvis tilgjengelig
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model_name,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json"
                    }
                )
                if res.status_code == 200:
                    response_text = res.json().get("response", "{}")
                    parsed = json.loads(response_text)
                    return self._enrich_lines(parsed)
        except Exception:
            pass

        # Fallback tolk (robust heuristisk tolk for fakturatekst)
        return self._fallback_invoice_parser(text)

    async def answer_cfo_question(self, question: str, accounting_summary: Dict[str, Any]) -> str:
        """
        Svarer på spørsmål om bedriftens økonomi basert på sanntidstall fra regnskapet.
        """
        prompt = f"""Du er Phink AI - Digital CFO og Økonomisk Rådgiver for bedriften.
Her er bedriftens nåværende nøkkeltall:
- Totale inntekter: {accounting_summary.get('total_revenue', 0.0):,.2f} NOK
- Totale kostnader: {accounting_summary.get('total_expenses', 0.0):,.2f} NOK
- Netto driftsresultat: {accounting_summary.get('net_income', 0.0):,.2f} NOK
- Likviditetsreserve (Bank): {accounting_summary.get('bank_balance', 0.0):,.2f} NOK
- Antall bokførte bilag: {accounting_summary.get('voucher_count', 0)}

Spørsmål fra brukeren:
"{question}"

Svar presist, profesjonelt og lettfattelig på norsk. Gi konkrete økonomiske råd basert på tallene over."""

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model_name,
                        "prompt": prompt,
                        "stream": False
                    }
                )
                if res.status_code == 200:
                    return res.json().get("response", "").strip()
        except Exception:
            pass

        # Smart respons i fallback-modus
        net = accounting_summary.get('net_income', 0.0)
        bank = accounting_summary.get('bank_balance', 0.0)
        status_word = "positivt og sunt" if net >= 0 else "i underskudd"
        return (
            f"Basert på regnskapet ditt nå: \n\n"
            f"• **Bankbeholdning:** {bank:,.2f} NOK\n"
            f"• **Driftsresultat:** {net:,.2f} NOK ({status_word})\n"
            f"• **Bokførte bilag:** {accounting_summary.get('voucher_count', 0)} stk.\n\n"
            f"*(Tips: Når du har startet Llama 3.1 via Ollama på din maskin, kan jeg gi enda dypere strategiske analyser og besvare fritekstspørsmål i sanntid!)*"
        )

    def _fallback_invoice_parser(self, text: str) -> Dict[str, Any]:
        """Heuristisk analyse av fakturaer ved fravær av kjørende lokal LLM."""
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        
        # Finn beløp (f.eks. 1250,00 eller 1250.00)
        amounts = re.findall(r'(\d+[\.,]\d{2})', text)
        total_amount = 0.0
        if amounts:
            cleaned_amounts = [float(a.replace(",", ".")) for a in amounts]
            total_amount = max(cleaned_amounts)
        
        vat_amount = round(total_amount * 0.20, 2) if total_amount > 0 else 0.0

        # Kontoklassifisering basert på nøkkelord
        text_lower = text.lower()
        if any(w in text_lower for w in ["software", "github", "aws", "microsoft", "google", "cloud", "lisens", "hosting"]):
            account = 6540
            account_name = "IT-drift, programvare og skylisenser"
            explanation = "Gjenkjente IT-/programvarerelaterte nøkkelord."
        elif any(w in text_lower for w in ["leie", "kontor", "eiendom", "husleie"]):
            account = 6300
            account_name = "Leie lokaler"
            explanation = "Gjenkjente husleie/lokale-nøkkelord."
        elif any(w in text_lower for w in ["reklame", "ads", "facebook", "marketing", "annonsering"]):
            account = 7320
            account_name = "Reklame og annonsering"
            explanation = "Gjenkjente markedsføringsrelaterte nøkkelord."
        elif any(w in text_lower for w in ["vare", "innkjøp", "produkt"]):
            account = 4300
            account_name = "Innkjøp av varer for videresalg"
            explanation = "Gjenkjente varekjøpsnøkkelord."
        else:
            account = 6800
            account_name = "Kontorrekvisita og trykksaker"
            explanation = "Generelt driftskjøp (standardkonto)."

        supplier = lines[0] if lines else "Ukjent leverandør"

        data = {
            "supplier": supplier,
            "invoice_date": "2026-11-17",
            "due_date": "2026-12-01",
            "total_amount": total_amount,
            "vat_amount": vat_amount,
            "kid_or_ref": "REF-AUTO",
            "suggested_expense_account": account,
            "account_name": account_name,
            "explanation": explanation
        }
        return self._enrich_lines(data)

    def _enrich_lines(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Lager balanserte debet/kredit forslag til bilag."""
        total = data.get("total_amount", 0.0)
        account = data.get("suggested_expense_account", 6540)
        desc = f"Faktura fra {data.get('supplier', 'leverandør')}"

        data["suggested_lines"] = [
            {"account_number": account, "description": desc, "debit": total, "credit": 0.0},
            {"account_number": 2400, "description": desc, "debit": 0.0, "credit": total}
        ]
        return data

llama_service = LlamaService()
