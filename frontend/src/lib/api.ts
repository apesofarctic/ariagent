import type {
  AuditRow, Consent, Forecast, ImportResult, Inference, Profile, Status, Txn, UploadResult,
} from "./types";

export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, init);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch { /* not json */ }
    throw new Error(detail);
  }
  return res.json();
}

const json = (body: unknown): RequestInit => ({
  method: "POST",
  headers: { "content-type": "application/json" },
  body: JSON.stringify(body),
});

export const api = {
  status: () => req<Status>("/api/status"),
  profile: () => req<Profile>("/api/profile"),
  transactions: () => req<Txn[]>("/api/transactions"),
  forecast: () => req<Forecast>("/api/forecast"),
  inferences: () => req<Inference[]>("/api/inferences"),
  deleteInference: (id: number) => req<{ deleted: string }>(`/api/inferences/${id}`, { method: "DELETE" }),
  audit: () => req<AuditRow[]>("/api/audit"),

  grantConsent: (scopes: Record<string, boolean>) =>
    req<Consent>("/api/consent", json({ scopes, adult: true })),
  revokeConsent: () => req<Consent>("/api/consent", { method: "DELETE" }),

  upload: (file: File, target: "demo" | "real") => {
    const form = new FormData();
    form.append("file", file);
    form.append("target", target);
    return req<UploadResult>("/api/data/upload", { method: "POST", body: form });
  },
  importData: (token: string, mapping: Record<string, string | null>, target: "demo" | "real") =>
    req<ImportResult>("/api/data/import", json({ token, mapping, target })),
  setMode: (mode: "demo" | "real") => req<{ data_mode: string }>("/api/data/mode", json({ mode })),
  resetDemo: () => req<{ ok: boolean }>("/api/data/demo/reset", { method: "POST" }),
  deleteAll: () => req<{ deleted: boolean }>("/api/data", { method: "DELETE" }),

  exportUrl: (format: "json" | "csv") => `${API_URL}/api/export?format=${format}`,
  streamUrl: (scripted: boolean) => `${API_URL}/api/stream${scripted ? "?mode=scripted" : ""}`,
};
