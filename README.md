# Phink Accounting &bull; Conta Edition 📊🧾🏦🎧

Et komplett, moderne og helhetlig norsk regnskapssystem inspirert av **Conta Regnskap / Conta Faktura**, bygget med **dobbel bokføring (NS 4102)**, **ekte bankavstemning**, **bilde- og PDF-bilagsmottak**, **Llama 3.1 AI-assistanse**, og en **integrert Kundeservicedesk (Human-in-the-Loop)** der du som operatør er til stede for kundene i sanntid.

---

## 🌟 Hovedmoduler i programmet (Conta-klone)

### 1. 🏦 Bank & Bankavstemning (Conta Bank)
* **Import av kontoutskrifter:** Støtte for transaksjonslister direkte fra nettbanken.
* **Automatisk matching:** Smart motor som matcher banktransaksjoner mot bokførte poster på konto 1920 (Bankinnskudd) basert på beløp, dato og referanse.
* **Avstemmingsdifferanse i sanntid:** Viser tydelig om bank og regnskap er 100% i balanse (Differanse = 0,00 NOK).
* **1-klikks hurtigbokføring:** Bokfør uavstemte poster som bankgebyr (7770) eller renteinntekt (8050) direkte med ett klikk.

### 2. 📥 Bilagsmottak (Innboks for Bilde & PDF)
* **Drag-and-drop opplasting:** Last opp kvitteringer og fakturaer som **både bilder (PNG, JPG, WEBP)** og **PDF-dokumenter**.
* **Forhåndsvisning:** Se originalbilaget direkte i grensesnittet i en innebygd viewer/modal.
* **AI-tolking (Meta Llama 3.1):** AI-en analyserer bilaget, trekker ut leverandør, beløp, MVA, KID og forfallsdato, og klargjør konteringslinjer.

### 3. ✍️ Føre regnskap (Conta-stil Bokføringsveiviser)
* **Kjøp / Utgift:** Enkel føring med valg av leverandør, MVA-sats (25%, 15%, 0%), kostnadskonto og betalingsmåte (bank eller leverandørgjeld).
* **Salg / Inntekt:** Direkte kobling mot fakturering.
* **Fritt bilag:** Fleksibel manuell debet/kredit med matematisk validering av balanse før bokføring.

### 4. 🧾 Conta Faktura & Kunder
* **Oppretting av salgsfaktura:** Vare- og tjenestelinjer, automatisk KID-generering og forfallsdato.
* **Automatisk bokføring:** Bokføres direkte i hovedboken: Debet 1500 (Kundefordringer), Kredit 3000 (Salgsinntekt), Kredit 2700 (Utgående MVA 25%).
* **Registrer innbetaling:** 1-klikks registrering av kundeoppgjør mot konto 1920.

### 5. 🏢 Leverandører & Leverandørreskontro
* **Leverandørregister:** Full oversikt over leverandører, org.nr, kontonummer og standard utgiftskonto.
* **Inngående fakturaer:** Sporing av forfall og utestående leverandørgjeld (konto 2400).
* **Betaling:** Utbetaling direkte fra driftskonto 1920.

### 6. 🏛️ MVA-melding (Merverdiavgift)
* **Termin 1–6:** Automatisk beregning av 2-månedlige terminer etter Skatteetatens standard.
* **MVA-grunnlag:** Spesifikasjon av utgående MVA (konto 2700), inngående MVA-fradrag (konto 2710) og netto MVA å betale/til gode.

### 7. 📈 Finansielle Rapporter & Hovedbok
* **Resultatregnskap (P&L):** Driftsinntekter, driftskostnader og årsresultat før skatt.
* **Balanserapport:** Eiendeler (bank, kundefordringer) vs Egenkapital og Gjeld.
* **Bilagsjournal / Hovedbok:** Fullstendig søk- og filtrerbar logg over alle historiske bilag med debet/kredit og filvedlegg.

### 8. 🎧 Kundeservice Desk & Operatørstasjon (Deg + AI)
* **1. linje Support (Llama 3.1):** Tar imot kundehenvendelser automatisk.
* **Eskalering til operatør (Deg):** Ved økonomiske hendelser eller spørsmål om bilag kan du snakke direkte med kundene i sanntid og godkjenne oppgjør eller gi bistand.

### 9. 🤖 Phink AI CFO (Meta Llama 3.1)
* Still strategiske spørsmål om bedriftens likviditet, skatt, kostnadskutt og nøkkeltall.

---

## 🚀 Oppstart

Kjør oppstartsskriptet fra rotmappen:
```cmd
start-all.bat
```
Eller i PowerShell:
```powershell
.\start.ps1
```

* **Frontend Dashbord:** `http://localhost:3000`
* **FastAPI Backend & API Docs:** `http://localhost:8000/docs`
* **Opplastede bilag (Statisk servering):** `http://localhost:8000/uploads/`
