"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import type { Mode, Txn } from "@/lib/types";
import type { Decisions } from "./agent-stream";
import { fmtINR, fmtDate } from "@/lib/app-context";

type Ev = { date: string; label: string; mode: Mode; signal?: string };

const LANES: Mode[] = ["protect", "grow", "guide"];
const LANE_COLOR: Record<Mode, string> = {
  protect: "var(--protect)", grow: "var(--grow)", guide: "var(--guide)",
};
const H = 172;
const PAD = { top: 14, right: 16, bottom: 26, left: 64 };

function deriveEvents(txns: Txn[]): Ev[] {
  const out: Ev[] = [];
  for (const t of txns) {
    const amt = fmtINR(Math.abs(t.amount));
    if (t.category === "salary") out.push({ date: t.date, label: `Salary ${amt}`, mode: "grow", signal: "salary_hike" });
    else if (t.category === "rent") out.push({ date: t.date, label: `Rent ${amt}`, mode: "protect", signal: "overdraft_forecast" });
    else if (t.category === "subscription") out.push({ date: t.date, label: `${t.merchant} ${amt}`, mode: "protect", signal: "duplicate_subscription" });
    else if (t.category === "health" || /firstcry|motherhood|clinic|pharmac/i.test(t.merchant))
      out.push({ date: t.date, label: `${t.merchant} ${amt}`, mode: "guide", signal: "life_event_baby" });
  }
  return out;
}

export function Timeline({ txns, decisions }: { txns: Txn[]; decisions: Decisions }) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(640);
  const [hover, setHover] = useState<{ ev: Ev; px: number; py: number } | null>(null);

  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const ro = new ResizeObserver(([e]) => setWidth(Math.max(320, e.contentRect.width)));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const events = useMemo(() => deriveEvents(txns), [txns]);
  const { x, laneY, months, suppressed } = useMemo(() => {
    const dates = txns.map((t) => +new Date(t.date));
    const lo = Math.min(...dates), hi = Math.max(...dates);
    const iw = width - PAD.left - PAD.right;
    const x = (d: string) => PAD.left + ((+new Date(d) - lo) / (hi - lo || 1)) * iw;
    const laneH = (H - PAD.top - PAD.bottom) / LANES.length;
    const laneY = (m: Mode) => PAD.top + LANES.indexOf(m) * laneH + laneH / 2;
    const months: { label: string; px: number }[] = [];
    const d = new Date(lo);
    d.setDate(1);
    while (+d <= hi) {
      if (+d >= lo) months.push({
        label: d.toLocaleDateString("en-IN", { month: "short" }), px: x(d.toISOString().slice(0, 10)),
      });
      d.setMonth(d.getMonth() + 1);
    }
    // the suppressed round-up nudge lives at "today" (last txn date) on the Grow lane
    const suppressed = decisions["roundup_potential"] === "suppress"
      ? { date: new Date(hi).toISOString().slice(0, 10) } : null;
    return { x, laneY, months, suppressed };
  }, [txns, width, decisions]);

  const dimmed = (ev: Ev) =>
    ev.signal ? decisions[ev.signal] === "suppress" || decisions[ev.signal] === "hold" : false;

  return (
    <div ref={wrapRef} className="relative">
      <svg width={width} height={H} role="img" aria-label="60-day activity timeline by mode">
        {LANES.map((m) => (
          <g key={m}>
            <text x={PAD.left - 10} y={laneY(m) + 3.5} textAnchor="end"
              className="text-[11px] font-semibold" fill={LANE_COLOR[m]}>
              {m[0].toUpperCase() + m.slice(1)}
            </text>
            <line x1={PAD.left} x2={width - PAD.right} y1={laneY(m)} y2={laneY(m)}
              stroke="var(--grid)" strokeWidth="1" />
          </g>
        ))}
        {months.map((mo) => (
          <text key={mo.label + mo.px} x={mo.px} y={H - 8} className="fill-ink-3 text-[10px]">
            {mo.label}
          </text>
        ))}

        {events.map((ev, i) => {
          const dim = dimmed(ev);
          return (
            <circle key={i} cx={x(ev.date)} cy={laneY(ev.mode)} r="5"
              fill={dim ? "var(--ink-3)" : LANE_COLOR[ev.mode]}
              opacity={dim ? 0.45 : 1}
              stroke="var(--surface)" strokeWidth="2"
              className="cursor-pointer"
              onPointerEnter={() => setHover({ ev, px: x(ev.date), py: laneY(ev.mode) })}
              onPointerLeave={() => setHover(null)}
            />
          );
        })}

        {suppressed && (
          <g className="cursor-pointer"
            onPointerEnter={() => setHover({
              ev: { date: suppressed.date, label: "Round-up nudge — suppressed by the Orchestrator", mode: "grow" },
              px: x(suppressed.date), py: laneY("grow"),
            })}
            onPointerLeave={() => setHover(null)}>
            <circle cx={x(suppressed.date)} cy={laneY("grow")} r="7" fill="none"
              stroke="var(--ink-3)" strokeWidth="1.5" strokeDasharray="2.5 2.5" opacity="0.7" />
            <circle cx={x(suppressed.date)} cy={laneY("grow")} r="3.5" fill="var(--ink-3)" opacity="0.55" />
          </g>
        )}
      </svg>

      {hover && (
        <div className="pointer-events-none absolute z-10 -translate-x-1/2 rounded-lg border border-border bg-surface px-2.5 py-1.5 text-xs shadow-[var(--shadow-pop)]"
          style={{ left: Math.max(70, Math.min(width - 90, hover.px)), top: Math.max(0, hover.py - 52) }}>
          <div className="text-ink-3">{fmtDate(hover.ev.date)}</div>
          <div className="font-medium">{hover.ev.label}</div>
        </div>
      )}

      <div className="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1 px-1 text-[11px] text-ink-2">
        {LANES.map((m) => (
          <span key={m} className="inline-flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full" style={{ background: LANE_COLOR[m] }} aria-hidden />
            {m === "protect" ? "Protect — threats" : m === "grow" ? "Grow — opportunities" : "Guide — life events"}
          </span>
        ))}
        <span className="inline-flex items-center gap-1.5 text-ink-3">
          <span className="h-2 w-2 rounded-full border border-dashed border-ink-3" aria-hidden />
          suppressed / held
        </span>
      </div>
    </div>
  );
}
