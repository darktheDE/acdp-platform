"use client";

import { AlertTriangle, RotateCcw } from "lucide-react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div
      role="alert"
      className="mx-auto my-12 max-w-lg rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 text-center shadow-xs"
    >
      <AlertTriangle className="mx-auto h-10 w-10 text-[var(--color-brand-accent)]" aria-hidden="true" />
      <h1 className="mt-3 text-xl font-bold text-[var(--color-text-primary)]">
        Không thể kết nối máy chủ dữ liệu
      </h1>
      <p className="mt-2 text-sm text-[var(--color-text-muted)]">
        {error.message || "FastAPI Gateway đang tạm gián đoạn hoặc chưa sẵn sàng."}
      </p>
      <button
        type="button"
        onClick={reset}
        className="mt-5 inline-flex min-h-10 items-center gap-2 rounded-lg bg-[var(--color-brand-primary)] px-4 py-2 text-sm font-medium text-white dark:text-slate-950"
      >
        <RotateCcw className="h-4 w-4" aria-hidden="true" />
        <span>Thử kết nối lại</span>
      </button>
    </div>
  );
}
