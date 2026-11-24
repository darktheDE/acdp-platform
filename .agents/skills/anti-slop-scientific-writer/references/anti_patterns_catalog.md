# Catalog of AI Structural Tropes & Anti-Patterns

> **Repository**: `acdp-platform`  
> **Source Grounding**: Synthesized from international empirical directories (`tropes.fyi`, *The Writing Whip*) and academic communication standards.

---

## 1. Top 10 High-Severity Structural Anti-Patterns

### 1. Negative Parallelism ("It's not X — it's Y")
- **Definition**: The single most common AI tell. The model negates a premise in one clause only to reframe it in the next, generating cheap rhetorical drama and false profundity.
- ❌ **Bad (AI Slop)**:
  - *"It's not bold. It's backwards."*
  - *"The question isn't whether to migrate to DuckDB. The question is when to execute."*
  - *"Không phải là thiếu dữ liệu, mà là thiếu quy chuẩn chuẩn hóa."*
- ✅ **Good (Scientific Directness)**:
  - *"This architecture is technically unviable."*
  - *"Migration to DuckDB requires establishing an execution schedule based on memory quotas."*
  - *"Hệ thống hiện thiếu quy chuẩn chuẩn hóa dữ liệu đầu vào."*

---

### 2. Announce-Then-Answer Preamble (Throat-Clearing)
- **Definition**: Starting the response by announcing what will be done, restating the prompt, or narrating steps instead of giving the answer.
- ❌ **Bad (AI Slop)**:
  - *"In this section, we will delve into the vector indexing architecture. Let's break this down step-by-step."*
  - *"Dưới đây là câu trả lời chi tiết cho thắc mắc của bạn về cấu trúc Parquet..."*
- ✅ **Good (Scientific Directness)**:
  - Start immediately with the technical analysis:  
    *"Vector indexing uses HNSW graphs with cosine distance metrics. Ingestion executes through the following pipeline:"*

---

### 3. Sycophancy & Fake Enthusiasm
- **Definition**: Flattering the user before answering, or agreeing with false premises to avoid polite friction.
- ❌ **Bad (AI Slop)**:
  - *"That's a fantastic question! You have great insight into data lakehouses."*
  - *"Chắc chắn rồi! Ý kiến của bạn rất tuyệt vời, tôi hoàn toàn đồng ý."*
- ✅ **Good (Scientific Directness)**:
  - Jump directly to objective analysis. If a premise is flawed, correct it politely and factually:  
    *"Qdrant is an in-memory or on-disk vector database, not a replacement for analytical SQL engines like DuckDB."*

---

### 4. The Tie-Back Loop
- **Definition**: Closing a response by summarizing what was just said and restating the user's original query.
- ❌ **Bad (AI Slop)**:
  - *"So, to answer your question: yes, DuckDB supports direct Parquet scanning. This gives you everything you need to ship."*
  - *"Tóm lại, như tôi đã trình bày ở trên, hệ thống của bạn hoàn toàn có thể triển khai thành công."*
- ✅ **Good (Scientific Directness)**:
  - Deliver the technical conclusion and stop. No conversational bookends.

---

### 5. Fractal Summaries (Summarizing at Every Level)
- **Definition**: Inserting summaries into every subsection, followed by a summary of the section, followed by a document-level summary.
- ❌ **Bad (AI Slop)**:
  - Starting with *"In this chapter we will examine X..."*, ending section 1 with *"As we have seen, X is important..."*, and ending the document with *"In conclusion, this chapter examined X, Y, and Z."*
- ✅ **Good (Scientific Directness)**:
  - Omit repetitive intros and outros. Allow each technical section to deliver its core data table, formula, or code block directly.

---

### 6. Reasoning Leaks (Voiceover of Internal Deliberation)
- **Definition**: Narrating the agent's internal planning process or decision tree inside the final output.
- ❌ **Bad (AI Slop)**:
  - *"I want to be precise about my own role here. I considered using PostgreSQL, but I will opt for DuckDB to keep dependencies lean."*
  - *"Tôi đang cân nhắc giữa hai giải pháp và sau khi suy nghĩ, tôi quyết định..."*
- ✅ **Good (Scientific Directness)**:
  - Present the selected architecture and the technical trade-offs objectively:  
    *"DuckDB was selected over PostgreSQL for local analysis to eliminate network serialization overhead for 500MB Parquet partitions."*

---

