# DELIVERABLE: Trang Hồ sơ Cá nhân Sinh viên (`/profile` — Định dạng Mini-CV)

- **Task ID**: `TASK-SRV-01`
- **Related Sprint**: Cycle 08 / TLCN (Phase 1)
- **Primary Owner**: Do Kien Hung
- **Date Completed**: 2026-11-26
- **Deliverable Type**: System Feature (PostgreSQL OLTP + R2 PDF Storage + FastAPI + Next.js 16)
- **Status**: Integrated into Codebase

---

## 1. Executive Summary & Objective

Sau khi đăng ký tài khoản trên ACDP Portal, sinh viên cần một trang `/profile` định dạng **Mini-CV** để khai báo MSSV, Khoa/Ngành học, Khóa, Kỹ năng (Skills), Vai trò thi đấu, Thành tích nổi bật và đính kèm CV. Dữ liệu này là nền tảng bắt buộc cho các tính năng kế tiếp: tạo/xin vào đội (`TASK-SRV-02`), xuất màn hình tổng hợp gửi Giảng viên hướng dẫn (`TASK-SRV-03`), và tư vấn cuộc thi cá nhân hóa qua RAG Chatbot (`TASK-SRV-04`).

Hệ thống hỗ trợ song song **Phương án A** (dán liên kết CV ngoài chuẩn `https://`) và **Phương án B** (tải trực tiếp tệp CV PDF ≤ 2 MB lên Cloudflare R2 tại `profiles/cv/{user_id}.pdf`) nhằm bảo đảm khả năng đọc/trích xuất văn bản phía máy chủ cho các bài toán AI/ML ở Phase 2 (KLTN) mà không phụ thuộc quyền chia sẻ link ngoài.

---

## 2. Research Findings / Technical Results

### 2.1. Thiết kế Schema `user_profiles` (`PG 17+` Parity)

Bảng `user_profiles` thiết lập quan hệ 1–1 với `users` (`ON DELETE CASCADE`, `UNIQUE(user_id)`) trong [`models.py`](../../src/acdp/api/db/models.py) và [`0004-serving-api-and-oltp-spec.md`](../specs/0004-serving-api-and-oltp-spec.md):

| Nhóm trường | Cột lưu trữ | Kiểu dữ liệu & Ràng buộc | Vai trò nghiệp vụ & Downstream |
| :--- | :--- | :--- | :--- |
| **Định danh & Học vụ** | `faculty`, `major`, `academic_year`, `phone` | `VARCHAR(160/32/24)` | Hiển thị trên thẻ Mini-CV và lọc ngành cho `TASK-SRV-04` |
| **Năng lực & Ghép đội** | `skills_json`, `preferred_roles_json`, `bio`, `achievements_summary`, `is_open_to_team` | `JSONB` (`[]`), `TEXT`, `BOOLEAN` | Khớp vai trò/kỹ năng trong `TASK-SRV-02` và tóm tắt gửi GVHD (`TASK-SRV-03`) |
| **CV & Liên kết** | `cv_url`, `cv_storage_key`, `cv_filename`, `cv_size_bytes`, `cv_uploaded_at`, `github_url`, `linkedin_url` | `VARCHAR`, `INTEGER`, `TIMESTAMPTZ` | Hỗ trợ cả link `https://` (Option A) lẫn PDF trên Cloudflare R2 (Option B) |

### 2.2. Bảo mật Upload & Quyền riêng tư

