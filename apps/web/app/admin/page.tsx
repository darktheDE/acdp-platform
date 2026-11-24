"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import {
  Activity,
  Bot,
  Database,
  FileCode2,
  Lock,
  RefreshCw,
  Search,
  ShieldAlert,
  ShieldCheck,
  Unlock,
  Users,
} from "lucide-react";
import {
  apiFetch,
  ApiError,
  type AdminCacheRefreshDTO,
  type AdminTelemetryDTO,
  type AdminUserDTO,
} from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";

interface RateLimitBlockEvent {
  tier: string;
  key: string;
  limit: number;
  retry_after: number;
  timestamp: number;
}

interface OpenApiPreview {
  title: string;
  version: string;
  paths: Array<{ path: string; methods: string[] }>;
}

export default function AdminPage() {
  const { user, accessToken, loading: authLoading } = useAuth();
  const [telemetry, setTelemetry] = useState<AdminTelemetryDTO | null>(null);
  const [users, setUsers] = useState<AdminUserDTO[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [queryText, setQueryText] = useState("");
  const [roleFilter, setRoleFilter] = useState<string>("all");
  const [activeFilter, setActiveFilter] = useState<string>("all");
  const [openApiPreview, setOpenApiPreview] = useState<OpenApiPreview | null>(null);

  const loadAdminData = useCallback(async () => {
    if (!accessToken || user?.role !== "admin") return;
    setLoading(true);
    setErrorMsg(null);
    try {
      const params = new URLSearchParams();
      if (queryText.trim()) params.set("q", queryText.trim());
      if (roleFilter !== "all") params.set("role", roleFilter);
      if (activeFilter !== "all") params.set("is_active", activeFilter);

      const queryString = params.toString();
      const usersUrl = queryString ? `/api/v1/admin/users?${queryString}` : "/api/v1/admin/users";

      const [telData, userList] = await Promise.all([
        apiFetch<AdminTelemetryDTO>("/api/v1/admin/telemetry", { token: accessToken }),
        apiFetch<AdminUserDTO[]>(usersUrl, { token: accessToken }),
      ]);
      setTelemetry(telData);
      setUsers(userList);
    } catch (err) {
      if (err instanceof ApiError) {
        setErrorMsg(`Lỗi tải dữ liệu quản trị (${err.status}): ${err.detail}`);
      } else {
        setErrorMsg("Không thể kết nối Admin API.");
      }
    } finally {
      setLoading(false);
    }
  }, [accessToken, user?.role, queryText, roleFilter, activeFilter]);

  useEffect(() => {
    if (authLoading) return;
    if (!accessToken || user?.role !== "admin") {
      setLoading(false);
      return;
    }
    void loadAdminData();
  }, [authLoading, accessToken, user?.role, loadAdminData]);

  const handleCacheRefresh = async (target: "all" | "duckdb_r2" | "rag" | "rate_limit") => {
    if (!accessToken) return;
    setBusyAction(`cache-${target}`);
    setStatusMsg(null);
    setErrorMsg(null);
    try {
      const res = await apiFetch<AdminCacheRefreshDTO>("/api/v1/admin/cache/refresh", {
        method: "POST",
        token: accessToken,
        body: JSON.stringify({ target }),
      });
      setStatusMsg(
        `Đã làm mới (${res.target}) lúc ${new Date(res.refreshed_at).toLocaleTimeString("vi-VN")}.`,
      );
      await loadAdminData();
    } catch (err) {
      setErrorMsg(err instanceof ApiError ? err.detail : "Không thể làm mới cache.");
    } finally {
      setBusyAction(null);
    }
  };

  const handleUpdateUser = async (
    targetUser: AdminUserDTO,
    patch: { role?: "student" | "lecturer" | "admin"; is_active?: boolean },
  ) => {
    if (!accessToken) return;
    setBusyAction(`user-${targetUser.id}`);
    setStatusMsg(null);
    setErrorMsg(null);
    try {
      const updated = await apiFetch<AdminUserDTO>(`/api/v1/admin/users/${targetUser.id}`, {
        method: "PATCH",
        token: accessToken,
        body: JSON.stringify(patch),
      });
      setUsers((prev) => prev.map((u) => (u.id === updated.id ? updated : u)));
      setStatusMsg(
        `Đã cập nhật ${updated.email}: role=${updated.role}, trạng thái=${updated.is_active ? "Active" : "Blocked"}.`,
      );
      const telData = await apiFetch<AdminTelemetryDTO>("/api/v1/admin/telemetry", { token: accessToken });
      setTelemetry(telData);
    } catch (err) {
      setErrorMsg(err instanceof ApiError ? err.detail : "Không thể cập nhật tài khoản.");
    } finally {
      setBusyAction(null);
    }
  };

  const handleLoadAdminOpenApi = async () => {
    if (!accessToken) return;
    setBusyAction("openapi");
    setErrorMsg(null);
    try {
      const schema = await apiFetch<{
        info?: { title?: string; version?: string };
        paths?: Record<string, Record<string, unknown>>;
      }>("/api/v1/admin/openapi.json", { token: accessToken });
      const paths = Object.entries(schema.paths || {}).map(([path, methodsObj]) => ({
        path,
        methods: Object.keys(methodsObj).map((m) => m.toUpperCase()),
      }));
      setOpenApiPreview({
        title: schema.info?.title || "ACDP Serving Gateway",
        version: schema.info?.version || "1.0.0",
        paths,
      });
    } catch (err) {
      setErrorMsg(err instanceof ApiError ? err.detail : "Không thể tải Admin OpenAPI schema.");
    } finally {
      setBusyAction(null);
    }
  };

  if (authLoading || loading) {
    return <div className="h-64 animate-pulse rounded-xl bg-[var(--color-surface)]" />;
  }

  if (!user || !accessToken) {
    return (
      <div className="mx-auto my-8 max-w-lg rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 text-center">
        <ShieldCheck className="mx-auto h-10 w-10 text-[var(--color-brand-primary)]" aria-hidden="true" />
        <h1 className="mt-3 text-xl font-bold text-[var(--color-text-primary)]">
          Trung tâm Quản trị ACDP
        </h1>
        <p className="mt-2 text-sm text-[var(--color-text-muted)]">
          Vui lòng đăng nhập bằng tài khoản Quản trị viên (ADMIN_EMAILS) để truy cập bảng điều khiển.
        </p>
        <Link
          href="/login"
          className="mt-4 inline-flex min-h-10 items-center rounded-lg bg-[var(--color-brand-primary)] px-4 py-2 text-sm font-semibold text-white dark:text-slate-950"
        >
          Đăng nhập Quản trị
        </Link>
      </div>
    );
  }

  if (user.role !== "admin") {
    return (
      <div className="mx-auto my-8 max-w-lg rounded-xl border border-[var(--color-brand-accent)]/40 bg-[var(--color-surface)] p-6 text-center">
        <ShieldAlert className="mx-auto h-10 w-10 text-[var(--color-brand-accent)]" aria-hidden="true" />
        <h1 className="mt-3 text-xl font-bold text-[var(--color-text-primary)]">
          403 Forbidden — Không đủ quyền truy cập
        </h1>
        <p className="mt-2 text-sm text-[var(--color-text-muted)]">
          Tài khoản <span className="font-mono font-semibold">{user.email}</span> hiện có vai trò{" "}
          <span className="font-mono uppercase">{user.role}</span>. Khu vực này chỉ dành cho Quản trị viên.
        </p>
        <Link
          href="/dashboard"
          className="mt-4 inline-flex min-h-10 items-center rounded-lg bg-[var(--color-brand-primary)] px-4 py-2 text-sm font-semibold text-white dark:text-slate-950"
        >
          Quay về Dashboard
        </Link>
      </div>
    );
  }

  const rateStats = telemetry?.rate_limit as
    | {
        total_checked?: number;
        blocked_ai?: number;
        blocked_auth?: number;
        blocked_public?: number;
        recent_blocks?: RateLimitBlockEvent[];
      }
    | undefined;
  const goldStats = telemetry?.gold_mart_cache as
    | { cached_entries?: number; hit_rate_pct?: number; ttl_seconds?: number }
    | undefined;
  const ragStats = telemetry?.rag_cache as
    | { cached_entries?: number; hit_rate_pct?: number; ttl_seconds?: number }
    | undefined;
  const recentBlocks = rateStats?.recent_blocks || [];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-1 text-xs font-semibold text-[var(--color-brand-primary)]">
            <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
            <span>RBAC Admin Control Center · Gate G5/G6</span>
          </div>
          <h1 className="mt-2 text-2xl font-bold tracking-tight text-[var(--color-text-primary)] sm:text-3xl">
            Quản trị Hệ thống & Kill-Switch
          </h1>
          <p className="mt-1 text-sm text-[var(--color-text-muted)]">
            Quản lý tài khoản RBAC, khóa tài khoản spam AI, làm mới DuckDB R2/RAG cache và giám sát Rate Limiter
          </p>
        </div>

        <button
          type="button"
          onClick={() => void loadAdminData()}
          disabled={loading}
          className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3.5 py-2 text-sm font-medium text-[var(--color-text-primary)] hover:bg-[var(--color-surface-subtle)]"
        >
          <RefreshCw className="h-4 w-4" aria-hidden="true" />
          <span>Tải lại Telemetry</span>
        </button>
      </div>

      {statusMsg && (
        <div
          role="status"
          className="rounded-lg border border-[var(--color-status-success)]/40 bg-emerald-50 px-4 py-2.5 text-sm text-[var(--color-status-success)] dark:bg-emerald-950/30"
        >
          {statusMsg}
        </div>
      )}

      {errorMsg && (
        <div
          role="alert"
          className="rounded-lg border border-[var(--color-brand-accent)]/40 bg-orange-50 px-4 py-2.5 text-sm text-[var(--color-brand-accent)] dark:bg-orange-950/30"
        >
          {errorMsg}
        </div>
      )}

      <section aria-label="Chỉ số vận hành" className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
          <div className="flex items-center justify-between text-xs font-medium text-[var(--color-text-muted)]">
            <span>Tài khoản OLTP</span>
            <Users className="h-4 w-4 text-[var(--color-brand-primary)]" aria-hidden="true" />
          </div>
          <p className="mt-2 font-mono text-2xl font-bold tabular-nums text-[var(--color-text-primary)]">
            {telemetry?.users_summary.total_users ?? 0}
          </p>
          <p className="mt-1 text-xs text-[var(--color-text-muted)]">
            Active: {telemetry?.users_summary.active_users ?? 0} · Blocked: {telemetry?.users_summary.blocked_users ?? 0}
          </p>
        </div>

        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
          <div className="flex items-center justify-between text-xs font-medium text-[var(--color-text-muted)]">
            <span>Rate Limiter (429)</span>
            <Activity className="h-4 w-4 text-[var(--color-brand-accent)]" aria-hidden="true" />
          </div>
          <p className="mt-2 font-mono text-2xl font-bold tabular-nums text-[var(--color-text-primary)]">
            {(rateStats?.blocked_ai ?? 0) + (rateStats?.blocked_auth ?? 0) + (rateStats?.blocked_public ?? 0)}
          </p>
          <p className="mt-1 text-xs text-[var(--color-text-muted)]">
            AI: {rateStats?.blocked_ai ?? 0} · Auth: {rateStats?.blocked_auth ?? 0} · Checked: {rateStats?.total_checked ?? 0}
          </p>
        </div>

        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
          <div className="flex items-center justify-between text-xs font-medium text-[var(--color-text-muted)]">
            <span>DuckDB R2 Gold Cache</span>
            <Database className="h-4 w-4 text-[var(--color-status-success)]" aria-hidden="true" />
          </div>
          <p className="mt-2 font-mono text-2xl font-bold tabular-nums text-[var(--color-text-primary)]">
            {goldStats?.hit_rate_pct ?? 0}%
          </p>
          <p className="mt-1 text-xs text-[var(--color-text-muted)]">
            Entries: {goldStats?.cached_entries ?? 0} · TTL: {goldStats?.ttl_seconds ?? 600}s
          </p>
        </div>

        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
          <div className="flex items-center justify-between text-xs font-medium text-[var(--color-text-muted)]">
            <span>RAG Response Cache</span>
            <Bot className="h-4 w-4 text-[var(--color-status-warning)]" aria-hidden="true" />
          </div>
          <p className="mt-2 font-mono text-2xl font-bold tabular-nums text-[var(--color-text-primary)]">
            {ragStats?.hit_rate_pct ?? 0}%
          </p>
          <p className="mt-1 text-xs text-[var(--color-text-muted)]">
            Entries: {ragStats?.cached_entries ?? 0} · TTL: {ragStats?.ttl_seconds ?? 300}s
          </p>
        </div>
      </section>

      <section className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
        <h2 className="text-base font-semibold text-[var(--color-text-primary)]">
          Thao tác Vận hành & Admin API Docs (Công khai `/docs` đã tắt)
        </h2>
        <div className="mt-3 flex flex-wrap gap-2.5">
          <button
            type="button"
            disabled={busyAction !== null}
            onClick={() => void handleCacheRefresh("all")}
            className="inline-flex min-h-10 items-center gap-2 rounded-lg bg-[var(--color-brand-primary)] px-4 py-2 text-sm font-semibold text-white disabled:opacity-60 dark:text-slate-950"
          >
            <RefreshCw className="h-4 w-4" aria-hidden="true" />
            <span>{busyAction === "cache-all" ? "Đang làm mới..." : "Làm mới DuckDB R2 & RAG Cache"}</span>
          </button>

          <button
            type="button"
            disabled={busyAction !== null}
            onClick={() => void handleCacheRefresh("rag")}
            className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-[var(--color-border)] px-3.5 py-2 text-sm font-medium text-[var(--color-text-primary)] hover:bg-[var(--color-surface-subtle)] disabled:opacity-60"
          >
            <span>Xóa RAG Cache</span>
          </button>

          <button
            type="button"
            disabled={busyAction !== null}
            onClick={() => void handleCacheRefresh("rate_limit")}
            className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-[var(--color-border)] px-3.5 py-2 text-sm font-medium text-[var(--color-text-primary)] hover:bg-[var(--color-surface-subtle)] disabled:opacity-60"
          >
            <span>Reset Bộ đếm Rate Limit</span>
          </button>

          <button
            type="button"
            disabled={busyAction !== null}
            onClick={() => void handleLoadAdminOpenApi()}
            className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-[var(--color-border)] px-3.5 py-2 text-sm font-medium text-[var(--color-brand-primary)] hover:bg-[var(--color-surface-subtle)] disabled:opacity-60"
          >
            <FileCode2 className="h-4 w-4" aria-hidden="true" />
            <span>{busyAction === "openapi" ? "Đang tải..." : "Kiểm tra Admin OpenAPI (/api/v1/admin/openapi.json)"}</span>
          </button>
        </div>

        {openApiPreview && (
          <div className="mt-4 rounded-lg border border-[var(--color-border)] bg-[var(--color-canvas)] p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-xs font-semibold text-[var(--color-text-primary)]">
                {openApiPreview.title} v{openApiPreview.version} · {openApiPreview.paths.length} API paths (Protected)
              </p>
              <button
                type="button"
                onClick={() => setOpenApiPreview(null)}
                className="text-xs text-[var(--color-text-muted)] hover:underline"
              >
                Ẩn
              </button>
            </div>
            <div className="mt-2 grid gap-1.5 sm:grid-cols-2">
              {openApiPreview.paths.map((item) => (
                <div
                  key={item.path}
                  className="flex items-center justify-between rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-2.5 py-1.5 font-mono text-[11px]"
                >
                  <span className="truncate text-[var(--color-text-primary)]">{item.path}</span>
                  <span className="ml-2 shrink-0 text-[var(--color-brand-primary)]">{item.methods.join(", ")}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </section>

      <section className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-base font-semibold text-[var(--color-text-primary)]">
            Quản lý Người dùng & Phân quyền RBAC ({users.length})
          </h2>
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative">
              <Search className="pointer-events-none absolute left-2.5 top-2.5 h-4 w-4 text-[var(--color-text-muted)]" aria-hidden="true" />
              <input
                type="text"
                value={queryText}
                onChange={(e) => setQueryText(e.target.value)}
                placeholder="Tìm email, họ tên, MSSV..."
                aria-label="Tìm người dùng"
                className="min-h-9 rounded-lg border border-[var(--color-border)] bg-[var(--color-canvas)] pl-8 pr-3 text-xs text-[var(--color-text-primary)]"
              />
            </div>
            <select
              aria-label="Lọc theo vai trò"
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              className="min-h-9 rounded-lg border border-[var(--color-border)] bg-[var(--color-canvas)] px-2.5 text-xs text-[var(--color-text-primary)]"
            >
              <option value="all">Tất cả vai trò</option>
              <option value="student">Student</option>
              <option value="lecturer">Lecturer</option>
              <option value="admin">Admin</option>
            </select>
            <select
              aria-label="Lọc theo trạng thái"
              value={activeFilter}
              onChange={(e) => setActiveFilter(e.target.value)}
              className="min-h-9 rounded-lg border border-[var(--color-border)] bg-[var(--color-canvas)] px-2.5 text-xs text-[var(--color-text-primary)]"
            >
              <option value="all">Tất cả trạng thái</option>
              <option value="true">Đang hoạt động</option>
              <option value="false">Đã khóa</option>
            </select>
          </div>
        </div>

        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[680px] text-left text-xs">
            <thead>
              <tr className="border-b border-[var(--color-border)] text-[var(--color-text-muted)]">
                <th className="py-2 pr-3 font-semibold">Người dùng</th>
                <th className="py-2 pr-3 font-semibold">MSSV / Mã</th>
                <th className="py-2 pr-3 font-semibold">Vai trò RBAC</th>
                <th className="py-2 pr-3 font-semibold">Trạng thái</th>
                <th className="py-2 text-right font-semibold">Hành động</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--color-border)]">
              {users.map((u) => {
                const isSelf = u.id === user.id;
                const isBusy = busyAction === `user-${u.id}`;
                return (
                  <tr key={u.id}>
                    <td className="py-2.5 pr-3">
                      <p className="font-semibold text-[var(--color-text-primary)]">
                        {u.full_name} {isSelf && <span className="font-mono text-[10px] text-[var(--color-brand-primary)]">(Bạn)</span>}
                      </p>
                      <p className="font-mono text-[11px] text-[var(--color-text-muted)]">{u.email}</p>
                    </td>
                    <td className="py-2.5 pr-3 font-mono text-[var(--color-text-muted)]">
                      {u.student_or_staff_id || "—"}
                    </td>
                    <td className="py-2.5 pr-3">
                      <select
                        aria-label={`Vai trò của ${u.email}`}
                        disabled={isSelf || isBusy}
                        value={u.role}
                        onChange={(e) =>
                          void handleUpdateUser(u, {
                            role: e.target.value as "student" | "lecturer" | "admin",
                          })
                        }
                        className="min-h-8 rounded-md border border-[var(--color-border)] bg-[var(--color-canvas)] px-2 text-xs text-[var(--color-text-primary)] disabled:opacity-60"
                      >
                        <option value="student">student</option>
                        <option value="lecturer">lecturer</option>
                        <option value="admin">admin</option>
                      </select>
                    </td>
                    <td className="py-2.5 pr-3">
                      <span
                        className={`inline-flex items-center rounded-full px-2 py-0.5 font-mono text-[11px] font-medium ${
                          u.is_active
                            ? "bg-emerald-50 text-[var(--color-status-success)] dark:bg-emerald-950/30"
                            : "bg-orange-50 text-[var(--color-brand-accent)] dark:bg-orange-950/30"
                        }`}
                      >
                        {u.is_active ? "Active" : "Blocked"}
                      </span>
                    </td>
                    <td className="py-2.5 text-right">
                      <button
                        type="button"
                        disabled={isSelf || isBusy}
                        onClick={() => void handleUpdateUser(u, { is_active: !u.is_active })}
                        className={`inline-flex min-h-8 items-center gap-1 rounded-md border px-2.5 py-1 text-xs font-medium disabled:opacity-40 ${
                          u.is_active
                            ? "border-[var(--color-brand-accent)]/40 text-[var(--color-brand-accent)] hover:bg-orange-50 dark:hover:bg-orange-950/30"
                            : "border-[var(--color-status-success)]/40 text-[var(--color-status-success)] hover:bg-emerald-50 dark:hover:bg-emerald-950/30"
                        }`}
                      >
                        {u.is_active ? (
                          <>
                            <Lock className="h-3.5 w-3.5" aria-hidden="true" />
                            <span>Khóa</span>
                          </>
                        ) : (
                          <>
                            <Unlock className="h-3.5 w-3.5" aria-hidden="true" />
                            <span>Mở khóa</span>
                          </>
                        )}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      <section className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
        <h2 className="text-base font-semibold text-[var(--color-text-primary)]">
          Nhật ký Chặn Rate Limit Gần nhất ({recentBlocks.length})
        </h2>
        {recentBlocks.length === 0 ? (
          <p className="mt-2 text-xs text-[var(--color-text-muted)]">
            Chưa ghi nhận sự kiện chặn 429 nào trong phiên chạy hiện tại.
          </p>
        ) : (
          <div className="mt-3 overflow-x-auto">
            <table className="w-full min-w-[560px] text-left text-xs">
              <thead>
                <tr className="border-b border-[var(--color-border)] text-[var(--color-text-muted)]">
                  <th className="py-2 pr-3 font-semibold">Tier</th>
                  <th className="py-2 pr-3 font-semibold">Key (User/IP)</th>
                  <th className="py-2 pr-3 font-semibold">Limit</th>
                  <th className="py-2 pr-3 font-semibold">Retry-After</th>
                  <th className="py-2 font-semibold">Thời điểm</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--color-border)] font-mono">
                {recentBlocks.map((ev, idx) => (
                  <tr key={`${ev.tier}-${ev.key}-${idx}`}>
                    <td className="py-2 pr-3 text-[var(--color-brand-accent)]">{ev.tier}</td>
                    <td className="py-2 pr-3 text-[var(--color-text-primary)]">{ev.key}</td>
                    <td className="py-2 pr-3">{ev.limit}</td>
                    <td className="py-2 pr-3">{ev.retry_after}s</td>
                    <td className="py-2 text-[var(--color-text-muted)]">
                      {new Date(ev.timestamp * 1000).toLocaleString("vi-VN")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
