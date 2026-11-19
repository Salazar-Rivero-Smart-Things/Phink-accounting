"use client";

import React, { useEffect, useState } from "react";
import { CheckCircle, PlusCircle, Printer, RefreshCw, Trash2, Users } from "lucide-react";

interface Employee {
  id: number;
  employee_number: string;
  full_name: string;
  email?: string;
  bank_account?: string;
  position: string;
  monthly_gross_salary: number;
  tax_percent: number;
  holiday_pay_percent: number;
  aga_zone: number;
  aga_percent: number;
  otp_percent: number;
  department_code: string;
  project_code: string;
}

interface JournalLine {
  account_number: number;
  account_name: string;
  description: string;
  debit: number;
  credit: number;
  department_code?: string;
  project_code?: string;
}

interface PayrollTotals {
  total_gross: number;
  total_overtime: number;
  total_bonus: number;
  total_tax_withholding: number;
  total_net_pay: number;
  total_holiday_pay: number;
  total_aga: number;
  total_aga_holiday: number;
  total_otp: number;
  total_employer_cost: number;
  sum_debit: number;
  sum_credit: number;
  is_balanced: boolean;
}

interface PayrollRunSummary {
  id: number;
  period: string;
  pay_date: string;
  total_gross: number;
  total_tax_withholding: number;
  total_net_pay: number;
  total_holiday_pay: number;
  total_aga: number;
  total_aga_holiday: number;
  total_otp: number;
  total_employer_cost: number;
  voucher_number?: number;
  tax_transfer_voucher_number?: number;
  lines: Array<{
    id: number;
    employee_name: string;
    gross_salary: number;
    overtime_pay: number;
    bonus_pay: number;
    tax_percent: number;
    tax_withholding: number;
    net_pay: number;
    holiday_pay: number;
    aga_amount: number;
    otp_amount: number;
    total_employer_cost: number;
  }>;
}

