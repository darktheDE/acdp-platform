---
name: ollama-bridge
description: >-
  Set up, configure, and orchestrate Ollama local and cloud open models, embeddings,
  and OpenAI-compatible endpoints for the ACDP platform and RAG chatbot MVP (src/acdp/3_chatbot_mvp.py).
  Use when the user asks to: set up Ollama, switch LLM provider to Ollama, run open models locally,
  use Ollama Cloud (:cloud), pull embedding models (qwen3-embedding, bge-m3), or troubleshoot Ollama connection.
  DO NOT use for: Cloudflare R2 object storage setup, Next.js frontend styling, or database migrations.
compatibility: Ollama v0.40+, LangChain v1.0+, langchain-ollama v1.1+, Python 3.11+, Windows 10/11
---

# Ollama Bridge: Open Models & Embeddings Orchestration Playbook

> **Repository**: `acdp-platform` | Faculty of Information Technology, HCMUTE  
> **Target Module**: [`src/acdp/3_chatbot_mvp.py`](../../src/acdp/3_chatbot_mvp.py)  
> **Hardware Boundary**: AMD Ryzen 5 PRO 4650U (6C/12T) | Integrated AMD Radeon Graphics (512MB VRAM) | 12GB RAM  
> **Authoritative References**: [Ollama Quickstart](https://docs.ollama.com/quickstart.md) | [Ollama GPU Support](https://docs.ollama.com/gpu.md) | [Ollama Cloud](https://docs.ollama.com/cloud.md)

---

## 1. Operating Architecture & Hardware Boundary

Ollama operates in two complementary execution modes:
1. **Local Mode (`http://localhost:11434`)**: Runs open weights directly on the host. On this system (integrated AMD Radeon with 512MB VRAM, unsupported by Windows ROCm), execution runs on the **CPU**. Only lightweight embeddings (`qwen3-embedding:4b`, `bge-m3`) and compact SLMs (1B–3B parameters) are viable.
2. **Cloud Mode (`https://ollama.com`)**: Offloads inference to Ollama cloud servers. No downloads or local VRAM constraints. CLI models append `:cloud` (e.g., `gemma4:cloud`, `llama3.3:cloud`), while API calls point to `https://ollama.com/api` or `https://ollama.com/v1`. Requires user authentication (`ollama signin` or `OLLAMA_API_KEY`).

Deep technical specifications and memory breakdown are maintained in:
👉 [`references/ollama_hardware_and_models.md`](./references/ollama_hardware_and_models.md)

---

## 2. Step-by-Step Operational Workflow

### Step 1: Deterministic Health & Endpoint Verification
Before attempting model pulls or running pipelines, verify that the local daemon and OpenAI-compatible endpoint are responsive:
```powershell
uv run python .agents/skills/ollama-bridge/scripts/validate_ollama.py
```
If the daemon is offline, start the Ollama desktop application or execute:
```powershell
ollama serve
```

### Step 2: Model Management Strategy

#### For Embeddings (Local):
Pull the required embedding model into the local engine:
```powershell
ollama pull qwen3-embedding:4b
# Or lightweight alternative:
ollama pull bge-m3
```

#### For Chat LLM:
- **Option A (Cloud - Recommended for Quality & Speed)**:
  Use large parameter models without consuming local RAM.
  1. Authenticate (User action only):
     ```powershell
     ollama signin
     # Or set API key:
     $env:OLLAMA_API_KEY = "your_key"
     ```
  2. Model targets: `gemma4:31b` (or `gemma4:cloud`), `llama3.3:70b`, `qwen2.5:72b`.
- **Option B (Local SLM - Fully Offline)**:
  Pull a model within the 12GB CPU budget:
  ```powershell
  ollama pull qwen2.5:3b
  ```

### Step 3: Wire into `src/acdp/3_chatbot_mvp.py`
Configure environment variables in `.env` or application config:
```bash
# Vector Embedding (Local Ollama)
EMBEDDING_MODEL=qwen3-embedding:4b
EMBED_BATCH_SIZE=16

# LLM Generation: choose one provider
# 1. Ollama Cloud
LLM_PROVIDER=ollama_cloud
CHAT_MODEL=gemma4:31b
OLLAMA_API_KEY=your_key_here

# 2. Ollama Local (CPU SLM)
# LLM_PROVIDER=ollama_local
# CHAT_MODEL=qwen2.5:3b
# OLLAMA_BASE_URL=http://localhost:11434/v1
```
Implementation code pattern is provided in:
👉 [`examples/chatbot_ollama_integration.py`](./examples/chatbot_ollama_integration.py)

---

## 3. Gotchas & Anti-Patterns Catalog

| Issue / Error Symptom | Root Cause | Deterministic Resolution |
| :--- | :--- | :--- |
| `dial tcp 127.0.0.1: connection refused` during SemanticChunker | Requesting embeddings for hundreds of sentences at once on CPU overloads the runner. | Use `BatchedRetryEmbeddings` with `batch_size <= 16` and exponential backoff. |
| Model inference extremely slow (< 1 token/s) | Attempting to run 7B+ or 14B+ models locally on integrated GPU without ROCm. | Switch `LLM_PROVIDER` to `ollama_cloud` or use compact `qwen2.5:3b`. |
| `401 Unauthorized` on `https://ollama.com` | Missing or invalid `OLLAMA_API_KEY`. | Prompt the user to run `ollama signin` or obtain an API key from `https://ollama.com/settings/keys`. Never generate dummy keys. |
| Port 11434 conflict | Another Ollama process is already running in background. | Check `Get-Process ollama` and verify with `validate_ollama.py`. |

---

## 4. Verification & Quality Checklist

- [x] Run `uv run python .agents/skills/ollama-bridge/scripts/validate_ollama.py` $\rightarrow$ Exit code 0.
- [x] Local daemon responding at `http://localhost:11434/api/version`.
- [x] OpenAI compatibility endpoint active at `http://localhost:11434/v1/models`.
- [x] Hardware memory limits strictly bounded to <= 3B parameters for local execution.

