"use client";

import React, { useEffect, useState } from "react";

/**
 * Viser logoen som et raskt 1-sekunds glimt (3/4 av skjermen) før innlogging / hovedside.
 */
export default function LogoSplash({ durationMs = 1000 }: { durationMs?: number }) {
  const [phase, setPhase] = useState<"visible" | "fading" | "done">("visible");

  useEffect(() => {
    const fadeStart = Math.max(200, durationMs - 200);
    const t1 = window.setTimeout(() => setPhase("fading"), fadeStart);
    const t2 = window.setTimeout(() => setPhase("done"), durationMs);
    return () => {
      window.clearTimeout(t1);
      window.clearTimeout(t2);
    };
  }, [durationMs]);

  if (phase === "done") return null;

  return (
    <div
      aria-label="Think Accounting"
      className={`fixed inset-0 z-[100] flex items-center justify-center bg-black transition-opacity duration-200 ${
        phase === "fading" ? "opacity-0 pointer-events-none" : "opacity-100"
      }`}
    >
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src="/brand/logo.png"
        alt="Think Accounting Logo"
        className="w-[75vw] h-[75vh] max-w-[75vw] max-h-[75vh] object-contain select-none drop-shadow-[0_0_40px_rgba(234,179,8,0.28)]"
      />
    </div>
  );
}
