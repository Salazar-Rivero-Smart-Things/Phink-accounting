from sqlalchemy.orm import Session
from app.models.accounting import Account

# Norsk Standard Kontoplan (NS 4102) - Utvidet Conta-kompatibel kontoplan for SMB / AS / ENK
DEFAULT_ACCOUNTS = [
    # 1xxx: Eiendeler, Anleggsmidler, Varelager, Fordringer og Bank
    {"account_number": 1000, "name": "Forskning og utvikling", "account_type": "ASSET", "vat_code": "NONE", "description": "Immaterielle eiendeler"},
    {"account_number": 1100, "name": "Bygninger og fast eiendom", "account_type": "ASSET", "vat_code": "NONE", "description": "Fast eiendom"},
    {"account_number": 1200, "name": "Maskiner og anlegg", "account_type": "ASSET", "vat_code": "HIGH_25", "description": "Varige driftsmidler"},
    {"account_number": 1230, "name": "Biler og kjøretøy", "account_type": "ASSET", "vat_code": "HIGH_25", "description": "Firmabiler og varebiler"},
    {"account_number": 1250, "name": "Inventar", "account_type": "ASSET", "vat_code": "HIGH_25", "description": "Varig kontor- og butikkinventar"},
    {"account_number": 1280, "name": "Kontormaskiner og IT-utstyr", "account_type": "ASSET", "vat_code": "HIGH_25", "description": "Servere og større IT-utstyr"},
    {"account_number": 1400, "name": "Lager av råvarer", "account_type": "ASSET", "vat_code": "NONE", "description": "Råvarelager"},
    {"account_number": 1460, "name": "Innkjøpte varer for videresalg (Varelager)", "account_type": "ASSET", "vat_code": "NONE", "description": "Handelsvarer på lager"},
    {"account_number": 1500, "name": "Kundefordringer", "account_type": "ASSET", "vat_code": "NONE", "description": "Utestående fakturaer til kunder"},
    {"account_number": 1580, "name": "Avsetning tap på krav", "account_type": "ASSET", "vat_code": "NONE", "description": "Usikre kundefordringer"},
    {"account_number": 1700, "name": "Forskuddsbetalt leie", "account_type": "ASSET", "vat_code": "NONE", "description": "Periodeavgrensning husleie"},
    {"account_number": 1710, "name": "Forskuddsbetalt forsikring", "account_type": "ASSET", "vat_code": "NONE", "description": "Periodeavgrensning forsikring"},
    {"account_number": 1900, "name": "Kontanter / Kasse", "account_type": "ASSET", "vat_code": "NONE", "description": "Kontantkasse"},
    {"account_number": 1920, "name": "Bankinnskudd drift", "account_type": "ASSET", "vat_code": "NONE", "description": "Hovedkonto bank"},
    {"account_number": 1950, "name": "Bankinnskudd for skattetrekk (Skattetrekkskonto)", "account_type": "ASSET", "vat_code": "NONE", "description": "Lovpålagt sperret konto for ansattes forskuddstrekk"},

    # 2xxx: Egenkapital, Gjeld, Skatt, MVA og Lønn
    {"account_number": 2000, "name": "Egenkapital / Aksjekapital", "account_type": "EQUITY", "vat_code": "NONE", "description": "Selskapets innskutt egenkapital"},
    {"account_number": 2050, "name": "Annen egenkapital", "account_type": "EQUITY", "vat_code": "NONE", "description": "Opptjent egenkapital"},
    {"account_number": 2220, "name": "Gjeld til kredittinstitusjoner (Banklån)", "account_type": "LIABILITY", "vat_code": "NONE", "description": "Langsiktig banklån"},
    {"account_number": 2380, "name": "Kassekreditt", "account_type": "LIABILITY", "vat_code": "NONE", "description": "Driftskreditt bank"},
    {"account_number": 2400, "name": "Leverandørgjeld", "account_type": "LIABILITY", "vat_code": "NONE", "description": "Ubetalte regninger til leverandører"},
    {"account_number": 2500, "name": "Betalbar skatt, ikke utlignet", "account_type": "LIABILITY", "vat_code": "NONE", "description": "Avsatt selskapsskatt"},
    {"account_number": 2600, "name": "Forskuddstrekk (Skattetrekk ansatte)", "account_type": "LIABILITY", "vat_code": "NONE", "description": "Trukket skatt fra ansattes lønn"},
    {"account_number": 2650, "name": "Fagforeningstrekk", "account_type": "LIABILITY", "vat_code": "NONE", "description": "Trukket fagforeningskontingent"},
    {"account_number": 2700, "name": "Utgående merverdiavgift (25%)", "account_type": "LIABILITY", "vat_code": "HIGH_25", "description": "MVA krevd inn ved salg (høy sats)"},
    {"account_number": 2701, "name": "Utgående merverdiavgift (15%)", "account_type": "LIABILITY", "vat_code": "MED_15", "description": "MVA ved salg av mat/drikke"},
    {"account_number": 2702, "name": "Utgående merverdiavgift (12%)", "account_type": "LIABILITY", "vat_code": "LOW_12", "description": "MVA ved persontransport/overnatting/kultur"},
    {"account_number": 2705, "name": "Utgående MVA tjenester fra utlandet (Snudd avregning 25%)", "account_type": "LIABILITY", "vat_code": "FOREIGN_25", "description": "Beregnet MVA ved kjøp av fjernleverbare tjenester fra utlandet"},
    {"account_number": 2710, "name": "Inngående merverdiavgift (25%)", "account_type": "ASSET", "vat_code": "HIGH_25", "description": "MVA-fradrag på kjøp (høy sats)"},
    {"account_number": 2711, "name": "Inngående merverdiavgift (15%)", "account_type": "ASSET", "vat_code": "MED_15", "description": "MVA-fradrag på næringsmidler"},
    {"account_number": 2712, "name": "Inngående merverdiavgift (12%)", "account_type": "ASSET", "vat_code": "LOW_12", "description": "MVA-fradrag på persontransport og hotell"},
    {"account_number": 2715, "name": "Inngående MVA tjenester fra utlandet (Fradrag 25%)", "account_type": "ASSET", "vat_code": "FOREIGN_25", "description": "MVA-fradrag på fjernleverbare tjenester fra utlandet (snudd avregning)"},
    {"account_number": 2740, "name": "Oppgjørskonto merverdiavgift", "account_type": "LIABILITY", "vat_code": "NONE", "description": "MVA-oppgjør mot Skatteetaten"},
    {"account_number": 2770, "name": "Skyldig arbeidsgiveravgift (AGA)", "account_type": "LIABILITY", "vat_code": "NONE", "description": "Påløpt arbeidsgiveravgift av lønn"},
    {"account_number": 2780, "name": "Påløpt arbeidsgiveravgift på feriepenger", "account_type": "LIABILITY", "vat_code": "NONE", "description": "Avsatt AGA på opptjente feriepenger"},
    {"account_number": 2800, "name": "Avsatt utbytte", "account_type": "LIABILITY", "vat_code": "NONE", "description": "Utbytte til aksjonærer"},
    {"account_number": 2900, "name": "Forskudd fra kunder", "account_type": "LIABILITY", "vat_code": "NONE", "description": "Mottatt forskuddsbetaling"},
    {"account_number": 2910, "name": "Gjeld til ansatte og eiere (Utlegg)", "account_type": "LIABILITY", "vat_code": "NONE", "description": "Privatutlegg og reiseregninger fra ansatte"},
    {"account_number": 2930, "name": "Skyldig lønn", "account_type": "LIABILITY", "vat_code": "NONE", "description": "Nettolønn klar til utbetaling"},
    {"account_number": 2940, "name": "Skyldige feriepenger", "account_type": "LIABILITY", "vat_code": "NONE", "description": "Opptjente feriepenger til ansatte"},
    {"account_number": 2960, "name": "Påløpt kostnad (inkl. OTP pensjon)", "account_type": "LIABILITY", "vat_code": "NONE", "description": "Påløpte drifts- og pensjonskostnader"},

    # 3xxx: Salgs- og driftsinntekter
    {"account_number": 3000, "name": "Salgsinntekt varer (25% mva)", "account_type": "REVENUE", "vat_code": "HIGH_25", "description": "Salg av handelsvarer med høy sats"},
    {"account_number": 3020, "name": "Salgsinntekt tjenester / konsulenttimer (25% mva)", "account_type": "REVENUE", "vat_code": "HIGH_25", "description": "Salg av timer og tjenester"},
    {"account_number": 3030, "name": "Salgsinntekt mat og næringsmidler (15% mva)", "account_type": "REVENUE", "vat_code": "MED_15", "description": "Servering og matvarer"},
    {"account_number": 3040, "name": "Salgsinntekt transport/hotell/kultur (12% mva)", "account_type": "REVENUE", "vat_code": "LOW_12", "description": "Persontransport og overnatting"},
    {"account_number": 3100, "name": "Salgsinntekt avgiftsfri (0% mva / eksport)", "account_type": "REVENUE", "vat_code": "NONE", "description": "Avgiftsfritt salg innenfor MVA-loven"},
    {"account_number": 3200, "name": "Salgsinntekt utenfor avgiftsområdet", "account_type": "REVENUE", "vat_code": "NONE", "description": "Helse, undervisning, finans"},
    {"account_number": 3400, "name": "Offentlige tilskudd og refusjoner", "account_type": "REVENUE", "vat_code": "NONE", "description": "Støtteordninger og tilskudd"},
    {"account_number": 3600, "name": "Leieinntekter fast eiendom", "account_type": "REVENUE", "vat_code": "NONE", "description": "Utleie av lokaler"},

    # 4xxx: Varekostnad og underleverandører (Prosjektkostnader)
    {"account_number": 4000, "name": "Innkjøp av råvarer og halvfabrikata", "account_type": "EXPENSE", "vat_code": "HIGH_25", "description": "Materialer til produksjon og prosjekt"},
    {"account_number": 4300, "name": "Innkjøp av varer for videresalg", "account_type": "EXPENSE", "vat_code": "HIGH_25", "description": "Ordinært varekjøp"},
    {"account_number": 4310, "name": "Innkjøp av varer fra utlandet (Import, skattefradrag)", "account_type": "EXPENSE", "vat_code": "FOREIGN_IMPORT", "description": "Fradragsberettiget vareimport fra utlandet (innførsels-MVA)"},
    {"account_number": 4360, "name": "Frakt, toll og spedisjon ved varekjøp", "account_type": "EXPENSE", "vat_code": "HIGH_25", "description": "Inngående frakt på varer"},
    {"account_number": 4500, "name": "Fremmedytelser og underleverandører", "account_type": "EXPENSE", "vat_code": "HIGH_25", "description": "Innleid arbeidskraft og underentreprenører på prosjekt"},
    {"account_number": 4510, "name": "Kjøp av tjenester fra utlandet (Skattefradrag / snudd avregning)", "account_type": "EXPENSE", "vat_code": "FOREIGN_25", "description": "Fradragsberettigede konsulent- og fjernleverbare tjenester fra utlandet"},

    # 5xxx: Lønnskostnad, Feriepenger, AGA og Personal
    {"account_number": 5000, "name": "Lønn til ansatte", "account_type": "EXPENSE", "vat_code": "NONE", "description": "Fastlønn og timelønn"},
    {"account_number": 5010, "name": "Overtidslønn", "account_type": "EXPENSE", "vat_code": "NONE", "description": "Utbetalt overtid"},
    {"account_number": 5020, "name": "Bonus og provisjon til ansatte", "account_type": "EXPENSE", "vat_code": "NONE", "description": "Resultatbonus og provisjon"},
    {"account_number": 5180, "name": "Feriepenger avsatt", "account_type": "EXPENSE", "vat_code": "NONE", "description": "Opptjente feriepenger (12%)"},
    {"account_number": 5190, "name": "Påløpt arbeidsgiveravgift på feriepenger", "account_type": "EXPENSE", "vat_code": "NONE", "description": "AGA av avsatte feriepenger"},
    {"account_number": 5330, "name": "Styrehonorar", "account_type": "EXPENSE", "vat_code": "NONE", "description": "Honorar til styremedlemmer"},
    {"account_number": 5400, "name": "Arbeidsgiveravgift (AGA)", "account_type": "EXPENSE", "vat_code": "NONE", "description": "Arbeidsgiveravgift av lønn (14,1%)"},
    {"account_number": 5420, "name": "Innberetningspliktig pensjonskostnad (OTP)", "account_type": "EXPENSE", "vat_code": "NONE", "description": "Obligatorisk tjenestepensjon"},
    {"account_number": 5800, "name": "Refusjon av sykepenger fra NAV", "account_type": "EXPENSE", "vat_code": "NONE", "description": "Krediteres ved refusjon fra NAV"},
    {"account_number": 5900, "name": "Gaver til ansatte", "account_type": "EXPENSE", "vat_code": "NONE", "description": "Personal- og jubileumsgaver"},
    {"account_number": 5920, "name": "Yrkesskade- og personalforsikring", "account_type": "EXPENSE", "vat_code": "NONE", "description": "Lovpålagt yrkesskadeforsikring"},
    {"account_number": 5950, "name": "Velferdstiltak og bedriftshelsetjeneste", "account_type": "EXPENSE", "vat_code": "NONE", "description": "HMS og sosiale tiltak ansatte"},

    # 6xxx: Driftskostnader (Lokaler, Verktøy, IT, Regnskap/Advokat, Kontor, Telefon)
    {"account_number": 6010, "name": "Avskrivning på maskiner, biler og inventar", "account_type": "EXPENSE", "vat_code": "NONE", "description": "Ordinære avskrivninger"},
    {"account_number": 6100, "name": "Frakt og transportkostnad ved salg", "account_type": "EXPENSE", "vat_code": "HIGH_25", "description": "Utgående frakt til kunder"},
    {"account_number": 6300, "name": "Leie lokaler", "account_type": "EXPENSE", "vat_code": "NONE", "description": "Husleie for kontor/lager"},
    {"account_number": 6340, "name": "Lys og varme (Strøm)", "account_type": "EXPENSE", "vat_code": "HIGH_25", "description": "Strøm og oppvarming i lokaler"},
    {"account_number": 6360, "name": "Renhold og vaktmestertjenester", "account_type": "EXPENSE", "vat_code": "HIGH_25", "description": "Vask og renhold av lokaler"},
    {"account_number": 6400, "name": "Leie maskiner og inventar", "account_type": "EXPENSE", "vat_code": "HIGH_25", "description": "Leie av driftsutstyr"},
    {"account_number": 6440, "name": "Leasing av biler og transportmidler", "account_type": "EXPENSE", "vat_code": "HIGH_25", "description": "Billeasing"},
    {"account_number": 6510, "name": "Håndverktøy og mindre redskap", "account_type": "EXPENSE", "vat_code": "HIGH_25", "description": "Verktøy under 30 000 kr"},
    {"account_number": 6540, "name": "IT-drift, programvare og skylisenser (inkl. småutstyr)", "account_type": "EXPENSE", "vat_code": "HIGH_25", "description": "SaaS, servere, programvare og inventar < 30 000 kr"},
    {"account_number": 6550, "name": "Driftsmateriale og programvarelisenser", "account_type": "EXPENSE", "vat_code": "HIGH_25", "description": "Programvare og lisenser (Conta-standard)"},
    {"account_number": 6555, "name": "Programvare, skytjenester & SaaS fra utlandet (Skattefradrag)", "account_type": "EXPENSE", "vat_code": "FOREIGN_25", "description": "Fradragsberettigede lisenser fra utlandet (Google, AWS, GitHub, OpenAI m.fl. — snudd avregning)"},
    {"account_number": 6620, "name": "Reparasjon og vedlikehold utstyr", "account_type": "EXPENSE", "vat_code": "HIGH_25", "description": "Vedlikehold maskiner og utstyr"},
    {"account_number": 6700, "name": "Revisjonshonorar", "account_type": "EXPENSE", "vat_code": "HIGH_25", "description": "Honorar til revisor"},
    {"account_number": 6720, "name": "Honorar for økonomisk og juridisk bistand", "account_type": "EXPENSE", "vat_code": "HIGH_25", "description": "Regnskapsfører, advokat og rådgivning"},
    {"account_number": 6800, "name": "Kontorrekvisita og trykksaker", "account_type": "EXPENSE", "vat_code": "HIGH_25", "description": "Småanskaffelser til kontor"},
    {"account_number": 6860, "name": "Møte, kurs og oppdatering", "account_type": "EXPENSE", "vat_code": "NONE", "description": "Fagkurs og kompetanseheving"},
    {"account_number": 6900, "name": "Telefon og internett", "account_type": "EXPENSE", "vat_code": "HIGH_25", "description": "Bredbånd og mobilabonnement"},
    {"account_number": 6940, "name": "Internett og datakommunikasjon", "account_type": "EXPENSE", "vat_code": "HIGH_25", "description": "Fiber, bredbånd og linjer"},

    # 7xxx: Bil, Reise, Salg/Reklame, Representasjon, Forsikring og Gebyrer
    {"account_number": 7000, "name": "Drivstoff og lading firmabil", "account_type": "EXPENSE", "vat_code": "HIGH_25", "description": "Diesel, bensin og elbillading"},
    {"account_number": 7020, "name": "Vedlikehold og verksted bil", "account_type": "EXPENSE", "vat_code": "HIGH_25", "description": "Service og dekk firmabil"},
    {"account_number": 7080, "name": "Bilgodtgjørelse (Kilometergodtgjørelse)", "account_type": "EXPENSE", "vat_code": "NONE", "description": "Bruk av privatbil i tjeneste etter statens satser"},
    {"account_number": 7140, "name": "Reisekostnad / diett", "account_type": "EXPENSE", "vat_code": "LOW_12", "description": "Tjenestereiser, fly, tog, taxi og hotell"},
    {"account_number": 7145, "name": "Tjenestereise og hotell i utlandet (Skattefradrag, 0% norsk MVA)", "account_type": "EXPENSE", "vat_code": "NONE", "description": "Fradragsberettiget næringsreise i utlandet (utenlandsk MVA kan ikke trekkes fra på norsk MVA-melding, men hele kostnaden gir skattefradrag)"},
    {"account_number": 7150, "name": "Diettkostnad, ikke oppgavepliktig", "account_type": "EXPENSE", "vat_code": "NONE", "description": "Diett etter statens satser"},
    {"account_number": 7320, "name": "Reklame og annonsering", "account_type": "EXPENSE", "vat_code": "HIGH_25", "description": "Markedsføring i Norge"},
    {"account_number": 7325, "name": "Annonsering & markedsføring i utlandet (Meta/Google Ads, skattefradrag)", "account_type": "EXPENSE", "vat_code": "FOREIGN_25", "description": "Fradragsberettiget annonsering kjøpt fra utlandet (Meta Ireland, Google Ireland — snudd avregning 25% MVA)"},
    {"account_number": 7350, "name": "Representasjon, fradragsberettiget", "account_type": "EXPENSE", "vat_code": "NONE", "description": "Enkel bevertning av kunder (0% MVA-fradrag)"},
    {"account_number": 7360, "name": "Representasjon, ikke fradragsberettiget", "account_type": "EXPENSE", "vat_code": "NONE", "description": "Ikke-fradragsberettiget bevertning"},
    {"account_number": 7400, "name": "Kontingenter og medlemskap", "account_type": "EXPENSE", "vat_code": "NONE", "description": "Bransje- og arbeidsgiverforeninger"},
    {"account_number": 7500, "name": "Forsikringspremie", "account_type": "EXPENSE", "vat_code": "NONE", "description": "Bedrifts-, ansvars- og innboforsikring (0% MVA)"},
    {"account_number": 7770, "name": "Bank- og kortgebyrer", "account_type": "EXPENSE", "vat_code": "NONE", "description": "Transaksjonsgebyrer bank og Vipps"},
    {"account_number": 7775, "name": "Inkassogebyr og purregebyr (Skattefradrag)", "account_type": "EXPENSE", "vat_code": "NONE", "description": "Fradragsberettigede inkassogebyrer, purregebyrer og inndrivelseskostnader på næringsrelaterte regninger (0 % MVA, fullt skattefradrag)"},
    {"account_number": 7830, "name": "Konstatert tap på kundefordringer", "account_type": "EXPENSE", "vat_code": "NONE", "description": "Endelig tap på utestående krav"},

    # 8xxx: Finansposter og Skatt
    {"account_number": 8050, "name": "Renteinntekter", "account_type": "REVENUE", "vat_code": "NONE", "description": "Renter på bankinnskudd"},
    {"account_number": 8060, "name": "Valutagevinst (Agio)", "account_type": "REVENUE", "vat_code": "NONE", "description": "Gevinst ved valutakursendring"},
    {"account_number": 8150, "name": "Rentekostnader og forsinkelsesrenter (inkl. inkasso)", "account_type": "EXPENSE", "vat_code": "NONE", "description": "Lånerenter og forsinkelsesrenter på næringsgjeld / inkasso (skattefradrag)"},
    {"account_number": 8160, "name": "Valutatap (Disagio)", "account_type": "EXPENSE", "vat_code": "NONE", "description": "Tap ved valutakursendring"},
    {"account_number": 8300, "name": "Betalbar skatt", "account_type": "EXPENSE", "vat_code": "NONE", "description": "Skattekostnad på resultat"}
]

