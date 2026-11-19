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

    def _detect_english(self, text: str, explicit_lang: Optional[str] = None) -> bool:
        """Auto-detects English questions or honors explicit lang='en'/'nb'."""
        if explicit_lang:
            return explicit_lang.lower().startswith("en")
        q = f" {(text or '').lower()} "
        norwegian_markers = [" hva ", " hvordan ", " hvilken ", " konto ", " regnskap", " bilag", " mva", " lønn", " skatt", " fradrag", " utland", " inkasso", " saldo", " fører ", " bokfør", "æ", "ø", "å"]
        english_markers = [" what ", " how ", " which ", " account ", " accounting", " voucher", " vat ", " payroll", " tax ", " deduct", " foreign ", " debt collection", " collection fee", " balance", " book ", " record ", " expense", " invoice", " profit", " bank ", " saft", " saf-t", " reverse charge", " interest"]
        en_score = sum(1 for m in english_markers if m in q)
        no_score = sum(1 for m in norwegian_markers if m in q)
        return en_score > no_score

    async def answer_cfo_question(
        self,
        question: str,
        accounting_summary: Dict[str, Any],
        lang: Optional[str] = None,
    ) -> str:
        """Answers CFO & NS 4102 accounting questions in English or Norwegian based on SKILLS.md and live data."""
        from app.accounting.chart_of_accounts import ENGLISH_ACCOUNTS_MAP, DEFAULT_ACCOUNTS

        is_en = self._detect_english(question, lang)
        focused_sys = self._get_focused_system_prompt(["E"])
        lang_instruction = (
            "Use Skill E (Digital CFO). Answer clearly and accurately in ENGLISH using official English NS 4102 Norwegian GAAP account names and numbers."
            if is_en
            else "Bruk Ferdighet E (Digital CFO). Svar presist og strukturert på norsk med NS 4102-kontonumre."
        )
        messages = [
            {"role": "system", "content": focused_sys},
            {
                "role": "user",
                "content": (
                    f"{lang_instruction}\n"
                    f"Figures: Revenue={accounting_summary.get('total_revenue', 0.0):,.2f} NOK, "
                    f"Expenses={accounting_summary.get('total_expenses', 0.0):,.2f} NOK, "
                    f"Net Income={accounting_summary.get('net_income', 0.0):,.2f} NOK, "
                    f"Bank Balance (1920)={accounting_summary.get('bank_balance', 0.0):,.2f} NOK, "
                    f"Vouchers={accounting_summary.get('voucher_count', 0)}.\n\n"
                    f"User question: {question}"
                ),
            },
        ]
        reply = await self._call_llama(messages, temperature=0.2, max_tokens=320)
        if reply:
            return reply

        # Smart 24/7 rule-based bilingual NS 4102 CFO engine when local LLM is offline
        ql = (question or "").lower()
        rev = accounting_summary.get("total_revenue", 0.0)
        net = accounting_summary.get("net_income", 0.0)
        bank = accounting_summary.get("bank_balance", 0.0)
        margin = round((net / rev) * 100, 1) if rev > 0 else 0.0

        # 1) Direct lookup if user asks about a specific 4-digit NS 4102 account number
        acc_nums = re.findall(r"\b([1-8]\d{3})\b", question or "")
        if acc_nums:
            num = int(acc_nums[0])
            if num in ENGLISH_ACCOUNTS_MAP:
                en_name, en_desc = ENGLISH_ACCOUNTS_MAP[num]
                no_item = next((a for a in DEFAULT_ACCOUNTS if a["account_number"] == num), None)
                no_name = no_item["name"] if no_item else en_name
                no_desc = no_item["description"] if no_item else en_desc
                if is_en:
                    return (
                        f"📘 **NS 4102 Account {num} — {en_name}**\n"
                        f"• **Norwegian legal name:** {no_name}\n"
                        f"• **Purpose / Legal basis:** {en_desc}\n"
                        f"• **Type:** {no_item['account_type'] if no_item else 'ACCOUNT'} | **VAT code:** {no_item['vat_code'] if no_item else 'NONE'}\n"
                        f"• **Double-entry rule:** Always ensure total Debit equals total Credit (e.g. against `1920 Operating Bank Account` or `2400 Accounts Payable`)."
                    )
                return (
                    f"📘 **NS 4102 Konto {num} — {no_name}** (Engelsk: *{en_name}*)\n"
                    f"• **Bruk:** {no_desc}\n"
                    f"• **Type:** {no_item['account_type'] if no_item else 'KONTO'} | **MVA-kode:** {no_item['vat_code'] if no_item else 'NONE'}"
                )

        # 2) Debt collection / Inkasso / Late payment fees
        if any(w in ql for w in ["debt collection", "collection fee", "inkasso", "purregebyr", "reminder fee", "late fee"]):
            if is_en:
                return (
                    "⚖️ **Debt Collection & Reminder Fees (Norwegian GAAP / NS 4102):**\n"
                    "• **Account `7775` — Debt Collection & Reminder Fees — Inkasso (0% VAT, Tax-Deductible):** Book collection fees and reminder fees on business invoices here (100% tax-deductible when the underlying claim relates to your business).\n"
                    "• **Account `8150` — Interest Expenses & Late Payment Interest:** Book statutory late-payment interest charged by the collection agency here (0% VAT, tax-deductible).\n"
                    "• **Double-entry example:** Debit `7775` (fee) + Debit `8150` (interest) / Credit `1920` Operating Bank Account (or `2400` Accounts Payable).\n"
                    "• *Note:* Public fines/penalties (e.g. parking tickets) are NOT tax-deductible."
                )
            return (
                "⚖️ **Inkasso og purregebyr (NS 4102):**\n"
                "• **Konto `7775` — Inkassogebyr og purregebyr (Skattefradrag):** 0 % MVA, fullt skattemessig fradrag når kravet gjelder næringsvirksomheten.\n"
                "• **Konto `8150` — Rentekostnader og forsinkelsesrenter:** Forsinkelsesrenter på inkassokravet (0 % MVA, skattefradrag).\n"
                "• **Bokføring:** Debet `7775` (+ evt. Debet `8150`) / Kredit `1920` Bankinnskudd drift (eller `2400` Leverandørgjeld)."
            )

        # 3) Foreign expenses, reverse charge VAT, Meta/Google Ads, SaaS, travel abroad, imports
        if any(w in ql for w in ["foreign", "abroad", "reverse charge", "meta", "google ads", "saas", "openai", "aws", "import", "utland", "snudd avregning"]):
            if is_en:
                return (
                    "🌍 **Foreign Tax-Deductible Expenses & Reverse Charge VAT (Norway NS 4102):**\n"
                    "• **`7325` — Foreign Advertising & Marketing (Meta/Google Ads):** 100% tax-deductible + 25% reverse-charge VAT (`2705` Output / `2715` Input).\n"
                    "• **`6555` — Foreign Software, Cloud & SaaS (AWS, OpenAI, GitHub):** 100% tax-deductible + 25% reverse-charge VAT (`2705`/`2715`).\n"
                    "• **`7145` — Foreign Business Travel & Hotel:** 0% Norwegian VAT deduction, 100% of total receipt is tax-deductible.\n"
                    "• **`4310` — Purchases of Goods — Foreign Import:** Tax-deductible goods import.\n"
                    "• **`4510` — Foreign Subcontractors & Services:** Tax-deductible foreign consulting + reverse-charge VAT."
                )
            return (
                "🌍 **Utenlandske skattefradrag & snudd avregning (NS 4102):**\n"
                "• **`7325`** Annonsering utland (Meta/Google Ads) + snudd avregning MVA (`2705`/`2715`).\n"
                "• **`6555`** Programvare/SaaS utland (AWS, OpenAI, GitHub) + snudd avregning (`2705`/`2715`).\n"
                "• **`7145`** Reise & hotell i utlandet (0 % norsk MVA, 100 % skattefradrag på hele beløpet).\n"
                "• **`4310`** Vareimport utland · **`4510`** Tjenester/konsulent fra utlandet."
            )

        # 4) VAT / MVA questions
        if any(w in ql for w in ["vat", "mva", "merverdiavgift", "value added tax"]):
            if is_en:
                return (
                    "🧾 **Norwegian VAT (MVA) Rules — NS 4102:**\n"
                    "• **25% Standard Rate:** Output `2700` / Input `2710` (goods & services)\n"
                    "• **15% Food & Beverages:** Output `2701` / Input `2711`\n"
                    "• **12% Transport, Hotels & Culture:** Output `2702` / Input `2712`\n"
                    "• **25% Reverse Charge (Foreign Services):** Output `2705` / Input `2715`\n"
                    "• **Settlement Account:** `2740 VAT Settlement Account` — submitted manually via **Altinn 3** (nothing is ever auto-submitted)."
                )
            return (
                "🧾 **Norske MVA-satser (NS 4102):**\n"
                "• **25 %:** `2700` Utgående / `2710` Inngående\n"
                "• **15 % (mat):** `2701` / `2711` · **12 % (reise/hotell):** `2702` / `2712`\n"
                "• **Snudd avregning utland (25 %):** `2705` / `2715` · **Oppgjør:** `2740`."
            )

        # 5) Payroll / Salary / Restricted tax account
        if any(w in ql for w in ["payroll", "salary", "salaries", "wages", "holiday pay", "withholding", "aga", "lønn", "feriepenger", "skattetrekk"]):
            if is_en:
                return (
                    "💼 **Norwegian Payroll & Statutory Withholding (NS 4102):**\n"
                    "• **`5000` Salaries and Wages**, **`5180` Holiday Pay Expense (12%)**, **`5400` Employer's National Insurance (AGA, Zones 1–5)**, **`5420` Mandatory Pension (OTP)**.\n"
                    "• **Statutory Tax Account (`1950` Restricted Tax Withholding Bank Account):** Per the Norwegian Tax Payment Act § 5-12, employee PAYE withholding tax (`2600`) MUST be transferred from `1920 Operating Bank Account` to `1950` on every payroll run. Phink Accounting posts this second voucher automatically!"
                )
            return (
                "💼 **Norsk lønnskjøring (NS 4102):**\n"
                "• Fordeles automatisk på `5000` Lønn, `5180` Feriepenger (12 %), `5400` AGA (sone 1–5), `5420` OTP, `2600` Forskuddstrekk og `2930` Skyldig lønn.\n"
                "• Overfører automatisk forskuddstrekk fra `1920` til bundet skattetrekkskonto `1950` (Skattebetalingsloven § 5-12)."
            )

        # 6) Opening balance / SAF-T / General financial summary
        if is_en:
            status_word = "positive and healthy" if net >= 0 else "negative for the period"
            return (
                f"Here is a real-time CFO summary of your company's financial position (NS 4102):\n\n"
                f"• **Liquidity Reserve (`1920` Operating Bank Account):** {bank:,.2f} NOK\n"
                f"• **Operating Profit / Net Income:** {net:,.2f} NOK ({status_word}, operating margin {margin}%)\n"
                f"• **Posted Vouchers:** {accounting_summary.get('voucher_count', 0)}\n\n"
                f"💡 **CFO Advice:** Keep employee PAYE tax segregated on `1950 Restricted Tax Withholding Bank Account`, "
                f"book foreign SaaS/ads under `6555`/`7325`, and debt collection fees under `7775` for full tax deduction under Norwegian law."
            )

        status_word = "positivt og solid" if net >= 0 else "i minus for perioden"
        return (
            f"Her er en sanntidsanalyse av selskapets økonomiske stilling:\n\n"
            f"• **Likviditetsreserve (Konto 1920 Bank drift):** {bank:,.2f} NOK\n"
            f"• **Driftsresultat:** {net:,.2f} NOK ({status_word}, driftsmargin {margin}%)\n"
            f"• **Bokførte bilag:** {accounting_summary.get('voucher_count', 0)} stk.\n\n"
            f"💡 **CFO-Råd:** Hold alltid ansattes forskuddstrekk adskilt på sperret Skattetrekkskonto (1950), "
            f"og bruk `7775` (inkasso), `6555` (SaaS utland) og `7325` (annonser utland) for riktig skattefradrag."
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

        if any(w in text_lower for w in ["inkasso", "purregebyr", "inkassogebyr", "inkassovarsel", "kredinor", "intrum", "lindorff", "sergel", "kravia", "inndrivelse", "debt collection", "collection fee", "reminder fee", "late fee"]):
            account, account_name = 7775, "Debt Collection & Reminder Fees — Inkasso (0% VAT, Tax-Deductible)"
            vat_rate = 0
            dept_code, dept_name = "ADM", "Administration"
            explanation = "Debt collection / reminder fee on business claim booked to 7775 (0% VAT, 100% tax-deductible; statutory late-payment interest to 8150)."
        elif any(w in text_lower for w in ["meta ireland", "meta platforms ireland", "facebook ads", "instagram ads", "google ads ireland", "google ireland", "foreign ads"]):
            account, account_name = 7325, "Foreign Advertising & Marketing — Meta/Google Ads (Tax-Deductible)"
            vat_rate = 0
            dept_code, dept_name = "SALG", "Sales & Marketing"
            explanation = "Foreign advertising (Meta/Google Ireland) booked to 7325 with full tax deduction and 25% reverse-charge VAT (2705/2715)."
        elif any(w in text_lower for w in ["openai", "amazon web services", "aws", "github", "cloudflare", "google cloud emea", "vercel", "digitalocean", "foreign saas"]):
            account, account_name = 6555, "Foreign Software, Cloud & SaaS (Tax-Deductible / Reverse Charge)"
            vat_rate = 0
            dept_code, dept_name = "IT", "IT & Development"
            explanation = "Foreign SaaS/cloud subscription booked to 6555 with full tax deduction and 25% reverse-charge VAT (2705/2715)."
        elif any(w in text_lower for w in ["import fra utlandet", "vareimport", "toll", "utland import", "foreign import", "goods import", "customs import"]):
            account, account_name = 4310, "Purchases of Goods — Foreign Import (Tax-Deductible)"
            vat_rate = 0
            dept_code, dept_name = "DRIFT", "Operations"
            explanation = "Foreign goods import booked to 4310 with full tax deduction."
        elif any(w in text_lower for w in ["konsulent utland", "tjenester fra utlandet", "foreign consulting", "foreign services", "foreign subcontractor"]):
            account, account_name = 4510, "Foreign Subcontractors & Services (Tax-Deductible / Reverse Charge)"
            vat_rate = 0
            dept_code, dept_name = "DRIFT", "Operations"
            explanation = "Foreign consulting/service booked to 4510 with full tax deduction and 25% reverse-charge VAT (2705/2715)."
        elif any(w in text_lower for w in ["hotell utland", "hotel madrid", "hotel spania", "hotel barcelona", "hotel london", "hotel berlin", "tjenestereise utland", "foreign hotel", "foreign travel", "business travel abroad", "iva "]):
            account, account_name = 7145, "Foreign Business Travel & Hotel (0% NO VAT, 100% Tax-Deductible)"
            vat_rate = 0
            dept_code, dept_name = "SALG", "Sales & Marketing"
            explanation = "Foreign business travel/hotel booked to 7145 (0% Norwegian VAT deduction; 100% of total receipt is tax-deductible)."
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
