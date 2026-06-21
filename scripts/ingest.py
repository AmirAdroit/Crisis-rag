"""
Ingest Persian crisis-survival docs -> chunk -> embed -> store in Qdrant.
Run once after editing data/raw, or whenever the knowledge base changes.

    python -m scripts.ingest
"""
import os
import glob
import re
import uuid
import yaml
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

CONFIG = yaml.safe_load(open("configs/config.yaml", encoding="utf-8"))


def normalize_fa(text: str) -> str:
    """Normalize Arabic vs Persian chars + digits for consistent retrieval."""
    text = text.replace("ي", "ی").replace("ك", "ک")
    text = text.replace("\u200c", " ")  # ZWNJ -> space (matching tolerance)
    return re.sub(r"[ \t]+", " ", text).strip()


def chunk_text(text: str, size: int, overlap: int):
    """Heading-aware char chunking. Keeps a section header with its body."""
    blocks, current, header = [], [], ""
    for line in text.splitlines():
        if line.startswith("#"):
            if current:
                blocks.append((header, "\n".join(current)))
                current = []
            header = line.lstrip("# ").strip()
        else:
            if line.strip():
                current.append(line.strip())
    if current:
        blocks.append((header, "\n".join(current)))

    chunks = []
    for header, body in blocks:
        body = normalize_fa(body)
        if len(body) <= size:
            chunks.append((header, body))
            continue
        start = 0
        while start < len(body):
            piece = body[start:start + size]
            chunks.append((header, piece))
            start += size - overlap
    return chunks


# Map filename -> domain category for metadata + filtering
CATEGORY = {
    "first_aid": "کمک‌های اولیه",
    "stress": "مدیریت استرس",
    "emergency_kit": "بسته اضطراری",
    "utility": "قطع خدمات شهری",
}


def category_of(path: str) -> str:
    name = os.path.basename(path)
    for key, val in CATEGORY.items():
        if key in name:
            return val
    return "عمومی"


def main():
    emb_cfg = CONFIG["embedding"]
    model = SentenceTransformer(emb_cfg["model_name"], device=emb_cfg["device"])

    client = QdrantClient(url=CONFIG["vector_store"]["url"])
    coll = CONFIG["vector_store"]["collection"]
    dim = model.get_sentence_embedding_dimension()

    client.recreate_collection(
        collection_name=coll,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
    )

    points = []
    for path in glob.glob("data/raw/*.md"):
        raw = open(path, encoding="utf-8").read()
        title = normalize_fa(raw.splitlines()[0].lstrip("# ").strip())
        for header, body in chunk_text(
            raw,
            CONFIG["chunking"]["chunk_size"],
            CONFIG["chunking"]["chunk_overlap"],
        ):
            text_for_embed = emb_cfg["passage_prefix"] + body
            vec = model.encode(text_for_embed, normalize_embeddings=True).tolist()
            points.append(PointStruct(
                id=str(uuid.uuid4()),
                vector=vec,
                payload={
                    "text": body,
                    "title": title,
                    "section": header,
                    "category": category_of(path),
                    "source": os.path.basename(path),
                },
            ))

    client.upsert(collection_name=coll, points=points)
    print(f"Indexed {len(points)} chunks into '{coll}'.")


if __name__ == "__main__":
    main()
