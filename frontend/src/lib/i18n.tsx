"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { Globe } from "lucide-react";

export type AppLang = "en" | "nb";

interface LanguageContextValue {
  lang: AppLang;
  setLang: (next: AppLang) => void;
  t: (nbText: string, enText: string) => string;
  openPicker: () => void;
}

const LanguageContext = createContext<LanguageContextValue>({
  lang: "en",
  setLang: () => undefined,
  t: (_nb, en) => en,
  openPicker: () => undefined,
});

const STORAGE_KEY = "phink_lang";

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<AppLang>("en");
  const [showPicker, setShowPicker] = useState(false);

  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved === "en" || saved === "nb") {
        setLangState(saved);
        setShowPicker(false);
      } else {
        // First visit: ask the user right at the beginning which language they want!
        setShowPicker(true);
      }
    } catch {
      setShowPicker(false);
    }
  }, []);

  function setLang(next: AppLang) {
    setLangState(next);
    setShowPicker(false);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // ignore storage errors
    }
  }

  function t(nbText: string, enText: string) {
    return lang === "en" ? enText : nbText;
  }

  return (
    <LanguageContext.Provider value={{ lang, setLang, t, openPicker: () => setShowPicker(true) }}>
      {children}

      {/* Velkomst-språkvelger helt i begynnelsen (første besøk eller ved klikk på språk) */}
      {showPicker && (
        <div className="fixed inset-0 z-[100] bg-slate-950/85 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-md rounded-2xl border border-amber-500/40 bg-slate-900 p-7 text-center shadow-2xl space-y-6">
            <div className="w-16 h-16 mx-auto rounded-2xl bg-black border border-amber-500/40 p-1.5 flex items-center justify-center shadow-lg">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="/brand/logo.png" alt="Phink Accounting" className="w-full h-full object-contain" />
            </div>

            <div className="space-y-1.5">
              <div className="inline-flex items-center gap-1.5 rounded-full bg-amber-500/15 border border-amber-500/30 px-3 py-1 text-[11px] font-semibold text-amber-300">
                <Globe className="w-3.5 h-3.5" />
                <span>Language / Språkvalg</span>
              </div>
              <h2 className="text-xl font-bold text-white">Choose Your Language / Velg språk</h2>
              <p className="text-xs text-slate-400">
                Select your preferred language. All NS 4102 legal accounting entries &amp; reports automatically adapt.
                <br />
                Velg ønsket språk. Alle regnskapsposter (NS 4102) og rapporter tilpasses automatisk.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setLang("en")}
                className="rounded-xl border-2 border-amber-500 bg-amber-500/15 hover:bg-amber-500/25 p-4 text-left transition-all cursor-pointer space-y-1"
              >
                <div className="text-sm font-bold text-white flex items-center justify-between">
                  <span>🇬🇧 English</span>
                  <span className="text-[10px] rounded bg-amber-500 text-slate-950 px-1.5 py-0.5 font-extrabold">
                    DEFAULT
                  </span>
                </div>
                <p className="text-[11px] text-slate-300">
                  Full English UI &amp; official English NS 4102 Chart of Accounts (Norwegian Accounting Act).
                </p>
              </button>

              <button
                type="button"
                onClick={() => setLang("nb")}
                className="rounded-xl border border-slate-700 bg-slate-800/80 hover:border-blue-400 hover:bg-slate-800 p-4 text-left transition-all cursor-pointer space-y-1"
              >
                <div className="text-sm font-bold text-white">🇳🇴 Norsk (Bokmål)</div>
                <p className="text-[11px] text-slate-300">
                  Norsk brukergrensesnitt &amp; Norsk Standard Kontoplan (NS 4102) og Altinn.
                </p>
              </button>
            </div>

            <p className="text-[11px] text-slate-500">
              You can switch language anytime from the top bar or sidebar.
            </p>
          </div>
        </div>
      )}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  return useContext(LanguageContext);
}

export function LanguageToggle({ compact = false }: { compact?: boolean }) {
  const { lang, setLang } = useLanguage();
  return (
    <div
      className={`inline-flex items-center rounded-lg border border-slate-700 bg-slate-900/90 p-0.5 text-[11px] font-bold ${
        compact ? "" : "shadow-xs"
      }`}
      title="Switch language / Bytt språk"
    >
      <button
        type="button"
        onClick={() => setLang("en")}
        className={`px-2 py-1 rounded-md transition-colors cursor-pointer ${
          lang === "en" ? "bg-amber-500 text-slate-950" : "text-slate-400 hover:text-white"
        }`}
      >
        EN
      </button>
      <button
        type="button"
        onClick={() => setLang("nb")}
        className={`px-2 py-1 rounded-md transition-colors cursor-pointer ${
          lang === "nb" ? "bg-blue-600 text-white" : "text-slate-400 hover:text-white"
        }`}
      >
        NO
      </button>
    </div>
  );
}
