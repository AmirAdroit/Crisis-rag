# مستندات فنی — همیار بحران (Crisis RAG)
## پروژه: HB | نسخه: 1.0.0 | آخرین به‌روزرسانی: ۷ تیر ۱۴۰۴

---

## ۱. معرفی سیستم

**همیار بحران** یک دستیار هوشمند تخصصی است که مهارت‌های بقا در شرایط بحران را به کاربران آموزش می‌دهد. سیستم به فارسی و انگلیسی پاسخ می‌دهد و فقط در حوزه بحران و بلایای طبیعی پاسخ می‌دهد.

### ویژگی‌های اصلی

| ویژگی | توضیح |
|-------|-------|
| پایگاه دانش | ۲۴ موضوع بحران، ۱۶۷ chunk، فارسی |
| دوزبانه | پرسش و پاسخ به فارسی و انگلیسی |
| فیلتر دامنه | رد خودکار سوالات غیرمرتبط |
| چت چندمرحله‌ای | حفظ ۳ مرحله تاریخچه مکالمه |
| ابزارهای آفلاین | ۳ ابزار نجات بدون نیاز به اینترنت |
| قابل‌تعویض | LLM قابل تعویض بدون تغییر کد |

---

## ۲. معماری کلی سیستم

```
┌─────────────────────────────────────────────────────────────┐
│                     کاربر (Browser)                         │
│                   app/static/index.html                     │
│         [چت] [حالت اضطرار] [SOS] [کیت اضطراری]            │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP POST /chat
                           │ {question, history}
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI App (port 8080)                   │
│                      app/server.py                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  RAG Pipeline (app/rag.py)                  │
│                                                             │
│  1. EMBED query                                             │
│     intfloat/multilingual-e5-base (768-dim)                 │
│                                                             │
│  2. RETRIEVE top-10                                         │
│     Qdrant (port 6333) ← cosine similarity                  │
│                                                             │
│  3. RERANK → top-3                                          │
│     BAAI/bge-reranker-v2-m3                                 │
│     ↓ (if max_score < 0.02 → off-topic رد)                 │
│                                                             │
│  4. GENERATE                                                │
│     Ollama/Qwen2.5-7B (port 11434)                          │
│     system prompt + retrieved chunks + history              │
└──────────────────────────┬──────────────────────────────────┘
                           │ {answer, sources}
                           ▼
                        کاربر
```

### سرویس‌های موازی

| سرویس | پورت | فایل اجرایی | نقش |
|-------|------|------------|-----|
| FastAPI + Uvicorn | 8080 | `uvicorn app.server:app` | API + Static files |
| Qdrant | 6333 | `tools/qdrant.exe` | Vector database |
| Ollama | 11434 | `ollama serve` | LLM inference |

---

## ۳. پایپ‌لاین RAG — جزئیات فنی

### مرحله ۱: Ingestion (ساخت ایندکس)

```
data/raw/*.md
      │
      ▼
  ChunkSplitter
  ├── تقسیم بر اساس عنوان‌های Markdown (# و ##)
  ├── حداکثر ~500 کاراکتر هر chunk
  ├── overlap: ~80 کاراکتر (حفظ context)
  └── metadata: {filename, category, heading}
      │
      ▼
  intfloat/multilingual-e5-base
  ├── prefix: "passage: " + متن chunk
  └── خروجی: بردار 768 بُعدی
      │
      ▼
  Qdrant Collection: "crisis_knowledge"
  └── 167 vector + metadata ذخیره شد
```

**اجرای ingestion:**
```powershell
python -m scripts.ingest
```

**زمان اجرا (اولین بار):** ~۵ دقیقه (دانلود مدل ~۲۷۸MB)
**زمان اجرا (دفعات بعد):** ~۳۰ ثانیه

---

### مرحله ۲: Query Pipeline

**ورودی:** `POST /chat` با `{question: str, history: list}`

