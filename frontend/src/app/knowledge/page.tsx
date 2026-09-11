"use client";
import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { api } from "@/lib/api";
import type { Inference } from "@/lib/types";
import { ModeBadge } from "@/components/badges";
import { fmtDate } from "@/lib/app-context";

export default function KnowledgePage() {
  const [items, setItems] = useState<Inference[] | null>(null);

  useEffect(() => {
    api.inferences().then(setItems, () => setItems([]));
  }, []);

  const remove = async (id: number) => {
    await api.deleteInference(id);
    setItems((xs) => xs?.filter((x) => x.id !== id) ?? null);
  };

  return (
    <div className="mx-auto max-w-3xl space-y-5">
      <div>
        <h1 className="text-xl font-bold tracking-tight">What Ariagent knows about me</h1>
        <p className="text-sm text-ink-3">
          Every inference, in plain language, with its evidence. If one is wrong, delete it —
          it will not be drawn again. (Your DPDP right to correction.)
        </p>
      </div>

      {items === null ? (
        <div className="h-40 animate-pulse rounded-2xl bg-surface-2" />
      ) : items.length === 0 ? (
        <div className="card p-8 text-center text-sm text-ink-3">
          Nothing yet. Run the agent loop on the dashboard — every inference it draws will
          appear here.
        </div>
      ) : (
        <AnimatePresence>
          {items.map((inf) => (
            <motion.section key={inf.id} layout exit={{ opacity: 0, height: 0, marginBottom: 0 }}
              className="card mb-3 p-4 sm:p-5">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="flex items-center gap-2.5">
                  <ModeBadge mode={inf.mode} />
                  <h2 className="text-[15px] font-semibold">{inf.title}</h2>
                </div>
                <span className="text-xs text-ink-3">
                  {fmtDate(inf.ts)} · confidence {(inf.confidence * 100).toFixed(0)}%
                </span>
              </div>
              <p className="mt-2 text-sm leading-relaxed text-ink-2">{inf.statement}</p>
              <div className="mt-3 rounded-xl bg-surface-2 p-3">
                <div className="text-[11px] font-semibold uppercase tracking-wide text-ink-3">Evidence</div>
                <ul className="mt-1.5 space-y-1">
                  {inf.evidence.map((e, i) => (
                    <li key={i} className="flex gap-2 text-[13px] leading-relaxed text-ink-2">
                      <span className="mt-[7px] h-1 w-1 shrink-0 rounded-full bg-ink-3" aria-hidden />
                      {e}
                    </li>
                  ))}
                </ul>
              </div>
              <div className="mt-3 flex justify-end">
                <button className="btn-danger px-3 py-1.5 text-xs" onClick={() => remove(inf.id)}>
                  This is wrong — delete it
                </button>
              </div>
            </motion.section>
          ))}
        </AnimatePresence>
      )}
    </div>
  );
}
