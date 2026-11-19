import Link from "next/link";
import {
  ArrowRight,
  Bell,
  Building2,
  CheckCircle,
  Cpu,
  Download,
  FileCheck,
  FolderCheck,
  Headphones,
  Landmark,
  Receipt,
  ShieldCheck,
  Smartphone,
  Users,
} from "lucide-react";
import LogoSplash from "@/components/LogoSplash";

const REASONS = [
  {
    icon: Cpu,
    title: "Lokal AI CFO som faktisk kan norsk regnskap",
    body: "Phink AI (Llama 3.1 + norsk regnskapsregelverk) tolker kvitteringer og fakturaer automatisk, foreslår riktig NS 4102-konto og beskytter deg mot klassiske MVA-feller som 12 % hotell/reise, 0 % forsikring og 0 % MVA-fradrag på kundemiddag.",
  },
  {
    icon: Users,
    title: "Helautomatisk norsk lønnskjøring på sekunder",
    body: "Slipp manuell fordeling! Systemet beregner og bokfører fastlønn (5000), overtid, bonus, feriepenger (5180/2940), AGA for alle soner 1–5 (5400/2770), OTP-pensjon og lovpålagt overføring til sperret skattetrekkskonto (1950) med øre-presisjon.",
  },
  {
    icon: Receipt,
    title: "Norsk fakturering med MVA & automatisk KID-integrasjon",
    body: "Send fakturaer med 25 %, 15 %, 12 % eller 0 % MVA. Du har KID-avtalen med banken din — og programmet gjenkjenner KID-innbetalinger automatisk, bokfører betalingen i regnskapet, og varsler deg under Varslinger dersom en faktura forblir uoppgjort!",
  },
  {
    icon: Download,
    title: "SAF-T Financial XML v1.30 — både eksport OG import",
    body: "Bytt enkelt fra Conta, Fiken eller Tripletex ved å importere din eksisterende SAF-T XML-fil direkte inn i Phink — og eksporter full Skatteetaten-godkjent SAF-T XML med ett klikk til revisor eller bokettersyn.",
  },
  {
    icon: FolderCheck,
    title: "Bilagsarkiv (5-års oppbevaring) & Prosjekt/Avdeling",
    body: "Hold store og små firmaer 100 % ryddige med avdelings- og prosjektregnskap, søkbart bilagsarkiv (Bokføringsloven § 13) og live Varslinger når fakturaer forfaller eller bankposter mangler avstemming.",
  },
  {
    icon: Headphones,
    title: "Ekte menneskelig kundeservice — ikke bare en robot",
    body: "Vår AI svarer lynraskt 24/7 på vanlige regnskapsspørsmål, men så fort noe gjelder betaling, MVA eller haster, kobles en ekte menneskelig kundebehandler direkte på saken din.",
  },
];

