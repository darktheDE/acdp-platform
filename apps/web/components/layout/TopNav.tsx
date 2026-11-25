"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useRef, useState } from "react";
import { Bookmark, Bot, Compass, LayoutDashboard, LogIn, LogOut, Menu, ShieldCheck, X } from "lucide-react";
import { LogoFull } from "@/components/brand/AcdpLogo";
import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { useAuth } from "@/lib/auth-context";

const BASE_NAV_ITEMS = [
  { href: "/dashboard", label: "Thống kê", icon: LayoutDashboard },
  { href: "/competitions", label: "Khám phá", icon: Compass },
  { href: "/copilot", label: "Trợ lý Thể lệ", icon: Bot },
  { href: "/bookmarks", label: "Đã lưu", icon: Bookmark },
];

export function TopNav() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const navItems =
    user?.role === "admin"
      ? [...BASE_NAV_ITEMS, { href: "/admin", label: "Quản trị", icon: ShieldCheck }]
      : BASE_NAV_ITEMS;

  const openDrawer = () => {
    dialogRef.current?.showModal();
    setDrawerOpen(true);
  };

  const closeDrawer = () => {
    dialogRef.current?.close();
    setDrawerOpen(false);
  };

  return (
    <header className="sticky top-0 z-30 border-b border-[var(--color-border)] bg-[var(--color-surface)]/95 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3 sm:px-6 lg:px-8">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={openDrawer}
            aria-label="Mở menu điều hướng"
            aria-expanded={drawerOpen}
            aria-controls="mobile-nav-drawer"
            className="inline-flex min-h-9 min-w-9 items-center justify-center rounded-lg border border-[var(--color-border)] text-[var(--color-text-primary)] md:hidden focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-brand-primary)]"
          >
            <Menu className="h-5 w-5" aria-hidden="true" />
          </button>
          <Link href="/" className="rounded-md focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[var(--color-brand-primary)]">
            <LogoFull />
          </Link>
        </div>

        <nav aria-label="Chính" className="hidden items-center gap-1 md:flex">
          {navItems.map((item) => {
            const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={`inline-flex min-h-9 items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-brand-primary)] ${
                  active
                    ? "bg-[var(--color-brand-primary)] text-white dark:text-slate-950"
                    : "text-[var(--color-text-muted)] hover:bg-[var(--color-surface-subtle)] hover:text-[var(--color-text-primary)]"
                }`}
              >
                <Icon className="h-4 w-4" aria-hidden="true" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="flex items-center gap-2">
          <ThemeToggle />
          {user ? (
            <div className="flex items-center gap-2">
              <span className="hidden items-center gap-1.5 text-xs font-medium text-[var(--color-text-muted)] sm:inline-flex">
                <span>{user.full_name}</span>
                <span className="rounded bg-[var(--color-surface-subtle)] px-1.5 py-0.5 font-mono text-[10px] uppercase text-[var(--color-brand-primary)]">
                  {user.role}
                </span>
              </span>
              <button
                type="button"
                onClick={() => void logout()}
                aria-label="Đăng xuất"
                className="inline-flex min-h-9 items-center gap-1.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-1.5 text-sm font-medium text-[var(--color-text-primary)] hover:bg-[var(--color-surface-subtle)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-brand-primary)]"
              >
                <LogOut className="h-4 w-4" aria-hidden="true" />
                <span className="hidden sm:inline">Thoát</span>
              </button>
            </div>
          ) : (
            <Link
              href="/login"
              className="inline-flex min-h-9 items-center gap-1.5 rounded-lg bg-[var(--color-brand-primary)] px-3.5 py-1.5 text-sm font-medium text-white transition-opacity hover:opacity-90 dark:text-slate-950 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-brand-primary)]"
            >
              <LogIn className="h-4 w-4" aria-hidden="true" />
              <span>Đăng nhập</span>
            </Link>
          )}
        </div>
      </div>

      <dialog
        ref={dialogRef}
        id="mobile-nav-drawer"
        aria-label="Menu điều hướng di động"
        onCancel={() => setDrawerOpen(false)}
        onClick={(e) => {
          if (e.target === dialogRef.current) closeDrawer();
        }}
        className="m-0 h-dvh max-h-none w-72 max-w-[80vw] border-r border-[var(--color-border)] bg-[var(--color-surface)] p-0 text-[var(--color-text-primary)] backdrop:bg-black/50 overscroll-contain"
      >
        <div className="flex items-center justify-between border-b border-[var(--color-border)] px-4 py-3">
          <LogoFull />
          <button
            type="button"
            onClick={closeDrawer}
            aria-label="Đóng menu"
            className="inline-flex min-h-9 min-w-9 items-center justify-center rounded-lg border border-[var(--color-border)]"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>
        <nav aria-label="Di động" className="flex flex-col gap-1 p-3">
          {navItems.map((item) => {
            const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={closeDrawer}
                aria-current={active ? "page" : undefined}
                className={`inline-flex min-h-11 items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium ${
                  active
                    ? "bg-[var(--color-brand-primary)] text-white dark:text-slate-950"
                    : "text-[var(--color-text-primary)] hover:bg-[var(--color-surface-subtle)]"
                }`}
              >
                <Icon className="h-4 w-4" aria-hidden="true" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </dialog>
    </header>
  );
}
