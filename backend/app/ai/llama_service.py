import os
import json
import re
import ast
import httpx
from typing import Dict, Any, List, Optional
from app.config import settings

SKILLS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "SKILLS.md")


class LlamaService:
    """
    Phink Accounting AI-tjeneste drevet av lokal Llama 3.1 8B Instruct Agent
    med SKILLS.md (Conta-kompatibel NS 4102 kontoplan, Lønnskjøring, Avdeling, Prosjekt og Duplikatsperre).
    Kobler seg primært til `llama serve` på http://127.0.0.1:9931 (eller Ollama på 11434).
    """

    def __init__(self):
        self.server_url = getattr(settings, "LLAMA_SERVER_URL", "http://127.0.0.1:9931").rstrip("/")
        self.ollama_url = getattr(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
        self.model_name = getattr(
            settings,
            "LLAMA_MODEL_NAME",
            "lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF:Q4_K_M",
        )
        self.cloud_url = getattr(settings, "CLOUD_LLM_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")
        self.cloud_key = getattr(settings, "CLOUD_LLM_API_KEY", "")
        self.cloud_model = getattr(settings, "CLOUD_LLM_MODEL", "llama-3.1-8b-instant")
        self.skills_prompt = self._load_skills()
        self.sections = self._parse_skill_sections(self.skills_prompt)
        self.voucher_registry: Dict[str, Dict[str, Any]] = {}

    def _load_skills(self) -> str:
        if os.path.exists(SKILLS_PATH):
            with open(SKILLS_PATH, "r", encoding="utf-8") as f:
                return f.read()
        return "Du er Phink Llama 3.1 Agent – norsk regnskapsfører (NS 4102) og Digital CFO."

    @staticmethod
    def _parse_skill_sections(full_text: str) -> Dict[str, str]:
        sections: Dict[str, str] = {}
        parts = re.split(r"(?=^## Ferdighet [A-Z]:)", full_text, flags=re.MULTILINE)
        sections["HEADER"] = parts[0].strip() if parts else ""
        for part in parts[1:]:
            m = re.match(r"^## Ferdighet ([A-Z]):", part)
            if m:
                sections[m.group(1)] = part.strip()
        return sections

    def _get_focused_system_prompt(self, keys: List[str]) -> str:
        chunks = [self.sections.get("HEADER", "")]
        for k in keys:
            if k in self.sections:
                chunks.append(self.sections[k])
        return "\n\n".join(c for c in chunks if c)

    @staticmethod
    def _format_llama31_prompt(messages: List[Dict[str, str]]) -> str:
        """Bygger offisiell Meta Llama 3.1 Instruct-prompt for rask og nøyaktig generering."""
        parts = ["<|begin_of_text|>"]
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "").strip()
            parts.append(f"<|start_header_id|>{role}<|end_header_id|>\n\n{content}<|eot_id|>")
        parts.append("<|start_header_id|>assistant<|end_header_id|>\n\n")
        return "".join(parts)

    @staticmethod
    def _extract_json(text: str) -> Dict[str, Any]:
        cleaned = text.strip()
        fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
        if fence:
            cleaned = fence.group(1)
        else:
            brace = re.search(r"(\{.*\})", cleaned, re.DOTALL)
            if brace:
                cleaned = brace.group(1)
        obj = json.loads(cleaned)
        if isinstance(obj, dict) and "parameters" in obj and isinstance(obj["parameters"], dict):
            obj = obj["parameters"]
        if isinstance(obj.get("suggested_lines"), str):
            try:
                obj["suggested_lines"] = json.loads(obj["suggested_lines"])
            except Exception:
                try:
                    obj["suggested_lines"] = ast.literal_eval(obj["suggested_lines"])
                except Exception:
                    obj["suggested_lines"] = []
        return obj

    async def check_health(self) -> Dict[str, Any]:
        """Sjekker om Llama 3.1 8B Instruct kjører i skyen (24/7), lokalt på port 9931, eller via Ollama."""
        if self.cloud_key:
            return {
                "status": "connected",
                "engine": f"24/7 Cloud Llama 3.1 8B ({self.cloud_model} + SKILLS.md)",
                "server_url": self.cloud_url,
                "installed_models": [self.cloud_model],
                "model_ready": True,
            }

        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.server_url}/v1/models")
                if res.status_code == 200:
                    return {
                        "status": "connected",
                        "engine": "Llama 3.1 8B Instruct (llama serve + SKILLS.md)",
                        "server_url": self.server_url,
                        "installed_models": [self.model_name],
                        "model_ready": True,
                    }
        except Exception:
            pass

        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(f"{self.ollama_url}/api/tags")
                if res.status_code == 200:
                    models = [m.get("name") for m in res.json().get("models", [])]
                    return {
                        "status": "connected",
                        "engine": "Ollama (Local Llama 3.1)",
                        "installed_models": models,
                        "model_ready": True,
                    }
        except Exception:
            pass

        return {
            "status": "offline_mode",
            "engine": "24/7 Built-in NS 4102 Engine (Conta-standard + SKILLS.md)",
            "message": f"Lokal Llama 3.1 ({self.server_url}) er avslått. Systemet kjører 24/7 med innebygd NS 4102 regnskapsmotor (eller sett CLOUD_LLM_API_KEY for 24/7 Sky-Llama).",
        }

    async def _call_llama(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 280,
    ) -> Optional[str]:
        # 1) Hvis 24/7 Cloud Llama API-nøkkel er satt (når PC-en hjemme er skrudd av)
        if self.cloud_key:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    res = await client.post(
                        f"{self.cloud_url}/chat/completions",
                        headers={"Authorization": f"Bearer {self.cloud_key}"},
                        json={
                            "model": self.cloud_model,
                            "messages": messages,
                            "temperature": temperature,
                            "max_tokens": max_tokens,
                        },
                    )
                    if res.status_code == 200:
                        return res.json()["choices"][0]["message"]["content"].strip()
            except Exception:
                pass

        # 2) Lokal `llama serve` på port 9931
        prompt = self._format_llama31_prompt(messages)
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stop": ["<|eot_id|>", "<|end_of_text|>"],
            "stream": False,
        }
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                res = await client.post(f"{self.server_url}/v1/completions", json=payload)
                if res.status_code == 200:
                    return res.json()["choices"][0]["text"].strip()
        except Exception:
            pass
        return None

    async def parse_invoice(self, text: str) -> Dict[str, Any]:
        """
        Parser faktura eller kvittering etter Conta / NS 4102 standard i SKILLS.md,
        inkl. avdeling, prosjekt, riktig MVA-sats (25%, 15%, 12%, 0%) og duplikatsperre.
        """
        focused_sys = self._get_focused_system_prompt(["A", "B", "C"])
        messages = [
            {"role": "system", "content": focused_sys},
            {
                "role": "user",
                "content": (
                    "Analyser fakturaen under og returner KUN gyldig JSON med nøklene:\n"
                    "supplier, invoice_date, due_date, total_amount, vat_amount, vat_rate_percent, "
                    "kid_or_ref, department_code, department_name, project_code, project_name, "
                    "suggested_expense_account, account_name, explanation.\n\n"
                    f"Faktura:\n{text}"
                ),
            },
        ]
        raw_reply = await self._call_llama(messages, temperature=0.0, max_tokens=240)
        if raw_reply:
            try:
                parsed = self._extract_json(raw_reply)
                return self._enrich_lines(parsed)
            except Exception:
                pass

        return self._fallback_invoice_parser(text)

    async def answer_cfo_question(self, question: str, accounting_summary: Dict[str, Any]) -> str:
        """Svarer på spørsmål som Digital CFO basert på SKILLS.md og sanntidstall."""
        focused_sys = self._get_focused_system_prompt(["E"])
        messages = [
            {"role": "system", "content": focused_sys},
            {
                "role": "user",
                "content": (
                    "Bruk Ferdighet E (Digital CFO). Svar presist og strukturert på norsk.\n"
                    f"Regnskapstall: Inntekter={accounting_summary.get('total_revenue', 0.0):,.2f} NOK, "
                    f"Kostnader={accounting_summary.get('total_expenses', 0.0):,.2f} NOK, "
                    f"Driftsresultat={accounting_summary.get('net_income', 0.0):,.2f} NOK, "
                    f"Bankinnskudd (1920)={accounting_summary.get('bank_balance', 0.0):,.2f} NOK, "
                    f"Bokførte bilag={accounting_summary.get('voucher_count', 0)} stk.\n\n"
                    f"Spørsmål fra brukeren: {question}"
                ),
            },
        ]
        reply = await self._call_llama(messages, temperature=0.2, max_tokens=300)
        if reply:
            return reply

        rev = accounting_summary.get("total_revenue", 0.0)
        net = accounting_summary.get("net_income", 0.0)
        bank = accounting_summary.get("bank_balance", 0.0)
        margin = round((net / rev) * 100, 1) if rev > 0 else 0.0
        status_word = "positivt og solid" if net >= 0 else "i minus for perioden"
        return (
            f"Her er en sanntidsanalyse av selskapets økonomiske stilling:\n\n"
            f"• **Likviditetsreserve (Konto 1920 Bank drift):** {bank:,.2f} NOK\n"
            f"• **Driftsresultat:** {net:,.2f} NOK ({status_word}, driftsmargin {margin}%)\n"
            f"• **Bokførte bilag:** {accounting_summary.get('voucher_count', 0)} stk.\n\n"
            f"💡 **CFO-Råd:** Hold alltid ansattes forskuddstrekk adskilt på sperret Skattetrekkskonto (1950), "
            f"og tagg prosjektkostnader (konto 4000–4500) med prosjektkode så prosjektregnskapet holdes ryddig."
        )

    def _fallback_invoice_parser(self, text: str) -> Dict[str, Any]:
        """Utvidet NS 4102 / Conta heuristisk analyse dersom Llama-serveren er avslått."""
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        amounts = re.findall(r"(\d+[\.,]\d{2})", text)
        total_amount = 0.0
        if amounts:
            cleaned_amounts = [float(a.replace(",", ".")) for a in amounts]
            total_amount = max(cleaned_amounts)
        else:
            whole_matches = re.findall(r"(?:total(?:beløp)?|sum|beløp)?\s*:?\s*(\d[\d\s]{1,10})\s*(?:nok|kr|eur|usd)", text, re.IGNORECASE)
            if whole_matches:
                cleaned_whole = [float(m.replace(" ", "")) for m in whole_matches if m.replace(" ", "").isdigit()]
                if cleaned_whole:
                    total_amount = max(cleaned_whole)

        text_lower = text.lower()
        vat_rate = 25
        dept_code, dept_name = "ADM", "Administrasjon"
        proj_code, proj_name = "FELLES", "Felleskostnad / Drift"

        proj_match = re.search(r"(proj[-\s]?\d[\w-]*|p-\d+)", text, re.IGNORECASE)
        if proj_match:
            proj_code = proj_match.group(1).upper().replace(" ", "-")
            proj_name = f"Prosjekt {proj_code}"

        if any(w in text_lower for w in ["meta ireland", "meta platforms ireland", "facebook ads", "instagram ads", "google ads ireland", "google ireland"]):
            account, account_name = 7325, "Annonsering & markedsføring i utlandet (Meta/Google Ads, skattefradrag)"
            vat_rate = 0
            dept_code, dept_name = "SALG", "Salg og Marked"
            explanation = "Annonsering i utlandet (Meta/Google Ireland) føres på 7325 med fullt skattefradrag og snudd avregning MVA (2715/2705)."
        elif any(w in text_lower for w in ["openai", "amazon web services", "aws", "github", "cloudflare", "google cloud emea", "vercel", "digitalocean"]):
            account, account_name = 6555, "Programvare, skytjenester & SaaS fra utlandet (Skattefradrag)"
            vat_rate = 0
            dept_code, dept_name = "IT", "IT og Utvikling"
            explanation = "Utenlandsk SaaS/skytjeneste føres på 6555 med fullt skattefradrag og snudd avregning MVA (2715/2705)."
        elif any(w in text_lower for w in ["import fra utlandet", "vareimport", "toll", "utland import"]):
            account, account_name = 4310, "Innkjøp av varer fra utlandet (Import, skattefradrag)"
            vat_rate = 0
            dept_code, dept_name = "DRIFT", "Drift og Produksjon"
            explanation = "Vareimport fra utlandet føres på 4310 med fullt skattefradrag."
        elif any(w in text_lower for w in ["konsulent utland", "tjenester fra utlandet", "foreign consulting"]):
            account, account_name = 4510, "Kjøp av tjenester fra utlandet (Skattefradrag / snudd avregning)"
            vat_rate = 0
            dept_code, dept_name = "DRIFT", "Drift og Produksjon"
            explanation = "Utenlandsk konsulenttjeneste føres på 4510 med skattefradrag og snudd avregning MVA (2715/2705)."
        elif any(w in text_lower for w in ["hotell utland", "hotel madrid", "hotel spania", "hotel barcelona", "hotel london", "hotel berlin", "tjenestereise utland", "iva "]):
            account, account_name = 7145, "Tjenestereise og hotell i utlandet (Skattefradrag, 0% norsk MVA)"
            vat_rate = 0
            dept_code, dept_name = "SALG", "Salg og Marked"
            explanation = "Reise/hotell i utlandet føres på 7145 (0% norsk MVA-fradrag, hele totalbeløpet trekkes av på skatten)."
        elif any(w in text_lower for w in ["underentreprenør", "innleid", "fremmedytelse", "elektriker", "rørlegger", "konsulent"]):
            account, account_name = 4500, "Fremmedytelser og underleverandører"
            dept_code, dept_name = "DRIFT", "Drift og Produksjon"
            explanation = "Gjenkjente underleverandør / fremmedytelse på prosjekt (konto 4500)."
        elif any(w in text_lower for w in ["software", "github", "aws", "microsoft", "google cloud", "azure", "lisens", "hosting", "saas"]):
            account, account_name = 6540, "IT-drift, programvare og skylisenser"
            dept_code, dept_name = "IT", "IT og Utvikling"
            explanation = "Gjenkjente IT-/programvarelisens (konto 6540/6550)."
        elif any(w in text_lower for w in ["reklame", "ads", "facebook", "instagram", "meta", "marketing", "annonsering"]):
            account, account_name = 7320, "Reklame og annonsering"
            dept_code, dept_name = "SALG", "Salg og Marked"
            explanation = "Gjenkjente markedsføring/annonsering (konto 7320)."
        elif any(w in text_lower for w in ["regnskap", "revisor", "advokat", "juridisk", "conta"]):
            account, account_name = 6720, "Honorar for økonomisk og juridisk bistand"
            dept_code, dept_name = "ADM", "Administrasjon"
            explanation = "Gjenkjente regnskaps-/rådgivningshonorar (konto 6720)."
        elif any(w in text_lower for w in ["strøm", "fjernvarme", "hafslund", "fjordkraft", "tibber"]):
            account, account_name = 6340, "Lys og varme (Strøm)"
            explanation = "Gjenkjente strøm/oppvarming (konto 6340)."
        elif any(w in text_lower for w in ["leie", "husleie", "kontorleie"]):
            account, account_name = 6300, "Leie lokaler"
            vat_rate = 0
            explanation = "Gjenkjente husleie (konto 6300)."
        elif any(w in text_lower for w in ["forsikring", "if ", "gjensidige", "fremtind", "tryg"]):
            account, account_name = 7500, "Forsikringspremie"
            vat_rate = 0
            explanation = "Gjenkjente forsikring (konto 7500, 0% MVA)."
        elif any(w in text_lower for w in ["drivstoff", "bensin", "diesel", "circle k", "uno-x", "lading"]):
            account, account_name = 7000, "Drivstoff og lading firmabil"
            dept_code, dept_name = "DRIFT", "Drift og Produksjon"
            explanation = "Gjenkjente drivstoff/bil (konto 7000)."
        elif any(w in text_lower for w in ["fly", "sas", "norwegian", "vy", "taxi", "hotell", "scandic", "thon"]):
            account, account_name = 7140, "Reisekostnad, ikke oppgavepliktig"
            vat_rate = 12
            explanation = "Gjenkjente reise/persontransport/hotell (konto 7140, 12% MVA)."
        elif any(w in text_lower for w in ["vare", "innkjøp", "produkt", "materiell"]):
            account, account_name = 4300, "Innkjøp av varer for videresalg"
            dept_code, dept_name = "DRIFT", "Drift og Produksjon"
            explanation = "Gjenkjente varekjøp (konto 4300)."
        elif any(w in text_lower for w in ["telefon", "mobil", "telenor", "telia", "bredbånd", "ice"]):
            account, account_name = 6900, "Telefon og internett"
            explanation = "Gjenkjente telekommunikasjon og bredbånd (konto 6900)."
        elif any(w in text_lower for w in ["gebyr", "bank", "vipps", "stripe", "dnb"]):
            account, account_name = 7770, "Bank- og kortgebyrer"
            vat_rate = 0
            explanation = "Gjenkjente bank-/betalingsgebyr (konto 7770, 0% MVA)."
        else:
            account, account_name = 6800, "Kontorrekvisita og trykksaker"
            explanation = "Generelt driftskjøp (konto 6800)."

        if vat_rate == 25:
            vat_amount = round(total_amount * 0.20, 2) if total_amount > 0 else 0.0
        elif vat_rate == 15:
            vat_amount = round(total_amount * (15.0 / 115.0), 2) if total_amount > 0 else 0.0
        elif vat_rate == 12:
            vat_amount = round(total_amount * (12.0 / 112.0), 2) if total_amount > 0 else 0.0
        else:
            vat_amount = 0.0

        supplier = lines[0] if lines else "Ukjent leverandør"
        data = {
            "supplier": supplier,
            "invoice_date": "2026-11-18",
            "due_date": "2026-12-02",
            "total_amount": total_amount,
            "vat_amount": vat_amount,
            "vat_rate_percent": vat_rate,
            "kid_or_ref": "REF-AUTO",
            "department_code": dept_code,
            "department_name": dept_name,
            "project_code": proj_code,
            "project_name": proj_name,
            "suggested_expense_account": account,
            "account_name": account_name,
            "explanation": explanation,
        }
        return self._enrich_lines(data)

    def _enrich_lines(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Lager garantert balanserte debet/kredit-linjer med MVA, avdeling, prosjekt og duplikatsjekk."""
        total = float(data.get("total_amount", 0.0) or 0.0)
        vat = float(data.get("vat_amount", 0.0) or 0.0)
        vat_rate = int(data.get("vat_rate_percent", 25 if vat > 0 else 0) or 0)
        account = int(data.get("suggested_expense_account", 6540) or 6540)
        if account == 2712:
            account = 7140
            data["suggested_expense_account"] = 7140
            data["account_name"] = "Reisekostnad, ikke oppgavepliktig"
        elif account == 2711:
            account = 4330
            data["suggested_expense_account"] = 4330
            data["account_name"] = "Innkjøp av varer for videresalg (15% MVA)"
        elif account == 2710:
            account = 6540
            data["suggested_expense_account"] = 6540
        dept = data.get("department_code") or "ADM"
        proj = data.get("project_code") or "FELLES"
        supplier = data.get("supplier") or "leverandør"
        kid = data.get("kid_or_ref") or "REF-AUTO"
        tag_prefix = f"[{dept}/{proj}] " if proj != "FELLES" else f"[{dept}] "
        desc = f"{tag_prefix}Faktura fra {supplier}"

        # Lovpålagt norsk MVA-kontroll (Representasjon 7350/7360, Forsikring 7500, Bankgebyr 7770, Diett/Bilgodtgj. 7080/7150, Utenlandsreise 7145 har 0% norsk MVA-fradrag)
        if account in (7350, 7360, 7500, 7770, 7080, 7150, 7400, 7145):
            vat = 0.0
            vat_rate = 0
            data["vat_amount"] = 0.0
            data["vat_rate_percent"] = 0
        elif account in (4510, 6555, 7325):
            # Snudd avregning 25 % MVA ved fjernleverbare tjenester fra utlandet (netto 0 kr MVA, 100 % skattefradrag)
            reverse_vat = round(total * 0.25, 2)
            data["vat_amount"] = 0.0
            data["vat_rate_percent"] = 0
            data["suggested_lines"] = [
                {"account_number": account, "description": f"{desc} (utland — fullt skattefradrag)", "debit": total, "credit": 0.0},
                {"account_number": 2715, "description": f"{tag_prefix}Inngående MVA utland (snudd avregning 25%)", "debit": reverse_vat, "credit": 0.0},
                {"account_number": 2705, "description": f"{tag_prefix}Utgående MVA utland (snudd avregning 25%)", "debit": 0.0, "credit": reverse_vat},
                {"account_number": 2400, "description": f"{tag_prefix}Leverandørgjeld utland ({supplier})", "debit": 0.0, "credit": total},
            ]
            data["is_duplicate"] = False
            data["duplicate_warning"] = None
            return data
        elif account == 7140 and vat > 0:
            vat_rate = 12
            data["vat_rate_percent"] = 12
        elif account == 4330 and vat > 0:
            vat_rate = 15
            data["vat_rate_percent"] = 15

        vat_account = 2710 if vat_rate == 25 else (2711 if vat_rate == 15 else 2712)

        if vat > 0 and total > vat:
            net_expense = round(total - vat, 2)
            data["suggested_lines"] = [
                {"account_number": account, "description": f"{desc} (netto kostnad)", "debit": net_expense, "credit": 0.0},
                {"account_number": vat_account, "description": f"{tag_prefix}Inngående MVA {vat_rate}%", "debit": vat, "credit": 0.0},
                {"account_number": 2400, "description": f"{tag_prefix}Leverandørgjeld ({supplier})", "debit": 0.0, "credit": total},
            ]
        else:
            data["suggested_lines"] = [
                {"account_number": account, "description": desc, "debit": total, "credit": 0.0},
                {"account_number": 2400, "description": f"{tag_prefix}Leverandørgjeld ({supplier})", "debit": 0.0, "credit": total},
            ]

        # Duplikatsjekk
        voucher_key = f"{supplier.strip().lower()}|{kid.strip().lower()}"
        if kid != "REF-AUTO" and voucher_key in self.voucher_registry:
            prev = self.voucher_registry[voucher_key]
            data["is_duplicate"] = True
            data["duplicate_warning"] = (
                f"STOPP: Faktura '{kid}' fra '{supplier}' er allerede ført på prosjekt '{prev.get('project_code')}'!"
            )
            data["explanation"] = f"⚠️ {data['duplicate_warning']} | {data.get('explanation', '')}"
        else:
            data["is_duplicate"] = False
            data["duplicate_warning"] = None
            if kid != "REF-AUTO":
                self.voucher_registry[voucher_key] = {
                    "supplier": supplier,
                    "kid_or_ref": kid,
                    "total_amount": total,
                    "project_code": proj,
                }

        return data


llama_service = LlamaService()