| Cơ chế kiểm soát | Thành phần thực thi | Ràng buộc kỹ thuật |
| :--- | :--- | :--- |
| **Chống XSS URL** | [`schemas/profile.py`](../../src/acdp/api/schemas/profile.py) | Chỉ chấp nhận `https://` cho `cv_url`, `github_url`, `linkedin_url`; từ chối `javascript:`, `data:`, `http://` (`422`) |
| **Kiểm định PDF** | [`routers/profile.py`](../../src/acdp/api/routers/profile.py) & [`cv_storage.py`](../../src/acdp/api/services/cv_storage.py) | Giới hạn `2 MB` (`413`), kiểm tra magic bytes `%PDF-` (`400`), chuẩn hóa tên file, đặt key cố định `profiles/cv/{user_id}.pdf` |
| **Header tải PDF an toàn** | `GET /api/v1/profile/{user_id}/cv` | Trả kèm `X-Content-Type-Options: nosniff` và `Content-Disposition: inline; filename="..."` |
| **Ẩn SĐT chéo tài khoản** | `GET /api/v1/profile/{user_id}` | Ẩn `phone` (`null`) nếu người xem là sinh viên khác; chỉ hiển thị cho chính chủ, `lecturer` hoặc `admin` |

---

## 3. Benchmarks & Quantitative Evidence

| Metric / Dimension | Baseline / Constraint | Measured Result | Verification Source |
| :--- | :--- | :--- | :--- |
| **Profile API Tests (`test_profile.py`)** | 100% pass, 0 warnings | `3 passed in 33.35s` (Supabase Cloud PG + Fake R2) | `tests/api/test_profile.py` |
| **API Regression Suite** | 100% pass across auth, RAG & OpenAPI | `10 passed in 79.47s` | `tests/api/test_profile.py`, `test_auth_and_bookmarks.py`, `test_rag_and_openapi.py` |
| **Ruff Static Lint** | 0 errors | `All checks passed!` | `uv run ruff check src/acdp/api tests/api/test_profile.py` |
| **OpenAPI-TypeScript Codegen** | 0 errors | `240.2ms` (`openapi.json` $\rightarrow$ `apps/web/types/api.d.ts`) | `apps/web/package.json` (`gen:api`) |
| **Next.js 16 Typecheck & Build** | 0 TypeScript / Turbopack errors | `Compiled in 4.8s`, `TypeScript in 5.2s`, `/profile` prerendered static | `apps/web` (`npm run typecheck`, `npm run build`) |

---

## 4. Key Decisions & Impact on ACDP

1. **Impact on Specs**: Cập nhật [`0004-serving-api-and-oltp-spec.md`](../specs/0004-serving-api-and-oltp-spec.md) bổ sung bảng thứ 6 (`user_profiles`) và 6 endpoints `/api/v1/profile/*`.
2. **Impact on ADRs**: Tuân thủ `ADR-0002` (Full Cloud Free-Tier: Supabase PostgreSQL OLTP + Cloudflare R2 Object Storage) và `DIR-015` (cơ chế nhẹ không cần ClamAV/worker riêng ở quy mô TLCN, chỉ dùng magic bytes `%PDF-` + giới hạn 2 MB).
3. **Impact on Downstream Tasks**: Hoàn thiện hợp đồng dữ liệu đầu vào cho `TASK-SRV-02` (lập đội), `TASK-SRV-03` (màn hình gửi giảng viên) và `TASK-SRV-04` (RAG tư vấn theo hồ sơ).

---

## 5. Manual Test, CLI Deployment & Advisor Demo Runbook

### Step 1: Chạy kiểm thử tự động Backend (`ruff` + `pytest`)

```powershell
uv run ruff check src/acdp/api tests/api/test_profile.py
$env:POSTGRES_MODE='cloud'; uv run pytest tests/api/test_profile.py -v
```

Captured Output:

```text
All checks passed!
============================= test session starts =============================
platform win32 -- Python 3.11.14, pytest-9.2.0, pluggy-1.7.0 -- D:\Code\final-thesis\acdp-platform\.venv\Scripts\python.exe
collected 3 items

tests/api/test_profile.py::test_profile_requires_auth_and_defaults_for_new_student PASSED [ 33%]
tests/api/test_profile.py::test_profile_upsert_syncs_user_normalizes_skills_and_validates_urls PASSED [ 66%]
tests/api/test_profile.py::test_profile_pdf_upload_download_delete_and_privacy PASSED [100%]

============================= 3 passed in 33.35s ==============================
```

### Step 2: Đồng bộ OpenAPI & Build Frontend Next.js 16

