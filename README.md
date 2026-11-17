# Phink Accounting 📊🤖🎧

Et moderne, helhetlig regnskapssystem bygget med **dobbel bokføring**, **Meta Llama 3.1 AI-assistanse**, og en **egen integrert Kundeservicedesk (Human-in-the-Loop)** for direkte håndtering av refusjoner, betalingsfeil og kundehenvendelser.

---

## 🌟 Hovedfunksjoner

1. **Dobbel bokføring & Norsk Standard Kontoplan (NS 4102):**
   - Strikt matematisk validering: Et bilag kan aldri lagres med ubalanse (`sum(debet) == sum(kredit)`).
   - Innebygde standardkontoer: Bank (1920), Leverandørgjeld (2400), Salg (3000), IT-drift (6540), Kontorrekvisita (6800) osv.

2. **Kundeservice & Operatørdriver (Deg + Llama):**
   - **1. linje Support (Llama 3.1):** AI-en tar imot henvendelser og analyserer saken.
   - **Eskalering til operatør (Deg):** Ved økonomiske hendelser som *refusjonskrav* eller *betalingsfeil* eskaleres saken direkte til din personlige operatørstasjon i dashbordet.
   - Hurtigknapper for refusjonsgodkjenning, avklaring av transaksjoner og direktechat med kunder.

3. **AI Bilagsmottak & Skanning (Llama 3.1):**
   - Analyserer fakturatekst og kvitteringer.
   - Trekker ut leverandør, beløp, MVA, KID og forfallsdato.
   - Genererer automatisk balanserte konteringsforslag i henhold til norsk regnskapsstandard.

4. **Llama CFO Chat:**
   - Still spørsmål i naturlig språk til din digitale økonomisjef basert på sanntidstall fra regnskapet (likviditet, driftsresultat, skatt og rådgivning).

5. **Sikkerhet & Personvern (Defense in Depth):**
   - **Lokal AI-inferens:** Regnskapstall sendes ikke til eksterne skyleverandører.
   - **Kryptografisk revisjonsspor (Audit Trail):** Append-only logg som forhindrer sletting eller usynlig manipulasjon av historiske bilag.
   - **AES-256 kryptering** for data i ro og **TLS 1.3** for data i transitt.

---

## 🏗️ Teknologier

* **Backend:** Python 3 (FastAPI, SQLAlchemy, Pydantic v2, PyPDF, Uvicorn)
* **Frontend:** Next.js (TypeScript, React 19, Tailwind CSS 4, Lucide Icons)
* **AI Engine:** Meta Llama 3.1 8B (koblet via lokal Ollama eller intern tolk)
* **Database:** SQLite / PostgreSQL

---

## 🚀 Hvordan starte prosjektet

### 1. Start Python Backend (Port 8000)
```powershell
cd backend
.\venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```
Swagger API-dokumentasjon er tilgjengelig på: `http://localhost:8000/docs`

### 2. Start Next.js Frontend (Port 3000)
```powershell
cd frontend
npm run dev
```
Åpne nettleseren på: `http://localhost:3000`

---

## ⚖️ Lisens & Attribusjon
Dette prosjektet benytter Meta Llama 3.1 i henhold til lisensbetingelsene:
*Llama 3.1 is licensed under the Llama 3.1 Community License, Copyright © Meta Platforms, Inc. All Rights Reserved.*
Notice-fil er tilgjengelig i prosjektets rotmappe: `NOTICE`.
