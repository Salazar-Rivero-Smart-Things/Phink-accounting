"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ArrowRight, Building2, CheckCircle, Lock, Mail, Receipt, Smartphone, User } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

type EntityType = "AS" | "ENK" | "PRIVATE" | "FORENING" | "INSTITUSJON";

const ENTITY_OPTIONS: Array<{ value: EntityType; label: string; desc: string }> = [
  { value: "AS", label: "Aksjeselskap (AS)", desc: "Krever 9-sifret organisasjonsnummer (MOD11)" },
  { value: "ENK", label: "Enkeltpersonforetak (ENK)", desc: "Oppgi organisasjonsnummer (9 siffer) og/eller fødselsnummer (11 siffer)" },
  { value: "PRIVATE", label: "Privatperson", desc: "Krever 11-sifret fødselsnummer" },
  { value: "FORENING", label: "Forening / Lag", desc: "Krever 9-sifret organisasjonsnummer (MOD11)" },
  { value: "INSTITUSJON", label: "Institusjon / Stiftelse", desc: "Krever 9-sifret organisasjonsnummer (MOD11)" },
];

export default function RegisterPage() {
  const [entityType, setEntityType] = useState<EntityType>("AS");
  const [fullName, setFullName] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [orgNumber, setOrgNumber] = useState("");
  const [nationalId, setNationalId] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [includeBank, setIncludeBank] = useState(false);
  const [includeSaft, setIncludeSaft] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState<"VIPPS_BEDRIFT" | "FAKTURA">("VIPPS_BEDRIFT");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [paymentNote, setPaymentNote] = useState<string | null>(null);

  const selectedEntity = ENTITY_OPTIONS.find((e) => e.value === entityType) ?? ENTITY_OPTIONS[0];
  const needsOrgNr = entityType !== "PRIVATE";
  const needsNationalId = entityType === "PRIVATE" || entityType === "ENK";
  const totalExVat = 299 + (includeBank ? 59 : 0) + (includeSaft ? 79 : 0);

  async function handleRegister(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setPaymentNote(null);

    try {
      const regRes = await fetch(`${API_BASE}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: email.trim(),
          password,
          full_name: fullName.trim(),
          entity_type: entityType,
          company_name: entityType === "PRIVATE" ? fullName.trim() : companyName.trim(),
          org_number: needsOrgNr && orgNumber.trim() ? orgNumber.trim() : null,
          national_id: needsNationalId && nationalId.trim() ? nationalId.trim() : null,
        }),
      });
      const regData = await regRes.json();
      if (!regRes.ok) throw new Error(regData.detail || "Registrering feilet.");

      localStorage.setItem("phink_token", regData.access_token);

      // Opprett valgt betaling (Vipps Bedrift eller tilsendt faktura) — gratis for administrator
      const payRes = await fetch(`${API_BASE}/billing/checkout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          plan_id: "PHINK_STANDARD",
          payment_method: paymentMethod,
          customer_name: entityType === "PRIVATE" ? fullName.trim() : companyName.trim() || fullName.trim(),
          customer_email: email.trim(),
          org_number: needsOrgNr && orgNumber.trim() ? orgNumber.trim() : null,
          include_bank_integration: includeBank,
          include_saft_import: includeSaft,
        }),
      });
      const payData = await payRes.json().catch(() => null);
      if (payData?.instructions) {
        setPaymentNote(payData.instructions);
      }

      window.setTimeout(() => {
        window.location.href = "/app";
      }, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Noe gikk galt under registrering.");
    } finally {
      setBusy(false);
    }
  }

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
            <div className="text-[11px] text-slate-400">Ny kunde-registrering</div>
          </div>
        </Link>
        <div className="flex items-center gap-3 text-xs">
          <Link href="/" className="text-slate-400 hover:text-white">
            Hvorfor velge oss?
          </Link>
          <Link
            href="/login"
            className="rounded-lg border border-slate-700 bg-slate-900 px-3.5 py-2 font-semibold text-white hover:bg-slate-800"
          >
            Allerede kunde? Logg inn
          </Link>
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center px-4 py-10">
        <div className="w-full max-w-2xl rounded-2xl border border-slate-800 bg-slate-900/90 p-8 shadow-2xl space-y-6">
          <div>
            <span className="inline-block rounded-full bg-amber-500/15 border border-amber-500/30 px-3 py-1 text-[11px] font-bold text-amber-300 mb-2">
              KUN FOR REGISTRERING AV NYE KUNDER
            </span>
            <h1 className="text-2xl font-bold text-white">Opprett din Phink Accounting-konto</h1>
            <p className="text-sm text-slate-400 mt-1">
              For både privatpersoner og norske bedrifter (ENK, AS, Forening og Institusjon). Betaling kun med{" "}
              <strong className="text-white">Vipps Bedrift</strong> eller{" "}
              <strong className="text-white">tilsendt faktura</strong>.
            </p>
          </div>

          {paymentNote ? (
            <div className="rounded-2xl border border-emerald-500/40 bg-emerald-950/60 p-6 space-y-3 text-emerald-100">
              <div className="flex items-center gap-2 font-bold text-lg text-emerald-300">
                <CheckCircle className="w-6 h-6" />
                <span>Konto opprettet! Sender deg inn i regnskapsprogrammet…</span>
              </div>
              <p className="text-sm">{paymentNote}</p>
            </div>
          ) : (
            <form onSubmit={handleRegister} className="space-y-5 text-sm">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  1. Velg kontotype / selskapsform
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                  {ENTITY_OPTIONS.map((opt) => (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => {
                        setEntityType(opt.value);
                      }}
                      className={`rounded-xl border p-3 text-left text-xs transition cursor-pointer ${
                        entityType === opt.value
                          ? "border-amber-500 bg-amber-500/15 text-white font-bold"
                          : "border-slate-700 bg-slate-950 text-slate-300 hover:border-slate-500"
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
                <p className="text-[11px] text-slate-400 mt-1.5">{selectedEntity.desc}</p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Fullt navn</label>
                  <div className="relative">
                    <User className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
                    <input
                      type="text"
                      required
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="Ola Nordmann"
                      className="w-full rounded-xl border border-slate-700 bg-slate-950 pl-9 pr-3 py-2 text-white"
                    />
                  </div>
                </div>

                {entityType !== "PRIVATE" && (
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">
                      Firma- / Organisasjonsnavn
                    </label>
                    <div className="relative">
                      <Building2 className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
                      <input
                        type="text"
                        required
                        value={companyName}
                        onChange={(e) => setCompanyName(e.target.value)}
                        placeholder={`Mitt ${entityType}`}
                        className="w-full rounded-xl border border-slate-700 bg-slate-950 pl-9 pr-3 py-2 text-white"
                      />
                    </div>
                  </div>
                )}

                {needsOrgNr && (
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">
                      Organisasjonsnummer (9 siffer){entityType === "ENK" ? " eller fødselsnr" : ""}
                    </label>
                    <input
                      type="text"
                      required={entityType !== "ENK"}
                      value={orgNumber}
                      onChange={(e) => setOrgNumber(e.target.value)}
                      placeholder="984 851 006"
                      className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 font-mono text-white"
                    />
                  </div>
                )}

                {needsNationalId && (
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">
                      Fødselsnummer (11 siffer){entityType === "ENK" ? " (valgfritt med orgnr)" : ""}
                    </label>
                    <input
                      type="text"
                      required={entityType === "PRIVATE"}
                      value={nationalId}
                      onChange={(e) => setNationalId(e.target.value)}
                      placeholder="DDMMÅÅXXXXX"
                      className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 font-mono text-white"
                    />
                  </div>
                )}

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">E-postadresse</label>
                  <div className="relative">
                    <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
                    <input
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="navn@firma.no"
                      className="w-full rounded-xl border border-slate-700 bg-slate-950 pl-9 pr-3 py-2 text-white"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Velg passord</label>
                  <div className="relative">
                    <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
                    <input
                      type="password"
                      required
                      minLength={6}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Minst 6 tegn"
                      className="w-full rounded-xl border border-slate-700 bg-slate-950 pl-9 pr-3 py-2 text-white"
                    />
                  </div>
                </div>
              </div>

              <div className="space-y-3 pt-2 border-t border-slate-800">
                <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3.5 text-xs">
                  <div className="flex items-center justify-between font-bold text-white">
                    <span>Phink Komplett — Ubegrenset bilag (ingen skjulte avgifter)</span>
                    <span className="text-amber-300">299 kr/mnd</span>
                  </div>
                  <div className="mt-2.5 space-y-2 text-slate-300">
                    <label className="flex items-center justify-between cursor-pointer">
                      <span className="inline-flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={includeBank}
                          onChange={(e) => setIncludeBank(e.target.checked)}
                        />
                        Bankintegrasjon (innlogging mot banken din + automatisk KID-føring)
                      </span>
                      <span className="font-mono text-amber-300">+ 59 kr/mnd</span>
                    </label>
                    <label className="flex items-center justify-between cursor-pointer">
                      <span className="inline-flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={includeSaft}
                          onChange={(e) => setIncludeSaft(e.target.checked)}
                        />
                        SAF-T XML filimport (importer regnskap fra Conta/Fiken/Tripletex)
                      </span>
                      <span className="font-mono text-amber-300">+ 79 kr</span>
                    </label>
                  </div>
                  <div className="mt-2.5 pt-2 border-t border-amber-500/20 flex items-center justify-between font-bold text-white">
                    <span>Totalt eks. MVA (inkl. 25 % MVA: {(totalExVat * 1.25).toFixed(2)} kr)</span>
                    <span className="text-amber-300">{totalExVat} kr</span>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                    3. Betalingsmetode (Kun Vipps Bedrift eller tilsendt faktura)
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      onClick={() => setPaymentMethod("VIPPS_BEDRIFT")}
                      className={`rounded-xl border px-3 py-2 text-xs font-semibold flex items-center justify-center gap-1.5 cursor-pointer ${
                        paymentMethod === "VIPPS_BEDRIFT"
                          ? "border-orange-500 bg-orange-500/20 text-orange-300"
                          : "border-slate-700 bg-slate-950 text-slate-400"
                      }`}
                    >
                      <Smartphone className="w-4 h-4" />
                      Vipps Bedrift
                    </button>
                    <button
                      type="button"
                      onClick={() => setPaymentMethod("FAKTURA")}
                      className={`rounded-xl border px-3 py-2 text-xs font-semibold flex items-center justify-center gap-1.5 cursor-pointer ${
                        paymentMethod === "FAKTURA"
                          ? "border-blue-500 bg-blue-500/20 text-blue-300"
                          : "border-slate-700 bg-slate-950 text-slate-400"
                      }`}
                    >
                      <Receipt className="w-4 h-4" />
                      Tilsendt faktura
                    </button>
                  </div>
                </div>
              </div>

              {error && (
                <div className="rounded-xl border border-red-800 bg-red-950/60 px-4 py-2.5 text-xs text-red-300">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={busy}
                className="w-full rounded-xl bg-gradient-to-r from-amber-500 to-yellow-500 hover:from-amber-400 hover:to-yellow-400 py-3 text-sm font-bold text-slate-950 shadow-lg flex items-center justify-center gap-2 disabled:opacity-50 cursor-pointer"
              >
                <span>{busy ? "Oppretter konto…" : "Fullfør registrering og åpne Phink Accounting"}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </form>
          )}
        </div>
      </main>

      <footer className="border-t border-slate-900 py-4 text-center text-xs text-slate-500">
        © 2026 Phink Accounting · www.phink-acounting.no
      </footer>
    </div>
  );
}
