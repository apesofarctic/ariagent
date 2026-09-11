"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";
import { useApp, fmtDate } from "@/lib/app-context";
import { api } from "@/lib/api";
import { ThemeToggle } from "./theme-toggle";

const NAV = [
  { href: "/", label: "Dashboard", icon: HomeIcon },
  { href: "/data", label: "Data", icon: DataIcon },
  { href: "/knowledge", label: "What Ariagent knows", icon: EyeIcon },
  { href: "/audit", label: "Audit log", icon: ScrollIcon },
  { href: "/settings", label: "Settings", icon: GearIcon },
];

export function Shell({ children }: { children: ReactNode }) {
  const { status, statusError, refreshStatus } = useApp();
  const pathname = usePathname();
  const router = useRouter();

  const consented = status?.consent.granted ?? null;
  const onboarding = pathname === "/onboarding";

  // Consent gate: nothing flows before the consent screen passes (DPDP).
  useEffect(() => {
    if (consented === false && !onboarding) router.replace("/onboarding");
  }, [consented, onboarding, router]);

  if (onboarding) return <main className="min-h-screen">{children}</main>;

  return (
    <div className="min-h-screen lg:pl-60">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-60 flex-col border-r border-border bg-surface lg:flex">
        <Link href="/" className="flex items-center gap-2.5 px-6 pt-6 pb-5">
          <Logo />
          <span className="text-[17px] font-bold tracking-tight">Ariagent</span>
        </Link>
        <nav className="flex flex-1 flex-col gap-1 px-3">
          {NAV.map(({ href, label, icon: Icon }) => {
            const active = pathname === href;
            return (
              <Link key={href} href={href}
                className={`flex items-center gap-3 rounded-[10px] px-3 py-2 text-sm transition-colors ${
                  active
                    ? "bg-primary-soft font-semibold text-primary"
                    : "font-medium text-ink-2 hover:bg-surface-2 hover:text-ink"
                }`}>
                <Icon className="h-[18px] w-[18px]" />
                {label}
              </Link>
            );
          })}
        </nav>
        <div className="px-6 py-5 text-xs leading-5 text-ink-3">
          Read-only · on-device analysis.<br />You approve every action.
        </div>
      </aside>

      <div className="flex min-h-screen flex-col">
        <header className="sticky top-0 z-20 border-b border-border bg-surface/90 backdrop-blur">
          <div className="flex items-center gap-3 px-4 py-2.5 sm:px-6">
            <Link href="/" className="flex items-center gap-2 lg:hidden">
              <Logo />
              <span className="font-bold tracking-tight">Ariagent</span>
            </Link>
            <div className="flex-1" />
            {status && <DataModeBanner />}
            <ThemeToggle />
          </div>
          <nav className="flex gap-1 overflow-x-auto px-3 pb-2 lg:hidden">
            {NAV.map(({ href, label }) => (
              <Link key={href} href={href}
                className={`whitespace-nowrap rounded-full px-3 py-1 text-xs font-medium ${
                  pathname === href ? "bg-primary-soft text-primary" : "text-ink-2"
                }`}>
                {label}
              </Link>
            ))}
          </nav>
        </header>

        {statusError && (
          <div className="mx-4 mt-4 rounded-xl border border-warn/40 bg-warn-soft px-4 py-3 text-sm text-ink sm:mx-6">
            <span className="font-semibold">Backend unreachable</span> — start it with{" "}
            <code className="rounded bg-surface px-1.5 py-0.5 text-xs">uvicorn app.main:app</code> in{" "}
            <code className="rounded bg-surface px-1.5 py-0.5 text-xs">backend/</code>.{" "}
            <button className="underline" onClick={refreshStatus}>Retry</button>
          </div>
        )}

        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 sm:px-6">{children}</main>
      </div>
    </div>
  );
}

function DataModeBanner() {
  const { status, refreshStatus } = useApp();
  const router = useRouter();
  if (!status) return null;

  if (status.data_mode === "real") {
    return (
      <div className="flex items-center gap-2 rounded-full border border-primary/30 bg-primary-soft py-1 pl-3 pr-1 text-xs font-semibold text-primary">
        <span className="h-1.5 w-1.5 rounded-full bg-primary" aria-hidden />
        <span className="hidden sm:inline">
          REAL DATA — consented {status.consent.granted_at ? fmtDate(status.consent.granted_at) : ""}, processed on-device
        </span>
        <span className="sm:hidden">REAL DATA</span>
        <button
          className="rounded-full bg-surface px-2 py-0.5 font-medium text-danger hover:bg-danger-soft"
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
    );
  }
  return (
    <div className="flex items-center gap-2 rounded-full border border-border bg-surface-2 px-3 py-1 text-xs font-semibold text-ink-2"
      title="Synthetic sandbox — zero compliance risk">
      <span className="h-1.5 w-1.5 rounded-full bg-ink-3" aria-hidden />
      <span className="hidden sm:inline">DEMO DATA — not real; nothing is stored or acted on</span>
      <span className="sm:hidden">DEMO</span>
    </div>
  );
}

function Logo() {
  return (
    <svg viewBox="0 0 28 28" className="h-7 w-7" aria-hidden>
      <rect x="1" y="1" width="26" height="26" rx="8" fill="#1d4ed8" />
      <path d="M8 19.5 14 8l6 11.5" fill="none" stroke="#fff" strokeWidth="2.4"
        strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="14" cy="16.2" r="1.6" fill="#34d399" />
    </svg>
  );
}

function HomeIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className={className}>
      <path d="M3 10.5 12 3l9 7.5" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M5.5 9.5V21h13V9.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
function DataIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className={className}>
      <ellipse cx="12" cy="5.5" rx="8" ry="3" />
      <path d="M4 5.5V18.5c0 1.66 3.58 3 8 3s8-1.34 8-3V5.5M4 12c0 1.66 3.58 3 8 3s8-1.34 8-3" />
    </svg>
  );
}
function EyeIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className={className}>
      <path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12Z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}
function ScrollIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className={className}>
      <path d="M7 3h11a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z" />
      <path d="M9 8h8M9 12h8M9 16h5" strokeLinecap="round" />
    </svg>
  );
}
function GearIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className={className}>
      <circle cx="12" cy="12" r="3" />
      <path d="M12 2.5v3M12 18.5v3M21.5 12h-3M5.5 12h-3M18.7 5.3l-2.1 2.1M7.4 16.6l-2.1 2.1M18.7 18.7l-2.1-2.1M7.4 7.4 5.3 5.3" strokeLinecap="round" />
    </svg>
  );
}
