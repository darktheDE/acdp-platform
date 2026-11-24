"use client";

import Link from "next/link";
import { Calendar, CheckCircle2, Clock, ExternalLink, Trophy, Users, XCircle } from "lucide-react";
import type { CompetitionSummaryDTO } from "@/lib/api-client";
import { formatCompetitionPrizeLabel, formatStatusLabel, formatVndFull } from "@/lib/formatters";
import { BookmarkButton } from "@/components/competitions/BookmarkButton";

export function CompetitionCard({ item }: { item: CompetitionSummaryDTO }) {
  const prizeLabel = formatCompetitionPrizeLabel(item.total_prize_vnd, item.has_scholarship);
  const statusInfo = formatStatusLabel(item.registration_status);

  const statusClasses =
    statusInfo.tone === "open"
      ? "bg-emerald-50 text-[var(--color-status-success)] dark:bg-emerald-950/40"
      : statusInfo.tone === "upcoming"
        ? "bg-amber-50 text-[var(--color-status-warning)] dark:bg-amber-950/40"
        : "bg-[var(--color-surface-subtle)] text-[var(--color-text-muted)]";

  return (
    <article
      aria-labelledby={`comp-${item.competition_key}`}
      className="flex flex-col justify-between rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5 transition-shadow hover:shadow-md"
    >
      <div>
        <div className="flex items-center justify-between gap-2">
          <span className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium ${statusClasses}`}>
            {statusInfo.tone === "open" ? (
              <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" />
            ) : statusInfo.tone === "upcoming" ? (
              <Clock className="h-3.5 w-3.5" aria-hidden="true" />
            ) : (
              <XCircle className="h-3.5 w-3.5" aria-hidden="true" />
            )}
            <span>{statusInfo.label}</span>
          </span>
          <span className="rounded-md bg-[var(--color-surface-subtle)] px-2 py-0.5 font-mono text-xs text-[var(--color-text-muted)]">
            {item.mode_canonical}
          </span>
        </div>

        <h2
          id={`comp-${item.competition_key}`}
          title={item.name}
          className="mt-3 line-clamp-2 text-base font-semibold text-[var(--color-text-primary)]"
        >
          <Link
            href={`/competitions/${item.competition_key}`}
            className="hover:text-[var(--color-brand-primary)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-brand-primary)]"
          >
            {item.name}
          </Link>
        </h2>
        {item.tagline && (
          <p className="mt-1 line-clamp-1 text-xs text-[var(--color-text-muted)]">{item.tagline}</p>
        )}

        <div className="mt-4 space-y-1.5 border-t border-[var(--color-border)] pt-3 text-xs text-[var(--color-text-muted)]">
          <div className="flex items-center gap-2 font-semibold text-[var(--color-brand-accent)]">
            <Trophy className="h-4 w-4 shrink-0" aria-hidden="true" />
            <span
              className="font-mono tabular-nums"
              title={item.total_prize_vnd > 0 ? formatVndFull(item.total_prize_vnd) : prizeLabel}
            >
              {prizeLabel}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 shrink-0" aria-hidden="true" />
            <span className="font-mono">
              Hạn ĐK: {item.registration_deadline_raw || "Chưa công bố"}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 shrink-0" aria-hidden="true" />
            <span>{item.team_profile || "Chưa rõ quy mô"}</span>
          </div>
        </div>

        <div className="mt-3 flex flex-wrap gap-1.5">
          {item.domain_groups.slice(0, 2).map((grp) => (
            <span
              key={grp}
              className="rounded-sm bg-[var(--color-surface-subtle)] px-2 py-0.5 text-[11px] text-[var(--color-text-primary)]"
            >
              {grp}
            </span>
          ))}
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between gap-2 border-t border-[var(--color-border)] pt-3">
        <BookmarkButton competitionKey={item.competition_key} compact />
        <div className="flex items-center gap-2">
          <Link
            href={`/competitions/${item.competition_key}`}
            className="inline-flex min-h-8 items-center rounded-lg border border-[var(--color-border)] px-3 py-1 text-xs font-medium text-[var(--color-text-primary)] hover:bg-[var(--color-surface-subtle)]"
          >
            Chi tiết
          </Link>
          <a
            href={item.canonical_url}
            target="_blank"
            rel="noopener noreferrer"
            aria-label={`Mở trang chính thức của ${item.name}`}
            className="inline-flex min-h-8 items-center gap-1 rounded-lg bg-[var(--color-brand-primary)] px-2.5 py-1 text-xs font-medium text-white dark:text-slate-950"
          >
            <span>BTC</span>
            <ExternalLink className="h-3 w-3" aria-hidden="true" />
          </a>
        </div>
      </div>
    </article>
  );
}
