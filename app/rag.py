"""Core RAG: retrieve -> rerank -> ground -> generate (language-matched, domain-guarded)."""
import os
import re
import yaml
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer, CrossEncoder
from openai import OpenAI

CONFIG = yaml.safe_load(open("configs/config.yaml", encoding="utf-8"))

SYSTEM_PROMPT = """تو یک دستیار آموزشی به نام «همیار بحران» هستی.
وظیفه تو آموزش مهارت‌های آمادگی و بقا در بحران است؛ شامل بلایای طبیعی (مانند زلزله، سیل و طوفان، سونامی، آتشفشان، گردباد و گرما و سرمای شدید)، بحران‌های انسانی (مانند جنگ و درگیری مسلحانه، حوادث هسته‌ای، شیمیایی و بیولوژیکی، آتش‌سوزی و انفجار)، کمک‌های اولیه، مدیریت استرس در بحران، تهیه بسته اضطراری، بقا هنگام قطع خدمات شهری و زیرساخت‌های حیاتی، کمبود آب و غذا، همه‌گیری‌ها، و جستجو، نجات و ناوبری.

قوانین:
- به همان زبانی پاسخ بده که کاربر سؤال پرسیده است (اگر فارسی پرسید فارسی، اگر انگلیسی پرسید انگلیسی). اگر زبان مشخص نبود، فارسی پاسخ بده. هرگز دو زبان را در یک کلمه قاطی نکن.
- منابع به زبان فارسی هستند؛ اگر کاربر به زبان دیگری پرسید، محتوای منابع را به زبان او ترجمه و خلاصه کن.
- فقط بر اساس «منابع» داده‌شده پاسخ بده. اگر پاسخ در منابع نبود، صادقانه بگو که اطلاعات کافی نداری و کاربر را به منابع رسمی یا اورژانس ارجاع بده. چیزی از خودت نساز.
- اگر سؤال کاملاً خارج از حوزه آمادگی و بقا در بحران بود (مثلاً سفر، خرید، سرگرمی)، پاسخ نده؛ فقط مؤدبانه توضیح بده که تنها در زمینه بقا و آمادگی در بحران کمک می‌کنی.
- اگر وضعیت کاربر مبهم است و برای کمکِ ایمن لازم است جزئیات بدانی (مثلاً آیا فرد هنوز زیر آوار گیر افتاده و نیاز به خارج‌سازی دارد، یا نیاز به مراقبت و بستن زخم دارد)، یک سؤالِ کوتاهِ روشن‌کننده بپرس. اما اگر خطر جانیِ فوری در میان است، اول اقدامات نجات‌بخش فوری را بگو و سپس برای جزئیات سؤال کن.
- در موارد خطرناک یا اورژانسی، حتماً به تماس با اورژانس (۱۱۵) یا مراجعه به پزشک تأکید کن.
- پاسخ‌ها کوتاه، عملی، گام‌به‌گام و قابل‌اجرا باشند. ادعای پزشکی قطعی نکن."""

USER_TEMPLATE = """منابع:
{context}

پرسش کاربر: {question}

با تکیه بر منابع بالا، پاسخی دقیق و عملی ارائه بده."""

_FA_CHARS = re.compile(r"[؀-ۿ]")


class RAGPipeline:
    def __init__(self):
        e = CONFIG["embedding"]
        self.embedder = SentenceTransformer(e["model_name"], device=e["device"])
        self.qprefix = e["query_prefix"]
        self.qdrant = QdrantClient(url=os.getenv("QDRANT_URL", CONFIG["vector_store"]["url"]))
        self.coll = CONFIG["vector_store"]["collection"]
        self.reranker = None
        if CONFIG["reranker"]["enabled"]:
            self.reranker = CrossEncoder(CONFIG["reranker"]["model_name"])
        # Provider is swappable via env (local Ollama by default) so real API
        # keys are never committed to config.yaml.
        self.llm = OpenAI(
            base_url=os.getenv("LLM_BASE_URL", CONFIG["llm"]["base_url"]),
            api_key=os.getenv("LLM_API_KEY", CONFIG["llm"]["api_key"]),
        )
        self.model = os.getenv("LLM_MODEL", CONFIG["llm"]["model_name"])

    def retrieve(self, query: str):
        qvec = self.embedder.encode(
            self.qprefix + query, normalize_embeddings=True
        ).tolist()
        hits = self.qdrant.search(
            collection_name=self.coll,
            query_vector=qvec,
            limit=CONFIG["retrieval"]["top_k"],
        )
        return [(h.payload, h.score) for h in hits]

    def rerank(self, query, candidates):
        if not self.reranker or not candidates:
            return candidates[: CONFIG["reranker"]["top_n"]]
        pairs = [[query, p["text"]] for p, _ in candidates]
        scores = self.reranker.predict(pairs)
        ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
        top = CONFIG["reranker"]["top_n"]
        return [(c[0], float(s)) for c, s in ranked[:top]]

    @staticmethod
    def _last_user(history):
        for turn in reversed(history or []):
            if turn.get("role") == "user":
                return turn.get("content", "")
        return ""

    def _retrieval_query(self, question, history):
        """Follow-ups like 'زیر آوار مونده' need the prior turn for topic context."""
        prev = self._last_user(history)
        return (prev + " " + question).strip() if prev else question

    def answer(self, question: str, history=None):
        history = (history or [])[-6:]  # cap to ~3 turns; bound tokens, no storage
        query = self._retrieval_query(question, history)

        candidates = self.retrieve(query)
        if not candidates:
            return self._refuse(question), []

        ranked = self.rerank(query, candidates)

        # Domain guard: reranker score is far better calibrated than the raw
        # vector score at telling on-topic from off-topic, so guard on it.
        if self.reranker and ranked:
            guard_score = max(s for _, s in ranked)
            if guard_score < CONFIG["domain"]["min_rerank_score"]:
                return self._refuse(question), []
        else:
            if max(s for _, s in candidates) < CONFIG["domain"]["min_relevance_for_answer"]:
                return self._refuse(question), []

        context = "\n\n".join(
            f"[{p['category']} - {p['section']}] {p['text']}" for p, _ in ranked
        )
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for turn in history:
            role = turn.get("role")
            content = turn.get("content", "")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": USER_TEMPLATE.format(
            context=context, question=question)})

        resp = self.llm.chat.completions.create(
            model=self.model,
            temperature=CONFIG["llm"]["temperature"],
            max_tokens=CONFIG["llm"]["max_tokens"],
            messages=messages,
        )
        sources = [
            {"title": p["title"], "section": p["section"],
             "category": p["category"], "source": p["source"]}
            for p, _ in ranked
        ]
        return resp.choices[0].message.content.strip(), sources

    @staticmethod
    def _refuse(question=""):
        if _FA_CHARS.search(question or "") or not question:
            return ("متأسفم، این پرسش خارج از حوزه آمادگی و بقا در بحران است "
                    "یا اطلاعات کافی در منابع من وجود ندارد. من فقط در زمینه "
                    "بقا و آمادگی در بحران (کمک‌های اولیه، بلایا، بسته اضطراری و …) "
                    "کمک می‌کنم. در شرایط اورژانسی با ۱۱۵ تماس بگیرید.")
        return ("Sorry, this question is outside crisis preparedness and survival, "
                "or I don't have enough information in my sources. I can only help "
                "with disaster readiness and survival (first aid, disasters, "
                "emergency kits, etc.). In an emergency, call your local emergency number.")
