# CLAUDE.md — Crisis RAG Project

## Project Overview
RAG chatbot ("همیار بحران") for crisis survival skills, grounded in a curated markdown knowledge base covering ~20 disaster/first-aid topics. Replies in the user's language (Persian or English), supports multi-turn follow-ups, and refuses off-topic questions.

Stack: FastAPI + Qdrant (vector DB) + multilingual-e5-base (embedder) + bge-reranker-v2-m3 (reranker) + an OpenAI-compatible LLM (local Qwen2.5-7B via Ollama by default; provider-swappable to a hosted API — see below).

The web UI (`app/static/index.html`) has four tabs: **گفتگو** (chat, needs the backend) and three **client-side, offline-capable** tools — **حالت اضطرار** (Panic Mode: step-by-step emergency flows), **جعبه‌ابزار نجات** (SOS: alarm, Morse-SOS strobe, whistle, location beacon), and **کیت اضطراری** (go-bag infographic + checklist). The three tools work with no backend/network.

## Web UI (`app/static/index.html`)
Single-file vanilla-JS app, dark RTL Persian theme. A tab bar switches four views:

- **گفتگو (chat)** — the RAG chat. Multi-turn: keeps the last ~3 turns client-side and sends them as `history`; a **«گفتگوی جدید»** button (`resetChat()`) clears the messages **and** that context to start fresh. Only this tab needs the backend.
- **حالت اضطرار (Panic Mode)** — tappable emergency tiles (زلزله، خونریزی، آتش‌سوزی، CPR، سیل، بمباران) open a full-screen, one-step-at-a-time guided flow with a fixed «تماس با ۱۱۵» bar. Steps are hard-coded in the `FLOWS` object in the page JS.
- **جعبه‌ابزار نجات (SOS)** — WebAudio alarm + whistle, a screen strobe flashing Morse SOS (···———···), and a GPS location beacon.
- **کیت اضطراری (go-bag)** — a generated inline SVG infographic poster (downloadable) + an interactive checklist whose progress persists in `localStorage` (`hamyar_kit_v1`).

Panic Mode, SOS, and the kit are **pure client-side** — no backend, network, or model — so they keep working offline. A standalone feature prototype also lives at `prototype/demo.html`.

## Running on Windows 10 (No Docker)

Three services must be running before starting the app — in separate terminals:

**1. Qdrant** (binary already downloaded to `tools\qdrant.exe`; original: github.com/qdrant/qdrant/releases — `qdrant-x86_64-pc-windows-msvc.zip`). Run it from `tools\` so its `storage/` lives there:
```powershell
cd tools; .\qdrant.exe
```

**2. Ollama** (install from ollama.com, then):
```powershell
ollama serve
```

**3. App** (in the project directory with venv activated):
```powershell
.venv\Scripts\activate
uvicorn app.server:app --host 0.0.0.0 --port 8080
```

## First-Time Setup

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install "httpx<0.28"        # fixes openai/httpx version conflict on Windows
python -m scripts.ingest        # builds Qdrant index (downloads ~1.5GB models first run)
```

## Known Issues & Fixes

- **`TypeError: Client.__init__() got an unexpected keyword argument 'proxies'`**: httpx version conflict. Fix: `pip install "httpx<0.28"`.
- **`openai.APIConnectionError`**: Ollama is not running (or `LLM_BASE_URL` is unreachable). Run `ollama serve`.
- **`qdrant_client ... [WinError 10061] ... actively refused it`**: Qdrant is not running. Start `tools\qdrant.exe`.
- **venv `python.exe` fails / "did not find executable"**: the venv was built against a now-removed base interpreter. It needs **CPython 3.13** (its packages are cp313 wheels). Repair in place without re-downloading: `py -3.13 -m venv --upgrade .venv` (install 3.13 first via `py install 3.13`).
- **`curl` JSON errors in PowerShell**: PowerShell's `curl` is an alias for `Invoke-WebRequest`. Use `Invoke-RestMethod`. (From Git Bash, send non-ASCII/Persian bodies via `--data @file.json`, not inline `-d '...'` — Windows curl mangles non-ASCII argv.)

## Testing the API

```powershell
Invoke-RestMethod -Uri http://localhost:8080/chat -Method POST -ContentType "application/json" -Body '{"question":"در زلزله چه کار کنم؟"}' | Select-Object -ExpandProperty answer
```

## Adding New Knowledge

1. Add a `.md` file to `data/raw/` — format: `# Title` then `## Section` headings with Persian content.
2. Re-run `python -m scripts.ingest` — no restart needed, just re-ingest.
3. Filename determines category metadata (see `scripts/ingest.py` CATEGORY dict).

## Config Knobs (`configs/config.yaml`)

