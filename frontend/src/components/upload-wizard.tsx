"use client";
import { useRef, useState } from "react";
import { motion } from "framer-motion";
import { api } from "@/lib/api";
import type { ImportResult, UploadResult } from "@/lib/types";
import { useApp } from "@/lib/app-context";

const FIELDS = [
  { key: "date", label: "Date", required: true },
  { key: "merchant", label: "Merchant / narration", required: true },
  { key: "amount", label: "Amount (signed)", required: false },
  { key: "debit", label: "Debit / withdrawal", required: false },
  { key: "credit", label: "Credit / deposit", required: false },
  { key: "category", label: "Category (optional)", required: false },
  { key: "balance", label: "Balance (optional)", required: false },
] as const;

export function UploadWizard({ target, onDone }: {
  target: "demo" | "real";
  onDone?: (r: ImportResult) => void;
}) {
  const { refreshStatus } = useApp();
  const [upload, setUpload] = useState<UploadResult | null>(null);
  const [mapping, setMapping] = useState<Record<string, string | null>>({});
  const [result, setResult] = useState<ImportResult | null>(null);
  const [busy, setBusy] = useState<"upload" | "import" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const pick = async (file: File) => {
    setBusy("upload"); setError(null); setResult(null);
    try {
      const r = await api.upload(file, target);
      setUpload(r);
      setMapping(r.mapping);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setBusy(null);
    }
  };

  const mappingOk =
    mapping.date && mapping.merchant && (mapping.amount || (mapping.debit && mapping.credit));

  const doImport = async () => {
    if (!upload) return;
    setBusy("import"); setError(null);
    try {
      const r = await api.importData(upload.token, mapping, target);
      setResult(r);
      setUpload(null);
      await refreshStatus();
      onDone?.(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Import failed");
    } finally {
      setBusy(null);
    }
  };

  return (
    <div>
      {/* Step 1 — choose a file */}
      {!upload && !result && (
        <button
          className="flex w-full flex-col items-center gap-2 rounded-2xl border-2 border-dashed border-border-strong bg-surface-2 px-4 py-8 text-center transition-colors hover:border-primary"
          onClick={() => fileRef.current?.click()}
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            const f = e.dataTransfer.files?.[0];
            if (f) pick(f);
          }}>
          <svg viewBox="0 0 24 24" fill="none" stroke="var(--primary)" strokeWidth="1.8" className="h-8 w-8">
            <path d="M12 16V4m0 0 4 4m-4-4L8 8" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M4 15v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3" strokeLinecap="round" />
          </svg>
          <span className="text-sm font-semibold">
            {busy === "upload" ? "Parsing…" : "Drop a statement here, or click to choose"}
          </span>
          <span className="text-xs text-ink-3">CSV · Excel (.xlsx) · PDF — exported from your bank</span>
        </button>
      )}
      <input ref={fileRef} type="file" accept=".csv,.txt,.xlsx,.xls,.pdf" className="hidden"
        onChange={(e) => { const f = e.target.files?.[0]; if (f) pick(f); e.target.value = ""; }} />

      {/* Step 2 — confirm the column mapping */}
      {upload && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
          <div className="mb-3 flex items-center justify-between">
            <div>
              <div className="text-sm font-semibold">{upload.filename}</div>
              <div className="text-xs text-ink-3">
                {upload.total_rows} rows found — confirm which column is which, then import.
              </div>
            </div>
            <button className="btn-ghost px-2.5 py-1 text-xs" onClick={() => setUpload(null)}>
              Choose another file
            </button>
          </div>

          <div className="mb-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
            {FIELDS.map((f) => (
              <label key={f.key} className="flex items-center justify-between gap-2 rounded-lg border border-border bg-surface px-3 py-2 text-sm">
                <span className={f.required ? "font-medium" : "text-ink-2"}>
                  {f.label}{f.required && <span className="text-danger"> *</span>}
                </span>
                <select
                  className="max-w-[46%] rounded-md border border-border bg-surface-2 px-2 py-1 text-xs"
                  value={mapping[f.key] ?? ""}
                  onChange={(e) => setMapping((m) => ({ ...m, [f.key]: e.target.value || null }))}>
                  <option value="">—</option>
                  {upload.columns.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
              </label>
            ))}
          </div>
          {!mappingOk && (
            <p className="mb-3 text-xs text-warn">
              Map Date, Merchant, and either a signed Amount column or both Debit and Credit.
            </p>
          )}

          <div className="overflow-x-auto rounded-xl border border-border">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-border bg-surface-2">
                  {upload.columns.map((c) => (
                    <th key={c} className="whitespace-nowrap px-2.5 py-2 font-semibold">
                      {c}
                      {Object.entries(mapping).find(([, v]) => v === c)?.[0] && (
                        <span className="ml-1 rounded bg-primary-soft px-1 py-0.5 text-[10px] font-semibold text-primary">
                          {Object.entries(mapping).find(([, v]) => v === c)?.[0]}
                        </span>
                      )}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {upload.preview.slice(0, 6).map((row, i) => (
                  <tr key={i} className="border-b border-border last:border-0">
                    {row.map((cell, j) => (
                      <td key={j} className="tabular whitespace-nowrap px-2.5 py-1.5 text-ink-2">{cell}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <button className="btn-primary mt-4 w-full py-2.5 text-sm" disabled={!mappingOk || busy === "import"}
            onClick={doImport}>
            {busy === "import" ? "Importing & categorising…" :
              target === "real" ? "Import my statement (analyse-only)" : "Import as test data"}
          </button>
        </motion.div>
      )}

      {/* Step 3 — result */}
      {result && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
          className="rounded-xl border border-protect/30 bg-protect-soft p-4">
          <div className="text-sm font-semibold text-protect">
            Imported {result.imported} transactions ({result.date_range[0]} → {result.date_range[1]})
          </div>
          <p className="mt-1 text-xs leading-relaxed text-ink-2">
            Categorised {result.categorizer.merchants} merchants — {result.categorizer.by_rules} by
            rules, {result.categorizer.by_llm} by the local model, {result.categorizer.uncategorized} left
            as “other”.{result.skipped > 0 && ` Skipped ${result.skipped} unreadable rows.`}
          </p>
          <button className="btn-ghost mt-3 px-3 py-1.5 text-xs" onClick={() => setResult(null)}>
            Import another file
          </button>
        </motion.div>
      )}

      {error && <p className="mt-3 text-sm text-danger">{error}</p>}
    </div>
  );
}
