export default function Loading() {
  return (
    <div className="space-y-4" aria-busy="true" aria-label="Đang tải dữ liệu">
      <div className="h-8 w-64 animate-pulse rounded-lg bg-[var(--color-surface-subtle)]" />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((idx) => (
          <div
            key={idx}
            className="h-28 animate-pulse rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)]"
          />
        ))}
      </div>
      <div className="h-72 animate-pulse rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)]" />
    </div>
  );
}
