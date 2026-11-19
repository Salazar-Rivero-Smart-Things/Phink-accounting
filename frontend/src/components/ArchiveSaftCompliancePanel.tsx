"use client";

import React, { useEffect, useState } from "react";
import {
  AlertTriangle,
  CheckCircle,
  Download,
  ExternalLink,
  FileText,
  FolderCheck,
  RefreshCw,
  Search,
  ShieldCheck,
  Upload,
} from "lucide-react";

interface ArchiveItem {
  id: number;
  voucher_number: number;
  date: string;
  description: string;
  department_code?: string | null;
  project_code?: string | null;
  document_url?: string | null;
  document_name?: string | null;
  total_debit: number;
  total_credit: number;
  is_balanced: boolean;
  retention_until?: string | null;
  lines: Array<{
    account_number: number;
    account_name: string;
    description: string;
    debit: number;
    credit: number;
  }>;
}

interface ComplianceResult {
  overall_status: "PASS" | "WARNING" | "FAIL";
  passed: number;
  warnings: number;
  failed: number;
  total_checks: number;
  checked_at: string;
  advisory_note: string;
  checks: Array<{ id: string; title: string; status: "PASS" | "WARNING" | "FAIL"; details: string }>;
}

interface TrialBalance {
  lines: Array<{
    account_number: number;
    account_name: string;
    account_type: string;
    debit: number;
    credit: number;
    balance: number;
  }>;
  total_debit: number;
  total_credit: number;
  is_balanced: boolean;
}

interface DimensionsReport {
  by_department: Array<{ code: string; revenue: number; expenses: number; net: number }>;
  by_project: Array<{ code: string; revenue: number; expenses: number; net: number }>;
}