```powershell
uv run python -m acdp.api.export_openapi --output openapi.json
Push-Location apps\web; npm run gen:api; npm run typecheck; npm run build; Pop-Location
```

Captured Output:

```text
Exported OpenAPI 3.1 schema -> openapi.json
🚀 ../../openapi.json → types/api.d.ts [240.2ms]
▲ Next.js 16.4.6 (Turbopack)
✓ Compiled successfully in 4.8s
✓ Generating static pages using 11 workers (6/6) in 386ms
├ ○ /profile
```

### Step 3: Kịch bản Demo trực tiếp trước Giảng viên

1. Mở `/login`, chuyển sang tab **Đăng ký SV** để tạo tài khoản mới $\rightarrow$ hệ thống tự động điều hướng sang `/profile?welcome=1`.
2. Điền MSSV (`23133030`), Ngành học (`Kỹ thuật Dữ liệu`), thêm các kỹ năng (`Python`, `DuckDB`, `SQL`), chọn vai trò `Data Engineer`, tải lên tệp CV PDF (≤ 2 MB) hoặc dán link CV `https://...` rồi bấm **Lưu hồ sơ Mini-CV**.
3. Quan sát thanh **Mức độ hoàn thiện hồ sơ** đạt `100%`, thẻ **Xem trước thẻ Mini-CV** cập nhật tức thì, và bấm **Sao chép tóm tắt gửi GVHD** để kiểm tra nội dung văn bản chuẩn hóa trong clipboard.

---

## 6. Associated Artifacts & Code Links

| Artifact | Path | Role |
| :--- | :--- | :--- |
| **Visual Dossier (HTML)** | [`TASK-SRV-01-student-mini-cv-profile-visual-dossier.html`](./TASK-SRV-01-student-mini-cv-profile-visual-dossier.html) | Interactive 3-tier summary & Mermaid architecture |
| **OLTP Model** | [`models.py`](../../src/acdp/api/db/models.py) | `UserProfile` (`user_profiles` table) |
| **Pydantic Schemas** | [`profile.py`](../../src/acdp/api/schemas/profile.py) | `ProfileUpdateRequest`, `StudentProfileDTO`, `PublicStudentProfileDTO` |
| **FastAPI Router** | [`profile.py`](../../src/acdp/api/routers/profile.py) | `/api/v1/profile/*` endpoints |
| **R2 Storage Service** | [`cv_storage.py`](../../src/acdp/api/services/cv_storage.py) | Cloudflare R2 PDF upload/download/delete |
| **Frontend Page** | [`page.tsx`](../../apps/web/app/profile/page.tsx) | `/profile` Mini-CV builder & live preview |
| **Automated Tests** | [`test_profile.py`](../../tests/api/test_profile.py) | Pytest integration suite |
| **Task Registry Entry** | [`task-registry.md`](../tasks/task-registry.md) | Synchronized task status (`done`) |

---

## 7. Search Provenance & Verifiable References (`DIR-020`)

| # | Search Query (`search_web`) | Purpose | Verified Canonical URL / DOI | Link Check Status |
| :---: | :--- | :--- | :--- | :---: |
| 1 | `FastAPI UploadFile official documentation request files` | Chuẩn hóa nhận file `multipart/form-data` bằng `UploadFile` | https://fastapi.tiangolo.com/tutorial/request-files/ | `HEALTHY` |
| 2 | `OWASP File Upload Cheat Sheet PDF validation magic bytes` | Xác thực magic bytes `%PDF-`, đổi tên file và header `X-Content-Type-Options: nosniff` | https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html | `HEALTHY` |
| 3 | `Cloudflare R2 S3 API boto3 Python official documentation` | Cấu hình `boto3` S3 client lưu PDF CV trên Cloudflare R2 | https://developers.cloudflare.com/r2/api/s3/api/ | `HEALTHY` |
| 4 | `PostgreSQL JSONB data type official documentation` | Thiết kế cột `skills_json` và `preferred_roles_json` dạng `JSONB` | https://www.postgresql.org/docs/current/datatype-json.html | `HEALTHY` |
