"""
APSIT AI — Retriever (Production Ready)
"""

import os
from dotenv import load_dotenv

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

load_dotenv()

# --------------------------------------------------
# Configuration
# --------------------------------------------------

MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2"
)

COLLECTION = os.getenv("QDRANT_COLLECTION")

if not COLLECTION:
    raise ValueError("QDRANT_COLLECTION is not set in .env")

print(f"🧠 Loading embedding model: {MODEL_NAME}")

model = SentenceTransformer(MODEL_NAME)

print("✅ Embedding model loaded")

qdrant = None


# --------------------------------------------------
# Lazy Qdrant Connection
# --------------------------------------------------

def get_qdrant():
    global qdrant

    if qdrant is None:

        print("🔌 Connecting to Qdrant...")

        qdrant = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY"),
            check_compatibility=False,
        )

        print("✅ Connected to Qdrant")

    return qdrant


# --------------------------------------------------
# Retriever
# --------------------------------------------------

def retrieve(query: str, limit: int = 8):
    """
    Returns:
        contexts,
        sources,
        images,
        pdfs,
        videos
    """

    try:

        client = get_qdrant()

        query_vector = model.encode(
            query,
            normalize_embeddings=True
        ).tolist()

        results = client.query_points(
            collection_name=COLLECTION,
            query=query_vector,
            limit=limit,
        ).points

        contexts = []
        sources = []
        images = []
        pdfs = []
        videos = []

        seen_text = set()

        for point in results:

            payload = point.payload or {}

            text = payload.get("content", "").strip()
            source = payload.get("url")

            if (
                text
                and len(text) > 40
                and text not in seen_text
            ):

                seen_text.add(text)

                contexts.append(text[:1200])

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

        print(
            f"✅ Retrieved "
            f"{len(contexts)} chunks | "
            f"{len(images)} images | "
            f"{len(pdfs)} pdfs | "
            f"{len(videos)} videos"
        )

        return (
            contexts,
            sources,
            images,
            pdfs,
            videos
        )

    except Exception as e:

        print(f"❌ Retriever error: {e}")

        return [], [], [], [], []