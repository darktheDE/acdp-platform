import type { Metadata } from "next";
import { DomainBarChart } from "@/components/charts/DomainBarChart";
import { ModeDonutChart } from "@/components/charts/ModeDonutChart";
import { OrganizerRanking } from "@/components/charts/OrganizerRanking";
import { SeasonalityChart } from "@/components/charts/SeasonalityChart";
import { apiFetch, type AnalyticsDashboardDTO } from "@/lib/api-client";
import { formatVndCompact, formatVndFull } from "@/lib/formatters";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Thống kê & Xu hướng",
};

export default async function DashboardPage() {
  const data = await apiFetch<AnalyticsDashboardDTO>("/api/v1/analytics/overview");
  const { kpi } = data;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[var(--color-text-primary)] sm:text-3xl">
            Thống kê &amp; Xu hướng Cuộc thi
          </h1>
          <p className="mt-1 text-sm text-[var(--color-text-muted)]">
            Bức tranh phân bổ giải thưởng, lịch cao điểm theo học kỳ HCM-UTE và các đơn vị tổ chức nổi bật
          </p>
        </div>
        <span className="font-mono text-xs text-[var(--color-text-muted)]">
          {kpi.unique_domains} nhóm ngành · {kpi.unique_organizers} đơn vị
        </span>
      </div>

      <section aria-label="Chỉ số KPI tổng quan" className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
          <p className="text-xs font-medium text-[var(--color-text-muted)]">Tổng số cuộc thi</p>
          <p className="mt-1 font-mono text-3xl font-bold tabular-nums text-[var(--color-text-primary)]">
            {kpi.total_competitions}
          </p>
          <p className="mt-1 text-xs text-[var(--color-status-success)]">
            {kpi.open_competitions} cuộc thi đang mở đăng ký
          </p>
        </div>
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
          <p className="text-xs font-medium text-[var(--color-text-muted)]">Tổng quỹ giải thưởng</p>
          <p
            title={formatVndFull(kpi.total_prize_pool_vnd)}
            className="mt-1 font-mono text-2xl font-bold tabular-nums text-[var(--color-brand-accent)]"
          >
            {formatVndCompact(kpi.total_prize_pool_vnd)}
          </p>
          <p className="mt-1 text-xs text-[var(--color-text-muted)]">Tổng hợp trên toàn hệ thống</p>
        </div>
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
          <p className="text-xs font-medium text-[var(--color-text-muted)]">Tỷ lệ miễn phí</p>
          <p className="mt-1 font-mono text-3xl font-bold tabular-nums text-[var(--color-status-success)]">
            {kpi.free_participation_pct.toFixed(0)}%
          </p>
          <p className="mt-1 text-xs text-[var(--color-text-muted)]">
            {kpi.scholarship_competitions} cuộc thi có học bổng
          </p>
        </div>
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
          <p className="text-xs font-medium text-[var(--color-text-muted)]">Quy mô đội tối đa TB</p>
          <p className="mt-1 font-mono text-3xl font-bold tabular-nums text-[var(--color-brand-primary)]">
            {kpi.avg_team_size_max.toFixed(1)}
          </p>
          <p className="mt-1 text-xs text-[var(--color-text-muted)]">Thành viên / đội</p>
        </div>
      </section>

      <div className="grid gap-6 lg:grid-cols-2">
        <DomainBarChart data={data.domains} />
        <SeasonalityChart data={data.seasonality} />
        <ModeDonutChart data={data.mode_team_matrix} />
        <OrganizerRanking data={data.top_organizers} />
      </div>
    </div>
  );
}
