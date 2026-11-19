"use client";

import React, { useEffect, useState } from "react";
import { AlertTriangle, Bell, CheckCircle, Info, RefreshCw, ArrowRight } from "lucide-react";

export interface NotificationItem {
  id: string;
  severity: "CRITICAL" | "WARNING" | "INFO";
  category: string;
  title: string;
  message: string;
  action_tab: string;
  action_label: string;
  created_at: string;
}

export default function NotificationsPanel({
  apiBase,
  onNavigate,
  onCountChange,
}: {
  apiBase: string;
  onNavigate: (tab: string) => void;
  onCountChange?: (count: number) => void;
}) {
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [dismissed, setDismissed] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  async function loadNotifications() {
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/accounting/notifications`);
      if (res.ok) {
        const data = await res.json();
        const list = Array.isArray(data.items) ? data.items : [];
        setItems(list);
        onCountChange?.(list.length);
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadNotifications();
  }, []);

  const visible = items.filter((i) => !dismissed.includes(i.id));

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Varslinger & Oppmerksomhetspunkter</h2>
          <p className="text-sm text-slate-500">
            Her ser du alt som krever handling: forfalte fakturaer, uavstemte bankposter, bilag i kø,
            skattetrekkskonto og regnskapsfaglige varsler.
          </p>
        </div>
        <button
          type="button"
          onClick={() => {
            setDismissed([]);
            void loadNotifications();
          }}
          className="inline-flex items-center gap-2 rounded-xl bg-slate-900 hover:bg-slate-800 px-4 py-2 text-xs font-semibold text-white cursor-pointer"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          Oppdater varslinger
        </button>
      </div>

      {loading ? (
        <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-500">
          Sjekker regnskap, fakturaer, bank og frister…
        </div>
      ) : visible.length === 0 ? (
        <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-8 text-center space-y-2">
          <CheckCircle className="w-10 h-10 text-emerald-600 mx-auto" />
          <h3 className="font-bold text-emerald-950 text-base">Alt ser strålende ut!</h3>
          <p className="text-xs text-emerald-800">
            Det er ingen aktive varslinger som krever oppmerksomhet akkurat nå.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {visible.map((n) => {
            const isCritical = n.severity === "CRITICAL";
            const isWarn = n.severity === "WARNING";
            return (
              <div
                key={n.id}
                className={`rounded-2xl border p-4 shadow-xs flex flex-wrap items-center justify-between gap-4 ${
                  isCritical
                    ? "border-red-200 bg-red-50/70"
                    : isWarn
                      ? "border-amber-200 bg-amber-50/70"
                      : "border-blue-200 bg-blue-50/60"
                }`}
              >
                <div className="flex items-start gap-3 min-w-0 flex-1">
                  <div
                    className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${
                      isCritical
                        ? "bg-red-100 text-red-700"
                        : isWarn
                          ? "bg-amber-100 text-amber-700"
                          : "bg-blue-100 text-blue-700"
                    }`}
                  >
                    {isCritical || isWarn ? <AlertTriangle className="w-5 h-5" /> : <Info className="w-5 h-5" />}
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-white/80 text-slate-700 border border-slate-200">
                        {n.category}
                      </span>
                      <span
                        className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${
                          isCritical
                            ? "bg-red-600 text-white"
                            : isWarn
                              ? "bg-amber-500 text-white"
                              : "bg-blue-600 text-white"
                        }`}
                      >
                        {isCritical ? "Kritisk" : isWarn ? "Handling kreves" : "Info"}
                      </span>
                    </div>
                    <h3 className="font-bold text-slate-900 text-sm mt-1">{n.title}</h3>
                    <p className="text-xs text-slate-700 mt-0.5">{n.message}</p>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <button
                    type="button"
                    onClick={() => onNavigate(n.action_tab)}
                    className="inline-flex items-center gap-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 px-3.5 py-2 text-xs font-semibold text-white cursor-pointer"
                  >
                    <span>{n.action_label}</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      const next = [...dismissed, n.id];
                      setDismissed(next);
                      onCountChange?.(items.length - next.length);
                    }}
                    className="rounded-xl border border-slate-300 bg-white hover:bg-slate-100 px-3 py-2 text-xs font-medium text-slate-600 cursor-pointer"
                  >
                    Skjul
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      <div className="rounded-xl border border-slate-200 bg-white p-4 text-xs text-slate-500 flex items-center gap-2">
        <Bell className="w-4 h-4 text-slate-400 shrink-0" />
        <span>Varslingene oppdateres automatisk basert på live data fra regnskap, bank, lønn og kundeservice.</span>
      </div>
    </div>
  );
}