const PLANS = [
  {
    name: "Phink Komplett",
    price: "299 kr",
    sub: "eks. MVA / mnd · Ingen skjulte avgifter",
    forWho: "Alt inkludert for Privat, ENK, AS, Forening & Institusjon",
    highlight: true,
    features: [
      "Ubegrenset antall bilag — ingen bilagsgrenser!",
      "Komplett NS 4102 regnskap, faktura med norsk MVA & automatisk KID-føring",
      "Helautomatisk lønnskjøring inkl. skattetrekkskonto (1950), AGA & OTP",
      "Bilagsarkiv (5 år), rapporter, SAF-T eksport, AI CFO & Varslinger ved uoppgjorte fakturaer",
    ],
  },
  {
    name: "Tillegg: Bankintegrasjon",
    price: "+ 59 kr",
    sub: "eks. MVA / mnd (valgfritt)",
    forWho: "Koble direkte til banken din",
    features: [
      "Logg inn og integrer banken din direkte mot regnskapet",
      "Automatisk innlesing av banktransaksjoner & KID-innbetalinger",
      "Matcher KID-fakturaer og fører betalinger automatisk på konto 1920/1500",
      "Umiddelbar varsling i Varslinger hvis kundefaktura ikke er betalt",
    ],
  },
  {
    name: "Tillegg: SAF-T Filimport",
    price: "+ 79 kr",
    sub: "eks. MVA (valgfritt ved import)",
    forWho: "Bytter du fra Conta, Fiken eller Tripletex?",
    features: [
      "Importer hele SAF-T Financial XML-filen din med ett klikk",
      "Validerer dobbel bokføring på hvert bilag automatisk",
      "Tar med kontoplan (NS 4102), kunder, leverandører og hovedbok",
      "SAF-T XML-eksport til Skatteetaten / revisor er alltid inkludert i 299 kr/mnd",
    ],
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* 1-sekunds logo-glimt (3/4 av skjermen) før forsiden vises */}
      <LogoSplash durationMs={1000} />

      {/* Toppnavigasjon */}
      <header className="sticky top-0 z-30 border-b border-slate-800/80 bg-slate-950/90 backdrop-blur-md">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-black border border-amber-500/40 overflow-hidden flex items-center justify-center">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="/brand/logo.png" alt="Phink Accounting" className="w-full h-full object-contain" />
            </div>
            <div>
              <div className="font-bold text-white leading-tight">Phink Accounting</div>
              <div className="text-[11px] text-amber-400/90">Norsk AI-regnskap &amp; lønn</div>
            </div>
          </Link>

          <nav className="hidden md:flex items-center gap-6 text-xs font-medium text-slate-300">
            <a href="#hvorfor" className="hover:text-white">Hvorfor velge oss</a>
            <a href="#selskapsformer" className="hover:text-white">Hvem det passer for</a>
            <Link href="/priser" className="hover:text-amber-300 font-semibold text-amber-400">Prisliste</Link>
          </nav>

          <div className="flex items-center gap-2.5 text-xs">
            <Link
              href="/login"
              className="rounded-xl border border-slate-700 bg-slate-900 hover:bg-slate-800 px-4 py-2 font-semibold text-white"
            >
              Logg inn
            </Link>
            <Link
              href="/register"
              className="rounded-xl bg-gradient-to-r from-amber-500 to-yellow-500 hover:from-amber-400 hover:to-yellow-400 px-4 py-2 font-bold text-slate-950 shadow-md"
            >
              Registrer deg
            </Link>
          </div>
        </div>
      </header>

      {/* Hero-seksjon */}
      <section className="relative overflow-hidden border-b border-slate-800/80">
        <div className="max-w-6xl mx-auto px-6 py-20 lg:py-24 grid lg:grid-cols-12 gap-12 items-center">
          <div className="lg:col-span-7 space-y-6">
            <div className="inline-flex items-center gap-2 rounded-full border border-amber-500/30 bg-amber-500/10 px-3.5 py-1.5 text-xs font-semibold text-amber-300">
              <ShieldCheck className="w-4 h-4" />
              <span>Bygget for norsk lovverk · NS 4102 · SAF-T v1.30 · Vipps Bedrift</span>
            </div>

            <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-white leading-[1.1]">
              Regnskap, lønn og faktura —{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-yellow-300">
                uten regnskapshodepine.
              </span>
            </h1>

            <p className="text-base sm:text-lg text-slate-300 leading-relaxed max-w-2xl">
              Lei av dyre regnskapsprogrammer som tar ekstra betalt for hver minste modul?{" "}
              <strong className="text-white">Phink Accounting</strong> samler alt på ett sted —
              automatisk lønnskjøring, norsk MVA-fakturering, bankavstemning, bilagsarkiv, SAF-T XML
              og din egen AI CFO som kan norske skatteregler.
            </p>

            <div className="flex flex-wrap items-center gap-3 pt-2">
              <Link
                href="/register"
                className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-amber-500 to-yellow-500 hover:from-amber-400 hover:to-yellow-400 px-6 py-3.5 text-sm font-bold text-slate-950 shadow-lg"
              >
                <span>Kom i gang nå (Registrer ny konto)</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                href="/login"
                className="inline-flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-900 hover:bg-slate-800 px-6 py-3.5 text-sm font-semibold text-white"
              >
                <span>Allerede kunde? Logg inn</span>
              </Link>
            </div>

            <div className="flex flex-wrap gap-x-6 gap-y-2 pt-2 text-xs text-slate-400">
              <span className="inline-flex items-center gap-1.5">
                <CheckCircle className="w-4 h-4 text-emerald-400" /> Ingen bindingstid
              </span>
              <span className="inline-flex items-center gap-1.5">
                <Smartphone className="w-4 h-4 text-orange-400" /> Kun Vipps Bedrift eller faktura
              </span>
              <span className="inline-flex items-center gap-1.5">
                <FileCheck className="w-4 h-4 text-blue-400" /> Innebygd regnskapsfaglig kontroll
              </span>
            </div>
          </div>

          <div className="lg:col-span-5 flex flex-col items-center">
            <div className="w-full max-w-md rounded-3xl border border-amber-500/30 bg-gradient-to-b from-slate-900 to-black p-6 shadow-2xl space-y-5">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src="/brand/logo.png"
                alt="Think / Phink Accounting"
                className="w-full max-h-64 object-contain mx-auto rounded-2xl"
              />
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="rounded-xl bg-slate-900/90 border border-slate-800 p-3">
                  <div className="text-slate-400">MVA-satser</div>
                  <div className="font-bold text-white mt-0.5">25% · 15% · 12% · 0%</div>
                </div>
                <div className="rounded-xl bg-slate-900/90 border border-slate-800 p-3">
                  <div className="text-slate-400">Lønn &amp; 1950</div>
                  <div className="font-bold text-emerald-400 mt-0.5">100 % automatisk</div>
                </div>
                <div className="rounded-xl bg-slate-900/90 border border-slate-800 p-3">
                  <div className="text-slate-400">SAF-T v1.30</div>
                  <div className="font-bold text-blue-400 mt-0.5">Eksport &amp; Import</div>
                </div>
                <div className="rounded-xl bg-slate-900/90 border border-slate-800 p-3">
                  <div className="text-slate-400">Varslinger</div>
                  <div className="font-bold text-amber-400 mt-0.5">Live fristkontroll</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Hvorfor velge Phink Accounting */}
      <section id="hvorfor" className="max-w-6xl mx-auto px-6 py-20 space-y-12">
        <div className="max-w-2xl space-y-3">
          <div className="text-xs font-bold uppercase tracking-wider text-amber-400">Hvorfor velge oss?</div>
          <h2 className="text-3xl font-extrabold text-white">
            Alt du trenger i ett norsk regnskapsprogram — raskere, smartere og ærligere priset
          </h2>
          <p className="text-sm text-slate-400">
            Tradisjonelle regnskapssystemer krever dyre tilleggspakker for lønn, prosjektregnskap, AI-tolking og
            SAF-T. Hos Phink Accounting får du hele pakken integrert fra start.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {REASONS.map((r) => {
            const Icon = r.icon;
            return (
              <div
                key={r.title}
                className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 space-y-3 hover:border-amber-500/40 transition"
              >
                <div className="w-11 h-11 rounded-xl bg-amber-500/15 text-amber-400 flex items-center justify-center">
                  <Icon className="w-5 h-5" />
                </div>
                <h3 className="font-bold text-white text-base">{r.title}</h3>
                <p className="text-xs text-slate-400 leading-relaxed">{r.body}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* Hvem passer det for */}
      <section id="selskapsformer" className="border-y border-slate-800/80 bg-slate-900/40">
        <div className="max-w-6xl mx-auto px-6 py-16 space-y-8">
          <div className="text-center max-w-2xl mx-auto space-y-2">
            <h2 className="text-2xl sm:text-3xl font-extrabold text-white">
              Skreddersydd for alle norske selskapsformer og privatpersoner
            </h2>
            <p className="text-sm text-slate-400">
              Registrer deg med 9-sifret organisasjonsnummer (automatisk MOD11 Brønnøysund-kontroll) eller 11-sifret fødselsnummer.
            </p>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-center text-xs">
            {[
              { name: "Privatperson", id: "Fødselsnummer (11 siffer)" },
              { name: "ENK", id: "Orgnr og/eller fødselsnr" },
              { name: "Aksjeselskap (AS)", id: "Organisasjonsnummer (MOD11)" },
              { name: "Foreninger & Lag", id: "Organisasjonsnummer (MOD11)" },
              { name: "Institusjoner", id: "Organisasjonsnummer (MOD11)" },
            ].map((e) => (
              <div key={e.name} className="rounded-2xl border border-slate-800 bg-slate-950 p-4 space-y-1">
                <Building2 className="w-5 h-5 text-amber-400 mx-auto mb-1" />
                <div className="font-bold text-white">{e.name}</div>
                <div className="text-[11px] text-slate-400">{e.id}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Priser */}
      <section id="priser" className="max-w-6xl mx-auto px-6 py-20 space-y-10">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <div className="text-xs font-bold uppercase tracking-wider text-amber-400">Ærlige norske priser</div>
          <h2 className="text-3xl font-extrabold text-white">
            Betal enkelt med Vipps Bedrift eller tilsendt faktura
          </h2>
          <p className="text-sm text-slate-400">
            Ingen utenlandske kortløsninger, ingen skjulte tillegg — kun norsk Vipps Bedrift eller faktura med 25 % MVA og KID.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {PLANS.map((p) => (
            <div
              key={p.name}
              className={`rounded-2xl border p-6 flex flex-col justify-between space-y-5 ${
                p.highlight
                  ? "border-amber-500 bg-gradient-to-b from-amber-500/10 to-slate-900 shadow-xl"
                  : "border-slate-800 bg-slate-900/60"
              }`}
            >
              <div className="space-y-3">
                <div className="text-xs font-semibold text-amber-400">{p.forWho}</div>
                <h3 className="text-lg font-bold text-white">{p.name}</h3>
                <div>
                  <span className="text-3xl font-extrabold text-white">{p.price}</span>
                  <span className="text-xs text-slate-400 ml-1.5">{p.sub}</span>
                </div>
                <ul className="space-y-2 pt-2 text-xs text-slate-300">
                  {p.features.map((f) => (
                    <li key={f} className="flex items-start gap-2">
                      <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <Link
                href="/register"
                className={`block text-center rounded-xl py-2.5 text-xs font-bold transition ${
                  p.highlight
                    ? "bg-amber-500 hover:bg-amber-400 text-slate-950"
                    : "bg-slate-800 hover:bg-slate-700 text-white"
                }`}
              >
                Velg {p.name}
              </Link>
            </div>
          ))}
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3 text-sm">
            <Bell className="w-5 h-5 text-amber-400 shrink-0" />
            <span className="text-slate-300">
              Innebygd <strong className="text-white">Varslinger</strong>,{" "}
              <strong className="text-white">Altinn/Brønnøysund</strong> og{" "}
              <strong className="text-white">Regnskapsfaglig kontroll</strong> før innsending.
            </span>
          </div>
          <Link
            href="/register"
            className="inline-flex items-center gap-2 rounded-xl bg-amber-500 hover:bg-amber-400 px-5 py-2.5 text-xs font-bold text-slate-950"
          >
            <span>Start registrering</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>

      <footer className="border-t border-slate-800 py-8 px-6 text-center text-xs text-slate-500 space-y-1">
        <div className="flex items-center justify-center gap-2 text-slate-300 font-semibold">
          <Landmark className="w-4 h-4 text-amber-400" />
          <span>Phink Accounting · www.phink-acounting.no</span>
        </div>
        <p>Norsk regnskap, lønn, faktura, bilagsarkiv &amp; SAF-T XML v1.30 — alt lokalt på domeneserveren.</p>
      </footer>
    </div>
  );
}
