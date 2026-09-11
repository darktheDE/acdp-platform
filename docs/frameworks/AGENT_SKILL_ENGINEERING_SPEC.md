# ACDP AI Agent Skill Engineering & Optimization Specification
> **Standard Operating Procedure for Skill Authoring, Optimization, and Evaluation across AI Agents**  
> **Applicable Agents**: Google Antigravity, Claude Code, Gemini CLI, Cursor, Windsurf  
> **Repository**: `acdp-platform` | Faculty of Information Technology, HCMUTE  

---

## 1. Executive Intent: Ending "Cosmetic / Fake Skills"

Trong phát triển phần mềm với sự trợ giúp của AI Agent, việc tạo ra một **Skill** không thể chỉ dừng lại ở việc sinh ra một vài dòng Prompt chung chung (ví dụ: *"Bạn là một lập trình viên Frontend giỏi, hãy viết code sạch"*). Nếu chỉ viết như vậy:
- **Không mang lại giá trị gia tăng**: Mô hình nền tảng (LLM) vốn đã có sẵn tri thức lập trình chung; một prompt sáo rỗng chỉ làm tiêu tốn context window vô ích.
- **Thiếu tính ràng buộc và kiểm chứng**: Không có bộ kiểm tra cú pháp, không có kịch bản chạy thử (script), không có tài liệu tham chiếu (references) và không lường trước các trường hợp biên (edge cases).
- **Rủi ro Instruction Bleeding**: Skill kích hoạt sai ngữ cảnh, làm nhiễu loạn các chỉ dẫn kiến trúc quan trọng khác.

Tài liệu này thiết lập **quy chuẩn kỹ thuật bắt buộc (Engineering Specification)** khi tạo mới, tối ưu hóa hoặc kích hoạt bất kỳ **Skill** nào trong thư mục `.agents/skills/`.

---

## 2. Nguồn Nghiên cứu & Cơ sở Lý luận Chuẩn Quốc tế (Authoritative Sources)

Quy chuẩn này được tổng hợp và chuẩn hóa trực tiếp từ 4 nguồn tài liệu kỹ thuật hàng đầu trong ngành AI Agent:

1. **The Agent Skills Open Standard (`agentskills.io`)**:
   - Tiêu chuẩn mở về cấu trúc thư mục skill, đặc tả YAML frontmatter (`name`, `description`, `compatibility`, `metadata`), nguyên lý phân tầng tải ngữ cảnh.
   - *Tài liệu tham khảo*: [Agent Skills Specification (agentskills.io)](https://agentskills.io) & [Agent Skills Best Practices](https://agentskills.io/docs/best-practices).
2. **Anthropic Engineering Research: "Building Effective Agents" & Context Engineering**:
   - Nguyên lý: *"Tool and skill descriptions act as prompts"* – Mỗi token trong phần mô tả là một chỉ dẫn kích hoạt.
   - Nguyên tắc phân định: **Tính Tất định (Determinism)** của Scripts vs. **Khả năng Suy luận (Reasoning)** của LLM.
   - Phát triển dựa trên đánh giá (*Evaluation-Driven Development*): Thử nghiệm skill với các ca kiểm thử thực tế và tinh chỉnh dựa trên lỗi sai thường gặp.
   - *Tài liệu tham khảo*: [Anthropic Research - Building Effective Agents](https://www.anthropic.com/research/building-effective-agents).
3. **Google Antigravity & Gemini CLI Customization Architecture**:
   - Cơ chế phát hiện (Discovery), thứ tự ưu tiên nạp (Precedence) và kỹ thuật Progressive Disclosure (nạp theo nhu cầu).
   - Phân định ranh giới giữa: **Rules** (luật bất biến gắn với thư mục), **Skills** (sổ tay nghiệp vụ nạp theo nhu cầu), **Subagents** (tiến trình cô lập ngữ cảnh) và **MCP Servers** (giao thức kết nối công cụ ngoại vi).
   - *Tài liệu tham khảo*: [Antigravity Customization System (`builtin/skills/agy-customizations`)](file:///C:/Users/VIP/.gemini/antigravity-cli/builtin/skills/agy-customizations/SKILL.md).
4. **Nghiên cứu về Hiện tượng "Lost in the Middle" & Context Budgeting**:
   - Giữ thân file chính dưới 500 dòng và 5.000 token để tránh suy giảm độ chú ý của mô hình chú ý (Attention Degradation).
   - *Tài liệu tham khảo*: Liu et al., *"Lost in the Middle: How Language Models Use Long Contexts"*, Stanford & UC Berkeley.

---

## 3. Cấu trúc Thư mục Chuẩn của một Agent Skill (Modular Anatomy)

Mỗi skill bắt buộc phải là một thư mục độc lập đặt dưới `.agents/skills/<skill-name>/` với cấu trúc sau:

```text
.agents/skills/<skill-name>/
├── SKILL.md                  # [BẮT BUỘC] Tệp chỉ dẫn chính kèm YAML frontmatter chuẩn
├── scripts/                  # [BẮT BUỘC nếu có tác vụ tự động] Mã lệnh thực thi tất định (Python, Bash, Node)
│   ├── validate.py           # Kịch bản kiểm tra cú pháp, schema, linter tự động
│   └── test_spike.sh         # Kịch bản chạy thử nghiệm nhanh (smoke test)
├── references/               # [BẮT BUỘC nếu có tài liệu chuyên sâu] Tri thức miền, catalog lỗi, cheat sheet
│   ├── api_specs.md          # Chi tiết thông số API hoặc hợp đồng dữ liệu
│   └── gotchas.md            # Các lỗi thường gặp và cách khắc phục
├── examples/                 # [KHUYẾN NGHỊ] Mẫu triển khai chuẩn (Few-shot learning)
│   └── sample_contract.json  # Dữ liệu mẫu hoặc mã nguồn mẫu chất lượng cao
└── resources/                # [TÙY CHỌN] Template, asset tĩnh hoặc dữ liệu kiểm thử
```

---

## 4. Bộ 6 Quy tắc Vàng Bắt buộc (The 6 Invariant Rules)

Mọi Skill khi được Agent hoặc Kỹ sư khởi tạo trong `acdp-platform` phải tuân thủ nghiêm ngặt 6 quy tắc sau:

### Quy tắc 1: Kiến trúc Phân tầng Ngữ cảnh (3-Tier Progressive Disclosure)
Không bao giờ nhồi nhét toàn bộ tài liệu vào bộ nhớ của mô hình cùng lúc. Quá trình xử lý phải qua 3 bước:
1. **Tier 1 - Khám phá (Discovery - Metadata)**: Chỉ có `name` và `description` trong YAML frontmatter được nạp vào system prompt ban đầu. Dung lượng tối đa: **1.024 ký tự**.
2. **Tier 2 - Kích hoạt (Activation - Core Workflow)**: Khi prompt của người dùng trùng khớp với mô tả, toàn bộ nội dung tệp `SKILL.md` mới được nạp vào context. Dung lượng khuyến nghị: **Dưới 500 dòng và dưới 5.000 tokens**.
3. **Tier 3 - Thực thi (Execution - Deep References & Scripts)**: Các tệp trong `references/` và `scripts/` **chỉ được đọc hoặc chạy khi có bước chỉ dẫn cụ thể trong `SKILL.md` yêu cầu**.

### Quy tắc 2: Đặc tả YAML Frontmatter & Kỹ thuật Negative Triggers
- **Ngôi xưng**: Luôn viết ở **ngôi thứ ba (Third-person)** mang tính mệnh lệnh khách quan (Ví dụ: *"Activate this skill when..."*, tuyệt đối không viết *"I can help you..."*).
- **Từ khóa kích hoạt (Positive Triggers)**: Liệt kê rõ các động từ và danh từ nghiệp vụ cụ thể mà người dùng thường gõ.
- **Điều kiện loại trừ (Negative Triggers - Chống kích hoạt nhầm)**: Bắt buộc nêu rõ các trường hợp **KHÔNG ĐƯỢC** kích hoạt skill để tránh hiện tượng *Instruction Bleeding* (Ví dụ: *"DO NOT activate this skill for backend API design or database migrations"*).

```yaml
---
name: frontend-designer
description: >-
  Design and build accessible, responsive UI/UX mockups, Tailwind CSS components,
  and Next.js 15 pages for the student portal and faculty dashboard.
  Use when the user asks for: UI previews, wireframes, Next.js components, Tailwind styling, or Recharts data widgets.
  DO NOT use for: Backend FastAPI REST routes, database migrations, or web scraping pipelines.
compatibility: Next.js 15+, React 19, Tailwind CSS v4, TypeScript 5.6+
---
```

### Quy tắc 3: Nguyên tắc Tách biệt: Tất định vs. Suy luận (Determinism vs. Reasoning)
- **Tác vụ Tất định (Deterministic Tasks)**: Kiểm tra linting, format code, validate schema JSON, check link hỏng, tính toán checksum... **BẮT BUỘC PHẢI VIẾT BẰNG SCRIPT** trong thư mục `scripts/` (ví dụ `python scripts/validate_schema.py`). Tuyệt đối không để LLM "tự đoán" hoặc tự tính nhẩm các tác vụ cơ học này.
- **Tác vụ Suy luận (Reasoning Tasks)**: Thiết kế giải thuật, tổng hợp văn phong, phân tích cảm xúc, cấu trúc giao diện UX... Giao cho LLM thực hiện dựa trên hướng dẫn từng bước.

### Quy tắc 4: Bộ nhớ Ngoài Một Tầng (Externalized References Rule)
- Đưa toàn bộ bảng mã lỗi, danh sách token màu sắc, đặc tả OpenAPI chi tiết vào thư mục `references/`.
- Trong `SKILL.md`, chỉ dẫn rõ liên kết tương đối:  
  *Ví dụ: "Khi gặp lỗi liên quan đến hydrat hóa React, xem hướng dẫn xử lý tại [`references/hydration-troubleshooting.md`](./references/hydration-troubleshooting.md)"*.
- **Giới hạn độ sâu**: Thư mục `references/` chỉ sâu đúng 1 cấp thư mục, không tạo cấu trúc lồng nhau phức tạp làm agent bị lạc đường dẫn.

### Quy tắc 5: Đánh giá & Kiểm thử Ngược (Evaluation-Driven Quality Gate)
Một skill chỉ được coi là hoàn thiện khi có:
1. **Verification Checklist**: Danh sách các lệnh kiểm tra tự động chạy được (ví dụ `ruff check`, `pytest`, `npm run lint`).
2. **Gotchas Catalog**: Liệt kê tối thiểu 3 lỗi sai phổ biến mà các AI agent thường mắc phải khi làm tác vụ đó kèm cách khắc phục (ví dụ: quên khai báo `'use client'`, import sai icon Lucide, hallucinate tham số Tailwind v4).
3. **Smoke Test Example**: Một ví dụ mẫu đầu vào và đầu ra chuẩn đặt trong `examples/` để agent tự đối sánh (Few-shot grounding).

### Quy tắc 6: Nguyên tắc Không Trùng lặp Tri thức Cơ bản (Anti-Duplication)
- Không giải thích lại những kiến thức căn bản mà mô hình LLM đã biết rất rõ (ví dụ: *"React useState là gì"*, *"Cách viết câu lệnh if trong Python"*).
- Tập trung 100% vào: **Ràng buộc đặc thù của dự án ACDP**, quy ước đặt tên của HCMUTE, cấu trúc thư mục JIT, và các chuẩn mực đã được phê duyệt trong `ADR-0001` và `SPEC-0001`.

---

## 5. Mẫu Chuẩn Cho Tệp `SKILL.md` (Production-Grade Template)

```markdown
---
name: [skill-name-lowercase-with-hyphens]
description: >-
  [Động từ hành động] [Mục tiêu cụ thể] using [Công nghệ cốt lõi].
  Trigger on: [Danh sách từ khóa người dùng thường nhắc].
  DO NOT use for: [Các tác vụ không thuộc phạm vi skill].
compatibility: [Yêu cầu môi trường / phiên bản thư viện]
---

# [Tên Đầy Đủ Của Kỹ Năng]

[Đoạn tóm tắt 2-3 câu về vai trò của Agent khi kích hoạt kỹ năng này].

---

## 1. Trigger Conditions & Boundaries
- **Kích hoạt khi**:
  - [Trường hợp 1]
  - [Trường hợp 2]
- **Không kích hoạt khi**:
  - [Trường hợp biên 1]

---

## 2. Invariant Project Standards (Ràng buộc Bất biến)
- [Chuẩn công nghệ 1]: Tuân thủ [Tên SPEC/ADR liên quan](../../docs/specs/...).
- [Chuẩn công nghệ 2]: Không được vi phạm [Quy định cụ thể].

---

## 3. Step-by-Step Execution Protocol (Quy trình Thực thi Từng bước)

### Bước 1: [Thu thập / Khởi tạo dữ liệu mẫu]
- Chạy script kiểm tra: `python scripts/check_preconditions.py`
- Đối chiếu schema: Xem [`references/schema-guide.md`](./references/schema-guide.md).

### Bước 2: [Thực hiện Logic Cốt lõi]
- [Hướng dẫn chi tiết từng thao tác kỹ thuật].

### Bước 3: [Xác minh & Đánh giá Kết quả]
- Chạy lệnh kiểm thử: `[Command]`
- Tiêu chí nghiệm thu: [Các điều kiện đầu ra bắt buộc].

---

## 4. Edge Cases & Gotchas (Lỗi Thường Gặp & Cách Khắc Phục)
| Tình huống / Lỗi phát sinh | Nguyên nhân | Cách khắc phục |
| :--- | :--- | :--- |
| [Tên lỗi 1] | [Lý do] | [Hành động cụ thể] |
| [Tên lỗi 2] | [Lý do] | [Hành động cụ thể] |

---

## 5. Reference Links
- Schema chuẩn: [`references/data-contract.md`](./references/data-contract.md)
- Ví dụ triển khai: [`examples/sample-output.json`](./examples/sample-output.json)
```

---

## 6. Quy trình Tạo Mới Skill Theo Nhu cầu (JIT Skill Lifecycle)

Khi triển khai một tác vụ mới mà repository chưa có sẵn skill tương ứng:
1. **Không tạo skill rỗng**: Tuyệt đối không tạo file `.md` chỉ chứa vài dòng prompt đơn giản rồi chạy ngay.
2. **Nghiên cứu tri thức miền**:
   - Sử dụng công cụ tìm kiếm hoặc đọc tài liệu công nghệ chính thức.
   - Xác định rõ các thông số kỹ thuật, lỗi thường gặp (gotchas) và lệnh kiểm tra.
3. **Đóng gói đầy đủ cấu trúc**:
   - Viết `SKILL.md` đầy đủ Frontmatter, Protocol, Gotchas.
   - Tạo ít nhất 1 script kiểm tra hoặc 1 tài liệu tham chiếu chi tiết trong `references/`.
4. **Đăng ký vào Hệ thống**:
   - Khai báo tên skill vào bảng danh mục trong [`AGENTS.md`](../../AGENTS.md) và [`.agents/skills/README.md`](../../.agents/skills/README.md).
   - Đảm bảo kiểm thử thử nghiệm (dry-run) thành công trước khi áp dụng vào việc giải quyết task lớn.
