---
name: academic-researcher
description: >-
  Conduct rigorous scientific literature reviews, analyze CS/Data Engineering papers,
  synthesize State-of-the-Art (SOTA) comparative matrices, and manage BibTeX citations.
  Use when the user asks for: paper summaries, literature reviews, SOTA matrices, BibTeX entries, or academic grounding.
  DO NOT use for: Writing informal blog posts, conversational user chats, frontend code, or database migrations.
compatibility: Python 3.13+, BibTeX, Markdown, LaTeX
---

# Academic Researcher Skill

This skill equips the AI agent to operate as a rigorous academic researcher in Computer Science and Data Engineering, focusing on Lakehouse architectures, Information Extraction, and Retrieval-Augmented Generation (RAG).

---

## 1. Trigger Conditions & Boundaries

- **Activate when**:
  - Searching for peer-reviewed literature across arXiv, IEEE Xplore, ACM DL, DBLP, and Google Scholar.
  - Synthesizing comparative literature matrices for thesis chapters or proposals.
  - Adding, validating, or formatting BibTeX citations in [`docs/academic/references.bib`](../../docs/academic/references.bib).
  - Benchmarking ACDP’s architectural claims against published academic papers.
- **DO NOT activate when**:
  - Writing code implementations (FastAPI, Next.js).
  - Designing slide animations or UI layouts.
  - Reviewing business competitor marketing pitches without peer-reviewed substance.

---

## 2. Invariant Academic Standards

1. **Zero Citation Hallucination**: NEVER fabricate a citation, paper title, author list, or DOI. If a paper cannot be verified via search or DBLP/arXiv, explicitly notify the user.
2. **Standardized Citation Keys**: Must use the strict pattern `[primary_author][year][keyword]` (e.g. `lewis2020rag`, `armbrust2021lakehouse`, `lappas2009team`).
3. **Mandatory BibTeX Fields**: Every entry must include `author`, `title`, `year`, and one of (`booktitle`, `journal`, `archivePrefix`).
4. **Authoritative Venues**: Prioritize top-tier venues cataloged in [`references/sota_venues_and_fields.md`](./references/sota_venues_and_fields.md) (NeurIPS, ICML, KDD, SIGMOD, VLDB, CIDR, ACL, EMNLP).

---

## 3. Step-by-Step Execution Protocol

### Step 1: Scientific Query Formulation
Deconstruct research questions using Boolean operators (`AND`, `OR`, exact quotes). Query authoritative venues for recent work (2023–2026).

### Step 2: Critical Paper Deconstruction
Extract 5 mandatory facets for each analyzed paper:
1. *Core Innovation*: Specific limitation solved.
2. *Algorithmic / Mathematical Formulation*: Loss function, scoring formula, or data flow.
3. *Empirical Benchmark*: Test datasets and baseline comparisons.
4. *Known Limitations*: Breakdown conditions or scalability bottlenecks.
5. *ACDP Integration*: How ACDP applies or improves upon this concept.

### Step 3: Synthesis into Literature Matrix
Format into `docs/academic/literature-review.md` following the reference structure in [`examples/sample_sota_matrix.md`](./examples/sample_sota_matrix.md).

### Step 4: BibTeX Validation Gate
Always run the deterministic BibTeX validator after editing citations:
```bash
python .agents/skills/academic-researcher/scripts/validate_bibtex.py --file docs/academic/references.bib
```

---

## 4. Edge Cases & Gotchas Catalog

| Gotcha / Common Failure Mode | Root Cause | Enforced Solution |
| :--- | :--- | :--- |
| **Hallucinated DOIs / URLs** | LLM predicting plausible-looking DOI hashes | Verify DOI against CrossRef / arXiv ID. If unverified, omit DOI and use clean URL. |
| **Malformed BibTeX syntax** | Missing closing brace or unescaped `%` / `&` characters | Escape special characters (`\%`, `\&`) and wrap titles with `{}` to preserve capitalization. |
| **Vague Relevance to ACDP** | Generic summary without domain grounding | Explicitly state how the paper influences ACDP's Lakehouse, RAG, or Ingestion layer. |

---

## 5. Verification Checklist

- [ ] Execute `python .agents/skills/academic-researcher/scripts/validate_bibtex.py --file docs/academic/references.bib`.
- [ ] Ensure all papers cited in text have matching keys in `references.bib`.
- [ ] Confirm venue ranking and publication year are verified against DBLP / Google Scholar.
