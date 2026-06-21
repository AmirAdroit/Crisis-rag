"""Core RAG: retrieve -> rerank -> ground -> generate (Persian-only, domain-guarded)."""
import yaml
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer, CrossEncoder
from openai import OpenAI

CONFIG = yaml.safe_load(open("configs/config.yaml", encoding="utf-8"))

SYSTEM_PROMPT = """تو یک دستیار آموزشی فارسی‌زبان به نام «همیار بحران» هستی.
وظیفه تو فقط آموزش مهارت‌های بقا در بحران در چهار حوزه است:
۱) کمک‌های اولیه ۲) مدیریت استرس در بحران ۳) تهیه بسته اضطراری ۴) بقا هنگام قطع خدمات شهری.

قوانین:
- فقط و فقط به زبان فارسی پاسخ بده.
- فقط بر اساس «منابع» داده‌شده پاسخ بده. اگر پاسخ در منابع نبود، صادقانه بگو که اطلاعات کافی نداری و کاربر را به منابع رسمی یا اورژانس ارجاع بده.
- اگر سؤال خارج از این چهار حوزه بود، مؤدبانه توضیح بده که فقط در زمینه مهارت‌های بقا در بحران کمک می‌کنی.
- در موارد خطرناک یا اورژانسی، حتماً به تماس با اورژانس (۱۱۵) یا مراجعه به پزشک تأکید کن.
- پاسخ‌ها کوتاه، عملی، گام‌به‌گام و قابل‌اجرا باشند. ادعای پزشکی قطعی نکن."""

USER_TEMPLATE = """منابع:
{context}

پرسش کاربر: {question}

با تکیه بر منابع بالا، پاسخی دقیق، عملی و فارسی ارائه بده."""


class RAGPipeline:
    def __init__(self):
        e = CONFIG["embedding"]
        self.embedder = SentenceTransformer(e["model_name"], device=e["device"])
        self.qprefix = e["query_prefix"]
        self.qdrant = QdrantClient(url=CONFIG["vector_store"]["url"])
        self.coll = CONFIG["vector_store"]["collection"]
        self.reranker = None
        if CONFIG["reranker"]["enabled"]:
            self.reranker = CrossEncoder(CONFIG["reranker"]["model_name"])
        self.llm = OpenAI(
            base_url=CONFIG["llm"]["base_url"],
            api_key=CONFIG["llm"]["api_key"],
        )

    def retrieve(self, question: str):
        qvec = self.embedder.encode(
            self.qprefix + question, normalize_embeddings=True
        ).tolist()
        hits = self.qdrant.search(
            collection_name=self.coll,
            query_vector=qvec,
            limit=CONFIG["retrieval"]["top_k"],
        )
        return [(h.payload, h.score) for h in hits]

    def rerank(self, question, candidates):
        if not self.reranker or not candidates:
            return candidates[: CONFIG["reranker"]["top_n"]]
        pairs = [[question, p["text"]] for p, _ in candidates]
        scores = self.reranker.predict(pairs)
        ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
        top = CONFIG["reranker"]["top_n"]
        return [(c[0], float(s)) for c, s in ranked[:top]]

    def answer(self, question: str):
        candidates = self.retrieve(question)
        if not candidates:
            return self._refuse(), []

        best_vec_score = max(s for _, s in candidates)
        ranked = self.rerank(question, candidates)

        # Domain guard: if nothing is relevant enough, refuse instead of hallucinate.
        if best_vec_score < CONFIG["domain"]["min_relevance_for_answer"]:
            return self._refuse(), []

        context = "\n\n".join(
            f"[{p['category']} - {p['section']}] {p['text']}" for p, _ in ranked
        )
        resp = self.llm.chat.completions.create(
            model=CONFIG["llm"]["model_name"],
            temperature=CONFIG["llm"]["temperature"],
            max_tokens=CONFIG["llm"]["max_tokens"],
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_TEMPLATE.format(
                    context=context, question=question)},
            ],
        )
        sources = [
            {"title": p["title"], "section": p["section"],
             "category": p["category"], "source": p["source"]}
            for p, _ in ranked
        ]
        return resp.choices[0].message.content.strip(), sources

    @staticmethod
    def _refuse():
        return ("متأسفم، این پرسش خارج از حوزه مهارت‌های بقا در بحران است "
                "یا اطلاعات کافی در منابع من وجود ندارد. من فقط در زمینه "
                "کمک‌های اولیه، مدیریت استرس، بسته اضطراری و قطع خدمات شهری "
                "می‌توانم کمک کنم. در شرایط اورژانسی با ۱۱۵ تماس بگیرید.")
