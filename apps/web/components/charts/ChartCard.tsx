"use client";

import { useState, type ReactNode } from "react";
import { Table2, BarChart2 } from "lucide-react";

interface ChartCardProps {
  title: string;
  subtitle: string;
  ariaLabel: string;
  children: ReactNode;
  tableContent: ReactNode;
}

export function ChartCard({ title, subtitle, ariaLabel, children, tableContent }: ChartCardProps) {
  const [showTable, setShowTable] = useState(false);

  return (
    <section
      role="region"
      aria-label={ariaLabel}
      className="flex flex-col rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5"
    >
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-[var(--color-text-primary)]">{title}</h2>
          <p className="mt-0.5 text-xs text-[var(--color-text-muted)]">{subtitle}</p>
        </div>
        <button
          type="button"
          onClick={() => setShowTable((prev) => !prev)}
          aria-pressed={showTable}
          className="inline-flex min-h-8 shrink-0 items-center gap-1.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-canvas)] px-2.5 py-1 text-xs font-medium text-[var(--color-text-primary)] hover:bg-[var(--color-surface-subtle)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-brand-primary)]"
        >
          {showTable ? (
            <>
              <BarChart2 className="h-3.5 w-3.5" aria-hidden="true" />
              <span>Biểu đồ</span>
            </>
          ) : (
            <>
              <Table2 className="h-3.5 w-3.5" aria-hidden="true" />
              <span>Xem dạng bảng</span>
            </>
          )}
        </button>
      </div>
      {showTable ? (
        <div className="max-h-80 overflow-auto rounded-lg border border-[var(--color-border)]">
          {tableContent}
        </div>
      ) : (
        <div className="h-80 w-full min-w-0">{children}</div>
      )}
    </section>
  );
}
