"use client";
import { useState } from "react";
import { motion } from "framer-motion";
import type { Mode, Nudge } from "@/lib/types";
import { ModeBadge } from "./badges";

const RAIL: Record<Mode, string> = {
  protect: "border-l-protect", grow: "border-l-grow", guide: "border-l-guide",
};

export type ActResult = {
  executed: boolean;
  prepared: boolean;
  detail: string;
  deep_link?: string | null;
};

export function ActionCard({ nudge, result }: { nudge: Nudge; result: ActResult | null }) {
  const [showWhy, setShowWhy] = useState(false);
  const [approved, setApproved] = useState(false);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 14, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ type: "spring", stiffness: 320, damping: 28 }}
      className={`card overflow-hidden border-l-[3px] ${RAIL[nudge.mode]}`}>
      <div className="p-4">
        <div className="flex items-start justify-between gap-3">
          <h3 className="text-[15px] font-semibold leading-snug">{nudge.title}</h3>
          <ModeBadge mode={nudge.mode} />
        </div>
        <p className="mt-1.5 text-sm leading-relaxed text-ink-2">{nudge.message}</p>

        {nudge.journey && (
          <ol className="mt-3 space-y-1.5 border-l-2 border-guide/30 pl-3">
            {nudge.journey.map((step, i) => (
              <li key={i} className="flex gap-2 text-[13px] text-ink-2">
                <span className="font-semibold text-guide">{i + 1}.</span> {step}
              </li>
            ))}
          </ol>
        )}

        <div className="mt-3.5 flex flex-wrap items-center gap-2">
          {!approved ? (
            <button className="btn-primary px-3.5 py-1.5 text-sm" onClick={() => setApproved(true)}>
              {nudge.action_label}
            </button>
          ) : result ? (
            <ResultChip result={result} />
          ) : (
            <span className="text-sm text-ink-3">Working…</span>
          )}
          <button className="btn-ghost px-3 py-1.5 text-sm" onClick={() => setShowWhy(v => !v)}
            aria-expanded={showWhy}>
            {showWhy ? "Hide reasoning" : "Why?"}
          </button>
          {nudge.reversible && (
            <span className="ml-auto inline-flex items-center gap-1 rounded-full bg-protect-soft px-2 py-0.5 text-[11px] font-semibold text-protect">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" className="h-3 w-3">
                <path d="M9 14 4 9l5-5" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M4 9h10a6 6 0 0 1 0 12h-3" strokeLinecap="round" />
              </svg>
              Reversible
            </span>
          )}
        </div>

        {showWhy && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }}
            className="mt-3 rounded-xl bg-surface-2 p-3">
            <div className="text-[11px] font-semibold uppercase tracking-wide text-ink-3">
              Reasoning trace
            </div>
            <ul className="mt-1.5 space-y-1">
              {nudge.reasoning.map((r, i) => (
                <li key={i} className="flex gap-2 text-[13px] leading-relaxed text-ink-2">
                  <span className="mt-[7px] h-1 w-1 shrink-0 rounded-full bg-ink-3" aria-hidden />
                  {r}
                </li>
              ))}
            </ul>
          </motion.div>
        )}

        {nudge.regulated && (
          <p className="mt-3 rounded-lg border border-border bg-surface-2 px-3 py-2 text-[11px] leading-relaxed text-ink-3">
            Suggestion only. Not investment/insurance advice. Your bank executes this,
            subject to suitability. Reversible.
          </p>
        )}
      </div>
    </motion.div>
  );
}

function ResultChip({ result }: { result: ActResult }) {
  if (result.prepared) {
    return (
      <span className="inline-flex flex-wrap items-center gap-2 text-sm">
        <span className="inline-flex items-center gap-1.5 rounded-full bg-primary-soft px-2.5 py-1 font-semibold text-primary">
          <Check /> Prepared — you complete it
        </span>
        {result.deep_link && (
          <span className="text-xs text-ink-3">
            Open in bank app: <code className="rounded bg-surface-2 px-1 py-0.5">{result.deep_link}</code>
          </span>
        )}
      </span>
    );
  }
  if (result.executed) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-protect-soft px-2.5 py-1 text-sm font-semibold text-protect">
        <Check /> {result.detail}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center rounded-full bg-danger-soft px-2.5 py-1 text-sm font-semibold text-danger">
      Blocked — {result.detail}
    </span>
  );
}

function Check() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.6" className="h-3.5 w-3.5">
      <path d="m5 12.5 4.5 4.5L19 7.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
