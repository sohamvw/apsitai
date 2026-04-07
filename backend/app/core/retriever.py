"""
APSIT AI — Retriever (Upgraded)
Returns text contexts, sources, AND media (images, pdfs, videos)
already stored in each Qdrant point payload from ingest.py.
"""

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
import os

print("🧠 Loading embedding model...")
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
model = SentenceTransformer(MODEL_NAME, use_auth_token=os.getenv("HF_TOKEN"))
print("✅ Model loaded")

qdrant     = None
COLLECTION = "apsit_final"


def get_qdrant():
    global qdrant
    if qdrant is None:
        qdrant = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY"),
            check_compatibility=False
        )
    return qdrant


def retrieve(query: str, limit: int = 5) -> tuple:
    """
    Returns: (contexts, sources, images, pdfs, videos)
    All media comes directly from the Qdrant payload — no extra fetch needed.
    """
    try:
        client       = get_qdrant()
        query_vector = model.encode(query).tolist()

        results = client.query_points(
            collection_name=COLLECTION,
            query=query_vector,
            limit=limit
        ).points

        contexts, sources, images, pdfs, videos = [], [], [], [], []

        for r in results:
            payload = r.payload or {}
            text    = payload.get("content", "")
            source  = payload.get("url")

            if text and len(text) > 30:
                contexts.append(text)

            if source and source not in sources:
                sources.append(source)

            for img in payload.get("images", []):
                if img and img not in images:
                    images.append(img)

            for pdf in payload.get("pdfs", []):
                if pdf and pdf not in pdfs:
                    pdfs.append(pdf)

            for vid in payload.get("videos", []):
                if vid and vid not in videos:
                    videos.append(vid)

        print(f"✅ {len(contexts)} chunks | {len(images)} imgs | {len(pdfs)} pdfs | {len(videos)} videos")
        return contexts, sources, images, pdfs, videos

    except Exception as e:
        print("❌ Retriever error:", e)
        return [], [], [], [], []
