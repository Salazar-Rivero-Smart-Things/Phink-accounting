# FOR DEEPSEEK Å LESES — Phink Accounting (Viktig lesning før du rører kode!)

> **TIL DEEPSEEK / AI-ASSISTENTER:**
> Les HELE denne filen før du foreslår eller gjør endringer i dette repoet.
> Dette er produksjonskoden for **Phink Accounting** (`www.phink-acounting.no`), et komplett norsk skybasert regnskapssystem bygget for **Salazar-Rivero-Smart-Things**.

---

## 1. Hva er dette prosjektet?

- **Navn:** Phink Accounting (Norsk regnskapssystem etter Bokføringsloven & NS 4102)
- **GitHub-repo:** `https://github.com/Salazar-Rivero-Smart-Things/Phink-accounting.git` (branch: `main`)
- **Domenenavn:** `https://www.phink-acounting.no` (registrert hos Domeneshop)
- **Stack:**
  - **Frontend:** Next.js 16 (App Router, TypeScript, Tailwind CSS) i `frontend/`
  - **Backend:** FastAPI + SQLAlchemy + Pydantic i `backend/`
  - **Database:**
    - Lokalt under utvikling/testing: SQLite (`backend/phink_accounting.db`)
    - Produksjon: MariaDB 11.4 (Domeneshop `phinkaccountin01.mysql.domeneshop.no`) eller PostgreSQL (f.eks. Railway)
  - **AI CFO / Bilagstolker:** `backend/app/ai/llama_service.py` + `backend/app/ai/SKILLS.md` (med smart regelbasert fallback dersom lokal LLM ikke kjører)

---

## 2. UFRAVIKELIGE FORRETNINGS- OG SIKKERHETSREGLER (ALDRI ENDRE UTEN EIERENS GODKJENNING!)

### A. Betalingsmetoder (STRENGT!)
- **KUN to betalingsmetoder er tillatt i hele systemet:**
  1. `VIPPS_BEDRIFT` (Vipps Bedrift)
  2. `FAKTURA` (Tilsendt faktura)
- **IKKE** legg til Stripe, kortbetaling, Klarna, PayPal eller andre betalingsmetoder. Backend (`backend/app/api/billing.py`) avviser alt annet med HTTP 400.

### B. Eksakt prisliste (skal stemme overalt: `/priser`, `BillingPanel.tsx`, `billing.py`, `SKILLS.md`)
- **Phink Komplett abonnement:** `299 kr/mnd` — ubegrenset antall bilag, ingen skjulte gebyrer.
- **Bankintegrasjon (tillegg):** `+ 59 kr/mnd`
- **KID-automatikk (tillegg):** `3 kr per KID-faktura`
- **SAF-T XML-import (engangs/tillegg):** `+ 79 kr`
- **Endre profil etter registrering:** `150 kr eks. MVA` for vanlige kunder — **`0 kr` (helt gratis)** for Administrator/Eier.

### C. Roller, Kontoer & Låste Innstillinger (KRITISK!)
- **Eier / Administrator-e-post (`OWNER_EMAILS`):** `riveroosx7@gmail.com`
  - Får automatisk `role="OWNER"`, `is_admin=True`, `is_support_agent=True`, `is_customer_account=True`, `billing_exempt=True` (gratis konto for alltid, 0 kr profilendring, faktureres aldri).
- **Innstillinger er LÅST for vanlige kunder etter registrering:**
  - Kunder fyller inn selskapsinfo og kontodetaljer én gang ved registrering på `/register`.
  - Etter registrering er fanen **Innstillinger** skrivebeskyttet (`disabled`) for kunder, og `POST /api/accounting/settings` returnerer **HTTP 403** for alle som ikke er `OWNER` eller `ADMIN`.
  - **KUN Administrator** kan redigere selskapsinnstillinger og kundeprofiler.
  - Når en vanlig kunde klikker **"Endre profil (150 kr)"**, endres IKKE profilen direkte — i stedet opprettes en betalt forespørsel (`150 kr`) + en høy-prioritets `SupportTicket` til Administrator i Kundeservice Desk (`PUT /api/auth/profile`).

### D. Altinn & Brønnøysund (ALDRI AUTO-INNSENDING!)
- **INGENTING skal sendes automatisk til Altinn, Skatteetaten eller Brønnøysundregistrene.**
- All innsending krever eksplisitt manuell handling fra brukeren:
  - MVA-melding: `POST /api/accounting/altinn/submit-vat-return`
  - Årsregnskap / Skattemelding ("Send inn regnskap"-knapp): `POST /api/accounting/altinn/submit-annual-accounts`

