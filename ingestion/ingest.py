import os
from dotenv import load_dotenv
from uuid import uuid4
from tqdm import tqdm

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

from crawler import crawl
from utils import chunk_text

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

COLLECTION = os.getenv("QDRANT_COLLECTION")

if not COLLECTION:
    raise ValueError("QDRANT_COLLECTION is not set in .env")

print("🔌 Connecting Qdrant...")
client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

print(f"📂 Using collection: {COLLECTION}")

if not client.collection_exists(COLLECTION):
    print("🆕 Collection not found. Creating...")

    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(
            size=384,
            distance=Distance.COSINE
        ),
    )

    print("✅ Collection created successfully!")

else:
    print("✅ Collection already exists.")

print("🧠 Loading model...")

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2"
)

print(f"🧠 Loading embedding model: {EMBEDDING_MODEL}")

model = SentenceTransformer(EMBEDDING_MODEL)


def safe_upsert(points):
    try:
        client.upsert(
            collection_name=COLLECTION,
            points=points,
            wait=True
        )
    except Exception as e:
        print(f"❌ Failed to upload batch of {len(points)} vectors")
        print(e)


def ingest():

    print("🚀 Crawling...")
    pages = crawl("https://www.apsit.edu.in", max_pages=5000)

    batch = []
    BATCH_SIZE = 15  # 🔥 FIX TIMEOUT

    for page in tqdm(pages):

        # ❌ SKIP PDFs (avoid garbage text)
        if page["url"].endswith(".pdf"):
            continue

        chunks = chunk_text(page["text"])

        # ✅ Batch encode all chunks at once
        vectors = model.encode(
            chunks,
            batch_size=32,
            show_progress_bar=False
        )

        for chunk, vector in zip(chunks, vectors):

            batch.append({
                "id": str(uuid4()),
                "vector": vector.tolist(),
                "payload": {
                    "content": chunk,
                    "url": page["url"],
                    "images": page["images"],
                    "pdfs": page["pdfs"],
                    "videos": page["videos"]
                }
            })

            if len(batch) >= BATCH_SIZE:
                safe_upsert(batch)
                batch = []

    if batch:
        safe_upsert(batch)

    print("\n✅ CLEAN INGESTION COMPLETE")


if __name__ == "__main__":
    ingest()