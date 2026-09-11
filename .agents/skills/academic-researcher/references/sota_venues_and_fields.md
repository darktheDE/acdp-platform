# SOTA Academic Venues & Search Protocols for ACDP

This reference guide lists top-tier publication venues, keyword search taxonomies, and BibTeX standards for the ACDP literature review.

---

## 1. Top-Tier Publication Venues (Core Domains)

### Data Engineering, Databases & Systems
- **SIGMOD**: ACM SIGMOD Conference on Management of Data
- **VLDB**: International Conference on Very Large Data Bases
- **CIDR**: Conference on Innovative Data Systems Research (*Medallion Lakehouse paper venue*)
- **ICDE**: IEEE International Conference on Data Engineering

### Artificial Intelligence & Retrieval (RAG / Information Extraction)
- **NeurIPS**: Neural Information Processing Systems (*Original RAG paper venue*)
- **ICML**: International Conference on Machine Learning
- **KDD**: ACM SIGKDD Conference on Knowledge Discovery and Data Mining
- **ACL / EMNLP**: Association for Computational Linguistics / Empirical Methods in NLP
- **SIGIR**: ACM SIGIR Conference on Research and Development in Information Retrieval

---

## 2. Academic Search Syntax Cheatsheet

When formulating search queries on Google Scholar, arXiv, or Semantic Scholar:

- **RAG for Administrative Rules**:
  ```text
  ("Retrieval-Augmented Generation" OR "RAG") AND ("administrative" OR "regulatory" OR "legal QA") AND ("hallucination mitigation" OR "faithful generation")
  ```
- **Information Extraction from Semi-Structured Web**:
  ```text
  ("LLM" OR "Large Language Model") AND ("web scraping" OR "unstructured text") AND ("schema extraction" OR "structured output")
  ```
- **Team Recommendation / Expert Finding**:
  ```text
  ("team formation" OR "expert finding") AND ("complementary skills" OR "vector similarity") AND ("social networks" OR "hackathon")
  ```

---

## 3. BibTeX Cleanliness Guidelines

1. **Title Capitalization**: Protect acronyms and proper names with braces: `{ICPC}`, `{LLM}`, `{RAG}`, `{DuckDB}`.
2. **Author Names**: Always format as `Lastname, Firstname and Lastname, Firstname`.
3. **DOIs**: Use canonical alphanumeric form without the `https://doi.org/` prefix when filling the `doi` field.