### 7. Em-Dash Addiction
- **Definition**: Overusing em-dashes (`—` or `--`) as dramatic pauses or parenthetical asides.
- ❌ **Bad (AI Slop)**:
  - *"The problem — and this is the part nobody talks about — is latency, which — unexpectedly — degraded by 40%."*
- ✅ **Good (Scientific Directness)**:
  - Use standard punctuation (periods, commas, parentheses):  
    *"The primary issue is query latency, which degraded by 40% under concurrent write loads."*

---

### 8. Monotonous Bold-First Bullet Points
- **Definition**: Formatting every single bullet point with an identical bold keyword prefix (`- **Keyword**: Explanation`).
- ❌ **Bad (AI Slop)**:
  - `- **Performance**: The system achieves low latency.`
  - `- **Security**: Tokens are kept in memory.`
  - `- **Scalability**: DuckDB handles parquet files.`
- ✅ **Good (Scientific Directness)**:
  - Use flowing prose or markdown tables for structured properties:
    | Dimension | Implementation | Verification |
    | :--- | :--- | :--- |
    | Performance | P95 latency < 120ms | Tested via Locust |
    | Security | In-memory token storage | Zero secrets in git |

---

### 9. Grandiose Stakes Inflation
- **Definition**: Inflating ordinary engineering decisions into world-historical transformations.
- ❌ **Bad (AI Slop)**:
  - *"This caching strategy will fundamentally revolutionize how students discover academic competitions forever."*
- ✅ **Good (Scientific Directness)**:
  - *"Redis caching reduces database query load by 78% during peak search windows."*

---

### 10. Hypophora (Manufactured Rhetorical Questions)
- **Definition**: Posing a rhetorical question that nobody asked, then immediately answering it for artificial suspense.
- ❌ **Bad (AI Slop)**:
  - *"The result? A catastrophic 500 Internal Server Error."*
  - *"Câu hỏi đặt ra là gì? Đó chính là hiệu năng của bộ nhớ cache."*
- ✅ **Good (Scientific Directness)**:
  - *"The request failed with HTTP 500 due to an unhandled memory overflow."*
  - *"Hiệu năng hệ thống phụ thuộc trực tiếp vào tỷ lệ trúng bộ nhớ đệm (cache hit ratio)."*

---

## 2. Additional Tropes (Quick Reference)

11. **Compulsive Counting**: Stating the number of points before listing them (*"Three constraints shape the design..."* $\rightarrow$ Just list the constraints).
12. **Invented Concept Labels**: Coining pretentious compound nouns (*"the supervision paradox"*, *"prompt debt"*).
13. **Rule of Three Pattern**: Forcing every sentence into a rhythmic tricolon (*"They compile. They run. They scale."*).
14. **Belaboring the Unnecessary**: Defending uncontroversial facts against imaginary objections.
15. **Vague Attributions**: Citing unnamed authorities (*"Industry experts suggest..."*, *"Observers argue..."* $\rightarrow$ Name the paper/author or omit).
16. **Synonym Cycling**: Refusing to repeat a technical term and cycling synonyms (*"the lakehouse... the storage layer... the data repository... the analytical vault"* $\rightarrow$ Stick to "lakehouse").
17. **Appeal to Familiarity**: Claiming consensus without proof (*"As we all know"*, *"Famously"*).
18. **Promotional Copy**: Writing like a marketing brochure instead of a computer scientist (*"an all-in-one seamless powerhouse"*).
19. **Wh-word Headings**: Overusing *"Where the system breaks"*, *"What we do differently"* as headings.
20. **Forced Analogies**: Inserting unsolicited metaphors (*"Think of DuckDB as a high-speed Formula 1 pit crew"* $\rightarrow$ Explain the vectorized engine).
21. **Title Case Headings**: Capitalizing every word in headings (*"Configuring The Database Connection"* $\rightarrow$ *"Configuring the database connection"*).
22. **Superficial -ing Clauses**: Tacking participle phrases at the end of sentences (*"..., highlighting its immense importance in modern computer science"* $\rightarrow$ Delete).
23. **Short Punchy Sentence Stacking**: Writing artificial staccato paragraphs (*"Clean code. Fast builds. Zero bugs. Real impact."*).
24. **The "Serves As" Dodge**: Using *"serves as"*, *"stands as"*, *"marks"* instead of direct verbs *"is"*, *"represents"*, *"measures"*.
25. **"Despite Its Challenges" Reflex**: Raising a critical design vulnerability only to handwave it away with optimistic fluff.
