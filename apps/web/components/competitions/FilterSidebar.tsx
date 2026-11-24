"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useRef, useState } from "react";
import { Filter, RotateCcw, Search, X } from "lucide-react";

const DOMAIN_OPTIONS = [
  { slug: "", label: "Tất cả lĩnh vực" },
  { slug: "ai-data-science", label: "AI & Data Science" },
  { slug: "software-web-mobile", label: "Software, Web & Mobile" },
  { slug: "web3-blockchain-fintech", label: "Web3, Blockchain & FinTech" },
  { slug: "security-iot-embedded", label: "Security, IoT & Embedded" },
  { slug: "startup-design-interdisciplinary", label: "Startup, Design & Interdisciplinary" },
];

const MODE_OPTIONS = [
  { value: "", label: "Tất cả hình thức" },
  { value: "Online", label: "Online" },
  { value: "Offline", label: "Offline" },
  { value: "Hybrid", label: "Hybrid" },
];

function FilterForm({ onDone }: { onDone?: () => void }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [q, setQ] = useState(searchParams.get("q") || "");
  const [domain, setDomain] = useState(searchParams.get("domain") || "");
  const [mode, setMode] = useState(searchParams.get("mode") || "");
  const [isFree, setIsFree] = useState(searchParams.get("is_free") === "true");

  const applyFilters = (e: React.FormEvent) => {
    e.preventDefault();
    const params = new URLSearchParams();
    if (q.trim()) params.set("q", q.trim());
    if (domain) params.set("domain", domain);
    if (mode) params.set("mode", mode);
    if (isFree) params.set("is_free", "true");
    const qs = params.toString();
    router.push(qs ? `/competitions?${qs}` : "/competitions");
    onDone?.();
  };

  const resetFilters = () => {
    setQ("");
    setDomain("");
    setMode("");
    setIsFree(false);
    router.push("/competitions");
    onDone?.();
  };

  return (
    <search>
      <form onSubmit={applyFilters} className="space-y-4">
        <div>
          <label htmlFor="filter-q" className="block text-xs font-semibold text-[var(--color-text-primary)]">
            Tìm kiếm cuộc thi
          </label>
          <div className="relative mt-1.5">
            <Search className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-[var(--color-text-muted)]" aria-hidden="true" />
            <input
              id="filter-q"
              name="q"
              type="search"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Tên cuộc thi, từ khóa..."
              className="min-h-10 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-canvas)] pl-9 pr-3 text-sm text-[var(--color-text-primary)]"
            />
          </div>
        </div>

        <div>
          <label htmlFor="filter-domain" className="block text-xs font-semibold text-[var(--color-text-primary)]">
            Nhóm lĩnh vực
          </label>
          <select
            id="filter-domain"
            name="domain"
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            className="mt-1.5 min-h-10 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-canvas)] px-3 text-sm text-[var(--color-text-primary)]"
          >
            {DOMAIN_OPTIONS.map((opt) => (
              <option key={opt.slug || "all"} value={opt.slug}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="filter-mode" className="block text-xs font-semibold text-[var(--color-text-primary)]">
            Hình thức tổ chức
          </label>
          <select
            id="filter-mode"
            name="mode"
            value={mode}
            onChange={(e) => setMode(e.target.value)}
            className="mt-1.5 min-h-10 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-canvas)] px-3 text-sm text-[var(--color-text-primary)]"
          >
            {MODE_OPTIONS.map((opt) => (
              <option key={opt.value || "all"} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2 pt-1">
          <input
            id="filter-free"
            name="is_free"
            type="checkbox"
            checked={isFree}
            onChange={(e) => setIsFree(e.target.checked)}
            className="h-4 w-4 accent-[var(--color-brand-primary)]"
          />
          <label htmlFor="filter-free" className="text-sm text-[var(--color-text-primary)]">
            Chỉ hiện cuộc thi miễn phí
          </label>
        </div>

        <div className="flex gap-2 pt-2">
          <button
            type="submit"
            className="min-h-10 flex-1 rounded-lg bg-[var(--color-brand-primary)] px-3 py-2 text-sm font-medium text-white dark:text-slate-950"
          >
            Áp dụng
          </button>
          <button
            type="button"
            onClick={resetFilters}
            aria-label="Xóa toàn bộ bộ lọc"
            className="inline-flex min-h-10 items-center justify-center rounded-lg border border-[var(--color-border)] px-3 text-sm text-[var(--color-text-primary)] hover:bg-[var(--color-surface-subtle)]"
          >
            <RotateCcw className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>
      </form>
    </search>
  );
}

export function FilterSidebar() {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [open, setOpen] = useState(false);

  const openModal = () => {
    dialogRef.current?.showModal();
    setOpen(true);
  };

  const closeModal = () => {
    dialogRef.current?.close();
    setOpen(false);
  };

  return (
    <>
      <div className="lg:hidden">
        <button
          type="button"
          onClick={openModal}
          aria-expanded={open}
          aria-controls="mobile-filter-drawer"
          className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2 text-sm font-medium text-[var(--color-text-primary)]"
        >
          <Filter className="h-4 w-4" aria-hidden="true" />
          <span>Bộ lọc cuộc thi</span>
        </button>
      </div>

      <aside
        aria-label="Bộ lọc cuộc thi"
        className="hidden w-72 shrink-0 self-start rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5 lg:block"
      >
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-[var(--color-text-muted)]">
          Bộ lọc đa chiều
        </h2>
        <FilterForm />
      </aside>

      <dialog
        ref={dialogRef}
        id="mobile-filter-drawer"
        aria-label="Bộ lọc cuộc thi di động"
        onCancel={() => setOpen(false)}
        onClick={(e) => {
          if (e.target === dialogRef.current) closeModal();
        }}
        className="m-0 h-dvh max-h-none w-80 max-w-[85vw] border-r border-[var(--color-border)] bg-[var(--color-surface)] p-5 text-[var(--color-text-primary)] backdrop:bg-black/50 overscroll-contain"
      >
        <div className="mb-4 flex items-center justify-between border-b border-[var(--color-border)] pb-3">
          <h2 className="text-base font-semibold">Bộ lọc cuộc thi</h2>
          <button
            type="button"
            onClick={closeModal}
            aria-label="Đóng bộ lọc"
            className="inline-flex min-h-9 min-w-9 items-center justify-center rounded-lg border border-[var(--color-border)]"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>
        <FilterForm onDone={closeModal} />
      </dialog>
    </>
  );
}
