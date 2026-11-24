# Sample Literature Review & SOTA Matrix (Gold Standard)

The following comparative table illustrates the required formatting and critical depth for the ACDP literature review chapter:

| Author & Year | Venue | Core Technique | Datasets / Evaluation | Identified Limitations | Relevance & Differentiation in ACDP |
| :--- | :---: | :--- | :--- | :--- | :--- |
| **Lewis et al. (2020)** | NeurIPS | Parametric-Memory + Dense Passage Retrieval (DPR) RAG | Natural Questions, TriviaQA, CuratedTREC | Retriever error propagation; high latency for dense index traversal | Provides the foundational architecture for the ACDP competition regulation assistant. |
| **Armbrust et al. (2021)** | CIDR | Medallion Lakehouse Architecture (Delta/Parquet) | TPC-DS, internal enterprise telemetry | Multi-node Spark clusters introduce massive operational overhead for small teams | Inspires ACDP's lean, in-process DuckDB implementation for local workstations. |
| **Xu et al. (2024)** | ACM Survey | LLM-based Information Extraction from Unstructured Web | DocVQA, Few-NERD, WebTables | High token cost; occasional hallucination on malformed HTML DOMs | Justifies ACDP's Pydantic schema enforcement and raw Bronze caching strategy. |
| **Lappas et al. (2009)** | KDD | Expert team formation in social networks with communication costs | DBLP co-authorship graphs | NP-hard complexity; does not incorporate dense skill vector embeddings | Forms the mathematical baseline for ACDP's teammate matchmaking engine. |
| **Gao et al. (2023)** | arXiv | Modular RAG taxonomy (Naive, Advanced, Modular) | Comprehensive literature survey | Lack of unified benchmarks for Vietnamese higher education domain | Establishes the design criteria for ACDP's Hybrid Search + Re-ranking pipeline. |
