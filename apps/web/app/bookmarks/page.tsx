"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AlertTriangle, Bookmark, Trash2 } from "lucide-react";
import { apiFetch, type BookmarkDTO } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import { formatVndCompact } from "@/lib/formatters";

export default function BookmarksPage() {
  const { user, accessToken, loading: authLoading } = useAuth();
  const [items, setItems] = useState<BookmarkDTO[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (authLoading) return;
    if (!accessToken) {
      setLoading(false);
      return;
    }
    let active = true;
    (async () => {
      try {
        const data = await apiFetch<BookmarkDTO[]>("/api/v1/bookmarks", { token: accessToken });
        if (active) setItems(data);
      } catch {
        if (active) setError("Không thể tải danh sách cuộc thi đã lưu.");
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [accessToken, authLoading]);

  const removeBookmark = async (key: string) => {
    if (!accessToken) return;
    try {
      await apiFetch<void>(`/api/v1/bookmarks/${key}`, { method: "DELETE", token: accessToken });
      setItems((prev) => prev.filter((b) => b.competition_key !== key));
    } catch {
      setError("Không thể xóa bookmark.");
    }
  };

  if (authLoading || loading) {
    return <div className="h-48 animate-pulse rounded-xl bg-[var(--color-surface)]" />;
  }

  if (!user) {
    return (
      <div className="mx-auto my-8 max-w-lg rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 text-center">
        <Bookmark className="mx-auto h-9 w-9 text-[var(--color-brand-primary)]" aria-hidden="true" />
        <h1 className="mt-3 text-xl font-bold text-[var(--color-text-primary)]">
          Theo dõi Cuộc thi Cá nhân
        </h1>
        <p className="mt-2 text-sm text-[var(--color-text-muted)]">
          Vui lòng đăng nhập tài khoản để lưu các cuộc thi quan tâm và ghi chú kế hoạch lập đội.
        </p>
        <Link
          href="/login"
          className="mt-4 inline-flex min-h-10 items-center rounded-lg bg-[var(--color-brand-primary)] px-4 py-2 text-sm font-semibold text-white dark:text-slate-950"
        >
          Đăng nhập ngay
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-[var(--color-text-primary)] sm:text-3xl">
          Cuộc thi Đã lưu ({items.length})
        </h1>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          Theo dõi danh sách cuộc thi bạn quan tâm, hạn chót đăng ký và ghi chú tìm đồng đội
        </p>
      </div>

      {error && (
        <div role="alert" className="rounded-lg border border-[var(--color-brand-accent)]/40 p-3 text-sm text-[var(--color-brand-accent)]">
          {error}
        </div>
      )}

      {items.length === 0 ? (
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-8 text-center">
          <p className="text-sm text-[var(--color-text-muted)]">Bạn chưa lưu cuộc thi nào.</p>
          <Link
            href="/competitions"
            className="mt-3 inline-flex min-h-10 items-center rounded-lg bg-[var(--color-brand-primary)] px-4 py-2 text-sm font-medium text-white dark:text-slate-950"
          >
            Khám phá cuộc thi
          </Link>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {items.map((bm) => (
            <article
              key={bm.id}
              className="flex flex-col justify-between rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5"
            >
              <div>
                {bm.is_archived && (
                  <div className="mb-2 inline-flex items-center gap-1.5 rounded-md bg-amber-50 px-2.5 py-1 text-xs font-medium text-[var(--color-status-warning)] dark:bg-amber-950/30">
                    <AlertTriangle className="h-3.5 w-3.5" aria-hidden="true" />
                    <span>Cuộc thi đã kết thúc hoặc tạm ngừng cập nhật</span>
                  </div>
                )}
                <h2 className="text-base font-semibold text-[var(--color-text-primary)]">
                  {bm.is_archived ? (
                    bm.competition_name
                  ) : (
                    <Link href={`/competitions/${bm.competition_key}`} className="hover:text-[var(--color-brand-primary)]">
                      {bm.competition_name}
                    </Link>
                  )}
                </h2>
                {bm.personal_note && (
                  <p className="mt-2 rounded-md bg-[var(--color-canvas)] p-2.5 text-xs text-[var(--color-text-primary)]">
                    Ghi chú: {bm.personal_note}
                  </p>
                )}
              </div>

              <div className="mt-4 flex items-center justify-between border-t border-[var(--color-border)] pt-3 text-xs text-[var(--color-text-muted)]">
                <span className="font-mono">
                  {bm.mode_canonical || "—"} · {bm.total_prize_vnd ? formatVndCompact(bm.total_prize_vnd) : "Theo thể lệ"}
                </span>
                <button
                  type="button"
                  onClick={() => void removeBookmark(bm.competition_key)}
                  aria-label={`Bỏ lưu ${bm.competition_name}`}
                  className="inline-flex min-h-8 items-center gap-1 rounded-md border border-[var(--color-border)] px-2.5 py-1 text-xs text-[var(--color-brand-accent)] hover:bg-[var(--color-surface-subtle)]"
                >
                  <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
                  <span>Gỡ</span>
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
