"use client";

import React, { useState } from "react";
import { Building2, Lock, Mail, ShieldCheck, User, X } from "lucide-react";

export interface AuthUser {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_admin?: boolean;
  is_support_agent?: boolean;
  is_customer_account?: boolean;
  billing_exempt?: boolean;
  plan_label?: string;
  entity_type: "PRIVATE" | "ENK" | "AS" | "FORENING" | "INSTITUSJON";
  entity_type_label: string;
  company_name?: string | null;
  org_number?: string | null;
  national_id_masked?: string | null;
}

const ENTITY_OPTIONS: Array<{ value: AuthUser["entity_type"]; label: string; hint: string }> = [
  { value: "AS", label: "Aksjeselskap (AS)", hint: "Krever 9-sifret organisasjonsnummer (MOD11)" },
  { value: "ENK", label: "Enkeltpersonforetak (ENK)", hint: "Oppgi organisasjonsnummer (9 siffer) og/eller fødselsnummer (11 siffer)" },
  { value: "PRIVATE", label: "Privatperson", hint: "Krever 11-sifret fødselsnummer" },
  { value: "FORENING", label: "Forening / Lag", hint: "Krever 9-sifret organisasjonsnummer (MOD11)" },
  { value: "INSTITUSJON", label: "Institusjon / Stiftelse", hint: "Krever 9-sifret organisasjonsnummer (MOD11)" },
];

export default function AuthModal({
  apiBase,
  onClose,
  onAuthenticated,
}: {
  apiBase: string;
  onClose: () => void;
  onAuthenticated: (user: AuthUser, token: string) => void;
}) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [entityType, setEntityType] = useState<AuthUser["entity_type"]>("AS");
  const [companyName, setCompanyName] = useState("");
  const [orgNumber, setOrgNumber] = useState("");
  const [nationalId, setNationalId] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedMeta = ENTITY_OPTIONS.find((o) => o.value === entityType) ?? ENTITY_OPTIONS[0];
  const needsOrgNr = entityType !== "PRIVATE";
  const needsNationalId = entityType === "PRIVATE" || entityType === "ENK";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const endpoint = mode === "login" ? `${apiBase}/auth/login` : `${apiBase}/auth/register`;
      const payload =
        mode === "login"
          ? { email, password }
          : {
              email,
              password,
              full_name: fullName,
              entity_type: entityType,
              company_name: entityType === "PRIVATE" ? fullName : companyName,
              org_number: needsOrgNr && orgNumber.trim() ? orgNumber.trim() : null,
              national_id: needsNationalId && nationalId.trim() ? nationalId.trim() : null,
            };

      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Innlogging / registrering feilet.");
      }
      localStorage.setItem("phink_token", data.access_token);
      onAuthenticated(data.user, data.access_token);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Noe gikk galt.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 backdrop-blur-xs p-4">
      <div className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white shadow-2xl overflow-hidden">
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4 bg-slate-50">
          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-xl bg-blue-600 text-white flex items-center justify-center">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900">
                {mode === "login" ? "Logg inn i Phink Accounting" : "Opprett bruker (Firma eller Privat)"}
              </h3>
              <p className="text-xs text-slate-500">www.phink-acounting.no — 100 % lokal lagring</p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700 cursor-pointer">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="px-6 pt-4">
          <div className="grid grid-cols-2 rounded-xl bg-slate-100 p-1 text-xs font-semibold">
            <button
              type="button"
              onClick={() => {
                setMode("login");
                setError(null);
              }}
              className={`py-2 rounded-lg transition cursor-pointer ${
                mode === "login" ? "bg-white text-slate-900 shadow-xs" : "text-slate-500"
              }`}
            >
              Logg inn
            </button>
            <button
              type="button"
              onClick={() => {
                setMode("register");
                setEmail("");
                setError(null);
              }}
              className={`py-2 rounded-lg transition cursor-pointer ${
                mode === "register" ? "bg-white text-slate-900 shadow-xs" : "text-slate-500"
              }`}
            >
              Ny bruker / Firma
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4 text-sm">
          {mode === "register" && (
            <>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Kontotype / Selskapsform
                </label>
                <select
                  value={entityType}
                  onChange={(e) => setEntityType(e.target.value as AuthUser["entity_type"])}
                  className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm text-slate-900 bg-white"
                >
                  {ENTITY_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
                <p className="mt-1 text-[11px] text-slate-500">{selectedMeta.hint}</p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Fullt navn</label>
                  <div className="relative">
                    <User className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                    <input
                      type="text"
                      required
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="Ola Nordmann"
                      className="w-full rounded-xl border border-slate-300 pl-9 pr-3 py-2 text-sm text-slate-900"
                    />
                  </div>
                </div>

                {entityType !== "PRIVATE" && (
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Firma- / Organisasjonsnavn
                    </label>
                    <div className="relative">
                      <Building2 className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                      <input
                        type="text"
                        required
                        value={companyName}
                        onChange={(e) => setCompanyName(e.target.value)}
                        placeholder={`Mitt ${entityType}`}
                        className="w-full rounded-xl border border-slate-300 pl-9 pr-3 py-2 text-sm text-slate-900"
                      />
                    </div>
                  </div>
                )}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {needsOrgNr && (
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Organisasjonsnummer (9 siffer){entityType === "ENK" ? " — eller fødselsnr" : ""}
                    </label>
                    <input
                      type="text"
                      required={entityType !== "ENK"}
                      value={orgNumber}
                      onChange={(e) => setOrgNumber(e.target.value)}
                      placeholder="984 851 006"
                      className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm font-mono text-slate-900"
                    />
                  </div>
                )}

                {needsNationalId && (
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Fødselsnummer (11 siffer){entityType === "ENK" ? " (valgfritt hvis orgnr)" : ""}
                    </label>
                    <input
                      type="text"
                      required={entityType === "PRIVATE"}
                      value={nationalId}
                      onChange={(e) => setNationalId(e.target.value)}
                      placeholder="DDMMÅÅXXXXX"
                      className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm font-mono text-slate-900"
                    />
                  </div>
                )}
              </div>
            </>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">E-postadresse</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="navn@firma.no"
                className="w-full rounded-xl border border-slate-300 pl-9 pr-3 py-2 text-sm text-slate-900"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Passord</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="password"
                required
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={mode === "login" ? "Skriv inn passord" : "Minst 6 tegn"}
                className="w-full rounded-xl border border-slate-300 pl-9 pr-3 py-2 text-sm text-slate-900"
              />
            </div>
          </div>

          {error && (
            <div className="rounded-xl border border-red-200 bg-red-50 px-3.5 py-2.5 text-xs text-red-700 font-medium">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={busy}
            className="w-full rounded-xl bg-blue-600 hover:bg-blue-700 py-2.5 text-sm font-semibold text-white shadow-xs disabled:opacity-50 cursor-pointer"
          >
            {busy ? "Behandler…" : mode === "login" ? "Logg inn" : "Opprett konto og logg inn"}
          </button>
        </form>
      </div>
    </div>
  );
}
