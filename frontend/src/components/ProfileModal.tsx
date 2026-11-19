"use client";

import React, { useEffect, useState } from "react";
import { CheckCircle, Lock, Receipt, Search, ShieldCheck, Smartphone, X } from "lucide-react";
import type { AuthUser } from "./AuthModal";

const ENTITY_OPTIONS: Array<{ value: AuthUser["entity_type"]; label: string }> = [
  { value: "AS", label: "Aksjeselskap (AS)" },
  { value: "ENK", label: "Enkeltpersonforetak (ENK)" },
  { value: "PRIVATE", label: "Privatperson" },
  { value: "FORENING", label: "Forening / Lag" },
  { value: "INSTITUSJON", label: "Institusjon / Stiftelse" },
];

export default function ProfileModal({
  apiBase,
  user,
  onClose,
  onUpdated,
}: {
  apiBase: string;
  user: AuthUser;
  onClose: () => void;
  onUpdated: (updated: AuthUser) => void;
}) {
  const [fullName, setFullName] = useState(user.full_name || "");
  const [companyName, setCompanyName] = useState(user.company_name || "");
  const [entityType, setEntityType] = useState<AuthUser["entity_type"]>(user.entity_type || "AS");
  const [orgNumber, setOrgNumber] = useState(user.org_number || "");
  const [nationalId, setNationalId] = useState("");
  const [paymentMethod, setPaymentMethod] = useState<"VIPPS_BEDRIFT" | "FAKTURA">("VIPPS_BEDRIFT");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const isAdmin = Boolean(user.is_admin);
  const [allUsers, setAllUsers] = useState<AuthUser[]>([]);
  const [targetUserId, setTargetUserId] = useState<number>(user.id);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchingUsers, setSearchingUsers] = useState(false);

  useEffect(() => {
    if (!isAdmin) return;
    const token = typeof window !== "undefined" ? localStorage.getItem("phink_token") || "" : "";
    const trimmed = searchQuery.trim();
    const url = trimmed
      ? `${apiBase}/auth/users?q=${encodeURIComponent(trimmed)}`
      : `${apiBase}/auth/users`;
    setSearchingUsers(true);
    fetch(url, { headers: token ? { Authorization: `Bearer ${token}` } : undefined })
      .then((r) => (r.ok ? r.json() : []))
      .then((list) => {
        if (Array.isArray(list)) setAllUsers(list);
      })
      .catch(() => undefined)
      .finally(() => setSearchingUsers(false));
  }, [apiBase, isAdmin, searchQuery]);

  function selectTargetUser(id: number, listOverride?: AuthUser[]) {
    setTargetUserId(id);
    const source = listOverride || allUsers;
    const found = source.find((u) => u.id === id);
    if (found) {
      setFullName(found.full_name || "");
      setCompanyName(found.company_name || "");
      setEntityType(found.entity_type || "AS");
      setOrgNumber(found.org_number || "");
      setNationalId("");
    }
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setSuccess(null);
    try {
      const token = localStorage.getItem("phink_token") || "";
      const res = await fetch(`${apiBase}/auth/profile`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          full_name: fullName,
          company_name: companyName,
          entity_type: entityType,
          org_number: orgNumber.trim() || null,
          national_id: nationalId.trim() || null,
          payment_method: paymentMethod,
          target_user_id: isAdmin ? targetUserId : undefined,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Kunne ikke oppdatere profilen.");
      setSuccess(data.message);
      if (data.user && !data.pending_admin_approval && data.user.id === user.id) {
        onUpdated(data.user);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Feil ved oppdatering.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 backdrop-blur-xs p-4">
      <div className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white shadow-2xl overflow-hidden">
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4 bg-slate-50">
          <div className="flex items-center gap-2.5">
            <ShieldCheck className="w-5 h-5 text-blue-600" />
            <div>
              <h3 className="font-bold text-slate-900 text-sm">
                {isAdmin ? "Administrator — Rediger bruker-/kundeprofil" : "Be Administrator om profilendring (150 kr)"}
              </h3>
              <p className="text-[11px] text-slate-500">
                {isAdmin
                  ? "Kun Administrator kan endre låste profiler (0 kr)"
                  : "Profilen er låst etter registrering. Send endringsforespørsel til Administrator (150 kr eks. MVA)."}
              </p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700 cursor-pointer">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSave} className="p-6 space-y-4 text-xs">
          {isAdmin && (
            <div className="rounded-xl border border-blue-200 bg-blue-50 p-3 space-y-2.5">
              <div>
                <label className="block font-bold text-blue-900 mb-1">
                  Søk etter registrert firma eller enkeltperson (navn, org.nr eller fødselsnummer):
                </label>
                <div className="relative">
                  <Search className="w-3.5 h-3.5 text-blue-500 absolute left-3 top-2.5" />
                  <input
                    type="search"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Skriv navn, firmanavn, 9-sifret org.nr eller 11-sifret fødselsnummer…"
                    className="w-full rounded-lg border border-blue-300 bg-white pl-8 pr-3 py-2 text-slate-900 placeholder:text-slate-400"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-blue-900 mb-1">
                  Velg bruker/kunde å redigere ({searchingUsers ? "Søker…" : `${allUsers.length} treff`}):
                </label>
                {allUsers.length > 0 ? (
                  <select
                    value={allUsers.some((u) => u.id === targetUserId) ? targetUserId : allUsers[0].id}
                    onChange={(e) => selectTargetUser(Number(e.target.value))}
                    className="w-full rounded-lg border border-blue-300 bg-white px-3 py-2 text-slate-900"
                  >
                    {allUsers.map((u) => (
                      <option key={u.id} value={u.id}>
                        {u.company_name ? `${u.company_name} — ` : ""}
                        {u.full_name} ({u.entity_type}
                        {u.org_number ? ` · Org.nr ${u.org_number}` : ""}
                        {u.national_id_masked ? ` · Fnr ${u.national_id_masked}` : ""}) — {u.email}
                      </option>
                    ))}
                  </select>
                ) : (
                  <div className="rounded-lg border border-blue-200 bg-white px-3 py-2 text-slate-500">
                    Ingen registrerte firmaer eller enkeltpersoner matchet «{searchQuery}».
                  </div>
                )}
                {searchQuery.trim() && allUsers.length > 0 && (
                  <div className="mt-2 max-h-32 overflow-y-auto divide-y divide-blue-100 rounded-lg border border-blue-200 bg-white">
                    {allUsers.map((u) => (
                      <button
                        key={u.id}
                        type="button"
                        onClick={() => selectTargetUser(u.id)}
                        className={`w-full text-left px-3 py-2 hover:bg-blue-50 cursor-pointer flex items-center justify-between ${
                          targetUserId === u.id ? "bg-blue-50 font-bold" : ""
                        }`}
                      >
                        <div>
                          <div className="text-slate-900">
                            {u.company_name || u.full_name} <span className="text-slate-500">({u.entity_type})</span>
                          </div>
                          <div className="text-[10px] text-slate-500">
                            {u.full_name} · {u.email}
                            {u.org_number ? ` · Org.nr ${u.org_number}` : ""}
                            {u.national_id_masked ? ` · Fnr ${u.national_id_masked}` : ""}
                          </div>
                        </div>
                        <span className="text-[10px] text-blue-700 font-semibold shrink-0 ml-2">Velg →</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {!isAdmin && (
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 flex items-start gap-2 text-slate-700">
              <Lock className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
              <span>
                Profilen din er låst etter første registrering. Fyll ut hva som skal rettes under — forespørselen sendes
                til Administrator sammen med endringsgebyret (150 kr eks. MVA).
              </span>
            </div>
          )}
          <div>
            <label className="block font-semibold text-slate-700 mb-1">Kontotype / Selskapsform</label>
            <select
              value={entityType}
              onChange={(e) => setEntityType(e.target.value as AuthUser["entity_type"])}
              className="w-full rounded-xl border border-slate-300 px-3 py-2 text-slate-900 bg-white"
            >
              {ENTITY_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Fullt navn</label>
              <input
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full rounded-xl border border-slate-300 px-3 py-2 text-slate-900"
              />
            </div>
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Firmanavn</label>
              <input
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                className="w-full rounded-xl border border-slate-300 px-3 py-2 text-slate-900"
              />
            </div>
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Organisasjonsnummer (9 siffer)</label>
              <input
                value={orgNumber}
                onChange={(e) => setOrgNumber(e.target.value)}
                placeholder="984 851 006"
                className="w-full rounded-xl border border-slate-300 px-3 py-2 font-mono text-slate-900"
              />
            </div>
            <div>
              <label className="block font-semibold text-slate-700 mb-1">Nytt fødselsnummer (valgfritt)</label>
              <input
                value={nationalId}
                onChange={(e) => setNationalId(e.target.value)}
                placeholder={user.national_id_masked || "11 siffer"}
                className="w-full rounded-xl border border-slate-300 px-3 py-2 font-mono text-slate-900"
              />
            </div>
          </div>

          {!isAdmin && (
            <div className="rounded-xl border border-amber-200 bg-amber-50 p-3.5 space-y-2">
              <div className="font-bold text-amber-950">Endringsgebyr: 150 kr eks. MVA (187,50 kr inkl. 25 % MVA)</div>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setPaymentMethod("VIPPS_BEDRIFT")}
                  className={`rounded-lg border px-3 py-2 font-semibold flex items-center justify-center gap-1.5 cursor-pointer ${
                    paymentMethod === "VIPPS_BEDRIFT"
                      ? "border-orange-500 bg-orange-100 text-orange-900"
                      : "border-slate-300 bg-white text-slate-600"
                  }`}
                >
                  <Smartphone className="w-3.5 h-3.5" />
                  Vipps Bedrift
                </button>
                <button
                  type="button"
                  onClick={() => setPaymentMethod("FAKTURA")}
                  className={`rounded-lg border px-3 py-2 font-semibold flex items-center justify-center gap-1.5 cursor-pointer ${
                    paymentMethod === "FAKTURA"
                      ? "border-blue-600 bg-blue-100 text-blue-900"
                      : "border-slate-300 bg-white text-slate-600"
                  }`}
                >
                  <Receipt className="w-3.5 h-3.5" />
                  Tilsendt faktura
                </button>
              </div>
            </div>
          )}

          {error && <div className="rounded-xl bg-red-50 border border-red-200 p-3 text-red-700">{error}</div>}
          {success && (
            <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-3 text-emerald-900 flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>{success}</span>
            </div>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-xl border border-slate-300 px-4 py-2 text-slate-700 hover:bg-slate-50 cursor-pointer"
            >
              Lukk
            </button>
            <button
              type="submit"
              disabled={busy}
              className="rounded-xl bg-blue-600 hover:bg-blue-700 px-5 py-2 font-bold text-white disabled:opacity-50 cursor-pointer"
            >
              {busy
                ? "Sender…"
                : isAdmin
                  ? "Lagre profilendring som Administrator (0 kr)"
                  : "Send forespørsel til Administrator (150 kr)"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
