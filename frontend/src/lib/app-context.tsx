"use client";
import {
  createContext, useCallback, useContext, useEffect, useState, type ReactNode,
} from "react";
import { api } from "./api";
import type { Status } from "./types";
import { useLocalValue } from "./use-local";

type Theme = "light" | "dark";

type AppState = {
  status: Status | null;
  statusError: string | null;
  refreshStatus: () => Promise<void>;
  theme: Theme;
  setTheme: (t: Theme) => void;
};

const Ctx = createContext<AppState | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<Status | null>(null);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [themeRaw, setThemeRaw] = useLocalValue("ariagent-theme", "light");
  const theme = themeRaw === "dark" ? "dark" : "light";

  const refreshStatus = useCallback(async () => {
    try {
      setStatus(await api.status());
      setStatusError(null);
    } catch (e) {
      setStatusError(e instanceof Error ? e.message : "Backend unreachable");
    }
  }, []);

  useEffect(() => {
    api.status().then(
      (s) => { setStatus(s); setStatusError(null); },
      (e) => setStatusError(e instanceof Error ? e.message : "Backend unreachable"),
    );
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  const setTheme = useCallback((t: Theme) => setThemeRaw(t), [setThemeRaw]);

  return (
    <Ctx.Provider value={{ status, statusError, refreshStatus, theme, setTheme }}>
      {children}
    </Ctx.Provider>
  );
}

export function useApp(): AppState {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useApp outside AppProvider");
  return ctx;
}

export const fmtINR = (n: number, compact = false): string =>
  new Intl.NumberFormat("en-IN", {
    style: "currency", currency: "INR", maximumFractionDigits: 0,
    ...(compact ? { notation: "compact" as const } : {}),
  }).format(n);

export const fmtDate = (iso: string): string =>
  new Date(iso + (iso.length === 10 ? "T00:00:00" : "")).toLocaleDateString("en-IN", {
    day: "numeric", month: "short",
  });
