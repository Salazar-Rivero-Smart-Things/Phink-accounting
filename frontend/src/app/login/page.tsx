"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Lock, Mail, ShieldCheck, ArrowRight, KeyRound, CheckCircle } from "lucide-react";
import LogoSplash from "@/components/LogoSplash";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Glemt passord state
  const [resetMode, setResetMode] = useState<"none" | "request" | "confirm">("none");
  const [resetEmail, setResetEmail] = useState("");
  const [resetCode, setResetCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [resetMsg, setResetMsg] = useState<string | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("phink_token");
    if (!token) return;
    fetch(`${API_BASE}/auth/me`, { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (d?.ok && d.user) window.location.replace("/app");
      })
      .catch(() => undefined);
  }, []);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim(), password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Feil e-postadresse eller passord.");
      localStorage.setItem("phink_token", data.access_token);
      window.location.href = "/app";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Innlogging feilet.");
    } finally {
      setBusy(false);
    }
  }

  async function handleRequestReset(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setResetMsg(null);
    try {
      const targetEmail = (resetEmail || email).trim();
      const res = await fetch(`${API_BASE}/auth/forgot-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: targetEmail }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Kunne ikke sende tilbakestillingskode.");
      setResetEmail(targetEmail);
      setResetMsg(data.message);
      setResetMode("confirm");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Feil ved forespørsel om nytt passord.");
    } finally {
      setBusy(false);
    }
  }

  async function handleConfirmReset(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setResetMsg(null);
    try {
      const res = await fetch(`${API_BASE}/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: resetEmail.trim(),
          reset_code: resetCode.trim(),
          new_password: newPassword,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Kunne ikke oppdatere passord.");
      setEmail(resetEmail.trim());
      setPassword("");
      setResetCode("");
      setNewPassword("");
      setResetMode("none");
      setResetMsg(data.message || "Passord oppdatert! Logg inn med det nye passordet.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Tilbakestilling feilet.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between">
      <LogoSplash durationMs={1000} />

      <header className="border-b border-slate-800/80 px-6 py-4 flex items-center justify-between max-w-6xl w-full mx-auto">
        <Link href="/" className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-black border border-amber-500/40 overflow-hidden flex items-center justify-center">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/brand/logo.png" alt="Phink Accounting" className="w-full h-full object-contain" />
          </div>
          <div>
            <div className="font-bold text-white leading-tight">Phink Accounting</div>
            <div className="text-[11px] text-slate-400">www.phink-acounting.no</div>
          </div>
        </Link>
        <div className="flex items-center gap-3 text-xs">
          <Link href="/" className="text-slate-400 hover:text-white">
            Tilbake til forsiden
          </Link>
          <Link
            href="/register"
            className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-3.5 py-2 font-semibold text-amber-300 hover:bg-amber-500/20"
          >
            Ny kunde? Registrer deg
          </Link>
        </div>
      </header>

      <main className="flex-1 flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900/90 p-8 shadow-2xl space-y-6">
          <div className="text-center space-y-2">
            <div className="w-16 h-16 mx-auto rounded-2xl bg-black border border-amber-500/40 p-1.5 flex items-center justify-center shadow-lg">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="/brand/logo.png" alt="Logo" className="w-full h-full object-contain" />
            </div>
            <h1 className="text-2xl font-bold text-white">Kunde- og Administratorinnlogging</h1>
            <p className="text-xs text-slate-400">
              Kun for registrerte kunder, bedrifter og administrator / kundeservice.
            </p>
          </div>

          {resetMode === "none" && (
            <form onSubmit={handleLogin} className="space-y-4">
              {resetMsg && (
                <div className="rounded-xl border border-emerald-700 bg-emerald-950/60 px-3.5 py-2.5 text-xs text-emerald-300 flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 shrink-0" />
                  <span>{resetMsg}</span>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">E-postadresse</label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                  <input
                    type="email"
                    required
                    autoComplete="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="din@epost.no"
                    className="w-full rounded-xl border border-slate-700 bg-slate-950 pl-10 pr-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:border-amber-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="block text-xs font-semibold text-slate-300">Passord</label>
                  <button
                    type="button"
                    onClick={() => {
                      setResetEmail(email);
                      setError(null);
                      setResetMsg(null);
                      setResetMode("request");
                    }}
                    className="text-xs text-amber-400 hover:text-amber-300 hover:underline font-medium cursor-pointer"
                  >
                    Glemt passord?
                  </button>
                </div>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                  <input
                    type="password"
                    required
                    autoComplete="current-password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full rounded-xl border border-slate-700 bg-slate-950 pl-10 pr-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:border-amber-500 focus:outline-none"
                  />
                </div>
              </div>

              {error && (
                <div className="rounded-xl border border-red-800 bg-red-950/60 px-3.5 py-2.5 text-xs text-red-300">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={busy}
                className="w-full rounded-xl bg-gradient-to-r from-amber-500 to-yellow-500 hover:from-amber-400 hover:to-yellow-400 py-3 text-sm font-bold text-slate-950 shadow-lg flex items-center justify-center gap-2 disabled:opacity-50 cursor-pointer"
              >
                <span>{busy ? "Logger inn…" : "Logg inn i regnskapsprogrammet"}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </form>
          )}

          {resetMode === "request" && (
            <form onSubmit={handleRequestReset} className="space-y-4">
              <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-200 flex items-start gap-2">
                <KeyRound className="w-4 h-4 shrink-0 mt-0.5 text-amber-400" />
                <span>Skriv inn din registrerte e-postadresse for å få en 6-sifret tilbakestillingskode.</span>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">E-postadresse</label>
                <input
                  type="email"
                  required
                  value={resetEmail}
                  onChange={(e) => setResetEmail(e.target.value)}
                  placeholder="din@epost.no"
                  className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:border-amber-500 focus:outline-none"
                />
              </div>
              {error && (
                <div className="rounded-xl border border-red-800 bg-red-950/60 px-3.5 py-2.5 text-xs text-red-300">
                  {error}
                </div>
              )}
              <button
                type="submit"
                disabled={busy}
                className="w-full rounded-xl bg-gradient-to-r from-amber-500 to-yellow-500 hover:from-amber-400 hover:to-yellow-400 py-3 text-sm font-bold text-slate-950 cursor-pointer disabled:opacity-50"
              >
                {busy ? "Sender kode…" : "Send tilbakestillingskode"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setError(null);
                  setResetMode("none");
                }}
                className="w-full text-center text-xs text-slate-400 hover:text-white cursor-pointer"
              >
                ← Tilbake til innlogging
              </button>
            </form>
          )}

          {resetMode === "confirm" && (
            <form onSubmit={handleConfirmReset} className="space-y-4">
              {resetMsg && (
                <div className="rounded-xl border border-emerald-700 bg-emerald-950/60 px-3.5 py-2.5 text-xs text-emerald-300">
                  {resetMsg}
                </div>
              )}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">6-sifret tilbakestillingskode</label>
                <input
                  type="text"
                  required
                  value={resetCode}
                  onChange={(e) => setResetCode(e.target.value)}
                  placeholder="123456"
                  className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3.5 py-2.5 text-sm font-mono tracking-widest text-white placeholder-slate-500 focus:border-amber-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Nytt passord (minst 6 tegn)</label>
                <input
                  type="password"
                  required
                  minLength={6}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:border-amber-500 focus:outline-none"
                />
              </div>
              {error && (
                <div className="rounded-xl border border-red-800 bg-red-950/60 px-3.5 py-2.5 text-xs text-red-300">
                  {error}
                </div>
              )}
              <button
                type="submit"
                disabled={busy}
                className="w-full rounded-xl bg-gradient-to-r from-amber-500 to-yellow-500 hover:from-amber-400 hover:to-yellow-400 py-3 text-sm font-bold text-slate-950 cursor-pointer disabled:opacity-50"
              >
                {busy ? "Lagrer nytt passord…" : "Lagre nytt passord"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setError(null);
                  setResetMode("none");
                }}
                className="w-full text-center text-xs text-slate-400 hover:text-white cursor-pointer"
              >
                ← Tilbake til innlogging
              </button>
            </form>
          )}

          <div className="pt-4 border-t border-slate-800 text-center text-xs text-slate-400 space-y-2">
            <div className="flex items-center justify-center gap-1.5 text-emerald-400">
              <ShieldCheck className="w-4 h-4" />
              <span>Kryptert lokal lagring — Norsk standard NS 4102 &amp; SAF-T</span>
            </div>
            <p>
              Har du ikke konto ennå?{" "}
              <Link href="/register" className="text-amber-400 hover:underline font-semibold">
                Registrer deg her →
              </Link>
            </p>
          </div>
        </div>
      </main>

      <footer className="border-t border-slate-900 py-4 text-center text-xs text-slate-500">
        © 2026 Phink Accounting · www.phink-acounting.no
      </footer>
    </div>
  );
}
