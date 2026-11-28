import Link from "next/link";
import { ArrowRight, BarChart3, Bot, CheckCircle2, Compass, Search, Sparkles } from "lucide-react";
import { CompetitionCard } from "@/components/competitions/CompetitionCard";
import { apiFetch, type AnalyticsDashboardDTO, type PaginatedCompetitionsDTO } from "@/lib/api-client";
import { formatVndCompact } from "@/lib/formatters";

export const dynamic = "force-dynamic";

const QUICK_FILTERS = [
  { label: "Đang mở đăng ký", href: "/competitions?status=open" },
  { label: "Miễn phí tham gia", href: "/competitions?is_free=true" },
  { label: "AI & Data Science", href: "/competitions?domain=ai-data-science" },
  { label: "Software, Web & Mobile", href: "/competitions?domain=software-web-mobile" },
  { label: "Security, IoT & Embedded", href: "/competitions?domain=security-iot-embedded" },
];

export default async function HomePage() {
  let overview: AnalyticsDashboardDTO | null = null;
  let featured: PaginatedCompetitionsDTO | null = null;

  const [overviewRes, featuredRes] = await Promise.allSettled([
    apiFetch<AnalyticsDashboardDTO>("/api/v1/analytics/overview"),
    apiFetch<PaginatedCompetitionsDTO>("/api/v1/competitions?sort=prize_desc&page_size=6"),
  ]);

  if (overviewRes.status === "fulfilled") {
    overview = overviewRes.value;
  }
  if (featuredRes.status === "fulfilled") {
    featured = featuredRes.value;
  }

  return (
    <div className="space-y-10">
      <section className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 sm:p-10">
        <p className="font-mono text-xs font-semibold uppercase tracking-wider text-[var(--color-brand-accent)]">
          FIT — Trường Đại học Công nghệ Kỹ thuật TP.HCM (HCM-UTE)
        </p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-[var(--color-text-primary)] sm:text-4xl">
          Khám phá Cuộc thi Công nghệ &amp; Tra cứu Thể lệ Xác thực
        </h1>
        <p className="mt-3 max-w-2xl text-sm leading-relaxed text-[var(--color-text-muted)] sm:text-base">
          Tìm kiếm nhanh hackathon, cuộc thi AI, Lập trình, An toàn thông tin phù hợp với kỹ năng của bạn,
          theo dõi mùa vụ học kỳ HCM-UTE và hỏi đáp điều lệ kèm liên kết gốc từ Ban tổ chức.
        </p>

        <form action="/competitions" method="get" className="mt-6 flex max-w-2xl flex-col gap-2.5 sm:flex-row">
          <label htmlFor="home-search" className="visually-hidden">
            Tìm kiếm cuộc thi theo tên hoặc lĩnh vực
          </label>
          <div className="relative flex-1">
            <Search
              className="pointer-events-none absolute left-3.5 top-3.5 h-4 w-4 text-[var(--color-text-muted)]"
              aria-hidden="true"
            />
            <input
              id="home-search"
              name="q"
              type="search"
              placeholder="Tìm cuộc thi theo tên, công nghệ, từ khóa (VD: AI, Hackathon, Security)..."
              className="min-h-11 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-canvas)] pl-10 pr-3 text-sm text-[var(--color-text-primary)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-brand-primary)]"
            />
          </div>
          <button
            type="submit"
            className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-[var(--color-brand-primary)] px-5 py-2 text-sm font-semibold text-white transition-opacity hover:opacity-90 dark:text-slate-950"
          >
            <span>Tìm cuộc thi</span>
            <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </button>
        </form>

        <div className="mt-4 flex flex-wrap items-center gap-2">
          <span className="text-xs font-medium text-[var(--color-text-muted)]">Gợi ý nhanh:</span>
          {QUICK_FILTERS.map((chip) => (
            <Link
              key={chip.href}
              href={chip.href}
              className="rounded-full border border-[var(--color-border)] bg-[var(--color-canvas)] px-3 py-1 text-xs font-medium text-[var(--color-text-primary)] transition-colors hover:border-[var(--color-brand-primary)] hover:text-[var(--color-brand-primary)]"
            >
              {chip.label}
            </Link>
          ))}
        </div>

        {overview && (
          <div className="mt-7 grid grid-cols-2 gap-3 sm:grid-cols-4">
            <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-canvas)] p-3.5">
              <p className="text-xs text-[var(--color-text-muted)]">Cuộc thi đang tổng hợp</p>
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
            <span>Khám phá tất cả cuộc thi</span>
          </Link>
          <Link
            href="/copilot"
            className="inline-flex min-h-11 items-center gap-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2 text-sm font-semibold text-[var(--color-text-primary)] hover:bg-[var(--color-surface-subtle)]"
          >
            <Bot className="h-4 w-4" aria-hidden="true" />
            <span>Hỏi Trợ lý Thể lệ AI</span>
          </Link>
          <Link
            href="/dashboard"
            className="inline-flex min-h-11 items-center gap-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2 text-sm font-semibold text-[var(--color-text-primary)] hover:bg-[var(--color-surface-subtle)]"
          >
            <BarChart3 className="h-4 w-4" aria-hidden="true" />
            <span>Xem thống kê xu hướng</span>
          </Link>
        </div>
      </section>

      <section aria-label="Quy trình sử dụng dành cho sinh viên" className="grid gap-4 md:grid-cols-3">
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
          <div className="inline-flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--color-surface-subtle)] text-[var(--color-brand-primary)]">
            <Compass className="h-5 w-5" aria-hidden="true" />
          </div>
          <h2 className="mt-3 text-base font-semibold text-[var(--color-text-primary)]">
            1. Lọc đúng sân chơi phù hợp
          </h2>
          <p className="mt-1.5 text-xs leading-relaxed text-[var(--color-text-muted)]">
            Sàng lọc nhanh theo nhóm ngành (AI/Data, Web/Mobile, Security/IoT), hình thức thi, lệ phí và số lượng thành viên đội.
          </p>
        </div>
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
          <div className="inline-flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--color-surface-subtle)] text-[var(--color-brand-accent)]">
            <Sparkles className="h-5 w-5" aria-hidden="true" />
          </div>
          <h2 className="mt-3 text-base font-semibold text-[var(--color-text-primary)]">
            2. Hỏi nhanh điều lệ &amp; giải thưởng
          </h2>
          <p className="mt-1.5 text-xs leading-relaxed text-[var(--color-text-muted)]">
            Tra cứu trực tiếp điều kiện dự thi, mốc thời gian và cơ cấu giải bằng tiếng Việt kèm liên kết nguồn chính thức để tự kiểm chứng.
          </p>
        </div>
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
          <div className="inline-flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--color-surface-subtle)] text-[var(--color-status-success)]">
            <CheckCircle2 className="h-5 w-5" aria-hidden="true" />
          </div>
          <h2 className="mt-3 text-base font-semibold text-[var(--color-text-primary)]">
            3. Lưu theo dõi &amp; canh mùa thi
          </h2>
          <p className="mt-1.5 text-xs leading-relaxed text-[var(--color-text-muted)]">
            Đánh dấu cuộc thi mục tiêu, ghi chú tìm đồng đội và đối chiếu cao điểm cuộc thi theo lịch học kỳ HK1, HK2, Hè tại HCM-UTE.
          </p>
        </div>
      </section>

      {featured && featured.items.length > 0 && (
        <section aria-label="Cuộc thi nổi bật" className="space-y-4">
          <div className="flex flex-wrap items-end justify-between gap-2">
            <div>
              <h2 className="text-xl font-bold tracking-tight text-[var(--color-text-primary)] sm:text-2xl">
                Cuộc thi Nổi bật
              </h2>
              <p className="mt-0.5 text-sm text-[var(--color-text-muted)]">
                Các sân chơi công nghệ có tổng giải thưởng và mức độ quan tâm cao
              </p>
            </div>
            <Link
              href="/competitions"
              className="inline-flex items-center gap-1 text-sm font-semibold text-[var(--color-brand-primary)] hover:underline"
            >
              <span>Xem toàn bộ ({featured.total})</span>
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </Link>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {featured.items.map((item) => (
              <CompetitionCard key={item.competition_key} item={item} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
