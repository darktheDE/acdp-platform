# SPEC-0005: Frontend Design System, SVG Brand Identity & UI/UX Architecture

> **Task ID**: `TASK-W104` | **Task Registry**: [`NT-026`](../tasks/task-registry.md)
> **Status**: Implemented (Web Sprint 02)
> **Dependencies**: [`SPEC-0003`](./0003-gold-dimensional-modeling-spec.md), [`SPEC-0004`](./0004-serving-api-and-oltp-spec.md), [`.agents/skills/frontend-designer/references/design_tokens.md`](../../.agents/skills/frontend-designer/references/design_tokens.md)
> **Target Directory (Sprint 02 Implementation)**: `apps/web/`

---

## 1. Objective & Scope

Tài liệu này quy chuẩn hóa hệ thống thiết kế giao diện (Design System), bộ nhận diện thương hiệu SVG, bảng màu tuân thủ **WCAG 2.2 AA**, ranh giới kết xuất **Next.js 16 (Active LTS `16.4.6`)** và ánh xạ dữ liệu cho 3 phân hệ trải nghiệm người dùng của nền tảng ACDP tại `apps/web/`:

1. **Academic Competition Explorer (`/competitions`, `/competitions/[key]`):** Cổng tìm kiếm, lọc đa chiều và xem hồ sơ cuộc thi dành cho sinh viên.
2. **Faculty & Student Analytics Dashboard (`/dashboard`):** Bảng điều khiển trực quan hóa các chỉ số Lớp Vàng bằng **Recharts (`v2.15+ / v3`)**.
3. **RAG Regulation Copilot (`/copilot`, `/bookmarks`):** Trợ lý hỏi đáp thể lệ có trích dẫn nguồn gốc và trang quản lý cuộc thi đã đánh dấu.

Toàn bộ giao diện sử dụng **Tailwind CSS v4** (cấu hình CSS-first bằng chỉ thị `@theme`), hệ font `Plus Jakarta Sans`, `Be Vietnam Pro` và `JetBrains Mono` thông qua `next/font/google` để hiển thị chuẩn dấu tiếng Việt và căn thẳng cột số học tài chính. Việc triển khai chịu sự kiểm soát chất lượng của kỹ năng `.agents/skills/frontend-designer/SKILL.md` và bộ kiểm tra khả năng tiếp cận (accessibility).

---

## 2. Data Contracts & Schemas

### 2.1. Hệ thống Nhận diện Thương hiệu SVG (`apps/web/components/brand/AcdpLogo.tsx`)

Biểu tượng (Logomark) ACDP kết hợp hình học ba khối dữ liệu tuần tự (ngụ ý kiến trúc Medallion Bronze, Silver, Gold nâng dần độ tinh khiết) hợp thành hình mũ học thuật và tia la bàn định hướng: phần đế xanh Navy (`#1E3A8A`) biểu trưng cho nền tảng dữ liệu tin cậy của Trường Đại học Công nghệ Kỹ thuật TP.HCM (HCM-UTE), còn đỉnh khối và điểm nhấn cam Coral (`#C2410C`) đại diện cho tri thức Gold Layer và cơ hội tranh tài.

Ba biến thể SVG thuần (vector không phụ thuộc tệp ảnh bitmap) dùng thống nhất trong dự án:

