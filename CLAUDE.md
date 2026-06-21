# CLAUDE.md — Crisis RAG Project

## Project Overview
Persian-language RAG chatbot ("همیار بحران") for crisis survival skills. Answers questions in Persian, grounded in a curated markdown knowledge base.

Stack: FastAPI + Qdrant (vector DB) + multilingual-e5-base (embedder) + bge-reranker-v2-m3 (reranker) + Qwen2.5-7B via Ollama (LLM).

## Running on Windows 10 (No Docker)

Three services must be running before starting the app — in separate terminals:

**1. Qdrant** (download Windows binary from github.com/qdrant/qdrant/releases — `qdrant-x86_64-pc-windows-msvc.zip`):
```powershell
.\qdrant.exe
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
- **`openai.APIConnectionError`**: Ollama is not running. Run `ollama serve` in a separate terminal.
- **`curl` JSON errors in PowerShell**: PowerShell's `curl` is an alias for `Invoke-WebRequest` and handles encoding differently. Use `Invoke-RestMethod` instead.

## Testing the API

```powershell
Invoke-RestMethod -Uri http://localhost:8080/chat -Method POST -ContentType "application/json" -Body '{"question":"در زلزله چه کار کنم؟"}' | Select-Object -ExpandProperty answer
```

## Adding New Knowledge

1. Add a `.md` file to `data/raw/` — format: `# Title` then `## Section` headings with Persian content.
2. Re-run `python -m scripts.ingest` — no restart needed, just re-ingest.
3. Filename determines category metadata (see `scripts/ingest.py` CATEGORY dict).

## Config Knobs (`configs/config.yaml`)

- `llm.model_name`: `qwen2.5:7b` or `qwen2.5:3b` (use 3b if RAM < 16GB)
- `llm.base_url`: `http://localhost:11434/v1` for Ollama local
- `vector_store.url`: `http://localhost:6333` for local Qdrant
- `domain.min_relevance_for_answer`: raise if chatbot answers off-topic; lower if it over-refuses

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
