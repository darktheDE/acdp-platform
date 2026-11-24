# Competitor Benchmarks & Strategic Positioning

This document evaluates the competitive landscape of student academic competitions and hackathons, establishing ACDP's Unique Value Proposition (UVP) for higher education institutions in Vietnam.

---

## 1. Competitive Landscape Overview

We analyze four major existing paradigms:
1. **Global Hackathon Aggregators** (e.g. *Devpost*, *HackerEarth*): Primarily tailored to US/European corporate hackathons; rely entirely on organizers manually submitting listings.
2. **EdTech Contest Platforms** (e.g. *Unstop / Dare2Compete*): Focuses heavily on Indian business school and engineering competitions; requires enterprise sponsorship to publish.
3. **Data Science Platforms** (e.g. *Kaggle Community Competitions*): Limited strictly to machine learning tabular/CV challenges; no team matchmaking across general engineering domains.
4. **Current Status Quo in Vietnam**: University clubs, youth unions (*Đoàn - Hội*), and faculty fanpages post fragmented JPEG flyers and status updates on Facebook.

---

## 2. Five-Dimensional Feature Comparison Matrix

| Feature Dimension | Devpost | Unstop | Status Quo (VN Facebook) | ACDP Platform |
| :--- | :---: | :---: | :---: | :---: |
| **Data Ingestion Method** | Manual Organizer Post | Manual Paid Listing | Manual Social Post | **Automated Multi-Source Scraper (Crawl4AI/Playwright)** |
| **Coverage of VN Contests** | $< 5\%$ | $< 2\%$ | High, but fragmented | **Comprehensive & Consolidated** |
| **Rulebook Q&A** | Static Text Only | Static Text Only | None (Buried in comments) | **RAG Copilot (BM25 + Qdrant Vectors)** |
| **Team Matchmaking** | Forum Thread | Basic Search | Word of mouth | **Vector Skill Complementarity Engine** |
| **Faculty / Mentor Matching**| ❌ No | ❌ No | ❌ No | **✅ Yes (Research Interest Alignment)** |
| **Faculty Administrative BI** | ❌ No | Enterprise Only | ❌ No | **✅ Yes (Domain & Student Analytics)** |
| **Cost to Student** | Free | Freemium | Free | **100% Free & Open Source** |

---

## 3. SWOT Analysis for ACDP

### Strengths (S)
- Eliminates manual event registration via automated headless web scraping and LLM parsing.
- Native Vietnamese language support for academic regulation RAG queries.
- Built specifically to serve university students, faculty advisors, and department heads.

### Weaknesses (W)
- Dependent on third-party website layouts and social media platform anti-bot measures.
- Requires compute resources for embeddings and vector storage.

### Opportunities (O)
- Potential expansion to all member universities across Vietnam National University and HCMC technical institutes.
- Direct integration with university student information systems (SIS) for automatic activity point (*điểm rèn luyện*) credentialing.

### Threats (T)
- Source platform DOM changes or anti-scraping protections (handled by anti-fragile LLM extraction).
