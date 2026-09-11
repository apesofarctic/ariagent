"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { api } from "@/lib/api";
import { useApp } from "@/lib/app-context";
import type { Mode } from "@/lib/types";

const MODES: { id: Mode; name: string; desc: string; ring: string; dot: string }[] = [
  {
    id: "protect", name: "Protect",
    desc: "Forecast overdrafts, catch duplicate subscriptions and odd charges — before the money is gone.",
    ring: "peer-checked:border-protect peer-checked:bg-protect-soft", dot: "bg-protect",
  },
  {
    id: "grow", name: "Grow",
    desc: "Spot idle cash, salary hikes and recurring surplus, and suggest ways to put them to work.",
    ring: "peer-checked:border-grow peer-checked:bg-grow-soft", dot: "bg-grow",
  },
  {
    id: "guide", name: "Guide",
    desc: "Recognise life events from spending patterns and walk you through the big moments, step by step.",
    ring: "peer-checked:border-guide peer-checked:bg-guide-soft", dot: "bg-guide",
  },
];

export default function Onboarding() {
  const router = useRouter();
  const { refreshStatus } = useApp();
  const [scopes, setScopes] = useState<Record<Mode, boolean>>({ protect: true, grow: true, guide: true });
  const [adult, setAdult] = useState(false);
  const [notice, setNotice] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canContinue = adult && Object.values(scopes).some(Boolean);

  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      await api.grantConsent(scopes);
      await refreshStatus();
      router.replace("/");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto flex min-h-screen max-w-xl flex-col justify-center px-4 py-10">
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}>
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-[#1d4ed8]">
            <svg viewBox="0 0 28 28" className="h-7 w-7" aria-hidden>
              <path d="M8 19.5 14 8l6 11.5" fill="none" stroke="#fff" strokeWidth="2.4"
                strokeLinecap="round" strokeLinejoin="round" />
              <circle cx="14" cy="16.2" r="1.6" fill="#34d399" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold tracking-tight">Before anything flows</h1>
          <p className="mx-auto mt-2 max-w-md text-sm leading-relaxed text-ink-2">
            Ariagent watches your transactions to <strong>warn you of overdrafts, find savings,
            and guide life events</strong> — and nothing else. It analyses on this device,
            never moves money itself, and you can see, export or delete everything it knows,
            or withdraw consent, at any time.
          </p>
        </div>

        <div className="space-y-3" role="group" aria-label="Choose what Ariagent may do">
          {MODES.map((m) => (
            <label key={m.id} className="block cursor-pointer">
              <input type="checkbox" className="peer sr-only" checked={scopes[m.id]}
                onChange={(e) => setScopes((s) => ({ ...s, [m.id]: e.target.checked }))} />
              <div className={`card flex items-start gap-3 p-4 transition-colors peer-focus-visible:outline-2 ${m.ring} ${
                scopes[m.id] ? "" : "opacity-70"
              }`}>
                <span className={`mt-1 h-2.5 w-2.5 shrink-0 rounded-full ${m.dot}`} aria-hidden />
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold">{m.name}</span>
                    <span className={`text-xs font-semibold ${scopes[m.id] ? "text-primary" : "text-ink-3"}`}>
                      {scopes[m.id] ? "Opted in" : "Off"}
                    </span>
                  </div>
                  <p className="mt-0.5 text-[13px] leading-relaxed text-ink-2">{m.desc}</p>
                </div>
              </div>
            </label>
          ))}
        </div>

        <label className="mt-5 flex items-start gap-2.5 text-sm text-ink-2">
          <input type="checkbox" className="mt-0.5 h-4 w-4 accent-[#1d4ed8]" checked={adult}
            onChange={(e) => setAdult(e.target.checked)} />
          <span>I confirm I am an adult account holder acting for myself.</span>
        </label>

        <button className="mt-2 text-left text-xs text-primary underline"
          onClick={() => setNotice((v) => !v)} aria-expanded={notice}>
          {notice ? "Hide privacy notice" : "Read the privacy notice"}
        </button>
        {notice && (
          <div className="mt-2 rounded-xl border border-border bg-surface-2 p-4 text-xs leading-relaxed text-ink-2">
            <p><strong>What we collect:</strong> transaction rows (date, amount, merchant, category)
              you provide — synthetic demo data by default, or a bank statement you upload yourself.
              Never credentials, OTPs, or full account numbers.</p>
            <p className="mt-2"><strong>Why:</strong> solely to compute the warnings, savings and
              guidance you opted into above. No other purpose, no resale, no ads.</p>
            <p className="mt-2"><strong>Where:</strong> all analysis runs on this device (local model).
              Your data never leaves the machine.</p>
            <p className="mt-2"><strong>Your rights (DPDP Act 2023):</strong> see everything Ariagent
              knows, correct or delete any inference, export all data, delete all data, and withdraw
              this consent — each in one click from Settings.</p>
          </div>
        )}

        {error && <p className="mt-3 text-sm text-danger">{error}</p>}

        <button className="btn-primary mt-6 w-full py-3 text-[15px]" disabled={!canContinue || busy}
          onClick={submit}>
          {busy ? "Setting up…" : "I consent — take me in"}
        </button>
        <p className="mt-3 text-center text-xs text-ink-3">
          Consent is per-mode, purpose-bound and revocable — withdrawing is as easy as giving it.
        </p>
      </motion.div>
    </div>
  );
}
