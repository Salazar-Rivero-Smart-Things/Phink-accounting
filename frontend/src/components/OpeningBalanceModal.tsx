"use client";

import React, { useEffect, useState } from "react";
import { Landmark, X, CheckCircle, AlertCircle } from "lucide-react";

interface OpeningBalanceModalProps {
  apiBase: string;
  onClose: () => void;
  onImported: () => void;
}

export default function OpeningBalanceModal({
  apiBase,
  onClose,
  onImported,
}: OpeningBalanceModalProps) {
  const [bankBalance, setBankBalance] = useState("");
  const [taxAccount, setTaxAccount] = useState("");
  const [receivables, setReceivables] = useState("");
  const [payables, setPayables] = useState("");
  const [equityAccount, setEquityAccount] = useState<number>(2050);
  const [date, setDate] = useState("2026-11-19");
  const [description, setDescription] = useState("Inngående balanse (Saldo på konto i dag)");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    setDate(new Date().toISOString().split("T")[0]);
  }, []);

  const parseNum = (v: string) => {
    const cleaned = v.replace(/\s+/g, "").replace(",", ".");
    const n = parseFloat(cleaned);
    return Number.isFinite(n) ? n : 0;
  };

  const bankVal = parseNum(bankBalance);
  const taxVal = parseNum(taxAccount);
  const recVal = parseNum(receivables);
  const payVal = parseNum(payables);
  const netEquity = Math.round(((bankVal + taxVal + recVal) - payVal) * 100) / 100;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);

    if (
      Math.abs(bankVal) < 0.01 &&
      Math.abs(taxVal) < 0.01 &&
      Math.abs(recVal) < 0.01 &&
      Math.abs(payVal) < 0.01
    ) {
      setError("Skriv inn hva du har på bankkonto i dag (eller minst én balanselinje).");
      return;
    }

    setBusy(true);
    try {
      const res = await fetch(`${apiBase}/accounting/opening-balance`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          bank_balance: bankVal,
          tax_account_1950: taxVal,
          receivables_1500: recVal,
          payables_2400: payVal,
          equity_account: equityAccount,
          date,
          description: description.trim() || "Inngående balanse (Saldo på konto i dag)",
          create_bank_statement_entry: true,
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.detail || "Kunne ikke lagre inngående balanse.");
      }
      setSuccessMsg(data.message || "Inngående balanse er bokført!");
      onImported();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Noe gikk galt.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 space-y-5">
        <div className="flex items-start justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0">
              <Landmark className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900 text-base">
                Importer inngående balanse (Saldo på konto i dag)
              </h3>
              <p className="text-xs text-slate-500">
                Legg inn manuelt hva du har på bedriftskontoen i dag. Bokføres automatisk og balansert i NS 4102.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-100 cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          {/* Hovedfelt: Saldo på driftskonto i dag */}
          <div className="p-4 rounded-xl bg-emerald-50/70 border border-emerald-200 space-y-2">
            <label className="block font-bold text-emerald-950 text-sm">
              Saldo på driftskonto i dag (Konto 1920) — NOK
            </label>
            <input
              type="text"
              inputMode="decimal"
              placeholder="F.eks. 125000 eller 48500,50"
              value={bankBalance}
              onChange={(e) => setBankBalance(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-white border border-emerald-300 rounded-xl text-base font-bold text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              autoFocus
            />
            <p className="text-[11px] text-emerald-800">
              Skriv inn nøyaktig saldo fra nettbanken din i dag (bruk minus foran ved kassekreditt/overtrekk).
              Bankavstemmingen oppdateres automatisk slik at den stemmer på øret.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Dato for saldo</label>
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-xs text-slate-900"
              />
            </div>
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Motkonto (Egenkapital)</label>
              <select
                value={equityAccount}
                onChange={(e) => setEquityAccount(Number(e.target.value))}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-xs text-slate-900"
              >
                <option value={2050}>2050 — Annen egenkapital (Anbefalt)</option>
                <option value={2000}>2000 — Aksjekapital / Innskutt egenkapital</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">Beskrivelse på bilag</label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-xs text-slate-900"
            />
          </div>

          {/* Valgfrie ekstra balanseposter */}
          <div className="border border-slate-200 rounded-xl overflow-hidden">
            <button
              type="button"
              onClick={() => setShowAdvanced((v) => !v)}
              className="w-full px-3.5 py-2.5 bg-slate-50 hover:bg-slate-100 text-left font-semibold text-slate-700 flex items-center justify-between cursor-pointer"
            >
              <span>Valgfritt: Flere inngående poster (skattetrekk, fordringer, gjeld)</span>
              <span className="text-slate-400">{showAdvanced ? "Skjul ▲" : "Vis ▼"}</span>
            </button>
            {showAdvanced && (
              <div className="p-3.5 grid grid-cols-1 md:grid-cols-3 gap-3 bg-white border-t border-slate-100">
                <div>
                  <label className="block font-semibold text-slate-600 mb-1">
                    Skattetrekkskonto (1950)
                  </label>
                  <input
                    type="text"
                    inputMode="decimal"
                    placeholder="0"
                    value={taxAccount}
                    onChange={(e) => setTaxAccount(e.target.value)}
                    className="w-full px-2.5 py-1.5 border border-slate-200 rounded-lg text-xs"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-600 mb-1">
                    Kundefordringer (1500)
                  </label>
                  <input
                    type="text"
                    inputMode="decimal"
                    placeholder="0"
                    value={receivables}
                    onChange={(e) => setReceivables(e.target.value)}
                    className="w-full px-2.5 py-1.5 border border-slate-200 rounded-lg text-xs"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-600 mb-1">
                    Leverandørgjeld (2400)
                  </label>
                  <input
                    type="text"
                    inputMode="decimal"
                    placeholder="0"
                    value={payables}
                    onChange={(e) => setPayables(e.target.value)}
                    className="w-full px-2.5 py-1.5 border border-slate-200 rounded-lg text-xs"
                  />
                </div>
              </div>
            )}
          </div>

          {/* Forhåndsvisning av balansepostering */}
          <div className="rounded-xl bg-slate-50 border border-slate-200 p-3 flex items-center justify-between text-[11px]">
            <span className="text-slate-600">
              Beregnet motpost på egenkapital (<strong>{equityAccount}</strong>):
            </span>
            <span className="font-mono font-bold text-slate-900">
              {netEquity.toLocaleString("nb-NO", { minimumFractionDigits: 2 })} NOK
            </span>
          </div>

          {error && (
            <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {successMsg && (
            <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900 flex items-center gap-2 font-semibold">
              <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>{successMsg}</span>
            </div>
          )}

          <div className="pt-2 border-t border-slate-100 flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50 font-semibold cursor-pointer"
            >
              {successMsg ? "Lukk" : "Avbryt"}
            </button>
            {!successMsg && (
              <button
                type="submit"
                disabled={busy}
                className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white font-bold shadow-xs cursor-pointer"
              >
                {busy ? "Bokfører saldo…" : "Importer & bokfør inngående balanse"}
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}
