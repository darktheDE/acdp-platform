import type { ReactNode } from "react";
import { LogoMonochrome } from "@/components/brand/AcdpLogo";
import { TopNav } from "@/components/layout/TopNav";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col">
      <a
        href="#main-content"
        className="visually-hidden fixed left-4 top-4 z-50 rounded-md bg-[var(--color-brand-primary)] px-4 py-2 text-sm font-semibold text-white dark:text-slate-950"
      >
        Chuyển tới nội dung chính
      </a>
      <TopNav />
      <main id="main-content" tabIndex={-1} className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 sm:px-6 lg:px-8">
        {children}
      </main>
      <footer className="border-t border-[var(--color-border)] bg-[var(--color-surface)] py-5">
        <div className="mx-auto flex max-w-7xl flex-col items-start justify-between gap-3 px-4 text-xs text-[var(--color-text-muted)] sm:flex-row sm:items-center sm:px-6 lg:px-8">
          <div className="flex items-center gap-2">
            <LogoMonochrome size={20} />
            <span>ACDP — Nền tảng Khám phá Cuộc thi Học thuật (Kỹ thuật Dữ liệu, FIT — HCM-UTE)</span>
          </div>
          <span className="font-mono">Medallion Lakehouse · DuckDB + PostgreSQL 18 + Qdrant</span>
        </div>
      </footer>
    </div>
  );
}
