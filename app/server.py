"""FastAPI server exposing the crisis-survival RAG chatbot."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.rag import RAGPipeline

app = FastAPI(title="همیار بحران - Crisis Survival Assistant")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

pipeline = None  # lazy init so models load once at startup


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    sources: list


@app.on_event("startup")
def _load():
    global pipeline
    pipeline = RAGPipeline()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    answer, sources = pipeline.answer(req.question)
    return ChatResponse(answer=answer, sources=sources)
