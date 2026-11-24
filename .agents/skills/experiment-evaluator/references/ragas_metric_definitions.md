# Ragas Metric Definitions & Mathematical Formulations

This document provides the theoretical definitions and mathematical formulations of the RAG evaluation metrics applied in the ACDP empirical benchmarks.

---

## 1. Faithfulness (Groundedness / Anti-Hallucination)

Measures the factual consistency of the generated answer against the retrieved context:

$$\text{Faithfulness} = \frac{|\text{Number of claims in generated answer that can be inferred from context}|}{|\text{Total number of claims in generated answer}|}$$

- **Target Threshold**: $> 0.90$
- **Academic Relevance**: Critical for competition rules where hallucinating an eligibility deadline or team constraint could disqualify students.

---

## 2. Answer Relevance

Evaluates how directly the generated answer addresses the original query, penalizing redundant or incomplete outputs:

$$\text{Answer Relevance} = \frac{1}{N} \sum_{i=1}^{N} \text{CosineSimilarity}(E(q), E(q_i^{\text{gen}}))$$

where $q_i^{\text{gen}}$ are synthetic questions generated back from the answer and $E(\cdot)$ is the text embedding.
- **Target Threshold**: $> 0.85$

---

## 3. Context Precision

Measures whether all ground-truth relevant chunks are ranked at the top of the retrieval results:

$$\text{Context Precision@K} = \frac{\sum_{k=1}^{K} (\text{Precision@}k \times v_k)}{\text{Total number of relevant chunks in top } K}$$

where $v_k \in \{0, 1\}$ denotes the binary relevance of the chunk at rank $k$.
- **Target Threshold**: $> 0.85$

---

## 4. Context Recall

Assesses whether the retriever fetched all necessary information required to formulate the complete answer:

$$\text{Context Recall} = \frac{|\text{Number of ground-truth sentences attributed to retrieved context}|}{|\text{Total number of sentences in ground-truth answer}|}$$

- **Target Threshold**: $> 0.80$