const fmt = (n: number) =>
  (n ?? 0).toLocaleString("nb-NO", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export default function PayrollPanel({
  apiBase,
  onPosted,
}: {
  apiBase: string;
  onPosted?: () => void;
}) {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [runs, setRuns] = useState<PayrollRunSummary[]>([]);
  const [period, setPeriod] = useState("2026-11");
  const [autoTransferTax, setAutoTransferTax] = useState(true);
  const [preview, setPreview] = useState<{
    totals: PayrollTotals;
    journal_lines: JournalLine[];
    tax_transfer_lines: JournalLine[];
  } | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Ny ansatt-skjema
  const [showAdd, setShowAdd] = useState(false);
  const [fullName, setFullName] = useState("");
  const [position, setPosition] = useState("Utvikler / Konsulent");
  const [bankAccount, setBankAccount] = useState("");
  const [salary, setSalary] = useState("50000");
  const [taxPct, setTaxPct] = useState("30");
  const [holidayPct, setHolidayPct] = useState("12");
  const [agaZone, setAgaZone] = useState("1");
  const [otpPct, setOtpPct] = useState("2");
  const [dept, setDept] = useState("ADM");
  const [proj, setProj] = useState("FELLES");

  async function loadAll() {
    try {
      const [eRes, rRes] = await Promise.all([
        fetch(`${apiBase}/payroll/employees`).then((r) => r.json()),
        fetch(`${apiBase}/payroll/runs`).then((r) => r.json()),
      ]);
      if (Array.isArray(eRes)) setEmployees(eRes);
      if (Array.isArray(rRes)) setRuns(rRes);
    } catch {
      // ignore initial offline
    }
  }

  async function loadPreview(p = period) {
    setError(null);
    try {
      const res = await fetch(`${apiBase}/payroll/preview`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ period: p, auto_transfer_tax_account: autoTransferTax }),
      });
      const data = await res.json();
      if (res.ok && data.ok) {
        setPreview({
          totals: data.totals,
          journal_lines: data.journal_lines,
          tax_transfer_lines: data.tax_transfer_lines,
        });
      }
    } catch {
      // ignore
    }
  }

  useEffect(() => {
    const currentMonth = new Date().toISOString().slice(0, 7);
    setPeriod(currentMonth);
    void loadAll().then(() => loadPreview(currentMonth));
  }, []);

  async function addEmployee(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`${apiBase}/payroll/employees`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          full_name: fullName,
          position,
          bank_account: bankAccount || null,
          monthly_gross_salary: Number(salary),
          tax_percent: Number(taxPct),
          holiday_pay_percent: Number(holidayPct),
          aga_zone: Number(agaZone),
          otp_percent: Number(otpPct),
          department_code: dept,
          project_code: proj,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Kunne ikke opprette ansatt.");
      setFullName("");
      setShowAdd(false);
      await loadAll();
      await loadPreview();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Feil ved oppretting.");
    } finally {
      setBusy(false);
    }
  }

  async function removeEmployee(id: number) {
    if (!window.confirm("Deaktivere denne ansatte fra lønnskjøring?")) return;
    await fetch(`${apiBase}/payroll/employees/${id}`, { method: "DELETE" });
    await loadAll();
    await loadPreview();
  }

  async function runPayroll() {
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const res = await fetch(`${apiBase}/payroll/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          period,
          auto_transfer_tax_account: autoTransferTax,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Lønnskjøring feilet.");
      setMessage(
        `Lønnskjøring ${data.period} bokført automatisk! Hovedbilag #${data.voucher_number}` +
          (data.tax_transfer_voucher_number
            ? ` + Skattetrekkskonto 1950 Bilag #${data.tax_transfer_voucher_number}`
            : "") +
          ` (Sum Debet == Sum Kredit: ${fmt(data.totals.sum_debit)} kr).`,
      );
      await loadAll();
      onPosted?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Feil under lønnskjøring.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Automatisk Lønnskjøring (NS 4102)</h2>
          <p className="text-sm text-slate-500">
            Fordeler alle punkter automatisk: Fastlønn (5000), Feriepenger (5180/2940), AGA (5400/2770),
            AGA feriepenger (5190/2780), OTP (5420/2960), Nettolønn (2930) og sperret Skattetrekkskonto (1950).
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setShowAdd((v) => !v)}
            className="inline-flex items-center gap-2 rounded-xl border border-slate-300 bg-white px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 cursor-pointer"
          >
            <PlusCircle className="w-4 h-4" />
            Ny ansatt
          </button>
          <button
            type="button"
            onClick={() => void loadPreview()}
            className="inline-flex items-center gap-2 rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 cursor-pointer"
          >
            <RefreshCw className="w-4 h-4" />
            Oppdater fordeling
          </button>
        </div>
      </div>

      {message && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900 flex items-center gap-2">
          <CheckCircle className="w-5 h-5 text-emerald-600 shrink-0" />
          <span>{message}</span>
        </div>
      )}
      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>
      )}

      {showAdd && (
        <form
          onSubmit={addEmployee}
          className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs space-y-4"
        >
          <h3 className="font-bold text-slate-900 text-sm">Legg til ansatt</h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            <input
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Fullt navn"
              className="rounded-lg border border-slate-300 px-3 py-2 text-slate-900"
            />
            <input
              value={position}
              onChange={(e) => setPosition(e.target.value)}
              placeholder="Stilling"
              className="rounded-lg border border-slate-300 px-3 py-2 text-slate-900"
            />
            <input
              value={bankAccount}
              onChange={(e) => setBankAccount(e.target.value)}
              placeholder="Kontonr (1234.56.78903)"
              className="rounded-lg border border-slate-300 px-3 py-2 text-slate-900 font-mono"
            />
            <input
              type="number"
              required
              step="0.01"
              value={salary}
              onChange={(e) => setSalary(e.target.value)}
              placeholder="Brutto månedslønn"
              className="rounded-lg border border-slate-300 px-3 py-2 text-slate-900"
            />
            <input
              type="number"
              step="0.1"
              value={taxPct}
              onChange={(e) => setTaxPct(e.target.value)}
              placeholder="Skattetrekk %"
              className="rounded-lg border border-slate-300 px-3 py-2 text-slate-900"
            />
            <select
              value={agaZone}
              onChange={(e) => setAgaZone(e.target.value)}
              className="rounded-lg border border-slate-300 px-3 py-2 text-slate-900 bg-white"
            >
              <option value="1">AGA Sone 1 (14,1%)</option>
              <option value="2">AGA Sone 2 (10,6%)</option>
              <option value="3">AGA Sone 3 (6,4%)</option>
              <option value="4">AGA Sone 4 (5,1%)</option>
              <option value="5">AGA Sone 5 (0,0% - Tiltakssonen)</option>
            </select>
            <input
              type="number"
              step="0.1"
              value={holidayPct}
              onChange={(e) => setHolidayPct(e.target.value)}
              placeholder="Feriepenger % (12)"
              className="rounded-lg border border-slate-300 px-3 py-2 text-slate-900"
            />
            <input
              type="number"
              step="0.1"
              value={otpPct}
              onChange={(e) => setOtpPct(e.target.value)}
              placeholder="OTP pensjon % (min 2)"
              className="rounded-lg border border-slate-300 px-3 py-2 text-slate-900"
            />
            <div className="flex gap-2">
              <input
                value={dept}
                onChange={(e) => setDept(e.target.value)}
                placeholder="Avd (ADM)"
                className="w-1/2 rounded-lg border border-slate-300 px-3 py-2 text-slate-900"
              />
              <input
                value={proj}
                onChange={(e) => setProj(e.target.value)}
                placeholder="Prosjekt"
                className="w-1/2 rounded-lg border border-slate-300 px-3 py-2 text-slate-900"
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={busy}
            className="rounded-xl bg-blue-600 hover:bg-blue-700 px-4 py-2 text-xs font-semibold text-white cursor-pointer"
          >
            Lagre ansatt
          </button>
        </form>
      )}

      {/* Ansattregister */}
      <div className="rounded-2xl border border-slate-200 bg-white overflow-hidden shadow-xs">
        <div className="px-5 py-3.5 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
          <div className="flex items-center gap-2 font-bold text-slate-800 text-sm">
            <Users className="w-4 h-4 text-blue-600" />
            <span>Aktive ansatte ({employees.length})</span>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-slate-50 text-slate-500 border-b border-slate-200">
              <tr>
                <th className="px-4 py-2.5">Ansatt</th>
                <th className="px-4 py-2.5">Avd / Prosjekt</th>
                <th className="px-4 py-2.5 text-right">Bruttolønn</th>
                <th className="px-4 py-2.5 text-right">Skatt</th>
                <th className="px-4 py-2.5 text-right">Feriepenger</th>
                <th className="px-4 py-2.5 text-right">AGA</th>
                <th className="px-4 py-2.5 text-right">OTP</th>
                <th className="px-4 py-2.5"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {employees.map((e) => (
                <tr key={e.id} className="hover:bg-slate-50/70">
                  <td className="px-4 py-2.5">
                    <div className="font-semibold text-slate-900">{e.full_name}</div>
                    <div className="text-[11px] text-slate-500">
                      {e.employee_number} · {e.position}
                    </div>
                  </td>
                  <td className="px-4 py-2.5 font-mono text-[11px] text-slate-600">
                    {e.department_code} / {e.project_code}
                  </td>
                  <td className="px-4 py-2.5 text-right font-mono font-semibold text-slate-900">
                    {fmt(e.monthly_gross_salary)}
                  </td>
                  <td className="px-4 py-2.5 text-right">{e.tax_percent}%</td>
                  <td className="px-4 py-2.5 text-right">{e.holiday_pay_percent}%</td>
                  <td className="px-4 py-2.5 text-right">
                    Sone {e.aga_zone} ({e.aga_percent}%)
                  </td>
                  <td className="px-4 py-2.5 text-right">{e.otp_percent}%</td>
                  <td className="px-4 py-2.5 text-right">
                    <button
                      onClick={() => void removeEmployee(e.id)}
                      className="text-slate-400 hover:text-red-600 cursor-pointer"
                      title="Deaktiver ansatt"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Kjør lønn + Live automatisk fordeling */}
      {preview && (
        <div className="rounded-2xl border border-blue-200 bg-white p-5 shadow-xs space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-4">
            <div className="flex flex-wrap items-center gap-3">
              <label className="text-xs font-semibold text-slate-700">
                Periode:
                <input
                  type="month"
                  value={period}
                  onChange={(e) => {
                    setPeriod(e.target.value);
                    void loadPreview(e.target.value);
                  }}
                  className="ml-2 rounded-lg border border-slate-300 px-2.5 py-1.5 text-xs font-mono"
                />
              </label>
              <label className="inline-flex items-center gap-2 text-xs text-slate-700">
                <input
                  type="checkbox"
                  checked={autoTransferTax}
                  onChange={(e) => setAutoTransferTax(e.target.checked)}
                />
                Automatisk overføring til Skattetrekkskonto 1950 (§ 5-12)
              </label>
            </div>
            <button
              type="button"
              onClick={() => void runPayroll()}
              disabled={busy}
              className="rounded-xl bg-emerald-600 hover:bg-emerald-700 px-5 py-2.5 text-xs font-bold text-white shadow-xs disabled:opacity-50 cursor-pointer"
            >
              {busy ? "Bokfører lønnskjøring…" : `Godkjenn og bokfør lønn (${period})`}
            </button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-xs">
            <div className="rounded-xl bg-slate-50 p-3 border border-slate-200">
              <div className="text-slate-500">Bruttolønn (5000)</div>
              <div className="font-bold text-slate-900 text-sm mt-0.5">{fmt(preview.totals.total_gross)} kr</div>
            </div>
            <div className="rounded-xl bg-emerald-50 p-3 border border-emerald-200">
              <div className="text-emerald-700">Netto utbetalt (2930)</div>
              <div className="font-bold text-emerald-900 text-sm mt-0.5">{fmt(preview.totals.total_net_pay)} kr</div>
            </div>
            <div className="rounded-xl bg-amber-50 p-3 border border-amber-200">
              <div className="text-amber-700">Skattetrekk → 1950</div>
              <div className="font-bold text-amber-900 text-sm mt-0.5">{fmt(preview.totals.total_tax_withholding)} kr</div>
            </div>
            <div className="rounded-xl bg-blue-50 p-3 border border-blue-200">
              <div className="text-blue-700">Feriepenger + AGA + OTP</div>
              <div className="font-bold text-blue-900 text-sm mt-0.5">
                {fmt(preview.totals.total_holiday_pay + preview.totals.total_aga + preview.totals.total_aga_holiday + preview.totals.total_otp)} kr
              </div>
            </div>
            <div className="rounded-xl bg-slate-900 p-3 text-white">
              <div className="text-slate-400">Total lønnskostnad</div>
              <div className="font-bold text-sm mt-0.5">{fmt(preview.totals.total_employer_cost)} kr</div>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-50 text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="px-3 py-2">Konto</th>
                  <th className="px-3 py-2">Beskrivelse</th>
                  <th className="px-3 py-2">Avd / Prosjekt</th>
                  <th className="px-3 py-2 text-right">Debet</th>
                  <th className="px-3 py-2 text-right">Kredit</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {preview.journal_lines.map((l, idx) => (
                  <tr key={idx}>
                    <td className="px-3 py-1.5 font-mono font-semibold text-slate-900">{l.account_number}</td>
                    <td className="px-3 py-1.5 text-slate-700">{l.description}</td>
                    <td className="px-3 py-1.5 font-mono text-[11px] text-slate-500">
                      {l.department_code} / {l.project_code}
                    </td>
                    <td className="px-3 py-1.5 text-right font-mono">{l.debit > 0 ? fmt(l.debit) : ""}</td>
                    <td className="px-3 py-1.5 text-right font-mono">{l.credit > 0 ? fmt(l.credit) : ""}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot className="bg-slate-50 font-bold border-t border-slate-200">
                <tr>
                  <td colSpan={3} className="px-3 py-2">
                    Sum hovedbilag ({preview.totals.is_balanced ? "BALANSERT ✓" : "UBALANSERT"})
                  </td>
                  <td className="px-3 py-2 text-right font-mono">{fmt(preview.totals.sum_debit)}</td>
                  <td className="px-3 py-2 text-right font-mono">{fmt(preview.totals.sum_credit)}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      )}

      {/* Tidligere lønnskjøringer */}
      {runs.length > 0 && (
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-slate-900 text-sm">Bokførte lønnskjøringer ({runs.length})</h3>
            <button
              type="button"
              onClick={() => window.print()}
              className="inline-flex items-center gap-1.5 text-xs text-slate-600 hover:text-slate-900 cursor-pointer"
            >
              <Printer className="w-3.5 h-3.5" />
              Skriv ut lønnsoversikt
            </button>
          </div>
          <div className="space-y-2">
            {runs.map((r) => (
              <div
                key={r.id}
                className="rounded-xl border border-slate-200 p-3.5 flex flex-wrap items-center justify-between gap-2 text-xs"
              >
                <div>
                  <div className="font-bold text-slate-900">
                    Periode {r.period} · Bilag #{r.voucher_number}
                    {r.tax_transfer_voucher_number ? ` (+ Skattetrekkskonto #${r.tax_transfer_voucher_number})` : ""}
                  </div>
                  <div className="text-slate-500 mt-0.5">
                    {r.lines.length} ansatte · Netto {fmt(r.total_net_pay)} kr · Skatt {fmt(r.total_tax_withholding)} kr · Total kostnad {fmt(r.total_employer_cost)} kr
                  </div>
                </div>
                <span className="rounded-full bg-emerald-100 text-emerald-800 px-2.5 py-1 font-semibold">
                  BOKFØRT
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
