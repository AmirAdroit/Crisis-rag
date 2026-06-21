# همیار بحران — Crisis Survival Skills RAG Assistant

A Persian-language, domain-restricted RAG chatbot for rapid crisis-survival training:
first aid, stress management, emergency kits, and utility-outage survival.

Stack: **Qwen2.5-7B-Instruct** (vLLM) + **RAG** + **Prompt Engineering**, with
multilingual embeddings, a reranker, Qdrant vector DB, and a FastAPI service.

---

## 1. Architecture

```
                ┌─────────────────────────────────────────────────────┐
   User (fa)    │                  FastAPI  (app/server.py)            │
  ─────────────▶│  POST /chat {question}                              │
                │                      │                               │
                │                      ▼                               │
                │            RAGPipeline (app/rag.py)                  │
                │   1. embed query  ──▶ e5-base (query: prefix)        │
                │   2. vector search ─▶ Qdrant (top_k=12)              │
                │   3. rerank        ─▶ bge-reranker-v2-m3 (top_n=4)   │
                │   4. domain guard  ─▶ refuse if low relevance        │
                │   5. build context + system prompt                  │
                │   6. generate      ─▶ Qwen2.5-7B via vLLM (OpenAI API)│
                │                      │                               │
                │   {answer, sources} ◀┘                               │
                └─────────────────────────────────────────────────────┘
       Offline (one-time):  data/raw/*.md ─▶ scripts/ingest.py ─▶ Qdrant
```

**Components & responsibilities**
- **Knowledge base** (`data/raw/*.md`): curated Persian crisis content, the single source of truth.
- **Ingestion** (`scripts/ingest.py`): normalize Persian text, heading-aware chunking, embed, upsert to Qdrant.
- **Embedder** (`multilingual-e5-base`): turns Persian text into vectors; strong Persian, CPU-friendly.
- **Vector DB** (Qdrant): cosine similarity search over chunks.
- **Reranker** (`bge-reranker-v2-m3`): reorders candidates by true relevance, cuts noise before the LLM.
- **LLM** (Qwen2.5-7B-Instruct via vLLM): generates grounded Persian answers.
- **Domain guard + system prompt**: enforce Persian-only, domain-only, source-grounded, safety-first behavior.

**Data flow**: query → embed → retrieve 12 → rerank to 4 → relevance check → grounded prompt → Qwen → answer + citations.

---

## 2. Why this design (justifications)

- **RAG + prompt engineering over fine-tuning**: small, factual, frequently-updated, safety-critical domain. RAG keeps knowledge in editable docs, gives citations, and avoids hallucination. No training data or GPU-hours needed. Fine-tuning (LoRA/QLoRA/full) would bake knowledge into weights — hard to update, risky for medical accuracy.
- **Qwen2.5-7B-Instruct**: strong Persian, Apache-2.0 (commercially safe), great instruction-following and RAG grounding, fits a single 24GB GPU at 4-bit/fp8. Alternatives rejected: Aya (CC-BY-NC, non-commercial), Gemma (restrictive license), Llama 3.1 (weaker Persian), Persian-only models (weaker instruction-following). Low on VRAM? Switch to **Qwen2.5-3B-Instruct** in `configs/config.yaml`.

---

## 3. Knowledge base creation

- **Collect**: official first-aid orgs (Red Crescent / Red Cross), disaster-management agencies, FEMA-equivalent guides — translated/adapted to Persian and verified.
- **Format**: Markdown (`.md`) with `#` title and `##` sections. Simple, diff-able, and the chunker is heading-aware.
- **Chunking**: heading-aware, ~500 chars with 80-char overlap. Persian is information-dense; this keeps each section coherent without splitting steps.
- **Metadata**: every chunk stores `title`, `section`, `category` (one of the four domains), and `source`. Used for citations and could enable category filtering.

---

## 4. Hardware requirements

| | Minimum | Recommended |
|---|---|---|
| **GPU** | 1× 12GB (e.g. RTX 3060) running Qwen-3B, or none (CPU/llama.cpp) | 1× 24GB (RTX 3090/4090) for Qwen-7B fp8 |
| **CPU** | 4 cores | 8+ cores |
| **RAM** | 16 GB | 32 GB |
| **Disk** | 30 GB | 50 GB SSD (model + caches) |

