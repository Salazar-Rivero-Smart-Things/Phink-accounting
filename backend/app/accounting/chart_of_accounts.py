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

def seed_default_accounts(db: Session):
    """Sikrer at hele Conta/NS 4102 kontoplanen er opprettet i databasen ved oppstart."""
    for item in DEFAULT_ACCOUNTS:
        existing = db.query(Account).filter(Account.account_number == item["account_number"]).first()
        if not existing:
            account = Account(**item)
            db.add(account)
    db.commit()