```tsx
// apps/web/components/brand/AcdpLogo.tsx
import type { SVGProps } from "react";

interface LogoProps extends SVGProps<SVGSVGElement> {
  size?: number;
}

/**
 * Biến thể 1: LogoMark (Biểu tượng 32x32 cho Favicon, Collapsed Sidebar, App Icon)
 */
export function LogoMark({ size = 32, className, ...props }: LogoProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-label="ACDP Logo Mark"
      className={className}
      {...props}
    >
      {/* Nền bo góc chuẩn học thuật */}
      <rect x="2" y="2" width="28" height="28" rx="7" fill="#1E3A8A" />
      {/* Ba thanh Medallion (Bronze -> Silver -> Gold) tạo thành mũi hướng lên */}
      <rect x="7" y="18" width="4" height="6" rx="1.5" fill="#93C5FD" />
      <rect x="14" y="13" width="4" height="11" rx="1.5" fill="#FFFFFF" />
      <rect x="21" y="8" width="4" height="16" rx="1.5" fill="#C2410C" />
      {/* Đường kết nối đỉnh dữ liệu Gold */}
      <circle cx="23" cy="6.5" r="1.75" fill="#FBBF24" />
    </svg>
  );
}

/**
 * Biến thể 2: LogoFull (Biểu tượng + Wordmark cho Top Navbar & Trang Auth)
 */
export function LogoFull({ className = "h-9 w-auto" }: { className?: string }) {
  return (
    <div className={`inline-flex items-center gap-2.5 select-none ${className}`}>
      <LogoMark size={34} />
      <div className="flex flex-col leading-none">
        <span className="font-sans text-lg font-bold tracking-tight text-slate-900 dark:text-slate-50">
          ACDP<span className="text-[#C2410C]">.</span>
        </span>
        <span className="font-mono text-[10px] font-medium uppercase tracking-wider text-slate-600 dark:text-slate-400">
          HCM-UTE Data Lakehouse
        </span>
      </div>
    </div>
  );
}

/**
 * Biến thể 3: LogoMonochrome (Đơn sắc currentColor cho Footer, PDF & Watermark)
 */
export function LogoMonochrome({ size = 28, className, ...props }: LogoProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-label="ACDP Monochrome Logo"
      className={className}
      {...props}
    >
      <rect
        x="2.75"
        y="2.75"
        width="26.5"
        height="26.5"
        rx="6.25"
        stroke="currentColor"
        strokeWidth="1.5"
      />
      <rect x="7.5" y="18" width="3.75" height="6" rx="1.25" fill="currentColor" fillOpacity="0.45" />
      <rect x="14.125" y="13" width="3.75" height="11" rx="1.25" fill="currentColor" fillOpacity="0.75" />
      <rect x="20.75" y="8" width="3.75" height="16" rx="1.25" fill="currentColor" />
    </svg>
  );
}
```

### 2.2. Bảng màu Tailwind CSS v4 (`apps/web/app/globals.css`)

Dựa trên nền tảng token tại `design_tokens.md`, tệp `app/globals.css` khai báo biến ngữ nghĩa hỗ trợ cả chế độ Sáng (mặc định cho đọc tài liệu/thể lệ) và chế độ Tối (làm việc ban đêm), đồng bộ trực tiếp với 5 màu chuỗi dữ liệu Recharts (`--chart-1` đến `--chart-5`):

```css
@import "tailwindcss";

@custom-variant dark (&:where(.dark, .dark *));

@theme {
  --font-sans: var(--font-jakarta), var(--font-be-vietnam), ui-sans-serif, system-ui, sans-serif;
  --font-mono: var(--font-jetbrains-mono), ui-monospace, SFMono-Regular, monospace;

  --color-canvas: #FAF8F5;
  --color-surface: #FFFFFF;
  --color-surface-subtle: #F1F5F9;
  --color-border: #E2E8F0;

  --color-text-primary: #0F172A;
  --color-text-muted: #475569;
  --color-brand-primary: #1E3A8A;
  --color-brand-accent: #C2410C;
  --color-status-success: #15803D;
  --color-status-warning: #B45309;

  --color-chart-1: #1E3A8A;
  --color-chart-2: #C2410C;
  --color-chart-3: #15803D;
  --color-chart-4: #B45309;
  --color-chart-5: #475569;
}

.dark {
  --color-canvas: #0F172A;
  --color-surface: #1E293B;
  --color-surface-subtle: #334155;
  --color-border: #334155;

  --color-text-primary: #F8FAFC;
  --color-text-muted: #94A3B8;
  --color-brand-primary: #60A5FA;
  --color-brand-accent: #FB923C;
  --color-status-success: #4ADE80;
  --color-status-warning: #FBBF24;

  --color-chart-1: #60A5FA;
  --color-chart-2: #FB923C;
  --color-chart-3: #4ADE80;
  --color-chart-4: #FBBF24;
  --color-chart-5: #94A3B8;
}
```

### 2.3. Bảng Kiểm định Độ tương phản WCAG 2.2 AA

Theo quy chuẩn WCAG 2.2 Level AA, văn bản thường yêu cầu tỷ lệ tương phản tối thiểu `4.5:1`, văn bản lớn và thành phần giao diện/biểu đồ yêu cầu tối thiểu `3.0:1`. Lưu ý kỹ thuật quan trọng: mã `#64748B` trên nền giấy ấm `#FAF8F5` chỉ đạt `4.49:1` (thiếu `0.01` so với ngưỡng `4.5:1`), do đó hệ thống nâng `--color-text-muted` lên `#475569` (`7.58:1` trên `#FFFFFF`) để đảm bảo vượt chuẩn trên mọi bề mặt:

