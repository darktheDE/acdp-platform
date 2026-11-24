import type { Metadata } from "next";
import Link from "next/link";
import { SearchX } from "lucide-react";
import { CompetitionCard } from "@/components/competitions/CompetitionCard";
import { FilterSidebar } from "@/components/competitions/FilterSidebar";
import { apiFetch, type PaginatedCompetitionsDTO } from "@/lib/api-client";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Khám phá Cuộc thi",
};

export default async function CompetitionsPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = await searchParams;
  const query = new URLSearchParams();
  for (const key of ["q", "domain", "mode", "is_free", "status", "sort"]) {
    const val = sp[key];
    if (typeof val === "string" && val.trim()) {
      query.set(key, val.trim());
    }
  }
  query.set("page_size", "50");

  const data = await apiFetch<PaginatedCompetitionsDTO>(`/api/v1/competitions?${query.toString()}`);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[var(--color-text-primary)] sm:text-3xl">
            Academic Competition Explorer
          </h1>
          <p className="mt-1 text-sm text-[var(--color-text-muted)]">
            Danh sách đã khử trùng từ tầng Gold (DuckDB mart_competition_explorer)
          </p>
        </div>
        <span className="font-mono text-xs text-[var(--color-text-muted)]">
          Hiển thị {data.items.length} / {data.total} cuộc thi
        </span>
      </div>

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
