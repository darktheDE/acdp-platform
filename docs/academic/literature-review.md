# State-of-the-Art (SOTA) Literature Review Matrix

This document provides a systematic review of scientific literature foundational to the ACDP system architecture across four technical domains:
1. **Medallion Data Lakehouse Architectures**
2. **Automated Web Ingestion & LLM Information Extraction**
3. **Retrieval-Augmented Generation (RAG) on Administrative Text**
4. **Team Formation & Expert Recommendation Algorithms**

---

## 1. Comparative Literature Review Matrix

| Domain | Paper & Author | Core Innovation | Strengths | Limitations | Application in ACDP |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Data Lakehouse** | *Armbrust et al. (2021)* - CIDR | Unifies data warehousing (ACID, schema enforcement) with data lakes (Parquet, low cost). | Solves data duplication, enables high-performance OLAP directly on object storage. | Heavy operational complexity when deployed on distributed engines (Spark/Delta). | ACDP implements an embedded Medallion Lakehouse (`DuckDB` + `Parquet`), achieving Lakehouse guarantees with zero cluster overhead. |
| **Information Extraction** | *Xu et al. (2024)* - arXiv | Survey of LLM-based zero-shot and few-shot information extraction on unstructured text. | High adaptability across schema variations; eliminates brittle rule-based regex parsers. | High latency and potential token cost; non-deterministic formatting without schema constraints. | ACDP pairs headless browser crawlers (`Crawl4AI`, `Playwright`) with `Pydantic` schema enforcement, guaranteeing strictly valid JSON. |
| **RAG Systems** | *Lewis et al. (2020)* - NeurIPS | Combining non-parametric memory (dense vector retrieval) with parametric generator (seq2seq LLM). | Answers knowledge-intensive queries by citing retrieved factual documents. | Susceptible to retriever error propagation and hallucinated numbers/dates. | ACDP implements Hybrid Search (`BM25` for exact dates/fees + `Qdrant` dense vectors) combined with `Cross-Encoder` re-ranking. |
| **RAG Survey** | *Gao et al. (2023)* - arXiv | Categorizes Naive, Advanced, and Modular RAG paradigms. | Establishes benchmarks for pre-retrieval chunking, re-ranking, and post-retrieval compression. | Does not address Vietnamese administrative/academic document structures. | ACDP adopts Modular RAG with structured clause-based chunking tailored to Vietnamese university competition rulebooks. |
| **Team Formation** | *Lappas et al. (2009)* - KDD | Formulating team formation as finding a skill-covering team minimizing communication cost. | Formal mathematical guarantees on skill complementarity and network density. | Computationally NP-hard; does not model vector embeddings of student soft skills or research alignment. | ACDP adapts the problem using vector cosine similarity for skill complementarity paired with rule-based academic constraints. |

---

## 2. Research Gap Addressed by ACDP

Existing commercial platforms (Devpost, Unstop) rely on manual event registration by organizers. In the Vietnamese higher-education landscape, over 90% of competition announcements remain locked in unstructured social media posts, fanpage graphics, and student union announcements. 

ACDP bridges this gap by creating an **autonomous, end-to-end data pipeline** that transforms unstructured public feeds into a structured, Lakehouse-backed knowledge base with hallucination-resistant RAG search and skill-complementary team formation.
