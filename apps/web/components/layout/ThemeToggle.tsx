"use client";

import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";

type Scheme = "light" | "dark";

function resolveRenderedScheme(): Scheme {
  if (typeof window === "undefined") return "light";
  try {
    const stored = localStorage.getItem("color-scheme");
    if (stored === "light" || stored === "dark") return stored;
  } catch {
    // Ignore storage errors in restricted environments
  }
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function applyScheme(storedValue: Scheme | null, rendered: Scheme): void {
  const meta = document.querySelector('meta[name="color-scheme"]');
  if (meta) {
    meta.setAttribute("content", storedValue ?? "light dark");
  }
  document.documentElement.classList.toggle("dark", rendered === "dark");
}

export function ThemeToggle() {
  const [rendered, setRendered] = useState<Scheme>("light");

  useEffect(() => {
    const current = resolveRenderedScheme();
    setRendered(current);

    const onStorage = (e: StorageEvent) => {
      if (e.key === "color-scheme") {
        const next = resolveRenderedScheme();
        setRendered(next);
        applyScheme(e.newValue === "light" || e.newValue === "dark" ? e.newValue : null, next);
      }
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const handleToggle = () => {
    const systemPref: Scheme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    const target: Scheme = rendered === "dark" ? "light" : "dark";
    const nextStored: Scheme | null = target === systemPref ? null : target;
    try {
      if (nextStored === null) {
        localStorage.removeItem("color-scheme");
      } else {
        localStorage.setItem("color-scheme", nextStored);
      }
    } catch {
      // Non-fatal if storage is blocked
    }
    applyScheme(nextStored, target);
    setRendered(target);
  };

  return (
    <button
      type="button"
      onClick={handleToggle}
      aria-label={rendered === "dark" ? "Chuyển sang giao diện sáng" : "Chuyển sang giao diện tối"}
      aria-pressed={rendered === "dark"}
      className="inline-flex min-h-9 min-w-9 items-center justify-center rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-2.5 text-sm font-medium text-[var(--color-text-primary)] transition-colors hover:bg-[var(--color-surface-subtle)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-brand-primary)]"
    >
      {rendered === "dark" ? (
        <Sun className="h-4 w-4 text-[var(--color-brand-accent)]" aria-hidden="true" />
      ) : (
        <Moon className="h-4 w-4 text-[var(--color-brand-primary)]" aria-hidden="true" />
      )}
    </button>
  );
}