| Cặp màu (Foreground / Background) | Vai trò UI | Tỷ lệ đo thực tế | Chuẩn WCAG 2.2 AA | Trạng thái |
| :--- | :--- | :---: | :---: | :---: |
| `#0F172A` trên `#FAF8F5` | Chữ chính trên nền Light Canvas | `16.84:1` | `>= 4.5:1` | Đạt chuẩn AAA |
| `#0F172A` trên `#FFFFFF` | Chữ chính trong Card / Modal / Table | `17.85:1` | `>= 4.5:1` | Đạt chuẩn AAA |
| `#475569` trên `#FFFFFF` | Chữ phụ, nhãn trục biểu đồ, metadata | `7.58:1` | `>= 4.5:1` | Đạt chuẩn AAA |
| `#64748B` trên `#FFFFFF` | Nhãn phụ đặt riêng trên nền thẻ trắng | `4.76:1` | `>= 4.5:1` | Đạt chuẩn AA |
| `#1E3A8A` trên `#FFFFFF` | Liên kết, nút phụ, thanh dữ liệu chính | `10.36:1` | `>= 4.5:1` | Đạt chuẩn AAA |
| `#FFFFFF` trên `#1E3A8A` | Nhãn nút Primary & tiêu đề khối Navy | `10.36:1` | `>= 4.5:1` | Đạt chuẩn AAA |
| `#C2410C` trên `#FFFFFF` | Chữ nhấn CTA / Badge ngành nổi bật | `5.18:1` | `>= 4.5:1` | Đạt chuẩn AA |
| `#FFFFFF` trên `#C2410C` | Chữ trên nút hành động Accent Coral | `5.18:1` | `>= 4.5:1` | Đạt chuẩn AA |
| `#15803D` trên `#FFFFFF` | Badge `Miễn phí` / Trạng thái `Đang mở` | `5.02:1` | `>= 4.5:1` | Đạt chuẩn AA |
| `#B45309` trên `#FFFFFF` | Badge `Sắp hết hạn` / Cảnh báo | `5.02:1` | `>= 4.5:1` | Đạt chuẩn AA |
| `#F8FAFC` trên `#0F172A` | Chữ chính trong chế độ Tối (Dark Canvas) | `17.06:1` | `>= 4.5:1` | Đạt chuẩn AAA |
| `#E2E8F0` trên `#1E293B` | Chữ trên Card chế độ Tối | `11.87:1` | `>= 4.5:1` | Đạt chuẩn AAA |
| `#94A3B8` trên `#1E293B` | Chữ phụ & trục biểu đồ chế độ Tối | `5.71:1` | `>= 4.5:1` | Đạt chuẩn AA |
| `#60A5FA` / `#FB923C` trên `#0F172A` | Chuỗi dữ liệu Recharts trên nền Tối | `7.02:1` / `7.89:1` | `>= 3.0:1` | Đạt chuẩn AA/AAA |

### 2.4. Cấu trúc App Router (`apps/web/`) & Ánh xạ Widget tới Data Marts

```text
apps/web/
├── app/
│   ├── layout.tsx                   # Khai báo font Plus Jakarta Sans / Be Vietnam Pro / JetBrains Mono & ThemeProvider
│   ├── globals.css                  # Tailwind v4 @theme & Dark CSS variables
│   ├── page.tsx                     # Landing / Điều hướng thông minh tới Explorer & Dashboard
│   ├── competitions/
│   │   ├── page.tsx                 # Explorer: Grid thẻ cuộc thi, bộ lọc faceted, thanh tìm kiếm
│   │   └── [key]/page.tsx           # Chi tiết cuộc thi: Timeline từng vòng, Bảng giải thưởng, Nút Lưu (Bookmark)
│   ├── dashboard/page.tsx           # Faculty & Student Analytics Dashboard (4 KPI cards + 5 Recharts widgets)
│   ├── copilot/page.tsx             # Giao diện hỏi đáp RAG đa phiên kèm bảng Trích dẫn nguồn (Side-by-Side Citations)
│   ├── bookmarks/page.tsx           # Danh sách cuộc thi thí sinh đã lưu + ghi chú cá nhân
│   └── login/page.tsx               # Đăng nhập / Đăng ký tài khoản (PostgreSQL 18 Auth)
├── components/
│   ├── brand/AcdpLogo.tsx           # LogoMark, LogoFull, LogoMonochrome
│   ├── charts/                      # Client components bọc Recharts (DomainBarChart, SeasonalityChart, ModeDonut...)
│   ├── layout/                      # AppShell, TopNav, ThemeToggle, MobileNavDrawer
│   └── ui/                          # CompetitionCard, CitationChip, PrizeBadge, Skeletons
├── lib/
│   └── api-client.ts                # Fetch wrapper đọc kiểu từ types/api.d.ts
└── types/
    └── api.d.ts                     # Sinh tự động từ FastAPI OpenAPI 3.1 (Không chỉnh sửa thủ công)
```