# Official English translations of Norwegian Standard Chart of Accounts (NS 4102)
# Compliant with the Norwegian Accounting Act (Regnskapsloven) & Bookkeeping Act (Bokføringsloven)
ENGLISH_ACCOUNTS_MAP = {
    # 1xxx: Assets (Non-current Assets, Inventory, Receivables & Bank)
    1000: ("Research and Development", "Intangible fixed assets (R&D)"),
    1100: ("Buildings and Real Property", "Real estate and commercial property"),
    1200: ("Machinery and Plant", "Tangible fixed operating assets"),
    1230: ("Company Vehicles", "Cars, vans and transport vehicles"),
    1250: ("Furniture and Fixtures", "Long-term office and store fixtures"),
    1280: ("Office Equipment and IT Hardware", "Servers and capitalised IT equipment"),
    1400: ("Inventory — Raw Materials", "Raw material stock"),
    1460: ("Inventory — Goods for Resale", "Merchandise held for resale"),
    1500: ("Accounts Receivable (Trade Debtors)", "Unpaid customer sales invoices"),
    1580: ("Provision for Doubtful Debts", "Allowance for bad/uncertain receivables"),
    1700: ("Prepaid Rent", "Accrual/prepayment for office rent"),
    1710: ("Prepaid Insurance", "Accrual/prepayment for insurance policies"),
    1900: ("Cash on Hand / Petty Cash", "Physical cash register"),
    1920: ("Operating Bank Account", "Primary business bank account"),
    1950: ("Restricted Tax Withholding Bank Account", "Statutory restricted account for employee PAYE withholding tax (Tax Payment Act § 5-12)"),

    # 2xxx: Equity, Liabilities, Taxes, VAT & Payroll
    2000: ("Share Capital / Paid-in Equity", "Company share capital / owner's paid-in equity"),
    2050: ("Retained Earnings / Other Equity", "Accumulated earned equity"),
    2220: ("Long-term Bank Loans", "Long-term debt to credit institutions"),
    2380: ("Bank Overdraft Facility", "Short-term operating credit line"),
    2400: ("Accounts Payable (Trade Creditors)", "Unpaid supplier invoices"),
    2500: ("Income Tax Payable (Not Assessed)", "Accrued corporate income tax"),
    2600: ("Employee Withholding Tax Payable (PAYE)", "Tax deducted from employee salaries"),
    2650: ("Trade Union Dues Payable", "Union fees deducted from salaries"),
    2700: ("Output VAT — High Rate (25%)", "VAT collected on standard-rate sales"),
    2701: ("Output VAT — Medium Rate (15%)", "VAT collected on food & beverages"),
    2702: ("Output VAT — Low Rate (12%)", "VAT collected on passenger transport, lodging & culture"),
    2705: ("Output VAT — Foreign Services (Reverse Charge 25%)", "Calculated output VAT on remotely delivered services purchased abroad"),
    2710: ("Input VAT — Deductible (25%)", "Deductible VAT on standard-rate purchases"),
    2711: ("Input VAT — Deductible (15%)", "Deductible VAT on food & groceries"),
    2712: ("Input VAT — Deductible (12%)", "Deductible VAT on passenger transport & hotel"),
    2715: ("Input VAT — Foreign Services (Reverse Charge Deduction 25%)", "Deductible input VAT on foreign services (reverse charge)"),
    2740: ("VAT Settlement Account", "VAT clearing account with the Norwegian Tax Administration (Skatteetaten)"),
    2770: ("Employer's National Insurance Contributions Payable (AGA)", "Accrued employer payroll tax"),
    2780: ("Accrued Employer's National Insurance on Holiday Pay", "Accrued AGA on earned holiday pay"),
    2800: ("Proposed Dividends Payable", "Approved dividends payable to shareholders"),
    2900: ("Customer Prepayments / Deferred Revenue", "Advance payments received from customers"),
    2910: ("Debt to Employees and Owners (Expense Reimbursements)", "Out-of-pocket expenses and travel claims"),
    2930: ("Net Salaries Payable", "Net payroll ready for bank payout"),
    2940: ("Holiday Pay Payable", "Accrued statutory holiday pay owed to employees"),
    2960: ("Accrued Expenses (incl. Mandatory Pension OTP)", "Accrued operating and pension liabilities"),

    # 3xxx: Operating Revenues
    3000: ("Sales Revenue — Goods (25% VAT)", "Taxable sale of goods at standard rate"),
    3020: ("Sales Revenue — Services & Consulting (25% VAT)", "Taxable sale of services and billable hours"),
    3030: ("Sales Revenue — Food & Beverages (15% VAT)", "Sale of food and groceries"),
    3040: ("Sales Revenue — Transport, Lodging & Culture (12% VAT)", "Passenger transport, hotel and cultural tickets"),
    3100: ("Sales Revenue — Zero-Rated / Export (0% VAT)", "VAT-exempt sales and international exports"),
    3200: ("Sales Revenue — Outside VAT Scope", "Health, education and financial services"),
    3400: ("Government Grants and Subsidies", "Public grants and reimbursements"),
    3600: ("Rental Income — Real Property", "Income from leasing premises"),

    # 4xxx: Cost of Goods Sold & Subcontractors
    4000: ("Purchases of Raw Materials & Components", "Materials for production and projects"),
    4300: ("Purchases of Goods for Resale", "Standard merchandise purchases"),
    4310: ("Purchases of Goods — Foreign Import (Tax-Deductible)", "Tax-deductible imported goods from abroad (import VAT)"),
    4360: ("Freight, Customs & Forwarding on Purchases", "Inbound freight and customs clearance"),
    4500: ("Subcontractors & External Services", "Hired contractors and project subcontractors"),
    4510: ("Foreign Subcontractors & Services (Tax-Deductible / Reverse Charge)", "Tax-deductible foreign consulting and remote services"),

    # 5xxx: Payroll, Holiday Pay, Employer Tax & Personnel
    5000: ("Salaries and Wages", "Fixed salaries and hourly wages"),
    5010: ("Overtime Pay", "Paid overtime wages"),
    5020: ("Employee Bonuses & Commissions", "Performance bonuses and sales commissions"),
    5180: ("Holiday Pay Expense (12%)", "Statutory accrued holiday pay"),
    5190: ("Employer's National Insurance on Holiday Pay", "AGA on accrued holiday pay"),
    5330: ("Board of Directors' Fees", "Remuneration to board members"),
    5400: ("Employer's National Insurance Contributions (AGA)", "Employer payroll tax (Zones 1–5)"),
    5420: ("Mandatory Occupational Pension Expense (OTP)", "Reportable statutory pension contributions"),
    5800: ("Sick Pay Reimbursements from NAV", "Credited upon NAV sick-leave refund"),
    5900: ("Employee Gifts & Recognition", "Staff and anniversary gifts"),
    5920: ("Occupational Injury & Personnel Insurance", "Statutory workers' compensation insurance"),
    5950: ("Employee Welfare & Occupational Health (HSE)", "Staff welfare and occupational health services"),

    # 6xxx: Operating Expenses (Premises, Tools, IT, Accounting/Legal, Office, Telecom)
    6010: ("Depreciation of Machinery, Vehicles & Fixtures", "Ordinary fixed-asset depreciation"),
    6100: ("Outbound Freight & Shipping", "Delivery freight to customers"),
    6300: ("Rent of Premises", "Office and warehouse rent"),
    6340: ("Electricity, Heating & Utilities", "Power and heating for premises"),
    6360: ("Cleaning & Janitorial Services", "Cleaning and maintenance of premises"),
    6400: ("Equipment & Machinery Rental", "Rental of operating equipment"),
    6440: ("Vehicle Leasing", "Leasing of company cars and vans"),
    6510: ("Hand Tools & Minor Equipment", "Tools below NOK 30,000 capitalisation threshold"),
    6540: ("IT Operations, Software & Cloud Licences (incl. Small Equipment)", "SaaS, servers, software and equipment < NOK 30,000"),
    6550: ("Operating Materials & Software Licences", "Software subscriptions and licences"),
    6555: ("Foreign Software, Cloud & SaaS (Tax-Deductible / Reverse Charge)", "Tax-deductible foreign software/cloud (Google, AWS, GitHub, OpenAI — reverse charge VAT)"),
    6620: ("Repair & Maintenance of Equipment", "Maintenance of machinery and equipment"),
    6700: ("Audit Fees", "Statutory auditor fees"),
    6720: ("Accounting, Legal & Advisory Fees", "Bookkeeping, legal counsel and consulting"),
    6800: ("Office Supplies & Stationery", "Small office consumables and printing"),
    6860: ("Courses, Seminars & Professional Training", "Conferences and staff training"),
    6900: ("Telephone & Mobile Subscriptions", "Mobile plans and telecommunications"),
    6940: ("Internet & Data Communications", "Broadband, fibre and network lines"),

    # 7xxx: Vehicles, Travel, Marketing, Representation, Insurance & Fees
    7000: ("Fuel & EV Charging — Company Vehicles", "Petrol, diesel and electric vehicle charging"),
    7020: ("Vehicle Maintenance & Servicing", "Workshop servicing and tyres"),
    7080: ("Mileage Allowance (Private Vehicle)", "Tax-free mileage reimbursement at Norwegian state rates"),
    7140: ("Business Travel & Lodging (Domestic)", "Flights, trains, taxis and hotels (12% VAT)"),
    7145: ("Foreign Business Travel & Hotel (0% NO VAT, 100% Tax-Deductible)", "Tax-deductible foreign business travel; foreign VAT not reclaimed in Norway, full cost tax-deductible"),
    7150: ("Per Diem / Travel Subsistence (Non-Reportable)", "Tax-free daily travel allowances at state rates"),
    7320: ("Advertising & Marketing (Domestic)", "Domestic marketing and campaigns"),
    7325: ("Foreign Advertising & Marketing — Meta/Google Ads (Tax-Deductible)", "Tax-deductible foreign ads (Meta Ireland, Google Ireland — 25% reverse charge VAT)"),
    7350: ("Client Entertainment — Tax-Deductible", "Modest client hospitality (0% VAT deduction)"),
    7360: ("Client Entertainment — Non-Deductible", "Non-deductible representation costs"),
    7400: ("Memberships & Trade Association Fees", "Industry and employer association dues"),
    7500: ("Business & Liability Insurance Premiums", "Commercial, liability and property insurance (0% VAT)"),
    7770: ("Bank & Payment Processing Fees", "Bank transaction fees and Vipps Bedrift fees"),
    7775: ("Debt Collection & Reminder Fees — Inkasso (0% VAT, Tax-Deductible)", "Tax-deductible collection, reminder and recovery fees on business invoices (0% VAT)"),
    7830: ("Confirmed Bad Debt Losses", "Final write-off of uncollectible trade receivables"),

    # 8xxx: Financial Items & Corporate Tax
    8050: ("Interest Income", "Interest earned on bank deposits"),
    8060: ("Foreign Exchange Gain (Agio)", "Realised currency exchange gains"),
    8150: ("Interest Expenses & Late Payment Interest (incl. Debt Collection)", "Loan interest and statutory late-payment/collection interest (tax-deductible)"),
    8160: ("Foreign Exchange Loss (Disagio)", "Realised currency exchange losses"),
    8300: ("Income Tax Expense", "Corporate income tax on profit"),
}


def get_localized_account_fields(account_number: int, fallback_name: str, fallback_desc: str | None, lang: str = "nb") -> tuple[str, str | None]:
    """Returns official English NS 4102 account name & description when lang='en', else Norwegian."""
    if (lang or "nb").lower().startswith("en") and account_number in ENGLISH_ACCOUNTS_MAP:
        en_name, en_desc = ENGLISH_ACCOUNTS_MAP[account_number]
        return en_name, en_desc
    return fallback_name, fallback_desc


def seed_default_accounts(db: Session):
    """Sikrer at hele Conta/NS 4102 kontoplanen er opprettet i databasen ved oppstart."""
    for item in DEFAULT_ACCOUNTS:
        existing = db.query(Account).filter(Account.account_number == item["account_number"]).first()
        if not existing:
            account = Account(**item)
            db.add(account)
    db.commit()
