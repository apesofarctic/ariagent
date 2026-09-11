"use client";
import { useCallback, useSyncExternalStore } from "react";

/* localStorage-backed state without hydration mismatches:
   the server snapshot is the fallback; clients re-read after hydration. */

const listeners = new Set<() => void>();
const subscribe = (cb: () => void) => {
  listeners.add(cb);
  return () => { listeners.delete(cb); };
};
const emit = () => listeners.forEach((l) => l());

export function useLocalValue(key: string, fallback: string): [string, (v: string) => void] {
  const value = useSyncExternalStore(
    subscribe,
    () => localStorage.getItem(key) ?? fallback,
    () => fallback,
  );
  const set = useCallback((v: string) => {
    localStorage.setItem(key, v);
    emit();
  }, [key]);
  return [value, set];
}
