"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useApp, fmtDate } from "@/lib/app-context";
import { useLocalValue } from "@/lib/use-local";
import type { Mode } from "@/lib/types";

const MODE_LABEL: Record<Mode, string> = { protect: "Protect", grow: "Grow", guide: "Guide" };

export default function SettingsPage() {
  const { status, refreshStatus, theme, setTheme } = useApp();
  const router = useRouter();
  const [scriptedRaw, setScriptedRaw] = useLocalValue("ariagent-scripted", "false");
  const scripted = scriptedRaw === "true";
  const [busy, setBusy] = useState<string | null>(null);

  const toggleScripted = (v: boolean) => setScriptedRaw(String(v));

  return (
    <div className="mx-auto max-w-2xl space-y-5">
      <div>
        <h1 className="text-xl font-bold tracking-tight">Settings</h1>
        <p className="text-sm text-ink-3">Appearance, consent, engine, and your data rights.</p>
      </div>

      <section className="card p-4 sm:p-5">
        <h2 className="text-sm font-semibold">Appearance</h2>
        <div className="mt-3 flex gap-2">
          {(["light", "dark"] as const).map((t) => (
            <button key={t}
              className={`rounded-[10px] border px-4 py-2 text-sm font-medium capitalize transition-colors ${
                theme === t ? "border-primary bg-primary-soft text-primary" : "border-border text-ink-2 hover:bg-surface-2"
              }`}
              onClick={() => setTheme(t)}>
              {t}
            </button>
          ))}
        </div>
      </section>

      <section className="card p-4 sm:p-5">
        <h2 className="text-sm font-semibold">Consent</h2>
        {status?.consent.granted ? (
          <>
            <p className="mt-1 text-xs text-ink-2">
              Granted {status.consent.granted_at ? fmtDate(status.consent.granted_at) : ""} for:
            </p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {(Object.keys(MODE_LABEL) as Mode[]).map((m) => (
                <span key={m} className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                  status.consent.scopes[m]
                    ? "bg-primary-soft text-primary"
                    : "bg-surface-2 text-ink-3 line-through"
                }`}>
                  {MODE_LABEL[m]}
                </span>
              ))}
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              <button className="btn-ghost px-3 py-1.5 text-xs"
                onClick={() => router.push("/onboarding")}>
                Change scopes
              </button>
              <button className="btn-danger px-3 py-1.5 text-xs" disabled={busy === "revoke"}
                onClick={async () => {
                  if (!confirm("Withdraw consent? Processing stops and you return to onboarding.")) return;
                  setBusy("revoke");
                  await api.revokeConsent();
                  await refreshStatus();
                  router.replace("/onboarding");
                }}>
                Withdraw consent
              </button>
            </div>
            <p className="mt-2 text-[11px] text-ink-3">
              Withdrawal is as easy as giving it (DPDP §6(4)) — it stops processing going forward.
            </p>
          </>
        ) : (
          <p className="mt-1 text-xs text-ink-3">No consent on file.</p>
        )}
      </section>

      <section className="card p-4 sm:p-5">
        <h2 className="text-sm font-semibold">Engine</h2>
        <div className="mt-2 space-y-2 text-sm">
          <div className="flex items-center justify-between rounded-lg border border-border px-3 py-2">
            <span className="text-ink-2">Language model</span>
            <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${
              status?.use_llm ? "bg-primary-soft text-primary" : "bg-surface-2 text-ink-2"
            }`}>
              {status?.use_llm ? `${status.llm_model} · local` : "off — deterministic text"}
            </span>
          </div>
          <div className="flex items-center justify-between rounded-lg border border-border px-3 py-2">
            <span className="text-ink-2">Data mode</span>
            <span className="rounded-full bg-surface-2 px-2.5 py-0.5 text-xs font-semibold text-ink-2">
              {status?.data_mode === "real" ? "REAL — analyse-only" : "DEMO — sandbox"}
            </span>
          </div>
          <label className="flex items-center justify-between rounded-lg border border-border px-3 py-2">
            <span>
              <span className="text-ink-2">Scripted runs</span>
              <span className="block text-[11px] text-ink-3">
                Skip the model entirely — fully deterministic demo, immune to model hiccups.
              </span>
            </span>
            <input type="checkbox" className="h-4 w-4 accent-[#1d4ed8]" checked={scripted}
              onChange={(e) => toggleScripted(e.target.checked)} />
          </label>
        </div>
        <p className="mt-2 text-[11px] text-ink-3">
          Money math (forecasts, suppression) is always deterministic Python — the model only
          writes language and classifies merchants, locally.
        </p>
      </section>

      <section className="card p-4 sm:p-5">
        <h2 className="text-sm font-semibold">Your data</h2>
        <p className="mt-1 text-xs text-ink-2">
          Everything Ariagent holds — transactions, inferences, decisions, audit log.
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          <a className="btn-ghost px-3 py-1.5 text-xs" href={api.exportUrl("json")}>Export my data (JSON)</a>
          <a className="btn-ghost px-3 py-1.5 text-xs" href={api.exportUrl("csv")}>Export my data (CSV)</a>
          <button className="btn-danger px-3 py-1.5 text-xs" disabled={busy === "delete"}
            onClick={async () => {
              if (!confirm("Delete everything Ariagent holds about you? This cannot be undone.")) return;
              setBusy("delete");
              await api.deleteAll();
              await refreshStatus();
              router.replace("/onboarding");
            }}>
            Delete my data
          </button>
        </div>
        <p className="mt-2 text-[11px] text-ink-3">
          Access, portability and erasure are DPDP §11–12 rights, not features.
        </p>
      </section>
    </div>
  );
}