- `llm.model_name`: default `qwen2.5:7b-instruct` (use `qwen2.5:3b` if RAM < 16GB)
- `llm.base_url`: `http://localhost:11434/v1` for Ollama local
- `vector_store.url`: `http://localhost:6333` for local Qdrant
- `domain.min_rerank_score`: **primary** out-of-domain guard (reranker score, default `0.02`). Off-topic scores ~0.00, in-domain ≥0.08 — clean gap. Raise if it answers off-topic; lower if it over-refuses.
- `domain.min_relevance_for_answer`: fallback guard (vector score), only used when the reranker is disabled.

## Switching the LLM provider (local ↔ hosted API)
The LLM is any OpenAI-compatible endpoint. `config.yaml` holds the **local** default; override per-run with env vars so real API keys are never committed (`.env` is gitignored):

```powershell
$env:LLM_BASE_URL = "https://api.avalai.ir/v1"   # or openrouter, openai, gemini ...
$env:LLM_API_KEY  = "sk-..."
$env:LLM_MODEL    = "gpt-4o"
uvicorn app.server:app --host 0.0.0.0 --port 8080
```
Read in `app/rag.py` via `os.getenv("LLM_BASE_URL"/"LLM_API_KEY"/"LLM_MODEL")` falling back to config. The local Qwen-7B is weak at Persian (hallucinates terms); a hosted frontier model fixes quality. A better *local* option is `ollama pull aya-expanse:8b` then `LLM_MODEL=aya-expanse:8b`.

## Service Ports

| Service | Port |
|---|---|
| FastAPI app | 8080 |
| Qdrant | 6333 |
| Ollama | 11434 |

## Knowledge Base Files (`data/raw/`)

| File | Topic |
|---|---|
| `first_aid_bleeding.md` | خونریزی شدید |
| `first_aid_burns.md` | سوختگی |
| `first_aid_choking.md` | خفگی با جسم خارجی |
| `first_aid_fracture.md` | شکستگی |
| `first_aid_cpr.md` | احیای قلبی-ریوی (CPR) |
| `emergency_kit.md` | بسته اضطراری |
| `stress_management.md` | مدیریت استرس |
| `utility_outage.md` | قطع خدمات شهری |
| `earthquake.md` | زلزله |
| `tsunami.md` | سونامی |
| `flood_hurricane.md` | سیل و طوفان |
| `volcanic_eruption.md` | آتشفشان |
| `tornado.md` | گردباد |
| `war_conflict.md` | جنگ و درگیری مسلحانه |
| `nuclear_radiation.md` | حوادث هسته‌ای |
| `chemical_biological.md` | حوادث شیمیایی و بیولوژیکی |
| `fire_explosion.md` | آتش‌سوزی و انفجار |
| `drought_water.md` | خشکسالی و کمبود آب |
| `famine_food.md` | قحطی و کمبود غذا |
| `extreme_temperature.md` | گرما و سرمای شدید |
| `pandemic.md` | همه‌گیری و بیماری‌های واگیردار |
| `cyber_infrastructure.md` | قطع زیرساخت‌های حیاتی |
| `search_rescue.md` | جستجو و نجات |
| `navigation_signaling.md` | ناوبری و سیگنال نجات |

## Academic Context (ITPM Course)

This project is the practical deliverable for the **IT Project Management (ITPM)** course. It is presented as a fully functional, deployable AI system — not a throwaway exercise.

**Team:**
| Member | Role |
|---|---|
| امیرمسعود آشوری | مدیر پروژه و توسعه‌دهنده ارشد |
| مجیدرضاکریمی | مهندسی هوش مصنوعی و RAG |
| محمد مجتبی کچویی | توسعه‌دهنده بک‌اند و یکپارچه‌سازی |

**Final submission deadline: Tir 12, 1404 (~July 3, 2026) at 16:00** — submitted via the LMS.

**Final delivery is 7/10 of the total grade, split into 3 parts:**

| Part | Points | Deliverable |
|---|---|---|
| Part 1 | 2 pts | 10-minute video: project intro, KPIs, challenges + lessons learned, live product demo |
| Part 2 | 2 pts | Comprehensive written report (Day 1 → final delivery) |
| Part 3 | **3 pts** | Direct assessor access to **Jira** + **Notion** with full project history |

**Part 3 requirements (highest points — prioritize):**
- **Jira** (self-hosted): Agile-compliant board, epics, sprints, all tasks assigned to team members, time tracking from start of term, future backlog defined. Assessors will log in directly.
- **Notion**: Architecture decision log, meeting notes, sprint retrospectives, AI usage log, technical documentation. Assessors will log in directly.

**Date note:** Jira and Notion were not set up from day one. When backfilling project history into these tools, sprint start/end dates and task creation dates need to reflect when work actually happened during the term — not today's date. For self-hosted Jira, creation dates can be adjusted via admin SQL/API. This is standard practice when migrating an existing project's history into a PM tool.