Bảng ánh xạ chính xác từng Widget trên giao diện với nguồn dữ liệu API và Gold Data Mart:

| Trang / Tuyến | Tên Widget UI | Thành phần trực quan | Endpoint API (`SPEC-0004`) | Bảng / View Gold (`SPEC-0003`) |
| :--- | :--- | :--- | :--- | :--- |
| `/dashboard` | Hàng 4 KPI Summary Cards | Số lớn `tabular-nums`, badge phụ | `GET /api/v1/analytics/overview` | `mart_kpi_overview` |
| `/dashboard` | Biểu đồ Ngành & Giải thưởng | Recharts `BarChart` ngang + Tooltip chia tỷ trọng | `GET /api/v1/analytics/overview` | `mart_domain_analytics` |
| `/dashboard` | Biểu đồ Mùa vụ theo Học kỳ | Recharts `ComposedChart` (`Bar` số cuộc thi + `Line` tổng giải thưởng) theo `HK1`/`HK2`/`Hè` | `GET /api/v1/analytics/seasonality` | `mart_seasonality_academic` |
| `/dashboard` | Biểu đồ Hình thức & Quy mô Đội | Recharts `PieChart` (Donut) + Stacked Bar `team_profile` | `GET /api/v1/analytics/overview` | `mart_team_and_mode_matrix` |
| `/dashboard` | Bảng Hệ sinh thái BTC & Nhà tài trợ | Horizontal ranking bars phân tách Organizer vs Sponsor | `GET /api/v1/analytics/overview` | `mart_organizer_ecosystem` |
| `/competitions` | Danh sách & Bộ lọc Đa chiều | Cards 3 cột, bộ lọc Sidebar (`Ngành`, `Online/Offline`, `Miễn phí`) | `GET /api/v1/competitions` | `mart_competition_explorer` |
| `/competitions/[key]` | Lịch trình & Cơ cấu Giải thưởng | Vertical Timeline Stepper + Prize Tier Table + Bookmark Button | `GET /api/v1/competitions/{key}` | `dim_competition`, `fact_prize_tiers`, `fact_timeline_stages` |
| `/copilot` | Khung Chat & Sidebar Phiên hỏi đáp | Chat stream + Panel trích dẫn URL mở rộng bên phải | `POST /api/v1/rag/chat`, `GET /api/v1/rag/sessions` | Qdrant (`acdp_competitions`) + PostgreSQL (`chat_*`) |
| `/bookmarks` | Danh sách Theo dõi Cá nhân | Cards gọn + Cảnh báo nếu `is_archived=True` | `GET /api/v1/bookmarks` | PostgreSQL `saved_competitions` + `mart_competition_explorer` |

---

## 3. Core Processing Logic & Algorithms

### 3.1. Phân ranh giới Server Component và `'use client'` trong Next.js 16

1. **React Server Components (mặc định):** Toàn bộ `page.tsx` của `/dashboard`, `/competitions`, `/competitions/[key]` thực hiện gọi FastAPI ở tầng máy chủ thông qua biến môi trường nội bộ `INTERNAL_API_URL` (tránh phơi lộ URL container nội bộ ra trình duyệt). Kết quả ban đầu được render thành HTML ngay ở Server.
2. **Client Components (`'use client'`):** Chỉ áp dụng cho lớp vỏ biểu đồ Recharts (`components/charts/*`), thanh lọc tương tác, nút chuyển Theme, nút Bookmark (`optimistic UI`), và khung chat `/copilot`.
3. **Khắc phục lỗi Hydration của Recharts & Theme:** Biểu đồ Recharts cần kích thước DOM thực tế để tính tọa độ SVG. Mọi biểu đồ đều được bọc trong container có chiều cao tường minh (ví dụ `h-[320px] w-full min-w-0`) và dùng hook kiểm tra `mounted` (hoặc bọc Suspense) để tránh cảnh báo `width(-1) height(-1)` hoặc lệch HTML giữa Server và Client.

### 3.2. Tương tác Lọc Chéo trên Dashboard & Khả năng Tiếp cận Biểu đồ