const fmt = (n: number) =>
  (n ?? 0).toLocaleString("nb-NO", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export default function ArchiveSaftCompliancePanel({
  apiBase,
  mode,
  onImported,
  onOpenOpeningBalance,
}: {
  apiBase: string;
  mode: "archive" | "saft" | "compliance";
  onImported?: () => void;
  onOpenOpeningBalance?: () => void;
}) {
  const [query, setQuery] = useState("");
  const [archive, setArchive] = useState<{ total_vouchers: number; with_attachments: number; items: ArchiveItem[] }>({
    total_vouchers: 0,
    with_attachments: 0,
    items: [],
  });
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [compliance, setCompliance] = useState<ComplianceResult | null>(null);
  const [trialBalance, setTrialBalance] = useState<TrialBalance | null>(null);
  const [dimReport, setDimReport] = useState<DimensionsReport | null>(null);
  const [importResult, setImportResult] = useState<Record<string, unknown> | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadArchive(q = query) {
    const url = q.trim()
      ? `${apiBase}/accounting/archive?q=${encodeURIComponent(q.trim())}`
      : `${apiBase}/accounting/archive`;
    const res = await fetch(url);
    if (res.ok) setArchive(await res.json());
  }

  async function loadComplianceAndReports() {
    setBusy(true);
    try {
      const [cRes, tbRes, dRes] = await Promise.all([
        fetch(`${apiBase}/accounting/compliance-check`).then((r) => r.json()),
        fetch(`${apiBase}/accounting/reports/trial-balance`).then((r) => r.json()),
        fetch(`${apiBase}/accounting/reports/dimensions`).then((r) => r.json()),
      ]);
      setCompliance(cRes);
      setTrialBalance(tbRes);
      setDimReport(dRes);
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    if (mode === "archive") void loadArchive();
    if (mode === "compliance") void loadComplianceAndReports();
  }, [mode]);

  async function handleSaftImport(file: File) {
    setBusy(true);
    setError(null);
    setImportResult(null);
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch(`${apiBase}/accounting/saft/import`, { method: "POST", body: form });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "SAF-T import feilet.");
      setImportResult(data);
      onImported?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "SAF-T import feilet.");
    } finally {
      setBusy(false);
    }
  }

  if (mode === "archive") {
    return (
      <div className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-slate-900">Bilagsarkiv (Bokføringsloven § 13)</h2>
            <p className="text-sm text-slate-500">
              Komplett, søkbart arkiv over alle bokførte bilag, vedlagte PDF/bilder og lovpålagt 5-års oppbevaring.
            </p>
          </div>
          <div className="text-xs font-semibold text-slate-600 bg-white border border-slate-200 rounded-xl px-4 py-2">
            {archive.total_vouchers} bilag · {archive.with_attachments} med vedlegg
          </div>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            void loadArchive(query);
          }}
          className="flex gap-2"
        >
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Søk etter bilagsnr, beskrivelse, konto eller dokumentnavn…"
              className="w-full rounded-xl border border-slate-300 bg-white pl-9 pr-3 py-2 text-sm text-slate-900"
            />
          </div>
          <button
            type="submit"
            className="rounded-xl bg-blue-600 hover:bg-blue-700 px-4 py-2 text-xs font-semibold text-white cursor-pointer"
          >
            Søk i arkiv
          </button>
        </form>

        <div className="space-y-2.5">
          {archive.items.map((item) => {
            const isOpen = expandedId === item.id;
            return (
              <div key={item.id} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold bg-slate-900 text-white px-2 py-0.5 rounded-md">
                        Bilag #{item.voucher_number}
                      </span>
                      <span className="font-semibold text-slate-900 text-sm">{item.description}</span>
                    </div>
                    <div className="text-xs text-slate-500 mt-1 flex flex-wrap gap-3">
                      <span>Dato: {item.date?.slice(0, 10)}</span>
                      <span>Beløp: {fmt(item.total_debit)} kr</span>
                      {item.department_code && <span>Avd: {item.department_code}</span>}
                      {item.project_code && <span>Prosjekt: {item.project_code}</span>}
                      {item.retention_until && <span>Oppbevares til: {item.retention_until}</span>}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {item.document_url && (
                      <a
                        href={item.document_url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 rounded-lg border border-blue-200 bg-blue-50 px-3 py-1.5 text-xs font-semibold text-blue-700 hover:bg-blue-100"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                        Vis vedlegg
                      </a>
                    )}
                    <button
                      type="button"
                      onClick={() => setExpandedId(isOpen ? null : item.id)}
                      className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 cursor-pointer"
                    >
                      {isOpen ? "Skjul linjer" : "Vis postering"}
                    </button>
                  </div>
                </div>
                {isOpen && (
                  <div className="mt-3 pt-3 border-t border-slate-100 overflow-x-auto">
                    <table className="w-full text-xs text-left">
                      <thead className="text-slate-500">
                        <tr>
                          <th className="py-1">Konto</th>
                          <th className="py-1">Beskrivelse</th>
                          <th className="py-1 text-right">Debet</th>
                          <th className="py-1 text-right">Kredit</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {item.lines.map((l, idx) => (
                          <tr key={idx}>
                            <td className="py-1 font-mono font-semibold">
                              {l.account_number} {l.account_name}
                            </td>
                            <td className="py-1 text-slate-600">{l.description}</td>
                            <td className="py-1 text-right font-mono">{l.debit > 0 ? fmt(l.debit) : ""}</td>
                            <td className="py-1 text-right font-mono">{l.credit > 0 ? fmt(l.credit) : ""}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  if (mode === "saft") {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">SAF-T Financial XML v1.30 (Eksport & Import)</h2>
          <p className="text-sm text-slate-500">
            Offisiell norsk Skatteetaten-standard (Standard Audit File - Tax). Eksporter komplett regnskap som XML,
            eller importer SAF-T XML fra Conta, Fiken, Tripletex eller Phink.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center">
                <Download className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-slate-900">Eksporter SAF-T XML</h3>
                <p className="text-xs text-slate-500">Header, NS 4102 kontoplan, kunder, leverandører, MVA-tabell & hovedbok</p>
              </div>
            </div>
            <a
              href={`${apiBase}/accounting/saft/export`}
              className="inline-flex items-center justify-center gap-2 w-full rounded-xl bg-emerald-600 hover:bg-emerald-700 px-4 py-2.5 text-sm font-semibold text-white"
            >
              <Download className="w-4 h-4" />
              Last ned norsk SAF-T (.xml)
            </a>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-blue-100 text-blue-700 flex items-center justify-center">
                <Upload className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-slate-900">Importer SAF-T XML</h3>
                <p className="text-xs text-slate-500">Validerer dobbel bokføring på hvert bilag før import</p>
              </div>
            </div>
            <label className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 hover:bg-slate-100 px-4 py-6 text-center cursor-pointer">
              <FileText className="w-6 h-6 text-blue-600 mb-1" />
              <span className="text-xs font-semibold text-slate-700">
                {busy ? "Importerer og validerer SAF-T XML…" : "Velg SAF-T .xml-fil for import"}
              </span>
              <input
                type="file"
                accept=".xml"
                disabled={busy}
                className="hidden"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) void handleSaftImport(f);
                }}
              />
            </label>
          </div>
        </div>

        {onOpenOpeningBalance && (
          <div className="rounded-2xl border border-emerald-200 bg-emerald-50/70 p-5 flex flex-wrap items-center justify-between gap-4">
            <div>
              <h3 className="font-bold text-emerald-950 text-sm">
                Manuell inngående balanse (Saldo på bankkonto i dag)
              </h3>
              <p className="text-xs text-emerald-800 mt-0.5">
                Har du ikke en SAF-T fil, eller vil du legge inn nøyaktig saldo på driftskontoen (1920) i dag manuelt?
                Klikk her for å importere inngående balanse med ett klikk.
              </p>
            </div>
            <button
              type="button"
              onClick={onOpenOpeningBalance}
              className="rounded-xl bg-emerald-600 hover:bg-emerald-700 px-4 py-2.5 text-xs font-bold text-white shadow-xs cursor-pointer"
            >
              + Importer saldo på konto i dag (Manuell balanse)
            </button>
          </div>
        )}

        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>
        )}
        {importResult && (
          <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-5 text-sm text-emerald-950 space-y-1">
            <div className="font-bold flex items-center gap-2">
              <FolderCheck className="w-5 h-5 text-emerald-600" />
              SAF-T import fullført: {String(importResult.filename)}
            </div>
            <div className="text-xs">
              Bilag importert: <strong>{String(importResult.vouchers_imported)}</strong> · Nye kontoer:{" "}
              <strong>{String(importResult.accounts_created)}</strong> · Kunder:{" "}
              <strong>{String(importResult.customers_created)}</strong> · Leverandører:{" "}
              <strong>{String(importResult.suppliers_created)}</strong> · Hoppet over (ubalansert):{" "}
              <strong>{String(importResult.skipped_unbalanced_count)}</strong>
            </div>
          </div>
        )}
      </div>
    );
  }

  // mode === "compliance"
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Regnskapsfaglig kontroll & Rapporter</h2>
          <p className="text-sm text-slate-500">
            Automatisk revisjons- og lovsjekk før systemet tas i bruk med ekte kundedata, samt Saldobalanse og Prosjekt/Avdeling.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void loadComplianceAndReports()}
          disabled={busy}
          className="inline-flex items-center gap-2 rounded-xl bg-slate-900 hover:bg-slate-800 px-4 py-2 text-xs font-semibold text-white cursor-pointer"
        >
          <RefreshCw className={`w-4 h-4 ${busy ? "animate-spin" : ""}`} />
          Kjør kontroll på nytt
        </button>
      </div>

      {compliance && (
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 pb-3">
            <div className="flex items-center gap-2.5">
              <ShieldCheck className="w-6 h-6 text-blue-600" />
              <div>
                <div className="font-bold text-slate-900">
                  Status: {compliance.passed}/{compliance.total_checks} bestått · {compliance.warnings} advarsler · {compliance.failed} feil
                </div>
                <div className="text-xs text-slate-500">Kontrollert: {compliance.checked_at.slice(0, 19).replace("T", " ")} UTC</div>
              </div>
            </div>
            <span
              className={`rounded-full px-3 py-1 text-xs font-bold ${
                compliance.overall_status === "PASS"
                  ? "bg-emerald-100 text-emerald-800"
                  : compliance.overall_status === "WARNING"
                    ? "bg-amber-100 text-amber-800"
                    : "bg-red-100 text-red-800"
              }`}
            >
              {compliance.overall_status}
            </span>
          </div>

          <div className="space-y-2">
            {compliance.checks.map((c) => (
              <div
                key={c.id}
                className="rounded-xl border border-slate-200 p-3.5 flex items-start justify-between gap-3 text-xs"
              >
                <div className="flex items-start gap-2.5">
                  {c.status === "PASS" ? (
                    <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  ) : (
                    <AlertTriangle
                      className={`w-4 h-4 shrink-0 mt-0.5 ${
                        c.status === "WARNING" ? "text-amber-500" : "text-red-600"
                      }`}
                    />
                  )}
                  <div>
                    <div className="font-semibold text-slate-900">{c.title}</div>
                    <div className="text-slate-600 mt-0.5">{c.details}</div>
                  </div>
                </div>
                <span
                  className={`shrink-0 rounded-md px-2 py-0.5 font-bold ${
                    c.status === "PASS"
                      ? "bg-emerald-50 text-emerald-700"
                      : c.status === "WARNING"
                        ? "bg-amber-50 text-amber-700"
                        : "bg-red-50 text-red-700"
                  }`}
                >
                  {c.status}
                </span>
              </div>
            ))}
          </div>

          <div className="rounded-xl bg-amber-50 border border-amber-200 p-3.5 text-xs text-amber-950">
            <strong>Regnskapsfaglig anbefaling:</strong> {compliance.advisory_note}
          </div>
        </div>
      )}

      {/* Saldobalanse */}
      {trialBalance && (
        <div className="rounded-2xl border border-slate-200 bg-white overflow-hidden shadow-xs">
          <div className="px-5 py-3.5 border-b border-slate-200 bg-slate-50 flex items-center justify-between text-sm font-bold text-slate-900">
            <span>Saldobalanse (NS 4102)</span>
            <span className={trialBalance.is_balanced ? "text-emerald-700 text-xs" : "text-red-600 text-xs"}>
              {trialBalance.is_balanced ? "BALANSERT ✓" : "UBALANSERT"}
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-50 text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-2">Konto</th>
                  <th className="px-4 py-2">Kontonavn</th>
                  <th className="px-4 py-2 text-right">Sum Debet</th>
                  <th className="px-4 py-2 text-right">Sum Kredit</th>
                  <th className="px-4 py-2 text-right">Saldo</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {trialBalance.lines.map((l) => (
                  <tr key={l.account_number}>
                    <td className="px-4 py-1.5 font-mono font-semibold">{l.account_number}</td>
                    <td className="px-4 py-1.5 text-slate-700">{l.account_name}</td>
                    <td className="px-4 py-1.5 text-right font-mono">{fmt(l.debit)}</td>
                    <td className="px-4 py-1.5 text-right font-mono">{fmt(l.credit)}</td>
                    <td className="px-4 py-1.5 text-right font-mono font-semibold">{fmt(l.balance)}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot className="bg-slate-50 font-bold border-t border-slate-200">
                <tr>
                  <td colSpan={2} className="px-4 py-2">TOTALT</td>
                  <td className="px-4 py-2 text-right font-mono">{fmt(trialBalance.total_debit)}</td>
                  <td className="px-4 py-2 text-right font-mono">{fmt(trialBalance.total_credit)}</td>
                  <td className="px-4 py-2 text-right font-mono">
                    {fmt(trialBalance.total_debit - trialBalance.total_credit)}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      )}

      {/* Prosjekt & Avdeling */}
      {dimReport && (dimReport.by_department.length > 0 || dimReport.by_project.length > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs">
            <h3 className="font-bold text-slate-900 text-sm mb-3">Resultat per avdeling</h3>
            <table className="w-full text-xs">
              <thead className="text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="py-1.5 text-left">Avdeling</th>
                  <th className="py-1.5 text-right">Inntekt</th>
                  <th className="py-1.5 text-right">Kostnad</th>
                  <th className="py-1.5 text-right">Resultat</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {dimReport.by_department.map((d) => (
                  <tr key={d.code}>
                    <td className="py-1.5 font-mono font-semibold">{d.code}</td>
                    <td className="py-1.5 text-right font-mono">{fmt(d.revenue)}</td>
                    <td className="py-1.5 text-right font-mono">{fmt(d.expenses)}</td>
                    <td className="py-1.5 text-right font-mono font-bold">{fmt(d.net)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs">
            <h3 className="font-bold text-slate-900 text-sm mb-3">Resultat per prosjekt</h3>
            <table className="w-full text-xs">
              <thead className="text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="py-1.5 text-left">Prosjekt</th>
                  <th className="py-1.5 text-right">Inntekt</th>
                  <th className="py-1.5 text-right">Kostnad</th>
                  <th className="py-1.5 text-right">Resultat</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {dimReport.by_project.map((p) => (
                  <tr key={p.code}>
                    <td className="py-1.5 font-mono font-semibold">{p.code}</td>
                    <td className="py-1.5 text-right font-mono">{fmt(p.revenue)}</td>
                    <td className="py-1.5 text-right font-mono">{fmt(p.expenses)}</td>
                    <td className="py-1.5 text-right font-mono font-bold">{fmt(p.net)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
