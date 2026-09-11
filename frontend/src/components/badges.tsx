"use client";
import type { Mode } from "@/lib/types";

export const MODE_META: Record<Mode, { label: string; cls: string; dot: string }> = {
  protect: { label: "Protect", cls: "bg-protect-soft text-protect", dot: "bg-protect" },
  grow: { label: "Grow", cls: "bg-grow-soft text-grow", dot: "bg-grow" },
  guide: { label: "Guide", cls: "bg-guide-soft text-guide", dot: "bg-guide" },
};

export function ModeBadge({ mode, muted = false }: { mode: Mode; muted?: boolean }) {
  const m = MODE_META[mode];
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[11px] font-semibold ${
      muted ? "bg-surface-2 text-ink-3" : m.cls
    }`}>
      <span className={`h-1.5 w-1.5 rounded-full ${muted ? "bg-ink-3" : m.dot}`} aria-hidden />
      {m.label}
    </span>
  );
}

const STAGE_LABEL: Record<string, string> = {
  sense: "Sense", reason: "Reason", decide: "Decide", explain: "Explain", act: "Act", done: "Done",
};

export function StageChip({ stage }: { stage: string }) {
  return (
    <span className="inline-flex rounded-md border border-border bg-surface-2 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-ink-2">
      {STAGE_LABEL[stage] ?? stage}
    </span>
  );
}
