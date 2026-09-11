"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { AuditRow } from "@/lib/types";

const STATUS_CLS: Record<AuditRow["status"], string> = {
  executed: "bg-protect-soft text-protect",
  prepared: "bg-primary-soft text-primary",
  held: "bg-surface-2 text-ink-2",
  suppressed: "bg-surface-2 text-ink-3",
  blocked: "bg-danger-soft text-danger",
  info: "bg-surface-2 text-ink-2",
};

export default function AuditPage() {
  const [rows, setRows] = useState<AuditRow[] | null>(null);

  useEffect(() => {
    api.audit().then(setRows).catch(() => setRows([]));
  }, []);

  return (
    <div className="mx-auto max-w-4xl space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold tracking-tight">Audit log</h1>
          <p className="text-sm text-ink-3">
            Every decision and action — who, what, when, why, and whether it can be undone.
          </p>
        </div>
        <div className="flex gap-2">
          <a className="btn-ghost px-3 py-1.5 text-xs" href={api.exportUrl("json")}>Export JSON</a>
          <a className="btn-ghost px-3 py-1.5 text-xs" href={api.exportUrl("csv")}>Export CSV</a>
        </div>
      </div>

      {rows === null ? (
        <div className="h-40 animate-pulse rounded-2xl bg-surface-2" />
      ) : rows.length === 0 ? (
        <div className="card p-8 text-center text-sm text-ink-3">
          Nothing logged yet — run the agent loop and come back.
        </div>
      ) : (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-border bg-surface-2 text-xs uppercase tracking-wide text-ink-3">
                  <th className="px-4 py-2.5 font-semibold">When</th>
                  <th className="px-4 py-2.5 font-semibold">Actor</th>
                  <th className="px-4 py-2.5 font-semibold">What</th>
                  <th className="px-4 py-2.5 font-semibold">Why</th>
                  <th className="px-4 py-2.5 font-semibold">Status</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.id} className="border-b border-border align-top last:border-0">
                    <td className="tabular whitespace-nowrap px-4 py-3 text-xs text-ink-3">
                      {new Date(r.ts).toLocaleString("en-IN", {
                        day: "numeric", month: "short", hour: "2-digit", minute: "2-digit",
                      })}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-xs font-semibold">{r.actor}</td>
                    <td className="max-w-[26ch] px-4 py-3 text-[13px] leading-snug text-ink-2">
                      <div className="font-medium text-ink">{r.action.replaceAll("_", " ")}</div>
                      {r.detail}
                    </td>
                    <td className="max-w-[26ch] px-4 py-3 text-[13px] leading-snug text-ink-2">{r.why}</td>
                    <td className="whitespace-nowrap px-4 py-3">
                      <span className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${STATUS_CLS[r.status]}`}>
                        {r.status}
                      </span>
                      {r.reversible && r.status !== "info" && (
                        <span className="ml-1.5 text-[11px] text-protect">reversible</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
