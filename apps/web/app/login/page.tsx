"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Eye, EyeOff } from "lucide-react";
import { apiFetch, ApiError, type TokenResponse, type UserProfileDTO } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";

export default function LoginPage() {
  const router = useRouter();
  const { setSession } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [studentId, setStudentId] = useState("");
  const [password, setPassword] = useState("");
  const [showPwd, setShowPwd] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setErrorMsg(null);
    try {
      if (mode === "register") {
        await apiFetch<UserProfileDTO>("/api/v1/auth/register", {
          method: "POST",
          body: JSON.stringify({
            email: email.trim(),
            full_name: fullName.trim(),
            password,
            student_or_staff_id: studentId.trim() || null,
          }),
        });
      }
      const token = await apiFetch<TokenResponse>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ email: email.trim(), password }),
      });
      setSession(token);
      router.push("/competitions");
    } catch (err) {
      if (err instanceof ApiError) {
        setErrorMsg(err.detail);
      } else {
        setErrorMsg("Không thể kết nối máy chủ xác thực.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto my-6 max-w-md rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-xs">
      <div className="flex gap-2 rounded-lg bg-[var(--color-canvas)] p-1" role="tablist" aria-label="Chế độ tài khoản">
        <button
          type="button"
          role="tab"
          aria-selected={mode === "login"}
          onClick={() => {
            setMode("login");
            setErrorMsg(null);
          }}
          className={`min-h-10 flex-1 rounded-md text-sm font-semibold ${
            mode === "login"
              ? "bg-[var(--color-brand-primary)] text-white dark:text-slate-950"
              : "text-[var(--color-text-muted)]"
          }`}
        >
          Đăng nhập
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={mode === "register"}
          onClick={() => {
            setMode("register");
            setErrorMsg(null);
          }}
          className={`min-h-10 flex-1 rounded-md text-sm font-semibold ${
            mode === "register"
              ? "bg-[var(--color-brand-primary)] text-white dark:text-slate-950"
              : "text-[var(--color-text-muted)]"
          }`}
        >
          Đăng ký SV
        </button>
      </div>

      <h1 className="mt-5 text-xl font-bold text-[var(--color-text-primary)]">
        {mode === "login" ? "Đăng nhập ACDP Portal" : "Tạo tài khoản Sinh viên HCM-UTE"}
      </h1>
      <p className="mt-1 text-xs text-[var(--color-text-muted)]">
        Lưu cuộc thi theo dõi và lịch sử hỏi đáp thể lệ RAG vào PostgreSQL 18
      </p>

      <form onSubmit={(e) => void handleSubmit(e)} className="mt-5 space-y-4">
        {mode === "register" && (
          <>
            <div>
              <label htmlFor="auth-fullname" className="block text-xs font-semibold text-[var(--color-text-primary)]">
                Họ và tên <span aria-hidden="true">*</span>
              </label>
              <input
                id="auth-fullname"
                name="name"
                type="text"
                required
                minLength={2}
                autoComplete="name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="mt-1.5 min-h-12 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-canvas)] px-3 text-sm"
              />
            </div>
            <div>
              <label htmlFor="auth-mssv" className="block text-xs font-semibold text-[var(--color-text-primary)]">
                MSSV / Mã giảng viên (tùy chọn)
              </label>
              <input
                id="auth-mssv"
                name="student_id"
                type="text"
                value={studentId}
                onChange={(e) => setStudentId(e.target.value)}
                placeholder="Ví dụ: 23133030"
                className="mt-1.5 min-h-12 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-canvas)] px-3 text-sm"
              />
            </div>
          </>
        )}

        <div>
          <label htmlFor="auth-email" className="block text-xs font-semibold text-[var(--color-text-primary)]">
            Email <span aria-hidden="true">*</span>
          </label>
          <input
            id="auth-email"
            name="email"
            type="email"
            required
            autoComplete="email"
            autoCapitalize="none"
            spellCheck={false}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1.5 min-h-12 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-canvas)] px-3 text-sm"
          />
        </div>

        <div>
          <label htmlFor="auth-password" className="block text-xs font-semibold text-[var(--color-text-primary)]">
            Mật khẩu <span aria-hidden="true">*</span>
          </label>
          <p id="pwd-hint" className="mt-0.5 text-[11px] text-[var(--color-text-muted)]">
            Tối thiểu 8 ký tự.
          </p>
          <div className="relative mt-1">
            <input
              id="auth-password"
              name="password"
              type={showPwd ? "text" : "password"}
              required
              minLength={8}
              aria-describedby="pwd-hint"
              autoComplete={mode === "login" ? "current-password" : "new-password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="min-h-12 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-canvas)] pl-3 pr-11 text-sm"
            />
            <button
              type="button"
              onClick={() => setShowPwd((p) => !p)}
              aria-pressed={showPwd}
              aria-label={showPwd ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
              className="absolute right-2 top-2 inline-flex min-h-8 min-w-8 items-center justify-center rounded-md text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]"
            >
              {showPwd ? <EyeOff className="h-4 w-4" aria-hidden="true" /> : <Eye className="h-4 w-4" aria-hidden="true" />}
            </button>
          </div>
        </div>

        {errorMsg && (
          <div
            role="alert"
            className="rounded-lg border border-[var(--color-brand-accent)]/40 bg-orange-50 px-3 py-2 text-xs text-[var(--color-brand-accent)] dark:bg-orange-950/30"
          >
            {errorMsg}
          </div>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="min-h-12 w-full rounded-lg bg-[var(--color-brand-primary)] px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-60 dark:text-slate-950"
        >
          {submitting ? "Đang xử lý..." : mode === "login" ? "Đăng nhập" : "Đăng ký & Đăng nhập"}
        </button>
      </form>
    </div>
  );
}
