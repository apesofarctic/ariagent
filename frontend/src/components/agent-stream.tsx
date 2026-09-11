"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { api } from "@/lib/api";
import type { Mode, Nudge, StreamEvent } from "@/lib/types";
import { ModeBadge, StageChip } from "./badges";
import { ActionCard, type ActResult } from "./action-card";

type FeedItem =
  | { kind: "log"; key: string; stage: string; agent: string; detail: string; mode?: Mode }
  | { kind: "card"; key: string; signal: string; nudge: Nudge; result: ActResult | null }
  | { kind: "restraint"; key: string; signal: string; mode: Mode; action: "hold" | "suppress"; reason: string };

export type Decisions = Record<string, "fire" | "hold" | "suppress" | "sequence">;

const AGENT_MODE_CLS: Record<Mode, string> = {
  protect: "text-protect", grow: "text-grow", guide: "text-guide",
};

export function AgentStream({ scripted, onDecisions }: {
  scripted: boolean;
  onDecisions?: (d: Decisions) => void;
}) {
  const [items, setItems] = useState<FeedItem[]>([]);
  const [running, setRunning] = useState(false);
  const [hasRun, setHasRun] = useState(false);
  const esRef = useRef<EventSource | null>(null);
  const decisionsRef = useRef<Decisions>({});
  const keyRef = useRef(0);

  useEffect(() => () => esRef.current?.close(), []);

  const run = useCallback(() => {
    esRef.current?.close();
    setItems([]);
    decisionsRef.current = {};
    onDecisions?.({});
    setRunning(true);
    setHasRun(true);

    const es = new EventSource(api.streamUrl(scripted));
    esRef.current = es;

    es.onmessage = (e) => {
      const ev: StreamEvent = JSON.parse(e.data);
      const key = `k${keyRef.current++}`;

      if (ev.stage === "done") {
        es.close();
        setRunning(false);
        return;
      }
      if (ev.stage === "decide" && ev.signal && ev.action) {
        decisionsRef.current = { ...decisionsRef.current, [ev.signal]: ev.action };
        onDecisions?.(decisionsRef.current);
      }
      setItems((prev) => {
        const next = [...prev];
        if (ev.stage === "decide" && ev.signal && ev.action) {
          if (ev.action === "hold" || ev.action === "suppress") {
            next.push({
              kind: "restraint", key, signal: ev.signal,
              mode: ev.mode ?? "grow", action: ev.action,
              reason: ev.detail.split("—")[1]?.trim() ?? ev.detail,
            });
            return next;
          }
        }
        if (ev.stage === "explain" && ev.nudge && ev.signal) {
          next.push({ kind: "card", key, signal: ev.signal, nudge: ev.nudge, result: null });
          return next;
        }
        if (ev.stage === "act" && ev.signal) {
          const i = next.findIndex((it) => it.kind === "card" && it.signal === ev.signal);
          if (i >= 0) {
            const card = next[i] as Extract<FeedItem, { kind: "card" }>;
            next[i] = {
              ...card,
              result: {
                executed: !!ev.executed, prepared: !!ev.prepared,
                detail: ev.detail, deep_link: ev.deep_link,
              },
            };
          }
          return next;
        }
        next.push({ kind: "log", key, stage: ev.stage, agent: ev.agent, detail: ev.detail, mode: ev.mode });
        return next;
      });
    };
    es.onerror = () => { es.close(); setRunning(false); };
  }, [scripted, onDecisions]);

  return (
    <section className="card flex min-h-[420px] flex-col" aria-label="Live agent reasoning">
      <div className="flex items-center justify-between gap-3 border-b border-border px-4 py-3">
        <div>
          <h2 className="text-sm font-semibold">Live agent reasoning</h2>
          <p className="text-xs text-ink-3">Sentinel → Insight → Orchestrator → Engagement → Action</p>
        </div>
        <button className="btn-primary px-4 py-2 text-sm" onClick={run} disabled={running}>
          {running ? (
            <span className="inline-flex items-center gap-2">
              <Spinner /> Reasoning…
            </span>
          ) : hasRun ? "Run again" : "Run Ariagent"}
        </button>
      </div>

      <div className="flex-1 space-y-2.5 overflow-y-auto p-4">
        {items.length === 0 && !running && (
          <div className="flex h-full min-h-[280px] flex-col items-center justify-center gap-2 text-center">
            <PulseGlyph />
            <p className="max-w-[26ch] text-sm text-ink-3">
              Run the loop to watch five agents sense, reason, decide — and explain every move.
            </p>
          </div>
        )}
        <AnimatePresence initial={false}>
          {items.map((item) =>
            item.kind === "card" ? (
              <ActionCard key={item.key} nudge={item.nudge} result={item.result} />
            ) : item.kind === "restraint" ? (
              <RestraintCard key={item.key} item={item} />
            ) : (
              <motion.div key={item.key}
                initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                transition={{ type: "spring", stiffness: 380, damping: 30 }}
                className="flex items-start gap-2.5 px-1">
                <StageChip stage={item.stage} />
                <div className="min-w-0 text-[13px] leading-relaxed text-ink-2">
                  <span className={`font-semibold ${item.mode ? AGENT_MODE_CLS[item.mode] : "text-ink"}`}>
                    {item.agent}
                  </span>{" "}
                  {item.detail}
                </div>
              </motion.div>
            )
          )}
        </AnimatePresence>
        {running && (
          <div className="flex items-center gap-2 px-1 text-xs text-ink-3">
            <Spinner /> thinking…
          </div>
        )}
      </div>
    </section>
  );
}

/* The signature moment: the Orchestrator holding back. The card deliberately
   arrives, then greys itself out — restraint made visible. */
function RestraintCard({ item }: { item: Extract<FeedItem, { kind: "restraint" }> }) {
  const held = item.action === "hold";
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: [0, 1, 1, 0.6], filter: ["grayscale(0)", "grayscale(0)", "grayscale(1)", "grayscale(1)"] }}
      transition={{ duration: 1.6, times: [0, 0.25, 0.7, 1] }}
      className="card border-dashed !shadow-none">
      <div className="flex items-start gap-3 p-3.5">
        <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-surface-2 text-ink-3">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="h-3.5 w-3.5">
            {held
              ? <path d="M9 5v14M15 5v14" strokeLinecap="round" />
              : <path d="M4 12h16" strokeLinecap="round" />}
          </svg>
        </div>
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-semibold text-ink-2">
              {held ? "Held for later" : "Suppressed"} — {label(item.signal)}
            </span>
            <ModeBadge mode={item.mode} muted />
          </div>
          <p className="mt-0.5 text-[13px] text-ink-3">
            {held ? "Worth surfacing, but not now: " : "Not worth your attention: "}
            {item.reason}. Restraint is a feature.
          </p>
        </div>
      </div>
    </motion.div>
  );
}

function label(signal: string): string {
  return signal.replaceAll("_", " ");
}

function Spinner() {
  return (
    <svg viewBox="0 0 24 24" className="h-3.5 w-3.5 animate-spin" fill="none" aria-hidden>
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeOpacity="0.25" strokeWidth="3" />
      <path d="M21 12a9 9 0 0 0-9-9" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}

function PulseGlyph() {
  return (
    <div className="relative flex h-12 w-12 items-center justify-center">
      <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary/15" />
      <span className="relative flex h-9 w-9 items-center justify-center rounded-full bg-primary-soft">
        <svg viewBox="0 0 24 24" fill="none" stroke="var(--primary)" strokeWidth="2" className="h-4.5 w-4.5">
          <path d="M3 12h4l3-7 4 14 3-7h4" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </span>
    </div>
  );
}
