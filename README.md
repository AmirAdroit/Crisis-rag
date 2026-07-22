# همیار بحران — Crisis Survival Skills RAG Assistant

A domain-restricted RAG chatbot for rapid crisis-survival training across ~20 topics
(first aid, natural disasters, human-caused crises, emergency kits, utility outages, …).
Replies in the user's language (Persian or English) and supports multi-turn follow-ups.

Stack: an **OpenAI-compatible LLM** (local **Qwen2.5-7B-Instruct** via Ollama by default,
provider-swappable to a hosted API) + **RAG** + **Prompt Engineering**, with multilingual
embeddings, a reranker, Qdrant vector DB, and a FastAPI service.

---

## Features (web UI)

`app/static/index.html` is a single-file, dark, RTL app with four tabs:

- **گفتگو (chat)** — RAG chat with **multi-turn** context (last ~3 turns, client-side) and a **«گفتگوی جدید»** reset button to start fresh. Replies in the user's language.
- **حالت اضطرار (Panic Mode)** — tap an emergency (earthquake, severe bleeding, fire, CPR, flood, shelter) → full-screen, one-step-at-a-time guidance with a fixed 115 call bar.
- **جعبه‌ابزار نجات (SOS)** — alarm + whistle (WebAudio), a Morse-SOS screen strobe, and a GPS location beacon.
- **کیت اضطراری (go-bag)** — a downloadable SVG infographic + a checklist with a readiness score saved in `localStorage`.

Panic Mode, SOS, and the kit are **fully client-side** and work offline (no backend/model). Only chat calls the API.

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
- **Domain guard + system prompt**: language-matched (Persian/English), domain-only (reranker-score guard), source-grounded, safety-first. Refuses off-topic and asks a clarifying question when a scenario is ambiguous.

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

## 8. Hosted LLM (OpenRouter / any OpenAI-compatible API)

No GPU, no local LLM — use a hosted API. The code is already provider-agnostic
via env vars (`app/rag.py:45-49`). The easiest option is **OpenRouter** with free
models.

### Free models (July 2026)

| Model ID | Context | Notes |
|---|---|---|
| `google/gemma-4-31b-it:free` | 262K | **Recommended** — multilingual, strong Persian |
| `nvidia/nemotron-3-super-120b-a12b:free` | 1M | Strong reasoning, English-primary |
| `nvidia/nemotron-3-nano-30b-a3b:free` | 256K | Lighter, faster |

Rate limits: 20 req/min, 50 req/day (bump to 1,000/day with a one-time $10 purchase).

### Quick start

```bash
# Set env vars
export LLM_BASE_URL="https://openrouter.ai/api/v1"
export LLM_API_KEY="sk-or-YOUR_KEY_HERE"
export LLM_MODEL="google/gemma-4-31b-it:free"

# Run (bare metal)
uvicorn app.server:app --host 0.0.0.0 --port 8080
```

### Docker (no GPU)

```bash
# Edit .env with your key, then:
docker compose -f docker-compose.yml -f docker-compose.openrouter.yml up -d --build
docker compose exec app python -m scripts.ingest
```

The `docker-compose.openrouter.yml` override disables the GPU `llm` service and
injects the three env vars into the app container.

### Test connection

```bash
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer sk-or-YOUR_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{"model":"google/gemma-4-31b-it:free","messages":[{"role":"user","content":"test"}]}'
```

### Server requirements (API-only, no GPU)

| Resource | Minimum | Recommended |
|---|---|---|
| CPU | 2 cores | 4+ cores |
| RAM | 4 GB | 8 GB |
| Disk | 5 GB | 10 GB |
| GPU | None | None |

Only Qdrant + embedder (~560 MB) + reranker (~1-2 GB) + FastAPI run locally.

---

## 9. API

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

## 10. Example queries & expected behavior

| Query (fa) | Behavior |
|---|---|
| خونریزی شدید را چطور کنترل کنم؟ | Grounded first-aid steps + 115 reminder, cites bleeding doc |
| برای کاهش استرس در بحران چه کنم؟ | 4-7-8 breathing / 5-4-3-2-1, cites stress doc |
| اگر بوی گاز حس کردم چه کار کنم؟ | Shut main valve, ventilate, no flames/switches, evacuate |
| پایتخت فرانسه کجاست؟ | **Refuses** — out of domain, redirects to crisis topics |

---

## 11. Project structure

```
crisis-rag/
├── app/
│   ├── rag.py            # retrieve → rerank → guard → generate
│   └── server.py         # FastAPI /chat, /health
├── scripts/
│   └── ingest.py         # build the vector index
├── data/raw/*.md         # Persian knowledge base (edit me)
├── configs/config.yaml   # all knobs in one place
├── .env                  # API keys (gitignored)
├── Dockerfile
├── docker-compose.yml               # full stack (GPU required)
├── docker-compose.openrouter.yml    # override: hosted API, no GPU
└── requirements.txt
```

---

## 12. Maintenance & testing

- **Update knowledge**: edit `data/raw/*.md`, re-run `python -m scripts.ingest`. No retraining.
- **Tune relevance**: the primary out-of-domain guard is `domain.min_rerank_score` (reranker score, default `0.02`). Raise it if it answers off-topic; lower if it over-refuses. `domain.min_relevance_for_answer` (vector score) is only the fallback when the reranker is disabled.
- **Evaluate**: keep a `tests/qa.jsonl` of question→expected-source pairs; assert the correct `source` appears in `sources` (retrieval accuracy is the thing to measure for RAG).

---

## 13. Current status, known limitations & roadmap

**Status (2026-06):** functional end-to-end. All current work lives on branch
`feature/answer-quality-rescue-tools` (**not yet merged to `master`**). Knowledge base = 24
topics / 167 chunks. Verified end-to-end on the local `qwen2.5:7b-instruct` (earthquake,
buried-person, English burn first-aid, off-topic refusal, multi-turn follow-up all pass).

**What was built this round:** the 3 offline rescue tools (Panic Mode, SOS toolkit, Emergency
go-bag), multi-turn chat + «گفتگوی جدید» reset, language matching (English in → English out),
the reranker-score refusal guard, provider-swappable LLM (env vars), and 4 new first-aid docs
(burns/choking/fracture/CPR).

**Known limitations (candidate backlog):**
- **LLM quality is the #1 lever.** Local Qwen-7B is weak at Persian (occasional awkward/invented
  phrasing). Fix = swap to a better model: finish `ollama pull aya-expanse:8b` (local) or set
  `LLM_BASE_URL`/`LLM_API_KEY`/`LLM_MODEL` to a hosted aggregator (Avalai/OpenRouter). One config
  flip — no code change. **Gated on the user supplying a key or bandwidth.**
- **No automated eval harness yet** — `tests/qa.jsonl` is proposed but not built. Regression
  testing is manual.
- **No bilingual (English) knowledge base** — English questions are answered from Persian chunks
  via prompt-only language matching. Deferred until chunks are expanded/made more robust.
- **Chat needs the backend online** — only the 3 rescue tools work offline. On-device/offline
  chat was explicitly deprioritized (unrealistic on a phone).
- **Single-file frontend** (`app/static/index.html`, vanilla JS) — fine for now; would need
  componentizing if the UI grows.
- **No auth, rate limiting, or deployment config** for a public/hosted launch.

**Deferred (decided not-this-round):** bilingual KB, offline/hybrid chat fallback.
