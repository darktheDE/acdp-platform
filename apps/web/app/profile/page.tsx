"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import {
  Check,
  Copy,
  ExternalLink,
  FileText,
  FileUp,
  Github,
  Linkedin,
  Plus,
  Save,
  Sparkles,
  Trash2,
  UserCircle,
  X,
} from "lucide-react";
import {
  apiFetch,
  apiFetchBlob,
  ApiError,
  type ProfileUpdateRequest,
  type StudentProfileDTO,
} from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";

const SUGGESTED_SKILLS = [
  "Python",
  "SQL",
  "Data Engineering",
  "Machine Learning",
  "FastAPI",
  "Next.js",
  "UI/UX",
  "Pitching",
  "Cybersecurity",
  "Cloud / Docker",
];

const SUGGESTED_ROLES = [
  "Team Leader",
  "Data Engineer",
  "AI / ML Engineer",
  "Backend Developer",
  "Frontend / UI-UX",
  "Business & Pitching",
];

const HCMUTE_MAJORS = [
  "Kỹ thuật Dữ liệu",
  "Công nghệ Thông tin",
  "Trí tuệ Nhân tạo",
  "An toàn Thông tin",
  "Kỹ thuật Phần mềm",
  "Hệ thống Thông tin",
];

function formatBytes(bytes: number | null | undefined): string {
  if (!bytes || bytes <= 0) return "0 KB";
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function ProfileWorkspace() {
  const searchParams = useSearchParams();
  const isWelcome = searchParams.get("welcome") === "1";
  const { user, accessToken, loading: authLoading, updateUserLocal } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [profile, setProfile] = useState<StudentProfileDTO | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploadingCv, setUploadingCv] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [copiedSummary, setCopiedSummary] = useState(false);

  const [fullName, setFullName] = useState("");
  const [studentId, setStudentId] = useState("");
  const [faculty, setFaculty] = useState("Khoa Công nghệ Thông tin");
  const [major, setMajor] = useState("");
  const [academicYear, setAcademicYear] = useState("");
  const [phone, setPhone] = useState("");
  const [bio, setBio] = useState("");
  const [skills, setSkills] = useState<string[]>([]);
  const [skillInput, setSkillInput] = useState("");
  const [preferredRoles, setPreferredRoles] = useState<string[]>([]);
  const [achievementsSummary, setAchievementsSummary] = useState("");
  const [cvUrl, setCvUrl] = useState("");
  const [githubUrl, setGithubUrl] = useState("");
  const [linkedinUrl, setLinkedinUrl] = useState("");
  const [isOpenToTeam, setIsOpenToTeam] = useState(true);

  const applyDtoToForm = (data: StudentProfileDTO) => {
    setProfile(data);
    setFullName(data.full_name || "");
    setStudentId(data.student_or_staff_id || "");
    setFaculty(data.faculty || "Khoa Công nghệ Thông tin");
    setMajor(data.major || "");
    setAcademicYear(data.academic_year || "");
    setPhone(data.phone || "");
    setBio(data.bio || "");
    setSkills(data.skills || []);
    setPreferredRoles(data.preferred_roles || []);
    setAchievementsSummary(data.achievements_summary || "");
    setCvUrl(data.cv_url || "");
    setGithubUrl(data.github_url || "");
    setLinkedinUrl(data.linkedin_url || "");
    setIsOpenToTeam(data.is_open_to_team ?? true);
  };

  useEffect(() => {
    if (authLoading) return;
    if (!accessToken) {
      setLoading(false);
      return;
    }
    let active = true;
    (async () => {
      try {
        const data = await apiFetch<StudentProfileDTO>("/api/v1/profile/me", { token: accessToken });
        if (active) applyDtoToForm(data);
      } catch {
        if (active) setErrorMsg("Không thể tải hồ sơ cá nhân.");
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [accessToken, authLoading]);

  const addSkill = (raw: string) => {
    const trimmed = raw.trim();
    if (!trimmed) return;
    if (skills.some((s) => s.toLowerCase() === trimmed.toLowerCase())) {
      setSkillInput("");
      return;
    }
    if (skills.length >= 20) {
      setErrorMsg("Tối đa 20 kỹ năng trong Mini-CV.");
      return;
    }
    setSkills((prev) => [...prev, trimmed]);
    setSkillInput("");
    setErrorMsg(null);
  };

  const removeSkill = (target: string) => {
    setSkills((prev) => prev.filter((s) => s !== target));
  };

  const toggleRole = (roleLabel: string) => {
    setPreferredRoles((prev) => {
      if (prev.includes(roleLabel)) {
        return prev.filter((r) => r !== roleLabel);
      }
      if (prev.length >= 6) {
        setErrorMsg("Chọn tối đa 6 vai trò thi đấu.");
        return prev;
      }
      setErrorMsg(null);
      return [...prev, roleLabel];
    });
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!accessToken) return;
    setSaving(true);
    setStatusMsg(null);
    setErrorMsg(null);

    const payload: ProfileUpdateRequest = {
      full_name: fullName.trim() || null,
      student_or_staff_id: studentId.trim() || null,
      faculty: faculty.trim() || null,
      major: major.trim() || null,
      academic_year: academicYear.trim() || null,
      phone: phone.trim() || null,
      bio: bio.trim() || null,
      skills,
      preferred_roles: preferredRoles,
      achievements_summary: achievementsSummary.trim() || null,
      cv_url: cvUrl.trim() || null,
      github_url: githubUrl.trim() || null,
      linkedin_url: linkedinUrl.trim() || null,
      is_open_to_team: isOpenToTeam,
    };

    try {
      const updated = await apiFetch<StudentProfileDTO>("/api/v1/profile/me", {
        method: "PUT",
        token: accessToken,
        body: JSON.stringify(payload),
      });
      applyDtoToForm(updated);
      updateUserLocal({
        full_name: updated.full_name,
        student_or_staff_id: updated.student_or_staff_id,
      });
      setStatusMsg("Đã lưu hồ sơ Mini-CV thành công.");
    } catch (err) {
      setErrorMsg(err instanceof ApiError ? err.detail : "Không thể lưu hồ sơ. Vui lòng thử lại.");
    } finally {
      setSaving(false);
    }
  };

  const handleUploadCvPdf = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !accessToken) return;
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setErrorMsg("Chỉ chấp nhận tệp định dạng PDF.");
      e.target.value = "";
      return;
    }
    if (file.size > 2 * 1024 * 1024) {
      setErrorMsg("Tệp PDF vượt quá giới hạn 2 MB.");
      e.target.value = "";
      return;
    }

    setUploadingCv(true);
    setStatusMsg(null);
    setErrorMsg(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const updated = await apiFetch<StudentProfileDTO>("/api/v1/profile/me/cv", {
        method: "POST",
        token: accessToken,
        body: formData,
      });
      applyDtoToForm(updated);
      setStatusMsg(`Đã tải lên CV "${updated.cv_filename ?? file.name}".`);
    } catch (err) {
      setErrorMsg(err instanceof ApiError ? err.detail : "Tải lên tệp PDF thất bại.");
    } finally {
      setUploadingCv(false);
      e.target.value = "";
    }
  };

  const handleDeleteCvPdf = async () => {
    if (!accessToken) return;
    setUploadingCv(true);
    setStatusMsg(null);
    setErrorMsg(null);
    try {
      const updated = await apiFetch<StudentProfileDTO>("/api/v1/profile/me/cv", {
        method: "DELETE",
        token: accessToken,
      });
      applyDtoToForm(updated);
      setStatusMsg("Đã gỡ tệp PDF CV đã tải lên.");
    } catch (err) {
      setErrorMsg(err instanceof ApiError ? err.detail : "Không thể gỡ tệp PDF.");
    } finally {
      setUploadingCv(false);
    }
  };

  const handlePreviewUploadedCv = async () => {
    if (!accessToken || !profile?.cv_download_path) return;
    try {
      const blob = await apiFetchBlob(profile.cv_download_path, { token: accessToken });
      const blobUrl = URL.createObjectURL(blob);
      window.open(blobUrl, "_blank", "noopener,noreferrer");
      setTimeout(() => URL.revokeObjectURL(blobUrl), 60_000);
    } catch {
      setErrorMsg("Không thể mở tệp PDF CV.");
    }
  };

  const advisorSummaryText = useMemo(() => {
    const lines = [
      `HỒ SƠ MINI-CV SINH VIÊN HCM-UTE`,
      `- Họ và tên: ${fullName || user?.full_name || "Chưa cập nhật"}`,
      `- MSSV: ${studentId || "Chưa cập nhật"}`,
      `- Email: ${profile?.email || user?.email || ""}`,
      `- Khoa / Ngành: ${faculty || "—"} · ${major || "Chưa cập nhật"} (${academicYear || "—"})`,
      phone ? `- Liên hệ: ${phone}` : null,
      `- Vai trò dự kiến: ${preferredRoles.length ? preferredRoles.join(", ") : "Chưa chọn"}`,
      `- Kỹ năng: ${skills.length ? skills.join(", ") : "Chưa cập nhật"}`,
      achievementsSummary ? `- Thành tích / Dự án: ${achievementsSummary}` : null,
      profile?.has_uploaded_cv
        ? `- CV PDF đính kèm: ${profile.cv_filename ?? "student-cv.pdf"} (Đã lưu trên hệ thống)`
        : null,
      cvUrl ? `- Link CV: ${cvUrl}` : null,
      githubUrl ? `- GitHub: ${githubUrl}` : null,
    ].filter(Boolean);
    return lines.join("\n");
  }, [
    fullName,
    user,
    studentId,
    profile,
    faculty,
    major,
    academicYear,
    phone,
    preferredRoles,
    skills,
    achievementsSummary,
    cvUrl,
    githubUrl,
  ]);

  const handleCopySummary = async () => {
    try {
      await navigator.clipboard.writeText(advisorSummaryText);
      setCopiedSummary(true);
      setTimeout(() => setCopiedSummary(false), 2500);
    } catch {
      setErrorMsg("Trình duyệt không cho phép sao chép tự động.");
    }
  };

  if (authLoading || loading) {
    return <div className="h-72 animate-pulse rounded-2xl bg-[var(--color-surface)]" />;
  }

  if (!user) {
    return (
      <div className="mx-auto my-8 max-w-lg rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 text-center">
        <UserCircle className="mx-auto h-10 w-10 text-[var(--color-brand-primary)]" aria-hidden="true" />
        <h1 className="mt-3 text-xl font-bold text-[var(--color-text-primary)]">
          Hồ sơ Cá nhân Sinh viên (Mini-CV)
        </h1>
        <p className="mt-2 text-sm text-[var(--color-text-muted)]">
          Vui lòng đăng nhập tài khoản để cập nhật MSSV, ngành học, kỹ năng và đính kèm CV phục vụ ghép đội thi đấu.
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

  const completeness = profile?.completeness_pct ?? 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[var(--color-text-primary)] sm:text-3xl">
            Hồ sơ Cá nhân (Mini-CV)
          </h1>
          <p className="mt-1 text-sm text-[var(--color-text-muted)]">
            Cập nhật thông tin học vụ, kỹ năng và CV để đồng đội tìm kiếm, giảng viên xét duyệt và trợ lý gợi ý cuộc thi phù hợp.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void handleCopySummary()}
          className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3.5 py-2 text-sm font-medium text-[var(--color-text-primary)] hover:bg-[var(--color-surface-subtle)]"
        >
          {copiedSummary ? (
            <>
              <Check className="h-4 w-4 text-[var(--color-status-success)]" aria-hidden="true" />
              <span>Đã sao chép tóm tắt gửi GVHD</span>
            </>
          ) : (
            <>
              <Copy className="h-4 w-4 text-[var(--color-brand-primary)]" aria-hidden="true" />
              <span>Sao chép tóm tắt gửi GVHD</span>
            </>
          )}
        </button>
      </div>

      {isWelcome && (
        <div className="flex items-start gap-3 rounded-xl border border-[var(--color-brand-primary)]/30 bg-[var(--color-brand-primary)]/5 p-4 text-sm text-[var(--color-text-primary)]">
          <Sparkles className="mt-0.5 h-5 w-5 shrink-0 text-[var(--color-brand-primary)]" aria-hidden="true" />
          <div>
            <p className="font-semibold">Chào mừng bạn đến với ACDP Portal!</p>
            <p className="mt-0.5 text-xs text-[var(--color-text-muted)]">
              Hãy hoàn thiện nhanh Mini-CV bên dưới (chỉ mất ~1 phút) để sẵn sàng lập đội thi và nhận gợi ý cuộc thi chuẩn ngành học.
            </p>
          </div>
        </div>
      )}

      {statusMsg && (
        <div
          role="status"
          className="rounded-lg border border-emerald-500/40 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-700 dark:text-emerald-300"
        >
          {statusMsg}
        </div>
      )}
      {errorMsg && (
        <div
          role="alert"
          className="rounded-lg border border-[var(--color-brand-accent)]/40 bg-red-500/10 px-4 py-3 text-sm text-[var(--color-brand-accent)]"
        >
          {errorMsg}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-12">
        <form onSubmit={(e) => void handleSave(e)} className="space-y-6 lg:col-span-7">
          <section className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5 space-y-4">
            <h2 className="text-base font-bold text-[var(--color-text-primary)]">1. Thông tin Sinh viên</h2>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label htmlFor="prof-fullname" className="block text-xs font-semibold text-[var(--color-text-primary)]">
                  Họ và tên <span aria-hidden="true">*</span>
                </label>
                <input
                  id="prof-fullname"
                  type="text"
                  required
                  minLength={2}
                  maxLength={120}
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="mt-1.5 min-h-11 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-canvas)] px-3 text-sm"
                />
              </div>
              <div>
                <label htmlFor="prof-mssv" className="block text-xs font-semibold text-[var(--color-text-primary)]">
                  MSSV / Mã định danh
                </label>
                <input
                  id="prof-mssv"
                  type="text"
                  maxLength={32}
                  placeholder="Ví dụ: 23133030"
                  value={studentId}
                  onChange={(e) => setStudentId(e.target.value)}
                  className="mt-1.5 min-h-11 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-canvas)] px-3 text-sm font-mono"
                />
              </div>
              <div>
                <label htmlFor="prof-email" className="block text-xs font-semibold text-[var(--color-text-primary)]">
                  Email tài khoản
                </label>
                <input
                  id="prof-email"
                  type="email"
                  disabled
                  value={profile?.email || user.email}
                  className="mt-1.5 min-h-11 w-full cursor-not-allowed rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-subtle)] px-3 text-sm text-[var(--color-text-muted)]"
                />
              </div>
              <div>
                <label htmlFor="prof-phone" className="block text-xs font-semibold text-[var(--color-text-primary)]">
                  Số điện thoại / Zalo liên hệ
                </label>
                <input
                  id="prof-phone"
                  type="tel"
                  maxLength={24}
                  placeholder="0901 234 567"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="mt-1.5 min-h-11 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-canvas)] px-3 text-sm"
                />
              </div>
              <div>
                <label htmlFor="prof-faculty" className="block text-xs font-semibold text-[var(--color-text-primary)]">
                  Khoa
                </label>
                <input
                  id="prof-faculty"
                  type="text"
                  maxLength={160}
                  value={faculty}
                  onChange={(e) => setFaculty(e.target.value)}
                  className="mt-1.5 min-h-11 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-canvas)] px-3 text-sm"
                />
              </div>
              <div>
                <label htmlFor="prof-major" className="block text-xs font-semibold text-[var(--color-text-primary)]">
                  Ngành học
                </label>
                <input
                  id="prof-major"
                  type="text"
                  list="hcmute-majors"
                  maxLength={160}
                  placeholder="Ví dụ: Kỹ thuật Dữ liệu"
                  value={major}
                  onChange={(e) => setMajor(e.target.value)}
                  className="mt-1.5 min-h-11 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-canvas)] px-3 text-sm"
                />
                <datalist id="hcmute-majors">
                  {HCMUTE_MAJORS.map((m) => (
                    <option key={m} value={m} />
                  ))}
                </datalist>
              </div>
              <div>
                <label htmlFor="prof-year" className="block text-xs font-semibold text-[var(--color-text-primary)]">
                  Khóa / Năm học
                </label>
                <input
                  id="prof-year"
                  type="text"
                  maxLength={32}
                  placeholder="Ví dụ: K23 (Năm 3)"
                  value={academicYear}
                  onChange={(e) => setAcademicYear(e.target.value)}
                  className="mt-1.5 min-h-11 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-canvas)] px-3 text-sm"
                />
              </div>
              <div className="flex items-end pb-1">
                <label className="inline-flex cursor-pointer items-center gap-2.5 text-sm font-medium text-[var(--color-text-primary)]">
                  <input
                    type="checkbox"
                    checked={isOpenToTeam}
                    onChange={(e) => setIsOpenToTeam(e.target.checked)}
                    className="h-4 w-4 rounded border-[var(--color-border)] accent-[var(--color-brand-primary)]"
                  />
                  <span>Đang sẵn sàng tìm & ghép đội thi</span>
                </label>
              </div>
            </div>
          </section>

          <section className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5 space-y-4">
            <h2 className="text-base font-bold text-[var(--color-text-primary)]">2. Kỹ năng & Vai trò thi đấu</h2>

            <div>
              <label htmlFor="prof-skill-input" className="block text-xs font-semibold text-[var(--color-text-primary)]">
                Kỹ năng (Skills — tối đa 20 thẻ)
              </label>
              <div className="mt-1.5 flex gap-2">
                <input
                  id="prof-skill-input"
                  type="text"
                  maxLength={40}
                  placeholder="Nhập kỹ năng rồi nhấn Enter (VD: Python, SQL)"
                  value={skillInput}
                  onChange={(e) => setSkillInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      addSkill(skillInput);
                    }
                  }}
                  className="min-h-11 flex-1 rounded-lg border border-[var(--color-border)] bg-[var(--color-canvas)] px-3 text-sm"
                />
                <button
                  type="button"
                  onClick={() => addSkill(skillInput)}
                  className="inline-flex min-h-11 items-center gap-1.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-canvas)] px-3.5 text-sm font-medium hover:bg-[var(--color-surface-subtle)]"
                >
                  <Plus className="h-4 w-4" aria-hidden="true" />
                  <span>Thêm</span>
                </button>
              </div>

              {skills.length > 0 && (
                <div className="mt-2.5 flex flex-wrap gap-1.5">
                  {skills.map((skill) => (
                    <span
                      key={skill}
                      className="inline-flex items-center gap-1 rounded-full bg-[var(--color-brand-primary)]/10 px-2.5 py-1 text-xs font-medium text-[var(--color-brand-primary)]"
                    >
                      <span>{skill}</span>
                      <button
                        type="button"
                        onClick={() => removeSkill(skill)}
                        aria-label={`Xóa kỹ năng ${skill}`}
                        className="rounded-full p-0.5 hover:bg-[var(--color-brand-primary)]/20"
                      >
                        <X className="h-3 w-3" aria-hidden="true" />
                      </button>
                    </span>
                  ))}
                </div>
              )}

              <div className="mt-2.5 flex flex-wrap items-center gap-1.5">
                <span className="text-[11px] text-[var(--color-text-muted)]">Gợi ý nhanh:</span>
                {SUGGESTED_SKILLS.filter((s) => !skills.some((x) => x.toLowerCase() === s.toLowerCase())).map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => addSkill(s)}
                    className="rounded-md border border-[var(--color-border)] bg-[var(--color-canvas)] px-2 py-0.5 text-[11px] text-[var(--color-text-muted)] hover:border-[var(--color-brand-primary)] hover:text-[var(--color-brand-primary)]"
                  >
                    + {s}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <p className="text-xs font-semibold text-[var(--color-text-primary)]">
                Vai trò mong muốn khi lập đội (chọn tối đa 6)
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
                {SUGGESTED_ROLES.map((roleLabel) => {
                  const selected = preferredRoles.includes(roleLabel);
                  return (
                    <button
                      key={roleLabel}
                      type="button"
                      aria-pressed={selected}
                      onClick={() => toggleRole(roleLabel)}
                      className={`min-h-9 rounded-lg border px-3 py-1 text-xs font-medium transition-colors ${
                        selected
                          ? "border-[var(--color-brand-primary)] bg-[var(--color-brand-primary)] text-white dark:text-slate-950"
                          : "border-[var(--color-border)] bg-[var(--color-canvas)] text-[var(--color-text-primary)] hover:bg-[var(--color-surface-subtle)]"
                      }`}
                    >
                      {roleLabel}
                    </button>
                  );
                })}
              </div>
            </div>
          </section>

          <section className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5 space-y-4">
            <h2 className="text-base font-bold text-[var(--color-text-primary)]">3. Đính kèm CV & Hồ sơ Năng lực</h2>

            <div className="rounded-xl border border-dashed border-[var(--color-border)] bg-[var(--color-canvas)] p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold text-[var(--color-text-primary)]">
                    Tải lên CV định dạng PDF (≤ 2 MB)
                  </p>
                  <p className="mt-0.5 text-[11px] text-[var(--color-text-muted)]">
                    Tệp PDF được lưu trực tiếp trên hệ thống để phục vụ xem nhanh khi lập đội và phân tích gợi ý cuộc thi.
                  </p>
                </div>
                <div>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="application/pdf,.pdf"
                    onChange={(e) => void handleUploadCvPdf(e)}
                    className="hidden"
                  />
                  <button
                    type="button"
                    disabled={uploadingCv}
                    onClick={() => fileInputRef.current?.click()}
                    className="inline-flex min-h-10 items-center gap-2 rounded-lg bg-[var(--color-brand-primary)] px-3.5 py-2 text-xs font-semibold text-white hover:opacity-90 disabled:opacity-60 dark:text-slate-950"
                  >
                    <FileUp className="h-4 w-4" aria-hidden="true" />
                    <span>{uploadingCv ? "Đang tải..." : "Chọn & Tải PDF"}</span>
                  </button>
                </div>
              </div>

              {profile?.has_uploaded_cv && (
                <div className="mt-3 flex flex-wrap items-center justify-between gap-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-xs">
                  <div className="flex items-center gap-2 text-[var(--color-text-primary)]">
                    <FileText className="h-4 w-4 text-[var(--color-brand-primary)]" aria-hidden="true" />
                    <span className="font-medium">{profile.cv_filename || "student-cv.pdf"}</span>
                    <span className="font-mono text-[11px] text-[var(--color-text-muted)]">
                      ({formatBytes(profile.cv_size_bytes)})
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => void handlePreviewUploadedCv()}
                      className="inline-flex items-center gap-1 rounded-md border border-[var(--color-border)] px-2.5 py-1 text-xs font-medium text-[var(--color-brand-primary)] hover:bg-[var(--color-surface-subtle)]"
                    >
                      <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
                      <span>Xem PDF</span>
                    </button>
                    <button
                      type="button"
                      disabled={uploadingCv}
                      onClick={() => void handleDeleteCvPdf()}
                      className="inline-flex items-center gap-1 rounded-md border border-[var(--color-border)] px-2.5 py-1 text-xs text-[var(--color-brand-accent)] hover:bg-[var(--color-surface-subtle)]"
                    >
                      <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
                      <span>Xóa</span>
                    </button>
                  </div>
                </div>
              )}
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="sm:col-span-2">
                <label htmlFor="prof-cv-url" className="block text-xs font-semibold text-[var(--color-text-primary)]">
                  Hoặc dán liên kết CV ngoài (Google Drive / TopCV / Portfolio — https://)
                </label>
                <input
                  id="prof-cv-url"
                  type="url"
                  maxLength={500}
                  placeholder="https://drive.google.com/file/d/..."
                  value={cvUrl}
                  onChange={(e) => setCvUrl(e.target.value)}
                  className="mt-1.5 min-h-11 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-canvas)] px-3 text-sm"
                />
              </div>
              <div>
                <label htmlFor="prof-github" className="block text-xs font-semibold text-[var(--color-text-primary)]">
                  GitHub (https://)
                </label>
                <input
                  id="prof-github"
                  type="url"
                  maxLength={300}
                  placeholder="https://github.com/username"
                  value={githubUrl}
                  onChange={(e) => setGithubUrl(e.target.value)}
                  className="mt-1.5 min-h-11 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-canvas)] px-3 text-sm"
                />
              </div>
              <div>
                <label htmlFor="prof-linkedin" className="block text-xs font-semibold text-[var(--color-text-primary)]">
                  LinkedIn (https://)
                </label>
                <input
                  id="prof-linkedin"
                  type="url"
                  maxLength={300}
                  placeholder="https://linkedin.com/in/username"
                  value={linkedinUrl}
                  onChange={(e) => setLinkedinUrl(e.target.value)}
                  className="mt-1.5 min-h-11 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-canvas)] px-3 text-sm"
                />
              </div>
            </div>

            <div>
              <label htmlFor="prof-bio" className="block text-xs font-semibold text-[var(--color-text-primary)]">
                Giới thiệu ngắn & Mục tiêu thi đấu
              </label>
              <textarea
                id="prof-bio"
                rows={3}
                maxLength={600}
                placeholder="Mô tả thế mạnh kỹ thuật và định hướng cuộc thi bạn muốn tham gia..."
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                className="mt-1.5 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-canvas)] p-3 text-sm"
              />
            </div>

            <div>
              <label htmlFor="prof-achievements" className="block text-xs font-semibold text-[var(--color-text-primary)]">
                Thành tích / Dự án tiêu biểu (hiển thị khi gửi Giảng viên)
              </label>
              <textarea
                id="prof-achievements"
                rows={3}
                maxLength={1000}
                placeholder="VD: Top 10 Data Science Hack 2025; Xây dựng pipeline ETL DuckDB..."
                value={achievementsSummary}
                onChange={(e) => setAchievementsSummary(e.target.value)}
                className="mt-1.5 w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-canvas)] p-3 text-sm"
              />
            </div>
          </section>

          <button
            type="submit"
            disabled={saving}
            className="inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-xl bg-[var(--color-brand-primary)] px-5 py-3 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-60 dark:text-slate-950"
          >
            <Save className="h-4 w-4" aria-hidden="true" />
            <span>{saving ? "Đang lưu hồ sơ..." : "Lưu hồ sơ Mini-CV"}</span>
          </button>
        </form>

        <aside className="space-y-4 lg:col-span-5">
          <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-[var(--color-text-primary)]">Mức độ hoàn thiện hồ sơ</h2>
              <span className="font-mono text-sm font-bold text-[var(--color-brand-primary)]">{completeness}%</span>
            </div>
            <div className="mt-2.5 h-2.5 w-full overflow-hidden rounded-full bg-[var(--color-surface-subtle)]">
              <div
                className="h-full rounded-full bg-[var(--color-brand-primary)] transition-all duration-300"
                style={{ width: `${completeness}%` }}
              />
            </div>
            {(profile?.missing_fields ?? []).length > 0 ? (
              <p className="mt-2.5 text-xs text-[var(--color-text-muted)]">
                Cần bổ sung: {(profile?.missing_fields ?? []).join(", ")}.
              </p>
            ) : (
              <p className="mt-2.5 text-xs font-medium text-emerald-600 dark:text-emerald-400">
                Hồ sơ Mini-CV đã hoàn thiện 100%, sẵn sàng lập đội và gửi Giảng viên!
              </p>
            )}
          </div>

          <div className="sticky top-20 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5 space-y-4">
            <div className="flex items-start justify-between gap-3 border-b border-[var(--color-border)] pb-3">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-wider text-[var(--color-brand-primary)]">
                  Xem trước thẻ Mini-CV
                </p>
                <h3 className="mt-1 text-lg font-bold text-[var(--color-text-primary)]">
                  {fullName || user.full_name}
                </h3>
                <p className="text-xs text-[var(--color-text-muted)]">
                  {studentId ? `MSSV: ${studentId} · ` : ""}
                  {major || "Chưa chọn ngành"} {academicYear ? `(${academicYear})` : ""}
                </p>
                <p className="text-xs text-[var(--color-text-muted)]">{faculty}</p>
              </div>
              <span
                className={`rounded-full px-2.5 py-1 text-[11px] font-semibold ${
                  isOpenToTeam
                    ? "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300"
                    : "bg-[var(--color-surface-subtle)] text-[var(--color-text-muted)]"
                }`}
              >
                {isOpenToTeam ? "Sẵn sàng ghép đội" : "Tạm ẩn ghép đội"}
              </span>
            </div>

            {bio && <p className="text-xs leading-relaxed text-[var(--color-text-primary)]">{bio}</p>}

            <div>
              <p className="text-[11px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
                Vai trò thi đấu
              </p>
              {preferredRoles.length > 0 ? (
                <div className="mt-1.5 flex flex-wrap gap-1.5">
                  {preferredRoles.map((r) => (
                    <span
                      key={r}
                      className="rounded-md border border-[var(--color-border)] bg-[var(--color-canvas)] px-2 py-0.5 text-xs font-medium"
                    >
                      {r}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="mt-1 text-xs text-[var(--color-text-muted)]">Chưa chọn vai trò</p>
              )}
            </div>

            <div>
              <p className="text-[11px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
                Kỹ năng nổi bật
              </p>
              {skills.length > 0 ? (
                <div className="mt-1.5 flex flex-wrap gap-1.5">
                  {skills.map((s) => (
                    <span
                      key={s}
                      className="rounded-full bg-[var(--color-brand-primary)]/10 px-2.5 py-0.5 text-xs font-medium text-[var(--color-brand-primary)]"
                    >
                      {s}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="mt-1 text-xs text-[var(--color-text-muted)]">Chưa thêm kỹ năng</p>
              )}
            </div>

            {achievementsSummary && (
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
                  Thành tích / Dự án
                </p>
                <p className="mt-1 whitespace-pre-line text-xs text-[var(--color-text-primary)]">
                  {achievementsSummary}
                </p>
              </div>
            )}

            <div className="flex flex-wrap gap-2 border-t border-[var(--color-border)] pt-3 text-xs">
              {profile?.has_uploaded_cv && (
                <button
                  type="button"
                  onClick={() => void handlePreviewUploadedCv()}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-canvas)] px-2.5 py-1.5 font-medium text-[var(--color-brand-primary)] hover:bg-[var(--color-surface-subtle)]"
                >
                  <FileText className="h-3.5 w-3.5" aria-hidden="true" />
                  <span>CV PDF ({profile.cv_filename || "cv.pdf"})</span>
                </button>
              )}
              {cvUrl && (
                <a
                  href={cvUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-canvas)] px-2.5 py-1.5 font-medium hover:bg-[var(--color-surface-subtle)]"
                >
                  <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
                  <span>Link CV</span>
                </a>
              )}
              {githubUrl && (
                <a
                  href={githubUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-canvas)] px-2.5 py-1.5 font-medium hover:bg-[var(--color-surface-subtle)]"
                >
                  <Github className="h-3.5 w-3.5" aria-hidden="true" />
                  <span>GitHub</span>
                </a>
              )}
              {linkedinUrl && (
                <a
                  href={linkedinUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-canvas)] px-2.5 py-1.5 font-medium hover:bg-[var(--color-surface-subtle)]"
                >
                  <Linkedin className="h-3.5 w-3.5" aria-hidden="true" />
                  <span>LinkedIn</span>
                </a>
              )}
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}

export default function ProfilePage() {
  return (
    <Suspense fallback={<div className="h-72 animate-pulse rounded-2xl bg-[var(--color-surface)]" />}>
      <ProfileWorkspace />
    </Suspense>
  );
}
