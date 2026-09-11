"use client";
import { useEffect, useId, useMemo, useRef, useState } from "react";
import type { Forecast } from "@/lib/types";
import { fmtINR, fmtDate } from "@/lib/app-context";

const H = 224;
const PAD = { top: 16, right: 12, bottom: 26, left: 56 };

/* Balance line, colored by zone via a userSpace gradient:
   green (safe) above the buffer, amber inside the buffer, red below zero. */
export function CashflowChart({ forecast }: { forecast: Forecast }) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(640);
  const [hover, setHover] = useState<number | null>(null);

  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const ro = new ResizeObserver(([e]) => setWidth(Math.max(320, e.contentRect.width)));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const { points, buffer } = forecast;
  const geom = useMemo(() => {
    const values = points.map((p) => p.balance);
    const lo = Math.min(...values, 0);
    const hi = Math.max(...values, buffer);
    const span = hi - lo || 1;
    const yMin = lo - span * 0.08;
    const yMax = hi + span * 0.08;
    const iw = width - PAD.left - PAD.right;
    const ih = H - PAD.top - PAD.bottom;
    const x = (i: number) => PAD.left + (i / (points.length - 1)) * iw;
    const y = (v: number) => PAD.top + (1 - (v - yMin) / (yMax - yMin)) * ih;
    const line = points.map((p, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(p.balance).toFixed(1)}`).join("");
    const area = `${line}L${x(points.length - 1).toFixed(1)},${y(yMin).toFixed(1)}L${x(0).toFixed(1)},${y(yMin).toFixed(1)}Z`;
    const ticks = niceTicks(yMin, yMax, 4);
    let minIdx = 0;
    values.forEach((v, i) => { if (v < values[minIdx]) minIdx = i; });
    return { x, y, line, area, ticks, yMin, yMax, minIdx };
  }, [points, buffer, width]);

  const gid = `zone-${useId()}`;
  const { x, y, line, area, ticks, minIdx } = geom;
  const minPt = points[geom.minIdx];
  const hoverPt = hover != null ? points[hover] : null;

  const onMove = (e: React.PointerEvent<SVGSVGElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const px = e.clientX - rect.left;
    const iw = width - PAD.left - PAD.right;
    const i = Math.round(((px - PAD.left) / iw) * (points.length - 1));
    setHover(Math.max(0, Math.min(points.length - 1, i)));
  };

  return (
    <div ref={wrapRef} className="relative">
      <svg width={width} height={H} role="img"
        aria-label={`Cashflow forecast for the next ${points.length - 1} days; lowest projected balance ${fmtINR(minPt.balance)} on ${fmtDate(minPt.date)}`}
        onPointerMove={onMove} onPointerLeave={() => setHover(null)}>
        <defs>
          <linearGradient id={gid} x1="0" x2="0" y1="0" y2={H} gradientUnits="userSpaceOnUse">
            <stop offset={y(buffer) / H} stopColor="var(--protect)" />
            <stop offset={y(buffer) / H} stopColor="var(--warn)" />
            <stop offset={y(0) / H} stopColor="var(--warn)" />
            <stop offset={y(0) / H} stopColor="var(--danger)" />
          </linearGradient>
        </defs>

        {ticks.map((t) => (
          <g key={t}>
            <line x1={PAD.left} x2={width - PAD.right} y1={y(t)} y2={y(t)}
              stroke="var(--grid)" strokeWidth="1" />
            <text x={PAD.left - 8} y={y(t) + 3.5} textAnchor="end"
              className="tabular fill-ink-3 text-[10px]">
              {compact(t)}
            </text>
          </g>
        ))}
        {/* zero baseline, slightly stronger */}
        <line x1={PAD.left} x2={width - PAD.right} y1={y(0)} y2={y(0)}
          stroke="var(--border-strong)" strokeWidth="1" />

        <path d={area} fill={`url(#${gid})`} opacity="0.1" />
        <path d={line} fill="none" stroke={`url(#${gid})`} strokeWidth="2"
          strokeLinejoin="round" strokeLinecap="round" />

        {/* direct label on the extreme — the story of the chart */}
        <g>
          <circle cx={x(minIdx)} cy={y(minPt.balance)} r="4.5"
            fill={minPt.balance < 0 ? "var(--danger)" : "var(--warn)"}
            stroke="var(--surface)" strokeWidth="2" />
          <text x={clampX(x(minIdx), width, 90)} y={y(minPt.balance) - 10} textAnchor="middle"
            className="tabular fill-ink text-[11px] font-semibold">
            {`low ${fmtINR(minPt.balance)} · ${fmtDate(minPt.date)}`}
          </text>
        </g>

        {/* x ticks: ~5 dates */}
        {points.filter((_, i) => i % Math.ceil(points.length / 5) === 0).map((p) => (
          <text key={p.date} x={x(points.indexOf(p))} y={H - 8} textAnchor="middle"
            className="fill-ink-3 text-[10px]">
            {fmtDate(p.date)}
          </text>
        ))}

        {hoverPt && hover != null && (
          <g pointerEvents="none">
            <line x1={x(hover)} x2={x(hover)} y1={PAD.top} y2={H - PAD.bottom}
              stroke="var(--border-strong)" strokeWidth="1" />
            <circle cx={x(hover)} cy={y(hoverPt.balance)} r="4.5"
              fill="var(--primary)" stroke="var(--surface)" strokeWidth="2" />
          </g>
        )}
      </svg>

      {hoverPt && hover != null && (
        <div className="pointer-events-none absolute z-10 -translate-x-1/2 rounded-lg border border-border bg-surface px-2.5 py-1.5 text-xs shadow-[var(--shadow-pop)]"
          style={{ left: x(hover), top: Math.max(0, y(hoverPt.balance) - 52) }}>
          <div className="text-ink-3">{fmtDate(hoverPt.date)}</div>
          <div className="tabular font-semibold">{fmtINR(hoverPt.balance)}</div>
        </div>
      )}
    </div>
  );
}

function niceTicks(lo: number, hi: number, n: number): number[] {
  const span = hi - lo;
  const step0 = span / n;
  const mag = 10 ** Math.floor(Math.log10(step0));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => span / s <= n + 1) ?? mag * 10;
  const start = Math.ceil(lo / step) * step;
  const out: number[] = [];
  for (let v = start; v <= hi; v += step) out.push(Math.round(v));
  return out;
}

function compact(v: number): string {
  if (Math.abs(v) >= 1000) return `${(v / 1000).toFixed(Math.abs(v) >= 100000 ? 0 : 0)}k`;
  return String(v);
}

function clampX(px: number, width: number, margin: number): number {
  return Math.max(margin, Math.min(width - margin, px));
}
