"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useApp, fmtDate } from "@/lib/app-context";
import { UploadWizard } from "@/components/upload-wizard";

export default function DataPage() {
  const { status, refreshStatus } = useApp();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const mode = status?.data_mode ?? "demo";
  const hasReal = (status?.real_data.count ?? 0) > 0;

  const switchMode = async (m: "demo" | "real") => {
    setError(null);
    try {
      await api.setMode(m);
      await refreshStatus();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Couldn't switch");
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-5">
      <div>
        <h1 className="text-xl font-bold tracking-tight">Data</h1>
        <p className="text-sm text-ink-3">
          You bring the data, Ariagent does the thinking — read-only, on-device, and you stay
          in control of every action.
        </p>
      </div>

      {/* mode switch */}
      <div className="grid grid-cols-2 gap-3" role="tablist" aria-label="Data mode">
        <button role="tab" aria-selected={mode === "demo"}
          onClick={() => switchMode("demo")}
          className={`card p-4 text-left transition-colors ${
            mode === "demo" ? "!border-ink-3 ring-1 ring-ink-3/30" : "opacity-75 hover:opacity-100"
          }`}>
          <div className="text-sm font-bold">Demo data</div>
          <p className="mt-1 text-xs leading-relaxed text-ink-2">
            Synthetic sandbox. Not real; nothing is stored or acted on. Zero risk — test how the
            agents think.
          </p>
        </button>
        <button role="tab" aria-selected={mode === "real"}
          onClick={() => hasReal && switchMode("real")}
          className={`card p-4 text-left transition-colors ${
            mode === "real" ? "!border-primary ring-1 ring-primary/30"
              : hasReal ? "opacity-75 hover:opacity-100" : "cursor-not-allowed opacity-50"
          }`}>
          <div className="text-sm font-bold text-primary">Real data</div>
          <p className="mt-1 text-xs leading-relaxed text-ink-2">
            {hasReal
              ? `${status?.real_data.count} imported transactions (${status?.real_data.source}). Analyse-only — actions are prepared, never executed.`
              : "Import your own bank statement below to unlock."}
          </p>
        </button>
      </div>
      {error && <p className="text-sm text-danger">{error}</p>}

      {mode === "demo" ? (
        <>
          <section className="card p-4 sm:p-5">
            <h2 className="text-sm font-semibold">Demo workspace</h2>
            <p className="mt-1 text-xs leading-relaxed text-ink-2">
              Currently loaded: <strong>{status?.demo_source === "synthetic"
                ? "the built-in 60-day “Priya” scenario"
                : `your test file (${status?.demo_source.replace("csv:", "")})`}</strong>.
              Upload any CSV of test transactions to see how the model reacts — it is treated as
              fake data.
            </p>
            <div className="mt-4">
              <UploadWizard target="demo" />
            </div>
            <button className="btn-ghost mt-3 px-3 py-1.5 text-xs"
              onClick={async () => { await api.resetDemo(); await refreshStatus(); }}>
              Reset to built-in demo scenario
            </button>
          </section>

          <section className="card p-4 sm:p-5">
            <h2 className="text-sm font-semibold">Run it on your actual money</h2>
            <p className="mt-1 text-xs leading-relaxed text-ink-2">
              The real-data path is consent-gated and analyse-only: upload a statement you exported
              from your bank; Ariagent normalises and categorises it on-device and the agents
              analyse your real numbers. Nothing executes — action cards become prepared
              instructions you complete in your own bank app.
            </p>
            {status?.consent.granted ? (
              <div className="mt-4">
                <div className="mb-2 inline-flex items-center gap-2 rounded-full bg-primary-soft px-3 py-1 text-xs font-semibold text-primary">
                  Consented {status.consent.granted_at ? fmtDate(status.consent.granted_at) : ""} · processed on-device
                </div>
                <UploadWizard target="real" onDone={() => router.push("/")} />
              </div>
            ) : (
              <button className="btn-primary mt-3 px-4 py-2 text-sm"
                onClick={() => router.push("/onboarding")}>
                Give consent to continue
              </button>
            )}
          </section>
        </>
      ) : (
        <section className="card p-4 sm:p-5">
          <h2 className="text-sm font-semibold">Real data workspace</h2>
          <p className="mt-1 text-xs leading-relaxed text-ink-2">
            {status?.real_data.count} transactions from <strong>{status?.real_data.source}</strong>{" "}
            ({status?.real_data.first} → {status?.real_data.last}), processed on-device. Actions are
            prepared for you to complete in your bank app — Ariagent never executes.
          </p>
          <div className="mt-4">
            <UploadWizard target="real" onDone={() => router.push("/")} />
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <button className="btn-danger px-3 py-1.5 text-xs"
              onClick={async () => {
                if (!confirm("Revoke consent and delete all imported data?")) return;
                await api.revokeConsent();
                await api.deleteAll();
                await refreshStatus();
                router.replace("/onboarding");
              }}>
              Revoke &amp; delete
            </button>
          </div>
        </section>
      )}

      {/* Account Aggregator stub */}
      <section className="card p-4 opacity-80 sm:p-5">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold">Connect via Account Aggregator</h2>
          <span className="rounded-full bg-surface-2 px-2.5 py-0.5 text-[11px] font-semibold text-ink-3">
            Coming soon
          </span>
        </div>
        <p className="mt-1 text-xs leading-relaxed text-ink-2">
          The RBI-licensed rail for programmatic access — consent-artefact based, end-to-end
          encrypted, revocable. This is what production uses instead of uploads.
        </p>
        <div className="mt-3 grid grid-cols-2 gap-2 text-xs sm:grid-cols-4">
          {[["FI types", "Deposit accounts"], ["Data range", "Last 6 months"],
            ["Frequency", "Daily refresh"], ["Consent expiry", "90 days"]].map(([k, v]) => (
            <div key={k} className="rounded-lg border border-border bg-surface-2 px-2.5 py-2">
              <div className="text-[10px] font-semibold uppercase tracking-wide text-ink-3">{k}</div>
              <div className="mt-0.5 font-medium text-ink-2">{v}</div>
            </div>
          ))}
        </div>
        <button className="btn-ghost mt-3 cursor-not-allowed px-3 py-1.5 text-xs" disabled>
          Request consent artefact
        </button>
      </section>

      <p className="text-xs leading-relaxed text-ink-3">
        Ariagent never asks for net-banking credentials or OTPs, and never stores full card or
        account numbers. Real data enters only when you bring it.
      </p>
    </div>
  );
}
