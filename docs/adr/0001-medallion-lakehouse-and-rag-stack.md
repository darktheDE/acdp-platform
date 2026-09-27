# ADR-0001: Core Architecture, Medallion Lakehouse, and Hybrid RAG Stack (Archived Inception Proposal)

- **Status**: Superseded / Archived Inception Proposal (Subject to Active R&D Tasks & DIR-011)
- **Date**: 2026-09-08
- **Authors**: Do Kien Hung, Nguyen Van Quang Duy
- **Scientific Advisor**: M.Sc. Tran Quang Khai
- **Consulted**: Faculty of Information Technology, HCMUTE

> [!WARNING]
> **Archived Inception Proposal (Tabula Rasa - DIR-011)**:  
> This initial document served as an early proposal draft. In accordance with **DIR-011 (Tabula Rasa in Tech Research)**, all technology selections mentioned herein are unverified starter placeholders.
> 
> Each layer of the architecture is currently being evaluated, benchmarked, and finalized from first principles under [`docs/rd-tasks/`](../rd-tasks/):
> - **Bronze Storage & Open Table Formats**: Under active research in [`T13.md`](../rd-tasks/T13.md) and [`NT-018`](../deliverables/NT-018-bronze-storage-and-table-format-evaluation.md).
> - **Data Ingestion & Discovery**: Under active research in [`T02.md`](../rd-tasks/T02.md) and [`NT-014`](../deliverables/NT-014-competition-landscape-survey.md).
> - **Overall System Architecture**: Under active research in [`T08_v2.md`](../rd-tasks/T08_v2.md).
> 
> Official replacement ADRs will be formally authored and approved only after empirical peer defense between Hưng and Duy is completed.

---

## 1. Architectural Concept & Problem Statement

The Academic Competition Discovery Platform (ACDP) addresses core engineering challenges:
1. Ingesting volatile, semi-structured event announcements from disparate web portals and social media channels.
2. Providing analytical aggregations for university administrators (OLAP) while supporting fast, low-latency relational queries for the student application (OLTP).
3. Answering intricate natural language queries about contest regulations with zero hallucination.

---

## 2. High-Level Architectural Drivers

- **Domain Relevance**: The project is under the Major in Data Engineering; modern data architecture (Medallion Lakehouse, metadata management, structured data extraction) is central.
- **Resilience Against Web Layout Drift**: The ingestion mechanism must be anti-fragile.
- **Accuracy & Grounding**: In academic rules, hallucinating an eligibility requirement or submission deadline is unacceptable.
- **Resource Efficiency**: Must run cost-effectively on local workstations (16GB RAM) or lightweight cloud VMs without requiring multi-node Spark clusters.

---

## 3. High-Level Architectural Pillars (Under Active R&D)

1. **Tiered Medallion Storage Pattern**:
   - `Bronze`: Raw, immutable web payloads and crawl metadata ensuring auditability and replayability.
   - `Silver`: Cleaned, validated, and deduplicated records.
   - `Gold`: Curated dimensional data marts for reporting and application serving.
2. **Anti-Fragile Ingestion**:
   - Dynamic web crawlers combined with LLM Schema Parsers constrained by strict schemas.
3. **Hybrid Search & Grounded Retrieval**:
   - Combining lexical keyword matching with dense vector similarity and re-ranking.
4. **Decoupled Serving & Presentation**:
   - High-throughput asynchronous REST APIs powering interactive student web portals and faculty analytics dashboards.

---

## 4. Current Status

The specific technologies for each pillar are actively being benchmarked under [`docs/rd-tasks/`](../rd-tasks/). Formal Architecture Decision Records (ADRs) will be issued following peer defense dossiers and mutual consensus.
