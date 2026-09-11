"use client";
import { useApp } from "@/lib/app-context";

export function ThemeToggle() {
  const { theme, setTheme } = useApp();
  const dark = theme === "dark";
  return (
    <button
      aria-label={dark ? "Switch to light theme" : "Switch to dark theme"}
      className="btn-ghost flex h-8 w-8 items-center justify-center !rounded-full"
      onClick={() => setTheme(dark ? "light" : "dark")}>
      {dark ? (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-4 w-4">
          <circle cx="12" cy="12" r="4" />
          <path d="M12 2.5v2M12 19.5v2M21.5 12h-2M4.5 12h-2M18.4 5.6 17 7M7 17l-1.4 1.4M18.4 18.4 17 17M7 7 5.6 5.6" strokeLinecap="round" />
        </svg>
      ) : (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-4 w-4">
          <path d="M20 14.5A8 8 0 0 1 9.5 4 8 8 0 1 0 20 14.5Z" strokeLinejoin="round" />
        </svg>
      )}
    </button>
  );
}
