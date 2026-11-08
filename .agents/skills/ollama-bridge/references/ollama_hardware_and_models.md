# Ollama Hardware Assessment & Model Selection Matrix (ACDP)

> **Document Type**: Technical Reference & Hardware Feasibility Matrix  
> **Target Service**: `src/acdp/3_chatbot_mvp.py` (RAG Chatbot MVP)  
> **Source Grounding**: [Ollama GPU Documentation](https://docs.ollama.com/gpu.md) & [Ollama Cloud](https://docs.ollama.com/cloud.md)

---

## 1. System Hardware Audit vs. Ollama GPU Requirements

| Parameter | Current Machine Specification | Ollama GPU Requirement (`gpu.md`) | Feasibility & Inference Mode |
| :--- | :--- | :--- | :--- |
| **Operating System** | Windows 10/11 64-bit | Windows 10/11 64-bit | Supported |
| **CPU** | AMD Ryzen 5 PRO 4650U (6 Cores, 12 Threads) | Modern x86_64 AVX2 | Runs CPU inference via llama.cpp backend |
| **System Memory** | 12.0 GB Total RAM (~6.5 GB free after OS) | 16 GB+ recommended for >=7B models | Constrained memory budget |
| **GPU Accelerator** | Integrated AMD Radeon(TM) Graphics (512 MB VRAM) | **AMD ROCm v7 / HIP7 Windows**: Radeon RX 7600–7900 or Radeon PRO W7500–W7900 | ❌ **NOT ROCm Supported** on Windows. Runs via CPU / Vulkan fallback |

### Key Bottleneck Analysis
- The integrated AMD Radeon graphics (Renoir architecture) has only 512 MB dedicated VRAM and is not supported by AMD ROCm on Windows.
- Inference for local models runs primarily on the **CPU** (using system RAM).
- Heavy models (> 4GB VRAM footprint) will cause swapping, high CPU thermals, or crash the Ollama runner process (`dial tcp 127.0.0.1: connection refused`).

---

## 2. Model Selection Matrix: Local vs. Cloud

### A. Recommended Local Models (Low Memory & CPU-Friendly)
Suitable for offline embeddings or lightweight summarization.

| Task | Recommended Model | Disk Size | RAM Footprint | Expected Speed on CPU | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Text Embedding** | `qwen3-embedding:4b` | ~2.5 GB | ~3.0 GB | 15–30 chunks/s | Active default in `3_chatbot_mvp.py`. Keep batch size <= 16. |
| **Text Embedding** | `bge-m3` | ~1.2 GB | ~1.8 GB | 25–50 chunks/s | Multilingual SOTA; very stable on 12GB RAM. |
| **Text Embedding** | `nomic-embed-text` | ~274 MB | ~500 MB | 80–120 chunks/s | Ultra-lightweight fallback. |
| **Local SLM Generation** | `qwen2.5:1.5b` | ~1.0 GB | ~1.8 GB | ~15–25 tokens/s | Fast, handles Vietnamese instructions reasonably well. |
| **Local SLM Generation** | `qwen2.5:3b` / `llama3.2:3b`| ~2.0 GB | ~3.5 GB | ~8–14 tokens/s | Upper limit for comfortable CPU inference without thrashing. |

### B. Recommended Cloud Models (Zero Local Hardware Burden)
Run on Ollama high-performance cloud infrastructure via `https://ollama.com`.

| Model Name (API / CLI) | Parameter Scale | Context Window | Use Case in ACDP | Pricing / Requirements |
| :--- | :--- | :--- | :--- | :--- |
| `gemma4:31b` / `gemma4:cloud` | 31B MoE / Dense | 128k | Complex contest regulation reasoning, multi-document comparison | Ollama Cloud Account / Usage credits |
| `llama3.3:70b` / `llama3.3:cloud` | 70B Dense | 128k | High-accuracy RAG synthesis, detailed rubric analysis | Ollama Cloud Account / Usage credits |
| `qwen2.5:72b` / `qwen2.5:cloud` | 72B Dense | 128k | Superior Vietnamese language comprehension and formal drafting | Ollama Cloud Account / Usage credits |

---

## 3. API Endpoints & Compatibility Cheatsheet

| Target | Direct Cloud Access | Local Ollama Daemon |
| :--- | :--- | :--- |
| **Native Ollama API** | `https://ollama.com/api` | `http://localhost:11434/api` |
| **OpenAI Compatibility** | `https://ollama.com/v1` | `http://localhost:11434/v1` |
| **Anthropic Compatibility**| `https://ollama.com` | `http://localhost:11434` |
| **Auth Header** | `Authorization: Bearer $OLLAMA_API_KEY` | None (omit header) |

---

## 4. Setup Commands Reference

### Authenticate for Cloud Models (Do not automate secrets):
```powershell
# 1. Interactive terminal sign-in:
ollama signin

# 2. Or set API key from https://ollama.com/settings/keys:
$env:OLLAMA_API_KEY = "your_ollama_cloud_key"
```

### Pull Local Models:
```powershell
ollama pull qwen3-embedding:4b
ollama pull qwen2.5:3b
```

