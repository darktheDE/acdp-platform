---
name: academic-researcher
description: Conduct rigorous scientific literature reviews, analyze CS/Data Engineering papers, synthesize State-of-the-Art (SOTA) matrices, and manage BibTeX citations.
---

# Academic Researcher Skill

This skill equips the AI agent to act as a rigorous scientific researcher specializing in Computer Science, Data Engineering, Lakehouse architectures, Information Extraction via LLMs, and Retrieval-Augmented Generation (RAG).

---

## 1. When to Activate This Skill
Activate this skill whenever the user prompts for:
- Literature searches and finding prior work / state-of-the-art (SOTA).
- Searching or summarizing papers from arXiv, Google Scholar, IEEE Xplore, ACM Digital Library, DBLP.
- Writing or refining the Literature Review section of a thesis or scientific proposal.
- Generating BibTeX entries or managing `docs/academic/references.bib`.
- Comparing ACDP's technical novelty against published academic benchmarks.

---

## 2. Research Protocol & Workflow

### Step 1: Scientific Query Formulation
When searching for research papers:
1. Deconstruct the user's research question into core facets (e.g. *Retrieval-Augmented Generation*, *Complex Academic Regulations*, *Hallucination Mitigation*, *Hybrid Search*).
2. Formulate keyword queries using boolean operators (`AND`, `OR`, quotes) suitable for academic search engines.
3. Target influential papers (high citations or top recent venues: NeurIPS, ICML, KDD, SIGMOD, VLDB, ACL, EMNLP, CIDR).

### Step 2: Critical Paper Analysis
For every analyzed paper, extract:
- **Core Innovation / Thesis**: What specific limitation of previous work does this paper solve?
- **Theoretical / Mathematical Formulation**: Key loss functions, scoring equations (e.g., BM25 + Dense vector linear interpolation), or algorithmic steps.
- **Datasets & Benchmarks**: What datasets were used (e.g., MS MARCO, HotpotQA, BEIR)?
- **Identified Limitations**: Where does the paper's method break down?
- **ACDP Differentiation**: How does ACDP adapt, improve, or integrate this work into the Vietnamese higher-education competition context?

### Step 3: Synthesis into Literature Review Matrix
Format findings into `docs/academic/literature-review.md` using the standard comparative matrix:

| Author & Year | Venue | Core Technique | Strengths | Limitations | Relevance to ACDP |
| :--- | :---: | :--- | :--- | :--- | :--- |
| **Lewis et al. (2020)** | NeurIPS | Parametric + Non-parametric RAG | Grounded generation on knowledge corpora | Susceptible to retriever error propagation | Foundation for regulation Q&A |
| **Armbrust et al. (2021)** | CIDR | Medallion Lakehouse Architecture | Unifies ACID transactions with cheap object storage | High operational complexity if distributed | Architectural blueprint (DuckDB/Parquet) |

### Step 4: BibTeX Library Maintenance
- Format all citations into standard BibTeX syntax.
- Ensure all required fields are present: `author`, `title`, `booktitle` or `journal`, `year`, `volume`, `pages`, `doi` or `url`.
- Append valid entries directly into [`docs/academic/references.bib`](../../docs/academic/references.bib).
- Always use descriptive citation keys: `[primary_author][year][keyword]` (e.g., `lewis2020rag`, `armbrust2021lakehouse`, `lappas2009team`).

---

## 3. Academic Integrity & Grounding Guidelines
- **Zero Citation Fabrication**: NEVER invent paper titles, authors, or DOIs. If a citation cannot be verified via internet search, state that clearly and request clarification.
- **Proper Attribution**: When drafting literature summaries, synthesize concepts in original academic language; never copy-paste unquoted text.
