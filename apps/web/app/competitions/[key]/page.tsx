import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, Bot, Calendar, ExternalLink, MapPin, Trophy, Users } from "lucide-react";
import { BookmarkButton } from "@/components/competitions/BookmarkButton";
import { apiFetch, ApiError, type CompetitionDetailDTO } from "@/lib/api-client";
import { formatCompetitionPrizeLabel, formatStatusLabel, formatVndFull } from "@/lib/formatters";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Chi tiết Cuộc thi",
};

export default async function CompetitionDetailPage({
  params,
}: {
  params: Promise<{ key: string }>;
}) {
  const { key } = await params;
  let comp: CompetitionDetailDTO;
  try {
    comp = await apiFetch<CompetitionDetailDTO>(`/api/v1/competitions/${key}`);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      notFound();
    }
    throw err;
  }

  const statusInfo = formatStatusLabel(comp.registration_status);
  const prizeLabel = formatCompetitionPrizeLabel(comp.total_prize_vnd, comp.has_scholarship);

  return (
    <div className="space-y-6">
      <div>
        <Link
          href="/competitions"
          className="inline-flex min-h-9 items-center gap-1.5 text-sm font-medium text-[var(--color-brand-primary)] hover:underline"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          <span>Quay lại danh sách cuộc thi</span>
        </Link>
      </div>

      <section className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-md bg-[var(--color-surface-subtle)] px-2.5 py-1 text-xs font-semibold text-[var(--color-text-primary)]">
            {statusInfo.label}
          </span>
          <span className="rounded-md bg-[var(--color-surface-subtle)] px-2.5 py-1 font-mono text-xs text-[var(--color-text-muted)]">
            {comp.mode_canonical}
          </span>
          {comp.domain_groups.map((grp) => (
            <span
              key={grp}
              className="rounded-md border border-[var(--color-border)] px-2.5 py-1 text-xs text-[var(--color-text-primary)]"
            >
              {grp}
            </span>
          ))}
        </div>

        <h1 className="mt-3 text-2xl font-bold tracking-tight text-[var(--color-text-primary)] sm:text-3xl">
          {comp.name}
        </h1>
        {comp.tagline && <p className="mt-1 text-sm text-[var(--color-text-muted)]">{comp.tagline}</p>}
        {comp.summary && <p className="mt-4 text-sm leading-relaxed text-[var(--color-text-primary)]">{comp.summary}</p>}

        <div className="mt-6 grid gap-3 border-t border-[var(--color-border)] pt-4 text-sm sm:grid-cols-2 lg:grid-cols-4">
          <div className="flex items-center gap-2 font-semibold text-[var(--color-brand-accent)]">
            <Trophy className="h-4 w-4 shrink-0" aria-hidden="true" />
            <span className="font-mono tabular-nums" title={formatVndFull(comp.total_prize_vnd)}>
              {prizeLabel}
            </span>
          </div>
          <div className="flex items-center gap-2 text-[var(--color-text-muted)]">
            <Calendar className="h-4 w-4 shrink-0" aria-hidden="true" />
            <span className="font-mono">Hạn ĐK: {comp.registration_deadline_raw || "Chưa rõ"}</span>
          </div>
          <div className="flex items-center gap-2 text-[var(--color-text-muted)]">
            <Users className="h-4 w-4 shrink-0" aria-hidden="true" />
            <span>{comp.team_profile || "Chưa rõ đội"}</span>
          </div>
          <div className="flex items-center gap-2 text-[var(--color-text-muted)]">
            <MapPin className="h-4 w-4 shrink-0" aria-hidden="true" />
            <span>{comp.location || comp.mode_canonical}</span>
          </div>
        </div>

        <div className="mt-5 flex flex-wrap gap-3">
          <a
            href={comp.canonical_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex min-h-10 items-center gap-2 rounded-lg bg-[var(--color-brand-primary)] px-4 py-2 text-sm font-semibold text-white dark:text-slate-950"
          >
            <span>Trang chính thức BTC</span>
            <ExternalLink className="h-4 w-4" aria-hidden="true" />
          </a>
          <Link
            href="/copilot"
            className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-[var(--color-border)] px-4 py-2 text-sm font-semibold text-[var(--color-text-primary)] hover:bg-[var(--color-surface-subtle)]"
          >
            <Bot className="h-4 w-4" aria-hidden="true" />
            <span>Hỏi RAG Copilot về thể lệ</span>
          </Link>
        </div>
      </section>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <section className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
            <h2 className="text-base font-semibold text-[var(--color-text-primary)]">
              Cơ cấu Giải thưởng ({comp.prizes.length})
            </h2>
            {comp.prizes.length === 0 ? (
              <p className="mt-2 text-sm text-[var(--color-text-muted)]">
                Chưa có bảng cơ cấu chi tiết từ nguồn thu thập; xem thêm trên trang chính thức.
              </p>
            ) : (
              <div className="mt-3 overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <caption className="visually-hidden">Chi tiết giải thưởng cuộc thi</caption>
                  <thead className="bg-[var(--color-surface-subtle)]">
                    <tr>
                      <th scope="col" className="px-3 py-2">Hạng giải</th>
                      <th scope="col" className="px-3 py-2">Phần thưởng</th>
                      <th scope="col" className="px-3 py-2 text-right">Quy đổi VNĐ</th>
                    </tr>
                  </thead>
                  <tbody>
                    {comp.prizes.map((p) => (
                      <tr key={p.tier_rank} className="border-t border-[var(--color-border)]">
                        <td className="px-3 py-2 font-medium">{p.tier_name}</td>
                        <td className="px-3 py-2">{p.reward_description}</td>
                        <td className="px-3 py-2 text-right font-mono tabular-nums">
                          {p.estimated_value_vnd > 0 ? formatVndFull(p.estimated_value_vnd) : p.is_scholarship ? "Học bổng" : "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
            <h2 className="text-base font-semibold text-[var(--color-text-primary)]">
              Lộ trình các Vòng thi ({comp.timeline_stages.length})
            </h2>
            {comp.timeline_stages.length === 0 ? (
              <p className="mt-2 text-sm text-[var(--color-text-muted)]">
                Chưa có danh sách vòng thi chi tiết.
              </p>
            ) : (
              <ol className="mt-4 space-y-4 border-l-2 border-[var(--color-border)] pl-4">
                {comp.timeline_stages.map((st) => (
                  <li key={st.stage_order} className="relative">
                    <p className="text-sm font-semibold text-[var(--color-text-primary)]">
                      {st.stage_order}. {st.stage_name}
                    </p>
                    <p className="font-mono text-xs text-[var(--color-brand-primary)]">
                      {st.start_date_raw || "?"} &rarr; {st.end_date_raw || "?"}
                    </p>
                    {st.description && (
                      <p className="mt-1 text-xs text-[var(--color-text-muted)]">{st.description}</p>
                    )}
                  </li>
                ))}
              </ol>
            )}
          </section>
        </div>

        <aside className="space-y-4">
          <BookmarkButton competitionKey={comp.competition_key} />
          <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 text-xs space-y-2">
            <h2 className="text-sm font-semibold text-[var(--color-text-primary)]">Đơn vị tổ chức &amp; Tài trợ</h2>
            <p className="text-[var(--color-text-muted)]">
              <strong>BTC:</strong> {comp.organizers.join(", ") || "Chưa rõ"}
            </p>
            {comp.partners_and_sponsors.length > 0 && (
              <p className="text-[var(--color-text-muted)]">
                <strong>Đối tác:</strong> {comp.partners_and_sponsors.join(", ")}
              </p>
            )}
            {comp.submission_platform && (
              <p className="text-[var(--color-text-muted)]">
                <strong>Nền tảng nộp bài:</strong> {comp.submission_platform}
              </p>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
