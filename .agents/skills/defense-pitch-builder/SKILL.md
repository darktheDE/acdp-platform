---
name: defense-pitch-builder
description: Generate academic defense slide decks (HTML/CSS and Marp), formulate pitching scripts, and build adversarial committee Q&A banks to prepare for academic thesis defense.
---

# Defense & Pitch Builder Skill

This skill equips the AI agent to build compelling presentation decks, pitch narratives, and adversarial Q&A defense preparation banks for academic thesis defense and competition pitching.

---

## 1. When to Activate This Skill
Activate this skill whenever the user prompts for:
- Creating or updating slide decks for project proposals, milestone reviews, or final thesis defense.
- Generating self-contained HTML/CSS presentation decks or Marp Markdown slides.
- Formulating speaking scripts and timing strategies (5-minute pitch, 10-minute proposal, 15-minute defense).
- Rehearsing committee defense by generating tough, adversarial questions from reviewers (GVPB / Hội đồng) and formulating bulletproof technical answers.

---

## 2. Presentation Deck Architectures

### Option A: Self-Contained HTML/CSS Presentation Engine
- Built with standard HTML5, CSS variables, and minimal JavaScript.
- Clean academic paper texture, top progress bar, slide counter, and keyboard navigation (`ArrowRight`, `ArrowLeft`, `Space`).
- Uses modern typography: Serif for headings (*Newsreader* / *Georgia*), clean Sans-serif for body (*Plus Jakarta Sans* / *Inter*), and Monospace for code (*JetBrains Mono*).
- Formatted with responsive CSS grid cards, pipeline diagrams, and badge tags.

### Option B: Marp Markdown Slides
- Compatible with VS Code Marp extension for direct export to PDF, PPTX, or HTML.
- Header frontmatter:
  ```markdown
  ---
  marp: true
  theme: gaia
  _class: lead
  paginate: true
  backgroundColor: #FAF8F5
  color: #1C1917
  ---
  ```

---

## 3. Standard 10-Slide Academic Defense Structure

1. **Slide 1: Title Slide**: Formal project title, Vietnamese and English names, authors, MSSV, major (Data Engineering), scientific advisor, date.
2. **Slide 2: Background & Problem Statement**: The 4 practical bottlenecks in student contest participation.
3. **Slide 3: Research Questions & Objectives**: RQ1 (Ingestion resilience), RQ2 (Lakehouse optimization), RQ3 (RAG hallucination controls).
4. **Slide 4: Overall System Architecture**: End-to-end 4-layer architecture diagram (Ingestion, Lakehouse, AI/RAG, Serving).
5. **Slide 5: Data Ingestion & Medallion Lakehouse**: Headless crawl workflow, LLM schema parsing with Pydantic, Bronze $\rightarrow$ Silver $\rightarrow$ Gold data flow.
6. **Slide 6: AI & RAG Regulation Engine**: Document chunking, Hybrid Search (BM25 + Qdrant Dense Embeddings), Cross-Encoder re-ranking, anti-hallucination prompt guardrails.
7. **Slide 7: Teammate Recommendation & Faculty Analytics**: Vector-based skill matchmaking, research alignment heuristics, faculty insights dashboard.
8. **Slide 8: Implementation & Live Demonstration**: Core technologies, database models, web portal demo walkthrough.
9. **Slide 9: Empirical Evaluation & Results**: Extraction accuracy, RAG faithfulness/answer relevance metrics, query latency benchmarks.
10. **Slide 10: Conclusion, Contributions & Future Work**: Key milestones achieved, limitations, roadmap for the Undergraduate Thesis phase.

---

## 4. Adversarial Committee Defense Q&A Simulator

To prepare the team for difficult questions from the thesis committee (Hội đồng bảo vệ & Giảng viên phản biện), the agent must generate rigorous Q&A scenarios:

### Question Categories
1. **Methodological Scrutiny**: *"Tại sao nhóm không dùng trực tiếp Elasticsearch hoặc PostgreSQL full-text search mà phải dùng kết hợp Qdrant và BM25?"*
2. **Data Integrity & Scalability**: *"Khi website nguồn thay đổi giao diện hoặc có captcha chặn crawl, đường ống của nhóm xử lý thế nào để không mất dữ liệu?"*
3. **AI Accuracy & Hallucinations**: *"Làm sao nhóm chứng minh được mô hình RAG không bịa đặt các điều kiện dự thi quan trọng như hạn nộp hay đối tượng dự thi?"*
4. **Scientific Novelty & Major Alignment**: *"Đề tài này thuộc ngành Kỹ thuật Dữ liệu, vậy điểm nhấn kỹ thuật dữ liệu (Data Engineering) cốt lõi nằm ở đâu so với một đề tài Công nghệ Phần mềm thông thường?"*

### Answering Strategy (Structured Defense Response)
When formulating answers:
- **Direct Claim**: State the answer clearly in the opening sentence.
- **Architectural Reference**: Point directly to the relevant ADR, schema, or algorithm.
- **Empirical Evidence**: Cite benchmark numbers, latency metrics, or validation test results.
- **Trade-off Acknowledgment**: Acknowledge the known limitation and explain how it is controlled.