```python
# 1. Embed سوال کاربر
query_embedding = embed("query: " + question)  # بردار 768-dim

# 2. Retrieve از Qdrant
results = qdrant.search(
    collection_name="crisis_knowledge",
    query_vector=query_embedding,
    limit=10,              # top-10 اولیه
    with_payload=True      # متن + metadata
)

# 3. Rerank
pairs = [(question, r.payload["text"]) for r in results]
scores = reranker.predict(pairs)  # cross-encoder score هر جفت

# 4. Domain Guard
max_score = max(scores)
if max_score < MIN_RERANK_SCORE:  # default: 0.02
    return {"answer": "متأسفم، فقط می‌توانم درباره...", "sources": []}

# 5. انتخاب top-3 chunk
top_chunks = [r for r, s in sorted(zip(results, scores), key=...) if rank < 3]

# 6. ساخت prompt
messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    *history[-3:],  # آخرین 3 مرحله
    {"role": "user", "content": question + "\n\nمنابع:\n" + chunks_text}
]

# 7. فراخوانی LLM
response = openai_client.chat.completions.create(
    model=LLM_MODEL,
    messages=messages,
    max_tokens=1024,
    temperature=0.3
)
```

---

### System Prompt

```
شما «همیار بحران» هستید — یک دستیار تخصصی برای مهارت‌های بقا در شرایط اضطراری.
وظیفه شما ارائه اطلاعات دقیق، ایمن، و کاربردی درباره مدیریت بحران است.

قوانین:
۱. فقط درباره موضوعات بحران، بلایا، کمک‌های اولیه، و مهارت‌های بقا پاسخ دهید
۲. اگر سوال خارج از این حوزه است، ادبانه رد کنید
۳. به همان زبانی که کاربر می‌پرسد پاسخ دهید (فارسی/انگلیسی)
۴. پاسخ‌ها باید مختصر، واضح، و قابل اجرا باشند
۵. برای مواقع اورژانسی، همیشه با «با اورژانس ۱۱۵ تماس بگیرید» شروع کنید
```

---

## ۴. مستندات API

### `POST /chat`

**توضیح:** پرسش از chatbot و دریافت پاسخ بر اساس پایگاه دانش

**URL:** `http://localhost:8080/chat`

**Request Body:**
```json
{
  "question": "در زلزله چه کار کنم؟",
  "history": [
    {"role": "user", "content": "سلام"},
    {"role": "assistant", "content": "سلام! در چه بحرانی می‌توانم کمک کنم؟"}
  ]
}
```

| فیلد | نوع | اجباری | توضیح |
|------|-----|--------|-------|
| `question` | string | ✅ | سوال کاربر به فارسی یا انگلیسی |
| `history` | array | ❌ | تاریخچه مکالمه (حداکثر ۶ پیام = ۳ مرحله) |

**Response (200 OK):**
```json
{
  "answer": "در هنگام زلزله مراحل زیر را انجام دهید:\n۱. بلافاصله زیر میز یا کنار دیوار بروید...",
  "sources": [
    {
      "text": "در هنگام بروز زلزله، اولین اقدام...",
      "metadata": {
        "filename": "earthquake.md",
        "category": "natural_disaster",
        "heading": "اقدامات فوری"
      },
      "score": 0.847
    }
  ]
}
```

| فیلد | نوع | توضیح |
|------|-----|-------|
| `answer` | string | پاسخ تولیدشده توسط LLM |
| `sources` | array | chunk‌های استفاده‌شده (حداکثر ۳) |
| `sources[].score` | float | امتیاز reranker (بالاتر = مرتبط‌تر) |

**Response (off-topic، 200 OK):**
```json
{
  "answer": "متأسفم، تنها در حوزه مهارت‌های بقا و مدیریت بحران می‌توانم کمک کنم.",
  "sources": []
}
```

**مثال با PowerShell:**
```powershell
Invoke-RestMethod -Uri http://localhost:8080/chat `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"question":"در زلزله چه کار کنم؟"}' |
  Select-Object -ExpandProperty answer
```

---

### `GET /health`

**توضیح:** بررسی سلامت سرویس

**Response (200 OK):**
```json
{"status": "ok"}
```

---

### `GET /`

**توضیح:** نمایش رابط کاربری وب (index.html)

**Response:** HTML page

---

## ۵. پایگاه دانش — ساختار و محتوا

### ساختار فایل‌ها

هر فایل در `data/raw/` با فرمت Markdown:

```markdown
# عنوان موضوع

