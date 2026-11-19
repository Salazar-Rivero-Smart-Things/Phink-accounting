import Link from "next/link";
import {
  ArrowRight,
  Building2,
  CheckCircle,
  Download,
  Landmark,
  Receipt,
  ShieldCheck,
  Smartphone,
  UserCheck,
} from "lucide-react";

const PRICE_ROWS = [
  {
    item: "Phink Komplett — Hovedabonnement",
    detail:
      "Ubegrenset bilag, NS 4102 kontoplan, fakturering med 25/15/12/0 % MVA, automatisk KID-føring, helautomatisk lønnskjøring (inkl. skattetrekkskonto 1950, AGA & OTP), bilagsarkiv (5 år), SAF-T eksport, varslinger, AI CFO og kundeservice.",
    exVat: "299 kr / mnd",
    incVat: "373,75 kr / mnd",
    badge: "Ingen skjulte avgifter",
  },
  {
    item: "Bankintegrasjon (valgfritt tillegg)",
    detail:
      "Logg inn og koble banken din direkte til programmet. Automatisk innlesing av banktransaksjoner, KID-innbetalinger og umiddelbar varsling ved uoppgjorte kundefakturaer.",
    exVat: "59 kr / mnd",
    incVat: "73,75 kr / mnd",
    badge: "Valgfritt",
  },
  {
    item: "KID-automatisasjon (automatisk KID-matching & bokføring)",
    detail:
      "Du har KID-avtale med banken din — Phink Accounting gjenkjenner KID-innbetalinger automatisk, bokfører betalingen på 1920/1500 og varsler i Varslinger ved uoppgjorte fakturaer.",
    exVat: "3 kr / KID-faktura",
    incVat: "3,75 kr / KID-faktura",
    badge: "Per bruk",
  },
  {
    item: "SAF-T Financial XML-import (valgfritt)",
    detail:
      "Importer eksisterende regnskap fra Conta, Fiken, Tripletex eller andre systemer med automatisk validering av dobbel bokføring.",
    exVat: "79 kr / import",
    incVat: "98,75 kr / import",
    badge: "Engangskostnad",
  },
  {
    item: "Endring / korrigering av bruker- eller firmaprofil",
    detail:
      "For kunder som ønsker å rette feilregistrerte opplysninger i profilen (f.eks. orgnr, fødselsnummer, selskapsform eller firmanavn).",
    exVat: "150 kr / endring",
    incVat: "187,50 kr / endring",
    badge: "Ved behov",
  },
];

