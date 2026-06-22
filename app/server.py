"""FastAPI server exposing the crisis-survival RAG chatbot."""
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from app.rag import RAGPipeline

app = FastAPI(title="همیار بحران - Crisis Survival Assistant")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

_STATIC = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=_STATIC), name="static")

pipeline = None  # lazy init so models load once at startup


class ChatRequest(BaseModel):
    question: str
    history: list = []  # ephemeral [{role, content}] turns sent by the client; not stored


class ChatResponse(BaseModel):
    answer: str
    sources: list


@app.on_event("startup")
def _load():
    global pipeline
    pipeline = RAGPipeline()


@app.get("/", include_in_schema=False)
def root():
    return FileResponse(_STATIC / "index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    answer, sources = pipeline.answer(req.question, req.history)
    return ChatResponse(answer=answer, sources=sources)
