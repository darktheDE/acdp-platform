import Link from "next/link";
import { ArrowRight, BarChart3, Bot, Compass } from "lucide-react";
import { apiFetch, type AnalyticsDashboardDTO } from "@/lib/api-client";
import { formatVndCompact } from "@/lib/formatters";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  let overview: AnalyticsDashboardDTO | null = null;
  try {
    overview = await apiFetch<AnalyticsDashboardDTO>("/api/v1/analytics/overview");
  } catch {
    overview = null;
  }

  return (
    <div className="space-y-8">
      <section className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 sm:p-10">
        <p className="font-mono text-xs font-semibold uppercase tracking-wider text-[var(--color-brand-accent)]">
          FIT — Trường Đại học Công nghệ Kỹ thuật TP.HCM (HCM-UTE)
        </p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-[var(--color-text-primary)] sm:text-4xl">
          Nền tảng Khám phá Cuộc thi Học thuật &amp; Trợ lý Thể lệ RAG
        </h1>
        <p className="mt-3 max-w-2xl text-sm leading-relaxed text-[var(--color-text-muted)] sm:text-base">
          Tổng hợp, chuẩn hóa dữ liệu cuộc thi qua kiến trúc Medallion Lakehouse (DuckDB Star Schema),
          phân tích mùa vụ học kỳ HCM-UTE và hỏi đáp thể lệ kèm trích dẫn nguồn xác thực.
        </p>

        {overview && (
          <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
            <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-canvas)] p-3.5">
              <p className="text-xs text-[var(--color-text-muted)]">Cuộc thi đã chuẩn hóa</p>
              <p className="mt-1 font-mono text-2xl font-bold tabular-nums text-[var(--color-text-primary)]">
                {overview.kpi.total_competitions}
              </p>
            </div>
            <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-canvas)] p-3.5">
              <p className="text-xs text-[var(--color-text-muted)]">Tổng quỹ giải thưởng</p>
              <p className="mt-1 font-mono text-xl font-bold tabular-nums text-[var(--color-brand-accent)]">
                {formatVndCompact(overview.kpi.total_prize_pool_vnd)}
              </p>
            </div>
            <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-canvas)] p-3.5">
              <p className="text-xs text-[var(--color-text-muted)]">Miễn phí tham gia</p>
              <p className="mt-1 font-mono text-2xl font-bold tabular-nums text-[var(--color-status-success)]">
                {overview.kpi.free_participation_pct.toFixed(0)}%
              </p>
            </div>
            <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-canvas)] p-3.5">
              <p className="text-xs text-[var(--color-text-muted)]">Đơn vị BTC &amp; Tài trợ</p>
              <p className="mt-1 font-mono text-2xl font-bold tabular-nums text-[var(--color-brand-primary)]">
                {overview.kpi.unique_organizers}
              </p>
            </div>
          </div>
        )}

        <div className="mt-6 flex flex-wrap gap-3">
          <Link
            href="/competitions"
            className="inline-flex min-h-11 items-center gap-2 rounded-lg bg-[var(--color-brand-primary)] px-4 py-2 text-sm font-semibold text-white dark:text-slate-950"
          >
            <Compass className="h-4 w-4" aria-hidden="true" />
            <span>Khám phá cuộc thi</span>
            <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </Link>
          <Link
            href="/dashboard"
            className="inline-flex min-h-11 items-center gap-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2 text-sm font-semibold text-[var(--color-text-primary)] hover:bg-[var(--color-surface-subtle)]"
          >
            <BarChart3 className="h-4 w-4" aria-hidden="true" />
            <span>Xem Dashboard OLAP</span>
          </Link>
          <Link
            href="/copilot"
            className="inline-flex min-h-11 items-center gap-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2 text-sm font-semibold text-[var(--color-text-primary)] hover:bg-[var(--color-surface-subtle)]"
          >
            <Bot className="h-4 w-4" aria-hidden="true" />
            <span>Hỏi RAG Copilot</span>
          </Link>
        </div>
      </section>
    </div>
  );
}