export default function PricingPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between">
      <header className="border-b border-slate-800/80 px-6 py-4 flex items-center justify-between max-w-6xl w-full mx-auto">
        <Link href="/" className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-black border border-amber-500/40 overflow-hidden flex items-center justify-center">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/brand/logo.png" alt="Phink Accounting" className="w-full h-full object-contain" />
          </div>
          <div>
            <div className="font-bold text-white leading-tight">Phink Accounting</div>
            <div className="text-[11px] text-amber-400/90">Prisliste · Ingen skjulte avgifter</div>
          </div>
        </Link>

        <div className="flex items-center gap-3 text-xs">
          <Link href="/" className="text-slate-400 hover:text-white">
            Forside
          </Link>
          <Link
            href="/login"
            className="rounded-lg border border-slate-700 bg-slate-900 px-3.5 py-2 font-semibold text-white hover:bg-slate-800"
          >
            Logg inn
          </Link>
          <Link
            href="/register"
            className="rounded-lg bg-amber-500 hover:bg-amber-400 px-3.5 py-2 font-bold text-slate-950"
          >
            Registrer deg
          </Link>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-16 space-y-12 w-full">
        <div className="text-center max-w-2xl mx-auto space-y-3">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-500/30 bg-amber-500/10 px-3.5 py-1 text-xs font-semibold text-amber-300">
            <ShieldCheck className="w-4 h-4" />
            <span>100 % åpen norsk prisliste — ubegrenset bilag</span>
          </span>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-white">
            Enkel pris: 299 kr/mnd — ingen skjulte avgifter
          </h1>
          <p className="text-sm text-slate-400">
            Du får hele regnskapsprogrammet med ubegrenset antall bilag for 299 kr i måneden. Betal kun for
            tilleggene du faktisk trenger (bankintegrasjon 59 kr/mnd eller SAF-T import 79 kr).
          </p>
        </div>

        {/* Full prisliste-tabell */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 overflow-hidden shadow-2xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-900 text-xs uppercase tracking-wider text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="px-6 py-4">Tjeneste / Modul</th>
                  <th className="px-6 py-4 text-right">Pris eks. MVA</th>
                  <th className="px-6 py-4 text-right">Pris inkl. 25 % MVA</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {PRICE_ROWS.map((row) => (
                  <tr key={row.item} className="hover:bg-slate-800/30 transition">
                    <td className="px-6 py-5">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-bold text-white">{row.item}</span>
                        <span className="rounded-full bg-amber-500/15 border border-amber-500/30 px-2.5 py-0.5 text-[10px] font-semibold text-amber-300">
                          {row.badge}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed">{row.detail}</p>
                    </td>
                    <td className="px-6 py-5 text-right font-mono font-bold text-amber-300 whitespace-nowrap">
                      {row.exVat}
                    </td>
                    <td className="px-6 py-5 text-right font-mono text-slate-300 whitespace-nowrap">
                      {row.incVat}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Betalingsmetoder & KID */}
        <div className="grid md:grid-cols-3 gap-5 text-xs">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 space-y-2">
            <Smartphone className="w-6 h-6 text-orange-400" />
            <h3 className="font-bold text-white text-sm">Kun Vipps Bedrift eller Faktura</h3>
            <p className="text-slate-400 leading-relaxed">
              Vi tar kun imot betaling via norsk <strong>Vipps Bedrift</strong> eller{" "}
              <strong>tilsendt norsk faktura</strong> (14 dagers forfall og KID).
            </p>
          </div>
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 space-y-2">
            <Receipt className="w-6 h-6 text-blue-400" />
            <h3 className="font-bold text-white text-sm">Automatisk KID-integrasjon</h3>
            <p className="text-slate-400 leading-relaxed">
              KID-avtalen har du gjennom banken din — når en kunde betaler med KID, registrerer og fører
              Phink Accounting betalingen automatisk og varsler ved uoppgjorte fakturaer.
            </p>
          </div>
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 space-y-2">
            <UserCheck className="w-6 h-6 text-emerald-400" />
            <h3 className="font-bold text-white text-sm">Alle norske selskapsformer</h3>
            <p className="text-slate-400 leading-relaxed">
              Samme enkle pris enten du er <strong>Privatperson</strong>, <strong>ENK</strong>,{" "}
              <strong>AS</strong>, <strong>Forening</strong> eller <strong>Institusjon</strong>.
            </p>
          </div>
        </div>

        {/* Hva som alltid er inkludert */}
        <div className="rounded-2xl border border-amber-500/30 bg-gradient-to-r from-amber-500/10 to-slate-900 p-6 flex flex-wrap items-center justify-between gap-6">
          <div className="space-y-2">
            <h2 className="font-bold text-white text-lg">Klar til å komme i gang for 299 kr/mnd?</h2>
            <div className="flex flex-wrap gap-x-5 gap-y-1.5 text-xs text-slate-300">
              <span className="inline-flex items-center gap-1.5">
                <CheckCircle className="w-4 h-4 text-emerald-400" /> Ubegrenset bilag
              </span>
              <span className="inline-flex items-center gap-1.5">
                <Download className="w-4 h-4 text-emerald-400" /> Gratis SAF-T eksport
              </span>
              <span className="inline-flex items-center gap-1.5">
                <Building2 className="w-4 h-4 text-emerald-400" /> Ingen bindingstid
              </span>
            </div>
          </div>
          <Link
            href="/register"
            className="inline-flex items-center gap-2 rounded-xl bg-amber-500 hover:bg-amber-400 px-6 py-3 text-sm font-bold text-slate-950 shadow-lg"
          >
            <span>Registrer deg nå</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </main>

      <footer className="border-t border-slate-800 py-6 text-center text-xs text-slate-500">
        <div className="flex items-center justify-center gap-2 text-slate-300 font-semibold mb-1">
          <Landmark className="w-4 h-4 text-amber-400" />
          <span>Phink Accounting · www.phink-acounting.no</span>
        </div>
        Alle priser oppgis eks. og inkl. 25 % norsk MVA.
      </footer>
    </div>
  );
}
