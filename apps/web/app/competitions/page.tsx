import type { Metadata } from "next";
import Link from "next/link";
import { SearchX, X } from "lucide-react";
import { CompetitionCard } from "@/components/competitions/CompetitionCard";
import { FilterSidebar } from "@/components/competitions/FilterSidebar";
import { apiFetch, type PaginatedCompetitionsDTO } from "@/lib/api-client";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Khám phá Cuộc thi",
};

const FILTER_LABELS: Record<string, string> = {
  q: "Từ khóa",
  domain: "Lĩnh vực",
  mode: "Hình thức",
  status: "Trạng thái",
  is_free: "Miễn phí",
  sort: "Sắp xếp",
};

const VALUE_LABELS: Record<string, string> = {
  open: "Đang mở",
  upcoming: "Sắp diễn ra",
  closed: "Đã đóng",
  true: "Có",
  prize_asc: "Giải thưởng tăng dần",
  deadline_asc: "Hạn ĐK gần nhất",
  name_asc: "Tên A → Z",
};

export default async function CompetitionsPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = await searchParams;
  const query = new URLSearchParams();
  const activePairs: Array<{ key: string; value: string }> = [];

  for (const key of ["q", "domain", "mode", "is_free", "status", "sort"]) {
    const val = sp[key];
    if (typeof val === "string" && val.trim()) {
      const trimmed = val.trim();
      query.set(key, trimmed);
      if (!(key === "sort" && trimmed === "prize_desc")) {
        activePairs.push({ key, value: trimmed });
      }
    }
  }
  query.set("page_size", "50");

  const data = await apiFetch<PaginatedCompetitionsDTO>(`/api/v1/competitions?${query.toString()}`);

  const buildWithoutParam = (removeKey: string): string => {
    const next = new URLSearchParams();
    for (const pair of activePairs) {
      if (pair.key !== removeKey) {
        next.set(pair.key, pair.value);
      }
    }
    const qs = next.toString();
    return qs ? `/competitions?${qs}` : "/competitions";
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[var(--color-text-primary)] sm:text-3xl">
            Khám phá Cuộc thi Học thuật
          </h1>
          <p className="mt-1 text-sm text-[var(--color-text-muted)]">
            Tổng hợp các cuộc thi IT, AI, Data &amp; Công nghệ dành cho sinh viên, đối chiếu từ trang chính thức Ban tổ chức
          </p>
        </div>
        <span className="font-mono text-xs text-[var(--color-text-muted)]">
          Hiển thị {data.items.length} / {data.total} cuộc thi
        </span>
      </div>

      {activePairs.length > 0 && (
        <div className="flex flex-wrap items-center gap-2" aria-label="Bộ lọc đang áp dụng">
          <span className="text-xs font-medium text-[var(--color-text-muted)]">Đang lọc:</span>
          {activePairs.map((pair) => (
            <Link
              key={pair.key}
              href={buildWithoutParam(pair.key)}
              aria-label={`Bỏ lọc ${FILTER_LABELS[pair.key] || pair.key}`}
              className="inline-flex items-center gap-1.5 rounded-full border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-1 text-xs font-medium text-[var(--color-text-primary)] hover:border-[var(--color-brand-accent)] hover:text-[var(--color-brand-accent)]"
            >
              <span>
                {FILTER_LABELS[pair.key] || pair.key}: {VALUE_LABELS[pair.value] || pair.value}
              </span>
              <X className="h-3 w-3" aria-hidden="true" />
            </Link>
          ))}
          <Link
            href="/competitions"
            className="text-xs font-medium text-[var(--color-brand-primary)] hover:underline"
          >
            Xóa tất cả
          </Link>
        </div>
      )}

      <div className="flex flex-col gap-6 lg:flex-row">
        <FilterSidebar />
        <div className="min-w-0 flex-1">
          {data.items.length === 0 ? (
            <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-10 text-center">
              <SearchX className="mx-auto h-10 w-10 text-[var(--color-text-muted)]" aria-hidden="true" />
              <h2 className="mt-3 text-base font-semibold text-[var(--color-text-primary)]">
                Không tìm thấy cuộc thi phù hợp
              </h2>
              <p className="mt-1 text-sm text-[var(--color-text-muted)]">
                Thử bỏ bớt điều kiện lọc hoặc quay lại toàn bộ danh sách gốc.
              </p>
              <Link
                href="/competitions"
                className="mt-4 inline-flex min-h-10 items-center rounded-lg bg-[var(--color-brand-primary)] px-4 py-2 text-sm font-medium text-white dark:text-slate-950"
              >
                Xóa toàn bộ bộ lọc
              </Link>
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {data.items.map((item) => (
                <CompetitionCard key={item.competition_key} item={item} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