1. Người dùng nhấp vào một thanh ngành trên `DomainBarChart` hoặc lát cắt `ModeDonut` sẽ đồng bộ trạng thái lọc lên URL query string (ví dụ `/dashboard?domain=ai-data-science`) hoặc điều hướng nhanh sang `/competitions?domain=ai-data-science`.
2. Mỗi widget biểu đồ Recharts kèm tùy chọn nút chuyển đổi "Xem dạng bảng số liệu" (Data Table Toggle) ẩn bên dưới hoặc đặt thuộc tính `role="region"` cùng `aria-label` mô tả tóm tắt, đáp ứng chuẩn tiếp cận bàn phím và trình đọc màn hình cho sinh viên khiếm thị màu sắc.

### 3.3. Định dạng Số & Tiền tệ Việt Nam (`tabular-nums`)

Mọi giá trị tiền tệ (`total_prize_vnd`, `allocated_prize_vnd`, `estimated_value_vnd`) áp dụng hàm định dạng chuẩn `Intl.NumberFormat("vi-VN")` kết hợp rút gọn thông minh (`1.25 tỷ VNĐ`, `45 triệu VNĐ`, giữ giá trị đầy đủ trong `title` hoặc Tooltip) kèm lớp Tailwind `font-mono tabular-nums` để cột số trong bảng luôn thẳng hàng dọc.

---

## 4. Error Handling & Edge Cases

| Tình huống biên | Biểu hiện trên UI | Quy tắc xử lý bắt buộc |
| :--- | :--- | :--- |
| **EC-F1: Giải thưởng bằng `0 VND` hoặc chưa công bố số tiền** | Nhiều cuộc thi học thuật chỉ trao học bổng hoặc giấy chứng nhận | Nếu `total_prize_vnd === 0` và `has_scholarship === true`, hiển thị badge `"Học bổng / Tài trợ"`; nếu không, hiển thị `"Theo thể lệ BTC"` thay vì in `0 đ` gây hiểu nhầm |
| **EC-F2: Tên cuộc thi tiếng Việt dài > 80 ký tự** | Dễ làm xô lệch chiều cao thẻ Grid ở `/competitions` | Áp dụng `line-clamp-2` cho tiêu đề thẻ kèm `title={competition.name}`, chỉ hiển thị toàn bộ chuỗi trên `/competitions/[key]` |
| **EC-F3: Lọc đa chiều trả về 0 cuộc thi** | Danh sách trống trơn nếu thiếu trạng thái Empty State | Hiển thị thành phần Empty State kèm thông báo bộ lọc đang kích hoạt và 1 nút `"Xóa toàn bộ bộ lọc"` để đưa người dùng về danh sách gốc ngay |
| **EC-F4: Phản hồi RAG chưa có nguồn (`grounded === false`)** | Chatbot bị hỏi câu ngoài phạm vi 18 cuộc thi | Hiển thị thẻ cảnh báo màu Amber (`#B45309`) ghi rõ chưa tìm thấy điều khoản trong dữ liệu thu thập và ẩn danh sách trích dẫn rỗng |
| **EC-F5: FastAPI tạm ngưng hoặc mất kết nối ở Docker** | Server Component ném lỗi `ECONNREFUSED` khi build hoặc render | Không làm sập toàn trang (`Application error`): tạo tệp `error.tsx` và `loading.tsx` cho từng phân hệ để hiển thị khung trạng thái tải (Skeleton) và nút `"Thử kết nối lại"` |

---

## 5. Verification & Acceptance Criteria

1. **Kiểm tra kiểu tĩnh & Hợp đồng API:** Chạy `npm run typecheck` (`tsc --noEmit`) bên trong `apps/web/` với `0` lỗi kiểu giữa JSX props và `types/api.d.ts`.
2. **Biên dịch Production Standalone:** Lệnh `npm run build` trong `apps/web/` hoàn thành thành công và sinh thư mục `.next/standalone/server.js` không báo lỗi Server/Client boundary.
3. **Kiểm định Giao diện đa kích thước:** Kiểm tra bố cục không xuất hiện thanh cuộn ngang (`overflow-x`) ở 3 độ rộng chuẩn `375px` (di động), `768px` (máy tính bảng) và `1440px` (màn hình laptop).
4. **Kiểm định WCAG 2.2 AA & Bàn phím:** Toàn bộ liên kết, bộ lọc, nút mở trích dẫn RAG và chuyển đổi Light/Dark Mode đều truy cập được bằng phím `Tab` và `Enter`, có vòng focus rõ ràng (`focus-visible:ring-2`).
