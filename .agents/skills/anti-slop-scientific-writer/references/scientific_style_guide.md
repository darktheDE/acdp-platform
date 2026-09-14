# Scientific Writing & Technical Documentation Style Guide

> **Repository**: `acdp-platform`  
> **Faculty**: Khoa Công nghệ Thông tin - Trường Đại học Công nghệ Kỹ thuật TP.HCM (HCM-UTE)  
> **Applicable Venues**: Undergraduate Theses, Research Papers, Technical Specs, ADRs, and Formal Documentation.

---

## 1. Core Principles of Scientific Communication

### 1.1. High Information Density (Tỷ Lệ Mật Độ Thông Tin Cao)
- Every sentence must advance the technical argument. If removing a sentence does not alter the reproducibility or empirical conclusions of the work, **delete it**.
- Avoid conversational pleasantries, emotional affirmations, and throat-clearing preambles.
- Maximum paragraph length: 4–6 sentences. A single paragraph must focus on exactly one core empirical observation, mechanism, or architectural constraint.

### 1.2. Quantitative Precision over Qualitative Claims
- **Prohibited**: *"Hệ thống có tốc độ xử lý rất nhanh và chịu tải tốt."*
- **Required**: *"Pipeline đạt thông lượng 450 tài liệu/phút với mức tiêu thụ RAM tối đa 1.8 GB trên cấu hình 8-core CPU."*
- When reporting evaluation metrics (RAG retrieval, latency, extraction accuracy), specify:
  1. The metric name (e.g., Hit Rate@5, MRR@10, F1-score).
  2. The sample size / dataset scale ($N = 1,200$).
  3. The baseline model compared against.

### 1.3. Active vs. Passive Voice Conventions
- **Methodology & Actions**: Use active voice with the research group pronoun (*"Chúng tôi xây dựng mô hình...", "We implement a hybrid retriever..."*).
- **System Behavior & Invariants**: Use direct present tense active voice (*"DuckDB executes queries directly on Parquet files"*, not *"Queries are executed by DuckDB"*).
- **Experimental Results**: State facts directly (*"Table 3 indicates that BM25 achieves a higher recall on keyword queries than dense vector embeddings alone"*).

---

## 2. Document Layout & Typography Standards (.md & .html)

### 2.1. Heading Hierarchy & Capitalization
- Use standard markdown heading hierarchy (`#`, `##`, `###`). Never skip heading levels (e.g., jumping from `#` to `###`).
- Use **Sentence case** for all headings:
  - ✅ `## Data ingestion and vectorization pipeline`
  - ❌ `## Data Ingestion And Vectorization Pipeline`
- Avoid Wh-question headings (*"What is the system doing?"*, *"Why choose DuckDB?"*). Use descriptive nominal phrases (*"System architecture and processing pipeline"*, *"Rationale for selecting DuckDB"*).

### 2.2. Visual Data Representation (Tables & Diagrams over Bullet Lists)
- When comparing 3 or more entities across multiple dimensions, use a Markdown table instead of nested bullet points.
- Use Mermaid diagrams (`mermaid`) for:
  - Sequence of interactions (`sequenceDiagram`).
  - Architectural topologies (`flowchart TD` or `flowchart LR`).
  - State lifecycles (`stateDiagram-v2`).
- Never describe complex relational workflows purely in plain conversational paragraphs when a visual diagram or table conveys it with zero ambiguity.

### 2.3. Hyperlinks and Verifiable Citations
- Every scientific claim regarding external algorithms, models, or university regulations must be backed by a valid citation.
- External URLs must be tested and verified to ensure 100% reachability (zero dead links, conforming to **DIR-006**).

---

## 3. Checklist: Self-Audit Before Finalizing Documents

Before submitting or saving any technical document or response:
- [ ] **Zero Preamble**: Does line 1 immediately deliver the answer, data table, or technical finding?
- [ ] **No AI Slop Words**: Are terms like *delve, tapestry, landscape, testament, crucial, robust, seamless* completely eradicated?
- [ ] **No Negative Parallelism**: Are there any *"It's not X — it's Y"* or *"Không phải X mà là Y"* structures?
- [ ] **Strictly Grounded**: Are all performance assertions backed by measured numbers or documented specs?
- [ ] **Zero Fractal Summaries**: Is there any redundant "In conclusion" or repeated recap at the bottom?
- [ ] **Institutional Accuracy**: Is the institution formatted as **Trường Đại học Công nghệ Kỹ thuật TP.HCM (HCM-UTE)**?
