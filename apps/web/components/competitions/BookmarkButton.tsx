"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Bookmark, Check } from "lucide-react";
import { apiFetch, type BookmarkDTO } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";

export function BookmarkButton({
  competitionKey,
  compact = false,
}: {
  competitionKey: string;
  compact?: boolean;
}) {
  const router = useRouter();
  const { accessToken, user } = useAuth();
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const [note, setNote] = useState("");
  const [feedback, setFeedback] = useState<string | null>(null);

  const handleSave = async () => {
    if (!user || !accessToken) {
      router.push("/login");
      return;
    }
    setSaving(true);
    setFeedback(null);
    try {
      if (saved) {
        await apiFetch<void>(`/api/v1/bookmarks/${competitionKey}`, {
          method: "DELETE",
          token: accessToken,
        });
        setSaved(false);
        setFeedback("Đã gỡ khỏi danh sách theo dõi.");
      } else {
        await apiFetch<BookmarkDTO>("/api/v1/bookmarks", {
          method: "POST",
          token: accessToken,
          body: JSON.stringify({
            competition_key: competitionKey,
            personal_note: note.trim() || null,
            notify_before_deadline: true,
          }),
        });
        setSaved(true);
        setFeedback("Đã lưu vào danh sách theo dõi.");
      }
    } catch {
      setFeedback("Không thể cập nhật trạng thái lưu.");
    } finally {
      setSaving(false);
    }
  };

  if (compact) {
    return (
      <button
        type="button"
        onClick={() => void handleSave()}
        disabled={saving}
        aria-pressed={saved}
        aria-label={saved ? "Bỏ lưu cuộc thi" : "Lưu cuộc thi"}
        className={`inline-flex min-h-8 items-center gap-1 rounded-lg border px-2.5 py-1 text-xs font-medium transition-colors ${
          saved
            ? "border-[var(--color-status-success)] text-[var(--color-status-success)]"
            : "border-[var(--color-border)] text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]"
        }`}
      >
        {saved ? <Check className="h-3.5 w-3.5" aria-hidden="true" /> : <Bookmark className="h-3.5 w-3.5" aria-hidden="true" />}
        <span>{saved ? "Đã lưu" : "Lưu"}</span>
      </button>
    );
  }

  return (
    <div className="space-y-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
      <label htmlFor="bookmark-note" className="block text-xs font-semibold text-[var(--color-text-primary)]">
        Ghi chú cá nhân / Kế hoạch lập đội
      </label>
      <input
        id="bookmark-note"
        type="text"
        value={note}
        onChange={(e) => setNote(e.target.value)}
        placeholder="Ví dụ: Tìm thêm 2 bạn làm NLP..."
        className="min-h-10 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-canvas)] px-3 text-sm text-[var(--color-text-primary)]"
      />
      <button
        type="button"
        onClick={() => void handleSave()}
        disabled={saving}
        aria-pressed={saved}
        className="inline-flex min-h-10 w-full items-center justify-center gap-2 rounded-lg bg-[var(--color-brand-primary)] px-4 py-2 text-sm font-semibold text-white dark:text-slate-950"
      >
        {saved ? <Check className="h-4 w-4" aria-hidden="true" /> : <Bookmark className="h-4 w-4" aria-hidden="true" />}
        <span>{saving ? "Đang xử lý..." : saved ? "Đã lưu theo dõi (Bấm để bỏ)" : "Lưu cuộc thi theo dõi"}</span>
      </button>
      {feedback && (
        <p role="status" className="text-xs text-[var(--color-text-muted)]">
          {feedback}
        </p>
      )}
    </div>
  );
}
