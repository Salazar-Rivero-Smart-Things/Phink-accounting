"use client";

import React, { useEffect, useState } from "react";
import { Bell, CheckCircle, CreditCard, Receipt, Send, Smartphone } from "lucide-react";

interface PlanItem {
  id: string;
  name: string;
  description: string;
  price_ex_vat: number;
  vat_percent: number;
  vat_amount: number;
  total_inc_vat: number;
}

interface BillingOrder {
  id: number;
  customer_name: string;
  customer_email: string;
  plan_name: string;
  payment_method: "VIPPS_BEDRIFT" | "FAKTURA";
  total_amount: number;
  vipps_number?: string | null;
  payment_reference: string;
  status: string;
  due_date?: string | null;
  created_at?: string | null;
}

interface MonthlyReminder {
  month: string;
  billed_this_month_count: number;
  due_count: number;
  due_customers: Array<{
    customer_name: string;
    customer_email: string;
    plan_name: string;
    total_amount: number;
    last_billed_at?: string | null;
  }>;
  needs_monthly_action: boolean;
}

const fmt = (n: number) =>
  (n ?? 0).toLocaleString("nb-NO", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export default function BillingPanel({
  apiBase,
  onChanged,
}: {
  apiBase: string;
  onChanged?: () => void;
}) {
  const [plans, setPlans] = useState<PlanItem[]>([]);
  const [vippsNumber, setVippsNumber] = useState("");
  const [orders, setOrders] = useState<BillingOrder[]>([]);
  const [monthly, setMonthly] = useState<MonthlyReminder | null>(null);

  const [selectedPlan, setSelectedPlan] = useState("PHINK_STANDARD");
  const [includeBank, setIncludeBank] = useState(false);
  const [includeSaft, setIncludeSaft] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState<"VIPPS_BEDRIFT" | "FAKTURA">("VIPPS_BEDRIFT");
  const [customerName, setCustomerName] = useState("");
  const [customerEmail, setCustomerEmail] = useState("");
  const [orgNumber, setOrgNumber] = useState("");
  const [busy, setBusy] = useState(false);
  const [resultMsg, setResultMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadAll() {
    try {
      const [pRes, oRes, mRes] = await Promise.all([
        fetch(`${apiBase}/billing/plans`).then((r) => r.json()),
        fetch(`${apiBase}/billing/orders`).then((r) => r.json()),
        fetch(`${apiBase}/billing/monthly-reminders`).then((r) => r.json()),
      ]);
      if (Array.isArray(pRes?.plans)) setPlans(pRes.plans);
      if (typeof pRes?.vipps_number === "string") setVippsNumber(pRes.vipps_number);
      if (Array.isArray(oRes)) setOrders(oRes);
      if (mRes?.month) setMonthly(mRes);
    } catch {
      // ignore offline
    }
  }

  useEffect(() => {
    void loadAll();
  }, []);

  async function saveVippsNumber() {
    if (!vippsNumber.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`${apiBase}/billing/vipps-config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ vipps_number: vippsNumber.trim() }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Kunne ikke lagre Vipps Bedrift-nummer.");
      setResultMsg(`Vipps Bedrift-nummer (${data.vipps_number}) lagret!`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Feil ved lagring.");
    } finally {
      setBusy(false);
    }
  }

  async function handleCheckout(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setResultMsg(null);
    try {
      const res = await fetch(`${apiBase}/billing/checkout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          plan_id: selectedPlan,
          payment_method: paymentMethod,
          customer_name: customerName,
          customer_email: customerEmail,
          org_number: orgNumber || null,
          include_bank_integration: includeBank,
          include_saft_import: includeSaft,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Kunne ikke opprette betaling.");
      setResultMsg(data.instructions);
      setCustomerName("");
      setCustomerEmail("");
      setOrgNumber("");
      await loadAll();
      onChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Betalingsfeil.");
    } finally {
      setBusy(false);
    }
  }

  async function markPaid(orderId: number) {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`${apiBase}/billing/orders/${orderId}/mark-paid`, { method: "POST" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Kunne ikke registrere betaling.");
      setResultMsg(`Betaling registrert og bokført på bilag #${data.voucher_number}!`);
      await loadAll();
      onChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Feil.");
    } finally {
      setBusy(false);
    }
  }

  async function sendDueMonthlyInvoices() {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`${apiBase}/billing/send-monthly-invoices`, { method: "POST" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Kunne ikke sende månedens fakturaer.");
      setResultMsg(`Sendte og bokførte ${data.created_count} månedlige faktura(er) for ${data.month}!`);
      await loadAll();
      onChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Feil.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">Betaling: Kun Vipps Bedrift &amp; Tilsendt Faktura</h2>
        <p className="text-sm text-slate-500">
          Phink Accounting mottar betaling kun via norsk <strong>Vipps Bedrift</strong> eller{" "}
          <strong>tilsendt faktura (25 % MVA &amp; KID)</strong> — med automatisk månedlig fakturapåminnelse i Varslinger.
        </p>
      </div>

      {/* Månedlig fakturapåminnelse */}
      {monthly && (
        <div
          className={`rounded-2xl border p-4 flex flex-wrap items-center justify-between gap-4 ${
            monthly.due_count > 0
              ? "border-amber-300 bg-amber-50 text-amber-950"
              : "border-emerald-200 bg-emerald-50 text-emerald-950"
          }`}
        >
          <div className="flex items-start gap-3">
            <Bell className="w-5 h-5 mt-0.5 shrink-0" />
            <div className="text-xs">
              <div className="font-bold text-sm">
                Månedlig fakturapåminnelse ({monthly.month})
              </div>
              <p className="mt-0.5">
                {monthly.due_count > 0
                  ? `${monthly.due_count} abonnementskunde(r) skal ha månedlig faktura for ${monthly.month}.`
                  : monthly.billed_this_month_count > 0
                    ? `${monthly.billed_this_month_count} kunde(r) er allerede fakturert denne måneden.`
                    : "Ingen månedlige abonnementsfakturaer er sendt for denne måneden ennå — opprett nedenfor."}
              </p>
            </div>
          </div>
          {monthly.due_count > 0 && (
            <button
              type="button"
              onClick={() => void sendDueMonthlyInvoices()}
              disabled={busy}
              className="inline-flex items-center gap-2 rounded-xl bg-amber-600 hover:bg-amber-700 px-4 py-2 text-xs font-bold text-white cursor-pointer"
            >
              <Send className="w-4 h-4" />
              Send {monthly.due_count} månedlige faktura(er) nå
            </button>
          )}
        </div>
      )}

      {resultMsg && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900 flex items-center gap-2">
          <CheckCircle className="w-5 h-5 text-emerald-600 shrink-0" />
          <span>{resultMsg}</span>
        </div>
      )}
      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>
      )}

      {/* Vipps Bedrift oppsett */}
      <div className="rounded-2xl border border-orange-200 bg-white p-5 shadow-xs flex flex-wrap items-end justify-between gap-4">
        <div className="flex-1 min-w-[240px]">
          <div className="flex items-center gap-2 font-bold text-slate-900 text-sm mb-1">
            <Smartphone className="w-4 h-4 text-orange-500" />
            <span>Ditt Vipps Bedrift-nummer</span>
          </div>
          <p className="text-xs text-slate-500 mb-2">
            Vises automatisk til kunder som velger Vipps Bedrift ved betaling.
          </p>
          <input
            type="text"
            value={vippsNumber}
            onChange={(e) => setVippsNumber(e.target.value)}
            placeholder="F.eks. #123456"
            className="w-full max-w-xs rounded-xl border border-slate-300 px-3 py-2 text-sm font-mono text-slate-900"
          />
        </div>
        <button
          type="button"
          onClick={() => void saveVippsNumber()}
          disabled={busy}
          className="rounded-xl bg-orange-500 hover:bg-orange-600 px-4 py-2 text-xs font-bold text-white cursor-pointer"
        >
          Lagre Vipps Bedrift nr
        </button>
      </div>

      {/* Opprett betaling / månedlig faktura */}
      <form
        onSubmit={handleCheckout}
        className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-5"
      >
        <h3 className="font-bold text-slate-900 text-base">Ny betaling eller månedlig faktura</h3>

        <div className="space-y-3">
          {plans.map((p) => (
            <div
              key={p.id}
              className="rounded-xl border border-blue-600 bg-blue-50/70 p-4 flex flex-wrap items-center justify-between gap-2"
            >
              <div>
                <div className="font-bold text-slate-900 text-sm">{p.name}</div>
                <div className="text-xs text-slate-600">{p.description}</div>
              </div>
              <div className="text-right">
                <div className="text-lg font-extrabold text-blue-700">{fmt(p.price_ex_vat)} kr/mnd</div>
                <div className="text-[11px] text-slate-500">eks. MVA ({fmt(p.total_inc_vat)} kr inkl. 25 % MVA)</div>
              </div>
            </div>
          ))}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <label className="flex items-center justify-between rounded-xl border border-slate-200 p-3 cursor-pointer hover:bg-slate-50">
              <span className="inline-flex items-center gap-2 font-medium text-slate-800">
                <input
                  type="checkbox"
                  checked={includeBank}
                  onChange={(e) => setIncludeBank(e.target.checked)}
                />
                Bankintegrasjon (innlogging &amp; automatisk KID)
              </span>
              <span className="font-mono font-bold text-blue-700">+ 59 kr/mnd</span>
            </label>
            <label className="flex items-center justify-between rounded-xl border border-slate-200 p-3 cursor-pointer hover:bg-slate-50">
              <span className="inline-flex items-center gap-2 font-medium text-slate-800">
                <input
                  type="checkbox"
                  checked={includeSaft}
                  onChange={(e) => setIncludeSaft(e.target.checked)}
                />
                SAF-T XML filimport
              </span>
              <span className="font-mono font-bold text-blue-700">+ 79 kr</span>
            </label>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <button
            type="button"
            onClick={() => setPaymentMethod("VIPPS_BEDRIFT")}
            className={`flex items-center gap-3 rounded-xl border p-4 text-left cursor-pointer ${
              paymentMethod === "VIPPS_BEDRIFT"
                ? "border-orange-500 bg-orange-50 ring-1 ring-orange-500"
                : "border-slate-200 hover:border-slate-300"
            }`}
          >
            <Smartphone className="w-6 h-6 text-orange-500 shrink-0" />
            <div>
              <div className="font-bold text-slate-900 text-sm">Vipps Bedrift</div>
              <div className="text-xs text-slate-500">Rask mobilbetaling til ditt Vipps Bedrift-nummer</div>
            </div>
          </button>

          <button
            type="button"
            onClick={() => setPaymentMethod("FAKTURA")}
            className={`flex items-center gap-3 rounded-xl border p-4 text-left cursor-pointer ${
              paymentMethod === "FAKTURA"
                ? "border-blue-600 bg-blue-50 ring-1 ring-blue-600"
                : "border-slate-200 hover:border-slate-300"
            }`}
          >
            <Receipt className="w-6 h-6 text-blue-600 shrink-0" />
            <div>
              <div className="font-bold text-slate-900 text-sm">Tilsendt faktura (14 dager)</div>
              <div className="text-xs text-slate-500">Automatisk bokført norsk faktura med 25 % MVA og KID</div>
            </div>
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          <input
            required
            value={customerName}
            onChange={(e) => setCustomerName(e.target.value)}
            placeholder="Kundenavn / Firmanavn"
            className="rounded-xl border border-slate-300 px-3 py-2 text-slate-900"
          />
          <input
            type="email"
            required
            value={customerEmail}
            onChange={(e) => setCustomerEmail(e.target.value)}
            placeholder="E-post for faktura / kvittering"
            className="rounded-xl border border-slate-300 px-3 py-2 text-slate-900"
          />
          <input
            value={orgNumber}
            onChange={(e) => setOrgNumber(e.target.value)}
            placeholder="Orgnr (valgfritt)"
            className="rounded-xl border border-slate-300 px-3 py-2 text-slate-900 font-mono"
          />
        </div>

        <button
          type="submit"
          disabled={busy}
          className={`inline-flex items-center gap-2 rounded-xl px-5 py-2.5 text-xs font-bold text-white shadow-xs disabled:opacity-50 cursor-pointer ${
            paymentMethod === "VIPPS_BEDRIFT"
              ? "bg-orange-500 hover:bg-orange-600"
              : "bg-blue-600 hover:bg-blue-700"
          }`}
        >
          <CreditCard className="w-4 h-4" />
          {paymentMethod === "VIPPS_BEDRIFT"
            ? "Opprett Vipps Bedrift-betaling"
            : "Opprett og send faktura (25 % MVA)"}
        </button>
      </form>

      {/* Ordrehistorikk */}
      <div className="rounded-2xl border border-slate-200 bg-white overflow-hidden shadow-xs">
        <div className="px-5 py-3.5 border-b border-slate-200 bg-slate-50 font-bold text-sm text-slate-900">
          Registrerte Vipps Bedrift &amp; Faktura-betalinger ({orders.length})
        </div>
        {orders.length === 0 ? (
          <div className="p-5 text-xs text-slate-500">Ingen betalinger registrert ennå.</div>
        ) : (
          <div className="divide-y divide-slate-100">
            {orders.map((o) => (
              <div key={o.id} className="p-4 flex flex-wrap items-center justify-between gap-3 text-xs">
                <div>
                  <div className="font-bold text-slate-900">
                    {o.customer_name} · {o.plan_name}
                  </div>
                  <div className="text-slate-500 mt-0.5">
                    {o.payment_method === "VIPPS_BEDRIFT" ? "Vipps Bedrift" : "Tilsendt faktura"} · Ref/KID:{" "}
                    <span className="font-mono">{o.payment_reference}</span> · {fmt(o.total_amount)} kr inkl. MVA
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={`rounded-full px-2.5 py-1 font-bold ${
                      o.status === "PAID"
                        ? "bg-emerald-100 text-emerald-800"
                        : "bg-amber-100 text-amber-800"
                    }`}
                  >
                    {o.status === "PAID" ? "BETALT" : o.status === "INVOICE_SENT" ? "FAKTURA SENDT" : "VENTER VIPPS"}
                  </span>
                  {o.status !== "PAID" && (
                    <button
                      type="button"
                      onClick={() => void markPaid(o.id)}
                      disabled={busy}
                      className="rounded-lg bg-emerald-600 hover:bg-emerald-700 px-3 py-1.5 text-white font-semibold cursor-pointer"
                    >
                      Marker betalt
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
