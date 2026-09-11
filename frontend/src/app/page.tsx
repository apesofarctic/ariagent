"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { Forecast, Profile, Txn } from "@/lib/types";
import { useApp, fmtINR } from "@/lib/app-context";
import { useLocalValue } from "@/lib/use-local";
import { AgentStream, type Decisions } from "@/components/agent-stream";
import { CashflowChart } from "@/components/cashflow-chart";
import { Timeline } from "@/components/timeline";

export default function Dashboard() {
  const { status } = useApp();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [txns, setTxns] = useState<Txn[]>([]);
  const [forecast, setForecast] = useState<Forecast | null>(null);
  const [decisions, setDecisions] = useState<Decisions>({});
  const [scriptedRaw] = useLocalValue("ariagent-scripted", "false");
  const scripted = scriptedRaw === "true";

  useEffect(() => {
    Promise.all([api.profile(), api.transactions(), api.forecast()]).then(
      ([p, t, f]) => { setProfile(p); setTxns(t); setForecast(f); },
      () => { /* banner in shell covers backend-down */ },
    );
  }, [status?.data_mode]);

  const nextDebit = profile?.profile.recurring.find((r) => r.type !== "salary");

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold tracking-tight">
            {profile ? `Hello, ${profile.profile.name}` : "Hello"}
          </h1>
          <p className="text-sm text-ink-3">
            {status?.data_mode === "real"
              ? "Analysing your imported statement — on-device, analyse-only."
              : "Watching the demo scenario — 60 days of synthetic activity."}
          </p>
        </div>
        <Link href="/data" className="btn-ghost px-3 py-1.5 text-sm">Manage data</Link>
      </div>

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-5">
        <div className="space-y-5 xl:col-span-3">
          {/* Financial snapshot */}
          <section className="card p-4 sm:p-5" aria-label="Financial snapshot">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <Stat label="Current balance"
                value={profile ? fmtINR(profile.balance) : "—"}
                tone={profile && profile.balance < (forecast?.buffer ?? 2000) ? "warn" : "protect"} />
              <Stat label={nextDebit ? `Upcoming ${nextDebit.type}` : "Upcoming debits"}
                value={nextDebit ? fmtINR(nextDebit.amount) : "—"}
                sub={nextDebit ? `on the ${ordinal(nextDebit.day_of_month)}` : undefined} />
              <Stat label="Forecast low"
                value={forecast ? fmtINR(forecast.min_balance) : "—"}
                tone={forecast && forecast.min_balance < 0 ? "danger" : forecast && forecast.min_balance < forecast.buffer ? "warn" : "protect"}
                sub={forecast?.overdraft_risk ? "overdraft risk ahead" : "looking safe"} />
            </div>
            <div className="mt-4 border-t border-border pt-4">
              <h2 className="mb-1 text-sm font-semibold">Cashflow forecast · next {forecast ? forecast.points.length - 1 : 35} days</h2>
              <p className="mb-2 text-xs text-ink-3">
                Deterministic projection from your recurring debits and average daily spend.
              </p>
              {forecast ? <CashflowChart forecast={forecast} /> :
                <div className="h-[224px] animate-pulse rounded-xl bg-surface-2" />}
            </div>
          </section>

          {/* 60-day timeline */}
          <section className="card p-4 sm:p-5" aria-label="Activity timeline">
            <h2 className="text-sm font-semibold">
              {txns.length > 0 ? `${spanDays(txns)}-day timeline` : "Timeline"}
            </h2>
            <p className="mb-2 text-xs text-ink-3">
              The events Ariagent is watching, colored by mode. Run the loop to see what it holds back.
            </p>
            {txns.length > 0 ? <Timeline txns={txns} decisions={decisions} /> :
              <div className="h-[172px] animate-pulse rounded-xl bg-surface-2" />}
          </section>
        </div>

        <div className="xl:col-span-2">
          <div className="xl:sticky xl:top-20">
            <AgentStream scripted={scripted} onDecisions={setDecisions} />
          </div>
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value, sub, tone }: {
  label: string; value: string; sub?: string; tone?: "protect" | "warn" | "danger";
}) {
  const toneCls = tone === "danger" ? "text-danger" : tone === "warn" ? "text-warn" : "text-ink";
  return (
    <div>
      <div className="text-xs font-medium text-ink-3">{label}</div>
      <div className={`tabular mt-0.5 text-xl font-bold ${toneCls}`}>{value}</div>
      {sub && <div className="text-xs text-ink-3">{sub}</div>}
    </div>
  );
}

function ordinal(n: number): string {
  const s = ["th", "st", "nd", "rd"], v = n % 100;
  return n + (s[(v - 20) % 10] || s[v] || s[0]);
}

function spanDays(txns: Txn[]): number {
  const ds = txns.map((t) => +new Date(t.date));
  return Math.round((Math.max(...ds) - Math.min(...ds)) / 86400000);
}