## بخش ۱: توضیحات کلی
متن توضیحات...

## بخش ۲: اقدامات فوری
۱. اولین اقدام
۲. دومین اقدام

## بخش ۳: نکات مهم
...
```

### فهرست موضوعات

| فایل | موضوع | تعداد chunk تقریبی |
|------|-------|------------------|
| earthquake.md | زلزله | ~۱۰ |
| flood_hurricane.md | سیل و طوفان | ~۸ |
| fire_explosion.md | آتش‌سوزی و انفجار | ~۷ |
| first_aid_cpr.md | احیای قلبی-ریوی | ~۶ |
| first_aid_bleeding.md | خونریزی شدید | ~۶ |
| first_aid_burns.md | سوختگی | ~۵ |
| first_aid_fracture.md | شکستگی | ~۵ |
| first_aid_choking.md | خفگی با جسم خارجی | ~۵ |
| emergency_kit.md | کیت اضطراری | ~۷ |
| stress_management.md | مدیریت استرس | ~۶ |
| utility_outage.md | قطع خدمات شهری | ~۵ |
| tsunami.md | سونامی | ~۶ |
| volcanic_eruption.md | آتشفشان | ~۵ |
| tornado.md | گردباد | ~۵ |
| war_conflict.md | جنگ و درگیری مسلحانه | ~۸ |
| nuclear_radiation.md | حوادث هسته‌ای | ~۷ |
| chemical_biological.md | حوادث شیمیایی/بیولوژیکی | ~۷ |
| drought_water.md | خشکسالی و کمبود آب | ~۵ |
| famine_food.md | قحطی و کمبود غذا | ~۵ |
| extreme_temperature.md | گرما و سرمای شدید | ~۶ |
| pandemic.md | همه‌گیری | ~۷ |
| cyber_infrastructure.md | قطع زیرساخت‌های دیجیتال | ~۵ |
| search_rescue.md | جستجو و نجات | ~۶ |
| navigation_signaling.md | ناوبری و سیگنال‌دهی | ~۶ |
| **مجموع** | **۲۴ موضوع** | **۱۶۷ chunk** |

### پارامترهای Chunking

| پارامتر | مقدار | توضیح |
|---------|-------|-------|
| max_chunk_size | ~500 کاراکتر | حداکثر طول هر chunk |
| overlap | ~80 کاراکتر | تداخل بین chunk‌های متوالی |
| split_strategy | heading-aware | اولویت تقسیم روی عنوان‌های MD |

---

## ۶. پیکربندی سیستم (`configs/config.yaml`)

```yaml
llm:
  model_name: "qwen2.5:7b-instruct"   # مدل پیش‌فرض Ollama
  base_url: "http://localhost:11434/v1"
  api_key: "ollama"
  max_tokens: 1024
  temperature: 0.3

vector_store:
  url: "http://localhost:6333"
  collection_name: "crisis_knowledge"

retrieval:
  top_k: 10                  # تعداد نتایج اولیه از Qdrant
  rerank_top_k: 3            # تعداد chunk پس از rerank

domain:
  min_rerank_score: 0.02     # آستانه رد سوالات خارج دامنه
  min_relevance_for_answer: 0.3  # fallback (وقتی reranker خاموش است)
