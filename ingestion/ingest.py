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

COLLECTION = "apsit_final"

print("🔌 Connecting Qdrant...")
client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

# 🔥 RESET COLLECTION
try:
    client.delete_collection(COLLECTION)
except:
    pass

client.create_collection(
    collection_name=COLLECTION,
    vectors_config=VectorParams(size=384, distance=Distance.COSINE),
)

print("🧠 Loading model...")
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")


def safe_upsert(points):
    try:
        client.upsert(
            collection_name=COLLECTION,
            points=points,
            wait=True
        )
    except Exception as e:
        print("❌ Skipped batch:", e)


def ingest():

    print("🚀 Crawling...")
    pages = crawl("https://www.apsit.edu.in", max_pages=3000)

    batch = []
    BATCH_SIZE = 15  # 🔥 FIX TIMEOUT

    for page in tqdm(pages):

        # ❌ SKIP PDFs (avoid garbage text)
        if page["url"].endswith(".pdf"):
            continue

        chunks = chunk_text(page["text"])

        for chunk in chunks:

            vector = model.encode(chunk).tolist()

            batch.append({
                "id": str(uuid4()),
                "vector": vector,
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