No GPU? Serve Qwen via **llama.cpp/Ollama** in GGUF Q4 on CPU (slower, ~6–8 GB RAM for 7B). See §7.

---

## 5. Installation — Linux (local dev, bare metal)

```bash
# System deps
sudo apt update && sudo apt install -y python3.11 python3.11-venv git

# Project
git clone <your-repo> crisis-rag && cd crisis-rag
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Start Qdrant (Docker is easiest even for local dev)
docker run -d -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant:v1.11.3

# Serve the LLM (GPU). Installs vLLM and serves an OpenAI-compatible API on :8000
pip install vllm==0.6.2
vllm serve Qwen/Qwen2.5-7B-Instruct --max-model-len 8192 --quantization fp8

# In config.yaml set base_url + qdrant url to localhost when running bare metal:
#   llm.base_url: http://localhost:8000/v1
#   vector_store.url: http://localhost:6333

# Build the index, then run the API
python -m scripts.ingest
uvicorn app.server:app --host 0.0.0.0 --port 8080
```

---

## 6. Installation — Docker (one command)

```bash
# Requires Docker + NVIDIA Container Toolkit for the GPU LLM service.
export HF_TOKEN=hf_xxx   # optional, only if a gated model is used

docker compose up -d --build        # starts qdrant + vLLM + app
# Wait for vLLM to finish loading (watch: docker compose logs -f llm)

# Build the knowledge index inside the app container:
docker compose exec app python -m scripts.ingest

# Test it:
curl -s http://localhost:8080/health
```

---

## 7. No-GPU alternative (Ollama)

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:7b        # or qwen2.5:3b for low RAM
ollama serve                  # exposes http://localhost:11434

# Ollama is OpenAI-compatible at /v1. In config.yaml:
#   llm.base_url: http://localhost:11434/v1
#   llm.model_name: qwen2.5:7b
```

---

## 8. API

`POST /chat`
```json
{ "question": "خونریزی شدید را چطور کنترل کنم؟" }
```
Response:
```json
{
  "answer": "ابتدا با پارچه تمیز فشار مستقیم و محکم روی زخم وارد کنید...",
  "sources": [
    {"title": "کمک‌های اولیه: خونریزی شدید", "section": "فشار مستقیم",
     "category": "کمک‌های اولیه", "source": "first_aid_bleeding.md"}
  ]
}
```

`curl` example:
```bash
curl -s -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"در بسته اضطراری چه چیزهایی باید باشد؟"}' | jq
```

---

## 9. Example queries & expected behavior

| Query (fa) | Behavior |
|---|---|
| خونریزی شدید را چطور کنترل کنم؟ | Grounded first-aid steps + 115 reminder, cites bleeding doc |
| برای کاهش استرس در بحران چه کنم؟ | 4-7-8 breathing / 5-4-3-2-1, cites stress doc |
| اگر بوی گاز حس کردم چه کار کنم؟ | Shut main valve, ventilate, no flames/switches, evacuate |
| پایتخت فرانسه کجاست؟ | **Refuses** — out of domain, redirects to crisis topics |

---

## 10. Project structure

```
crisis-rag/
├── app/
│   ├── rag.py            # retrieve → rerank → guard → generate
│   └── server.py         # FastAPI /chat, /health
├── scripts/
│   └── ingest.py         # build the vector index
├── data/raw/*.md         # Persian knowledge base (edit me)
├── configs/config.yaml   # all knobs in one place
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## 11. Maintenance & testing

- **Update knowledge**: edit `data/raw/*.md`, re-run `python -m scripts.ingest`. No retraining.
- **Tune relevance**: raise `domain.min_relevance_for_answer` if it answers off-topic; lower if it over-refuses.
- **Evaluate**: keep a `tests/qa.jsonl` of question→expected-source pairs; assert the correct `source` appears in `sources` (retrieval accuracy is the thing to measure for RAG).