```

### تنظیم از طریق Environment Variables

```powershell
# تعویض به API پولی
$env:LLM_BASE_URL = "https://api.avalai.ir/v1"
$env:LLM_API_KEY  = "sk-..."
$env:LLM_MODEL    = "gpt-4o"
uvicorn app.server:app --host 0.0.0.0 --port 8080
```

---

## ۷. ساختار کد

```
crisis-rag/
├── app/
│   ├── server.py          # FastAPI app، روتر، CORS، startup events
│   ├── rag.py             # کل پایپ‌لاین RAG (embed، retrieve، rerank، generate)
│   └── static/
│       └── index.html     # Frontend کامل (۴ تب، vanilla JS، RTL)
├── scripts/
│   └── ingest.py          # Ingestion pipeline (parse → chunk → embed → index)
├── data/
│   └── raw/               # ۲۴ فایل MD پایگاه دانش
├── configs/
│   └── config.yaml        # تمام پارامترهای قابل تنظیم
├── tools/
│   └── qdrant.exe         # باینری Qdrant برای Windows
├── requirements.txt
└── CLAUDE.md              # مستندات توسعه‌دهنده
```

---

## ۸. راهنمای استقرار

### پیش‌نیازها

| نرم‌افزار | نسخه | لینک |
|----------|------|------|
| Python | 3.13 | python.org |
| Ollama | آخرین نسخه | ollama.com |
| Qdrant | 1.x | github.com/qdrant/qdrant/releases |

**حداقل سخت‌افزار:**
- RAM: ۱۶GB (برای Qwen2.5-7B + embedding models)
- فضای دیسک: ۱۰GB
- OS: Windows 10/11، macOS 12+، Ubuntu 20.04+

### مراحل نصب (اولین بار)

```powershell
# 1. Clone repo
git clone <repo-url>
cd crisis-rag

# 2. ایجاد virtual environment
python -m venv .venv
.venv\Scripts\activate

# 3. نصب وابستگی‌ها
pip install -r requirements.txt
pip install "httpx<0.28"   # رفع conflict Windows

# 4. دانلود مدل LLM
ollama pull qwen2.5:7b-instruct

# 5. ساخت ایندکس (اولین بار ~5 دقیقه)
python -m scripts.ingest

# 6. اجرای سرویس‌ها (سه ترمینال جداگانه)
cd tools; .\qdrant.exe          # Terminal 1
ollama serve                     # Terminal 2
uvicorn app.server:app --host 0.0.0.0 --port 8080  # Terminal 3
```

### بررسی سلامت سیستم

```powershell
# تست API
Invoke-RestMethod -Uri http://localhost:8080/health

# تست یک سوال ساده
Invoke-RestMethod -Uri http://localhost:8080/chat `
  -Method POST -ContentType "application/json" `
  -Body '{"question":"در زلزله چه کار کنم؟"}' |
  Select-Object -ExpandProperty answer
```

---

## ۹. مشکلات شناخته‌شده و راه‌حل‌ها

| مشکل | علت | راه‌حل |
|------|-----|-------|
| `TypeError: Client.__init__() ... proxies` | conflict نسخه httpx/openai | `pip install "httpx<0.28"` |
| `openai.APIConnectionError` | Ollama اجرا نمی‌کند | `ollama serve` را اجرا کنید |
| `[WinError 10061] ... refused` | Qdrant اجرا نمی‌کند | `tools\qdrant.exe` را اجرا کنید |
| کیفیت پاسخ فارسی ضعیف | Qwen2.5-7B فارسی محدود | `ollama pull aya-expanse:8b` یا LLM_MODEL=gpt-4o |
| WebAudio در iOS کار نمی‌کند | iOS autoplay policy | کاربر باید ابتدا tap کند |

---

## ۱۰. تکنولوژی‌های استفاده‌شده

| دسته | نام | نسخه/توضیح |
|------|-----|-----------|
| **Backend** | FastAPI | 0.115+ |
| **ASGI Server** | Uvicorn | 0.32+ |
| **Vector DB** | Qdrant | 1.12+ |
| **Embedding** | intfloat/multilingual-e5-base | HuggingFace، ۲۷۸MB |
| **Reranker** | BAAI/bge-reranker-v2-m3 | HuggingFace، ۵۶۸MB |
| **LLM Client** | openai (Python) | compatible با Ollama |
| **LLM (local)** | Qwen2.5-7B-instruct | via Ollama |
| **ML Framework** | sentence-transformers | 3.x |
| **Config** | PyYAML | — |
| **Frontend** | Vanilla JS | ES6+، بدون framework |
| **Styling** | CSS3 | RTL، تم تاریک، CSS Variables |
| **Web APIs** | WebAudio، Geolocation، localStorage | native browser |
