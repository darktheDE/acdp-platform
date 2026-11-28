"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { AlertTriangle, Bot, ExternalLink, Lock, MessageSquarePlus, Send, Trash2 } from "lucide-react";
import {
  apiFetch,
  ApiError,
  type ChatMessageDTO,
  type ChatSessionDTO,
  type RagChatResponse,
  type RagCitationDTO,
} from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";

export interface CompetitionScopeOption {
  value: string;
  label: string;
}

interface UiMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: RagCitationDTO[];
  grounded?: boolean;
  latencyMs?: number | null;
}

const SAMPLE_PROMPTS = [
  "Cuộc thi nào đang mở cho sinh viên năm 1–2 và miễn phí tham gia?",
  "Zalo AI Challenge có cơ cấu giải thưởng và hạn nộp bài ra sao?",
  "IT Consultant Challenge yêu cầu quy mô đội thi mấy người?",
  "Những cuộc thi AI / Data nào cho phép ghép nhóm liên trường?",
];

export function CopilotWorkspace({
  competitionScopes = [],
  initialDomain = "",
  initialQuestion = "",
}: {
  competitionScopes?: CompetitionScopeOption[];
  initialDomain?: string;
  initialQuestion?: string;
}) {
  const { accessToken, user, loading: authLoading } = useAuth();
  const [sessions, setSessions] = useState<ChatSessionDTO[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<UiMessage[]>([]);
  const [domainFilter, setDomainFilter] = useState(initialDomain);
  const [input, setInput] = useState(initialQuestion);
  const [sending, setSending] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  useEffect(() => {
    if (!accessToken) {
      setSessions([]);
      return;
    }
    let active = true;
    (async () => {
      try {
        const list = await apiFetch<ChatSessionDTO[]>("/api/v1/rag/sessions", { token: accessToken });
        if (active) setSessions(list);
      } catch {
        // Non-fatal
      }
    })();
    return () => {
      active = false;
    };
  }, [accessToken]);

  const loadSession = async (sessionId: string) => {
    if (!accessToken) return;
    setErrorMsg(null);
    setActiveSessionId(sessionId);
    try {
      const rows = await apiFetch<ChatMessageDTO[]>(`/api/v1/rag/sessions/${sessionId}/messages`, {
        token: accessToken,
      });
      setMessages(
        rows.map((m) => ({
          id: m.id,
          role: m.role,
          content: m.content,
          citations: m.citations || [],
          grounded: m.role === "assistant" ? (m.citations?.length ?? 0) > 0 : undefined,
          latencyMs: m.latency_ms,
        })),
      );
    } catch {
      setErrorMsg("Không thể tải lịch sử phiên hỏi đáp.");
    }
  };

  const deleteSession = async (sessionId: string) => {
    if (!accessToken) return;
    try {
      await apiFetch<void>(`/api/v1/rag/sessions/${sessionId}`, {
        method: "DELETE",
        token: accessToken,
      });
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
      if (activeSessionId === sessionId) {
        setActiveSessionId(null);
        setMessages([]);
      }
    } catch {
      setErrorMsg("Không thể xóa phiên hỏi đáp.");
    }
  };

  const startNewChat = () => {
    setActiveSessionId(null);
    setMessages([]);
    setErrorMsg(null);
  };

  const submitQuestion = async (e?: React.FormEvent) => {
    e?.preventDefault();
    const trimmed = input.trim();
    if (trimmed.length < 2 || sending) return;

    setSending(true);
    setErrorMsg(null);
    const tempUserId = `u-${Date.now()}`;
    setMessages((prev) => [...prev, { id: tempUserId, role: "user", content: trimmed, citations: [] }]);
    setInput("");

    try {
      const res = await apiFetch<RagChatResponse>("/api/v1/rag/chat", {
        method: "POST",
        token: accessToken,
        body: JSON.stringify({
          session_id: activeSessionId,
          message: trimmed,
          domain_filter: domainFilter || null,
        }),
      });
      if (user && accessToken && !activeSessionId) {
        setActiveSessionId(res.session_id);
        const updated = await apiFetch<ChatSessionDTO[]>("/api/v1/rag/sessions", { token: accessToken });
        setSessions(updated);
      }
      setMessages((prev) => [
        ...prev,
        {
          id: `a-${Date.now()}`,
          role: "assistant",
          content: res.answer,
          citations: res.citations,
          grounded: res.grounded,
          latencyMs: res.latency_ms,
        },
      ]);
    } catch (err) {
      if (err instanceof ApiError && err.status === 429) {
        setErrorMsg(`Bạn đang hỏi quá nhanh, vui lòng chờ giây lát rồi thử lại (${err.detail}).`);
      } else if (err instanceof ApiError && err.status === 401) {
        setErrorMsg("Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.");
      } else if (err instanceof ApiError && err.status === 503) {
        setErrorMsg("Trợ lý AI đang tạm bận, vui lòng thử lại sau ít phút.");
      } else {
        setErrorMsg("Lỗi kết nối trợ lý thể lệ. Vui lòng thử lại.");
      }
    } finally {
      setSending(false);
    }
  };

  if (authLoading) {
    return <div className="h-64 animate-pulse rounded-xl bg-[var(--color-surface)]" />;
  }

  if (!user || !accessToken) {
    return (
      <div className="mx-auto my-8 max-w-lg rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 text-center">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-[var(--color-surface-subtle)] text-[var(--color-brand-primary)]">
          <Lock className="h-6 w-6" aria-hidden="true" />
        </div>
        <h2 className="mt-3 text-xl font-bold text-[var(--color-text-primary)]">
          Đăng nhập để hỏi đáp Trợ lý Thể lệ
        </h2>
        <p className="mt-2 text-sm text-[var(--color-text-muted)]">
          Đăng nhập tài khoản sinh viên để đặt câu hỏi trực tiếp về thể lệ cuộc thi, lưu lịch sử tra cứu cá nhân và sử dụng hạn mức AI miễn phí hằng ngày.
        </p>
        <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
          <Link
            href="/login"
            className="inline-flex min-h-10 items-center rounded-lg bg-[var(--color-brand-primary)] px-4 py-2 text-sm font-semibold text-white dark:text-slate-950"
          >
            Đăng nhập / Đăng ký ngay
          </Link>
          <Link
            href="/competitions"
            className="inline-flex min-h-10 items-center rounded-lg border border-[var(--color-border)] px-4 py-2 text-sm font-medium text-[var(--color-text-primary)] hover:bg-[var(--color-surface-subtle)]"
          >
            Xem danh sách cuộc thi
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="grid gap-6 lg:grid-cols-4">
      <aside className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 lg:col-span-1">
        <button
          type="button"
          onClick={startNewChat}
          className="inline-flex min-h-10 w-full items-center justify-center gap-2 rounded-lg bg-[var(--color-brand-primary)] px-3 py-2 text-sm font-semibold text-white dark:text-slate-950"
        >
          <MessageSquarePlus className="h-4 w-4" aria-hidden="true" />
          <span>Phiên hỏi đáp mới</span>
        </button>

        <div className="mt-4">
          <label htmlFor="rag-domain-scope" className="block text-xs font-semibold text-[var(--color-text-primary)]">
            Chọn cuộc thi cần hỏi
          </label>
          <select
            id="rag-domain-scope"
            value={domainFilter}
            onChange={(e) => setDomainFilter(e.target.value)}
            className="mt-1.5 min-h-10 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-canvas)] px-2.5 text-xs text-[var(--color-text-primary)]"
          >
            <option value="">Tất cả cuộc thi trong hệ thống</option>
            {competitionScopes.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </div>

        <div className="mt-5">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-[var(--color-text-muted)]">
            Lịch sử hỏi đáp ({sessions.length})
          </h2>
          {sessions.length === 0 ? (
            <p className="mt-2 text-xs text-[var(--color-text-muted)]">Chưa có phiên nào.</p>
          ) : (
            <ul className="mt-2 space-y-1.5">
              {sessions.map((s) => (
                <li key={s.id} className="flex items-center justify-between gap-1">
                  <button
                    type="button"
                    onClick={() => void loadSession(s.id)}
                    className={`min-h-9 flex-1 truncate rounded-md px-2.5 py-1.5 text-left text-xs ${
                      activeSessionId === s.id
                        ? "bg-[var(--color-surface-subtle)] font-semibold text-[var(--color-brand-primary)]"
                        : "text-[var(--color-text-primary)] hover:bg-[var(--color-surface-subtle)]"
                    }`}
                  >
                    {s.title}
                  </button>
                  <button
                    type="button"
                    onClick={() => void deleteSession(s.id)}
                    aria-label={`Xóa phiên ${s.title}`}
                    className="inline-flex min-h-8 min-w-8 items-center justify-center rounded-md text-[var(--color-text-muted)] hover:text-[var(--color-brand-accent)]"
                  >
                    <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </aside>

      <section className="flex min-h-[540px] flex-col rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5 lg:col-span-3">
        <div className="flex-1 space-y-4 overflow-y-auto pr-1">
          {messages.length === 0 && (
            <div className="rounded-xl border border-dashed border-[var(--color-border)] bg-[var(--color-canvas)] p-6 text-center">
              <Bot className="mx-auto h-9 w-9 text-[var(--color-brand-primary)]" aria-hidden="true" />
              <h2 className="mt-2 text-base font-semibold text-[var(--color-text-primary)]">
                Trợ lý Tra cứu Thể lệ Cuộc thi
              </h2>
              <p className="mx-auto mt-1 max-w-xl text-xs leading-relaxed text-[var(--color-text-muted)]">
                Câu trả lời được đối chiếu trực tiếp từ thể lệ chính thức của Ban tổ chức và luôn đính kèm đường dẫn gốc để bạn kiểm tra lại.
              </p>
              <div className="mt-4 flex flex-wrap justify-center gap-2">
                {SAMPLE_PROMPTS.map((sample) => (
                  <button
                    key={sample}
                    type="button"
                    onClick={() => setInput(sample)}
                    className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-1.5 text-left text-xs text-[var(--color-text-primary)] hover:bg-[var(--color-surface-subtle)]"
                  >
                    {sample}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m) => (
            <div
              key={m.id}
              className={`rounded-xl p-4 text-sm ${
                m.role === "user"
                  ? "ml-auto max-w-2xl bg-[var(--color-brand-primary)] text-white dark:text-slate-950"
                  : "border border-[var(--color-border)] bg-[var(--color-canvas)] text-[var(--color-text-primary)]"
              }`}
            >
              {m.role === "assistant" && m.grounded === false && (
                <div
                  role="status"
                  className="mb-3 flex items-center gap-2 rounded-lg border border-[var(--color-status-warning)]/40 bg-amber-50 px-3 py-2 text-xs font-medium text-[var(--color-status-warning)] dark:bg-amber-950/30"
                >
                  <AlertTriangle className="h-4 w-4 shrink-0" aria-hidden="true" />
                  <span>Chưa tìm thấy thông tin xác thực trong dữ liệu thể lệ hiện có. Bạn vui lòng xem thêm trên trang chính thức BTC.</span>
                </div>
              )}

              <p className="whitespace-pre-wrap leading-relaxed">{m.content}</p>

              {m.role === "assistant" && m.citations.length > 0 && (
                <div className="mt-3 border-t border-[var(--color-border)] pt-2.5">
                  <p className="mb-1.5 font-mono text-[11px] font-semibold uppercase text-[var(--color-text-muted)]">
                    Nguồn tham chiếu ({m.citations.length}) {m.latencyMs ? `· ${m.latencyMs} ms` : ""}
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {m.citations.map((c) => (
                      <a
                        key={c.url}
                        href={c.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 rounded-md border border-[var(--color-border)] bg-[var(--color-surface)] px-2.5 py-1 text-xs font-medium text-[var(--color-brand-primary)] hover:underline"
                      >
                        <span>{c.domain}</span>
                        <ExternalLink className="h-3 w-3" aria-hidden="true" />
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}

          {sending && (
            <div
              role="status"
              aria-live="polite"
              className="max-w-md rounded-xl border border-[var(--color-border)] bg-[var(--color-canvas)] p-4 text-xs text-[var(--color-text-muted)]"
            >
              Đang đối chiếu thể lệ và trích xuất nguồn xác thực...
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {errorMsg && (
          <div
            role="alert"
            className="mt-3 rounded-lg border border-[var(--color-brand-accent)]/40 bg-orange-50 px-3 py-2 text-xs text-[var(--color-brand-accent)] dark:bg-orange-950/30"
          >
            {errorMsg}
          </div>
        )}

        <form onSubmit={(e) => void submitQuestion(e)} className="mt-4 flex gap-2 border-t border-[var(--color-border)] pt-4">
          <label htmlFor="copilot-input" className="visually-hidden">
            Nhập câu hỏi về thể lệ cuộc thi
          </label>
          <input
            id="copilot-input"
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && e.nativeEvent.isComposing) {
                e.preventDefault();
              }
            }}
            placeholder="Đặt câu hỏi về điều kiện dự thi, hạn nộp, giải thưởng..."
            className="min-h-12 flex-1 rounded-lg border border-[var(--color-border)] bg-[var(--color-canvas)] px-3.5 text-sm text-[var(--color-text-primary)]"
          />
          <button
            type="submit"
            disabled={sending || input.trim().length < 2}
            aria-label="Gửi câu hỏi"
            className="inline-flex min-h-12 items-center gap-2 rounded-lg bg-[var(--color-brand-primary)] px-4 py-2 text-sm font-semibold text-white disabled:opacity-50 dark:text-slate-950"
          >
            <Send className="h-4 w-4" aria-hidden="true" />
            <span>{sending ? "Đang tra..." : "Gửi"}</span>
          </button>
        </form>
      </section>
    </div>
  );
}