### E. Norsk regnskapsskikk (NS 4102) — Regler som alltid må overholdes
- **Dobbel bokføring:** Hvert eneste bilag MÅ ha `sum(debit) == sum(credit)` på øret. Ubalanserte bilag skal alltid avvises.
- **MVA-satser:** 25 % (`2700`/`2710`), 15 % (`2701`/`2711`), 12 % (`2702`/`2712`), 0 %, samt snudd avregning / omvendt avgiftsplikt (`2705`/`2715`).
- **Utenlandske skattefradragskontoer (lagt inn i `chart_of_accounts.py` og `SKILLS.md`):**
  - `4310` Varekjøp import utland
  - `4510` Fremmedytelse / tjenester fra utlandet
  - `6555` Programvare / SaaS / skytjenester fra utlandet (f.eks. OpenAI, AWS, GitHub)
  - `7145` Reise / hotell i utlandet (0 % norsk MVA, 100 % skattemessig fradrag)
  - `7325` Annonsering utland (Meta Ads, Google Ads, TikTok)
- **Lønnskjøring (`backend/app/api/payroll.py`):** Fordeler automatisk på `5000`, `5010`, `5020`, `5180`, `5400` (AGA sone 1–5), `5190`, `5420`, `2930`, `2600`, `2940`, `2770`, `2780`, `2960` + oppretter automatisk Bilag #2 som overfører forskuddstrekk fra `1920` til bundet skattetrekkskonto `1950` (Skattebetalingsloven § 5-12).
- **Inngående balanse (`POST /api/accounting/opening-balance`):** Lar brukeren legge inn dagens saldo på bankkonto (`1920`) manuelt mot egenkapital (`2050`/`2000`), og legger inn avstemt åpningstransaksjon i banken.
- **Tom oppstart for ekte bruk:** `SEED_DEMO_DATA` i `backend/app/main.py` er `false` som standard slik at nye databaser starter 100 % blanke (0 kr) klare for SAF-T XML-import eller manuell inngående balanse.

### F. Hemmeligheter & Sikkerhet (KRITISK!)
- **ALDRI** commit eller push `backend/.env`, `*.db`, passord, SSH-nøkler eller tokens til GitHub!
- **ALDRI** start `llama-server` uten at brukeren eksplisitt ber om det.

---

## 3. Viktige filer i repoet (Kart for rask orientering)

```text
Phinx-accounting/
├── FOR_DEEPSEEK_AA_LESES.md          <-- DENNE FILEN (les alltid først)
├── database/
│   ├── phink_accounting_schema.sql   <-- Standard SQLite / PostgreSQL skjema (20 tabeller)
│   └── domeneshop_mariadb_11_4.sql   <-- Domeneshop MariaDB 11.4 skjema (med USE `phinkaccountin01`;)
├── deploy/
│   └── Caddyfile                     <-- Reverse proxy med auto-HTTPS for www.phink-acounting.no
├── backend/
│   ├── .env.example                  <-- Mal for miljøvariabler (kopieres lokalt til .env)
│   ├── requirements.txt              <-- Python-avhengigheter (inkl. pymysql & cryptography)
│   └── app/
│       ├── main.py                   <-- FastAPI oppstart, CORS, seeding (SEED_DEMO_DATA=false default)
│       ├── config.py                 <-- Laster .env via python-dotenv
│       ├── database.py               <-- SQLAlchemy engine (pool_pre_ping for MariaDB/MySQL) + migreringer
│       ├── models/accounting.py      <-- Alle SQLAlchemy-tabeller (20 tabeller)
│       ├── schemas/accounting.py     <-- Pydantic-skjemaer med dobbel-bokføring-validering
│       ├── data/chart_of_accounts.py <-- Norsk standard kontoplan (NS 4102)
│       ├── ai/
│       │   ├── llama_service.py      <-- AI CFO + bilagstolkning + sikker fallback
│       │   └── SKILLS.md             <-- Regnskaps- og prisregler for AI-assistenten
│       └── api/
│           ├── accounting.py         <-- Bilag, bank, KID-matching, MVA, rapporter, Altinn, IB, reset, låste innstillinger
│           ├── auth.py               <-- Registrering (PRIVAT/ENK/AS/FORENING/INSTITUSJON), login, roller, 150 kr profilendring
│           ├── billing.py            <-- Vipps Bedrift & Faktura + månedlige fakturapåminnelser
│           ├── payroll.py            <-- Ansattregister + automatisk norsk lønnskjøring
│           ├── saft_compliance.py    <-- Bilagsarkiv, Saldobalanse, SAF-T XML v1.30 eksport/import, 8-punkts kontroll, varslinger
│           ├── ai.py                 <-- AI-endepunkter
│           └── support.py            <-- Kundeservice Desk (tickets & meldinger)
└── frontend/
    ├── next.config.ts                <-- Proxyer /api/* og /uploads/* til BACKEND_INTERNAL_URL (default http://127.0.0.1:8000)
    ├── public/brand/logo.png         <-- Offisiell gullfarget Phink/Think Accounting logo
    └── src/
        ├── app/
        │   ├── page.tsx              <-- Landingsside (markedsføring)
        │   ├── priser/page.tsx       <-- Fullstendig norsk prisliste
        │   ├── register/page.tsx     <-- Kun registrering av ny konto
        │   ├── login/page.tsx        <-- Kun innlogging (kunder + administrator)
        │   └── app/page.tsx          <-- Beskyttet arbeidsflate (krever innlogging -> redirect /login)
        └── components/
            ├── AccountingWorkspace.tsx      <-- Hoved-dashboard (alle faner)
            ├── OpeningBalanceModal.tsx      <-- Manuell inngående balanse (Saldo på konto i dag)
            ├── ArchiveSaftCompliancePanel.tsx <-- Bilagsarkiv, SAF-T eksport/import, 8-punkts kontroll
            ├── PayrollPanel.tsx             <-- Lønnskjøring UI
            ├── BillingPanel.tsx             <-- Vipps Bedrift & Faktura UI
            ├── NotificationsPanel.tsx       <-- Varslinger (KID, forfall, månedlig fakturering)
            ├── ProfileModal.tsx             <-- Profilendring (kunde=150 kr forespørsel, admin=0 kr direkte på alle brukere)
            └── LogoSplash.tsx               <-- 1-sekunds logo-glimt (75vw x 75vh)
```

---

## 4. Tekniske feller du MÅ unngå (Windows + Next.js 16 + Domeneshop)

1. **Windows PowerShell ExecutionPolicy:**
   - `npm` og `npx` feiler ofte med `PSSecurityException` i PowerShell.
   - **Bruk ALLTID `npm.cmd` og `npx.cmd`** i PowerShell (eller kjør fra vanlig `cmd.exe`).
2. **Backend Python-miljø:**
   - System-Python mangler FastAPI/SQLAlchemy.
   - **Bruk ALLTID virtualenv:** `backend\venv\Scripts\python.exe` (f.eks. `.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000`).
3. **Next.js 16 `cacheComponents: true`:**
   - **IKKE** kall `new Date()` eller `Date.now()` direkte inne i render eller `useState(...)` i Client Components — det krasjer `npm.cmd run build` under prerendering!
   - Sett i stedet en statisk streng i `useState("2026-11-19")` og oppdater med `new Date()` inne i `useEffect(() => { ... }, [])`.
4. **Domeneshop MariaDB 11.4 tilkobling:**
   - Domeneshop blokkerer direkte ekstern MySQL-tilkobling fra hjemme-IP med `Access denied (1045)`.
   - Skal man koble lokalt til Domeneshop MariaDB kreves SSH-tunnel:
     `ssh -L 3307:phinkaccountin01.mysql.domeneshop.no:3306 <domeneshop-bruker>@login.domeneshop.no -N`
   - For rask lokal utvikling: bruk `DATABASE_URL=sqlite:///./phink_accounting.db` (ikke overskriv brukerens lokale `backend/.env`).

---

## 5. Slik kjører og verifiserer du lokalt (trygg sjekkliste før commit)

### Starte lokalt (2 terminaler)
**Terminal 1 — Backend (port 8000):**
```powershell
cd backend
$env:DATABASE_URL = "sqlite:///./phink_accounting.db"
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Terminal 2 — Frontend (port 3000):**
```powershell
cd frontend
npm.cmd run build
npm.cmd run start -- -H 127.0.0.1 -p 3000
```

### Obligatorisk sjekk før du committer eller pusher
1. **TypeScript-sjekk:** `cd frontend && npx.cmd tsc --noEmit` (må gi 0 feil)
2. **Produksjonsbygg:** `cd frontend && npm.cmd run build` (må gi exit code 0)
3. **Backend-import & test:** `cd backend && .\venv\Scripts\python.exe -c "import app.main; print('OK')"`
4. **Git-sikkerhetssjekk:** `git status` — bekreft at **ingen** `.env`, `.db`, passord eller nøkler er staget!

---

## 6. Kort oppsummering av brukerens preferanser
- Språk i UI og svar til eier: **Norsk** (tydelig, konkret og kortfattet).
- Be alltid om bekreftelse før offentlig deploy/publisering eller destruktive databaseoperasjoner i produksjon.
- Ved tvil om regnskapsregler eller priser: sjekk denne filen og `backend/app/ai/SKILLS.md` først!
