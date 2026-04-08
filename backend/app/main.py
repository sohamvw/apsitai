"""
APSIT AI Assistant — Upgraded main.py
=======================================
Features added:
  ✅ Rate limiting (10 req/min per IP)
  ✅ Redis-backed persistent session memory
  ✅ Answer cache — same question = instant answer, no re-query
  ✅ Agentic query breakdown (Gemini breaks complex Q into sub-queries)
  ✅ Google Custom Search fallback when Qdrant has no answer
  ✅ Live Moodle announcements injected into every response
  ✅ Smart redirects (fees → payment portal, admission → admission portal)
  ✅ Media (images, PDFs, videos) returned from Qdrant payload
  ✅ Callup questions for instant predefined answers
  ✅ /admin/cache-clear endpoint for manual cache flush
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from collections import defaultdict
import time, os, httpx, json

from google import genai
from dotenv import load_dotenv

from app.core.retriever import retrieve
from app.multilingual.language_detector import detect_lang
from app.memory.session_memory import (
    add_turn, get_history,
    cache_get, cache_set,
    redis_available
)
from app.core.callup import match_callup
from app.core.moodle import fetch_moodle_announcements

load_dotenv()

# ──────────────────────────────────────────────────────────
# APP
# ──────────────────────────────────────────────────────────
app = FastAPI(title="APSIT AI Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────────────────
# RATE LIMITER  (10 requests / 60 seconds per IP)
# ──────────────────────────────────────────────────────────
RATE_LIMIT = 10
RATE_WINDOW = 60
_rate_store: dict[str, list] = defaultdict(list)

def check_rate_limit(ip: str):
    now = time.time()
    hits = [t for t in _rate_store[ip] if now - t < RATE_WINDOW]
    if len(hits) >= RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=f"Too many requests. Limit: {RATE_LIMIT} per minute."
        )
    hits.append(now)
    _rate_store[ip] = hits

# ──────────────────────────────────────────────────────────
# GEMINI CLIENT
# ──────────────────────────────────────────────────────────
_gemini_client = None

def get_gemini():
    global _gemini_client
    if _gemini_client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise Exception("GEMINI_API_KEY missing from environment")
        _gemini_client = genai.Client(api_key=api_key)
    return _gemini_client

# ──────────────────────────────────────────────────────────
# GOOGLE CUSTOM SEARCH FALLBACK
# ──────────────────────────────────────────────────────────
async def google_search_fallback(query: str) -> tuple[str, list]:
    """
    Searches site:apsit.edu.in via Google Custom Search API.
    Returns (snippet_text, source_urls)
    Requires env vars: GOOGLE_CSE_API_KEY, GOOGLE_CSE_ID
    """
    api_key = os.getenv("GOOGLE_CSE_API_KEY")
    cse_id  = os.getenv("GOOGLE_CSE_ID")

    if not api_key or not cse_id:
        return "", []

    try:
        params = {
            "key": api_key,
            "cx":  cse_id,
            "q":   f"{query} site:apsit.edu.in",
            "num": 5,
        }
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(
                "https://www.googleapis.com/customsearch/v1",
                params=params
            )
            data = r.json()

        items   = data.get("items", [])
        snippet = "\n".join(i.get("snippet", "") for i in items)
        links   = [i.get("link", "") for i in items if i.get("link")]
        return snippet, links

    except Exception as e:
        print("❌ Google Search fallback error:", e)
        return "", []

# ──────────────────────────────────────────────────────────
# AGENTIC QUERY BREAKDOWN
# ──────────────────────────────────────────────────────────
def decompose_query(query: str) -> list[str]:
    """
    Uses Gemini to break a complex question into 1–3 focused sub-queries.
    Simple questions are returned as-is (single element list).
    """
    try:
        gemini = get_gemini()
        prompt = f"""
You are a query analyzer for APSIT college AI assistant.
Break this student question into 1-3 focused sub-queries for better search.
Return ONLY a JSON array of strings. No explanation.
Example: ["fees for BTech CSE", "scholarship options at APSIT"]

Question: {query}
"""
        resp = gemini.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        text = resp.text.strip().strip("```json").strip("```").strip()
        sub_queries = json.loads(text)
        if isinstance(sub_queries, list) and all(isinstance(q, str) for q in sub_queries):
            return sub_queries[:3]
    except Exception as e:
        print("⚠️ Query decomposition failed:", e)

    return [query]

# ──────────────────────────────────────────────────────────
# SMART REDIRECT RULES
# ──────────────────────────────────────────────────────────
REDIRECT_RULES = [
    {
        "keywords": ["pay", "payment", "fee", "fees", "challan", "receipt", "फी"],
        "message":  "For fee payment, please visit the official APSIT Payment Portal:",
        "links":    [{"label": "💳 Pay Fees Online", "url": "https://admission.apsit.org.in/"}],
    },
    {
        "keywords": ["admission", "apply", "application", "enroll", "registration", "प्रवेश"],
        "message":  "For admissions and registration, visit the APSIT Admission Portal:",
        "links":    [{"label": "🎓 Admission Portal", "url": "https://admission.apsit.org.in/"}],
    },
    {
        "keywords": ["moodle", "elearn", "e-learn", "study material", "notes", "lecture", "announcement"],
        "message":  "Check the APSIT e-Learning portal for announcements and study materials:",
        "links":    [{"label": "📚 Open Moodle", "url": "https://elearn.apsit.edu.in/moodle/"}],
    },
]

def get_redirect(query: str) -> Optional[dict]:
    q_lower = query.lower()
    for rule in REDIRECT_RULES:
        if any(kw in q_lower for kw in rule["keywords"]):
            return rule
    return None

# ──────────────────────────────────────────────────────────
# REQUEST MODEL
# ──────────────────────────────────────────────────────────
class QueryRequest(BaseModel):
    query:      str
    session_id: Optional[str] = "default"
    language:   Optional[str] = "auto"

# ──────────────────────────────────────────────────────────
# HEALTH
# ──────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {
        "status":        "running",
        "redis":         redis_available(),
        "cache_backend": "redis" if redis_available() else "in-memory",
    }

# ──────────────────────────────────────────────────────────
# MAIN QUERY ENDPOINT
# ──────────────────────────────────────────────────────────
@app.post("/query")
async def query(request: QueryRequest, req: Request):

    # ── rate limit ──────────────────────────────────────────
    client_ip = req.client.host
    check_rate_limit(client_ip)

    q          = request.query.strip()
    session_id = request.session_id

    # ── language detection ──────────────────────────────────
    if request.language and request.language != "auto":
        lang = request.language
    else:
        lang = detect_lang(q)

    lang_map = {
        "mr": "Answer strictly in Marathi. Do NOT use English.",
        "hi": "Answer strictly in Hindi. Do NOT use English.",
        "en": "Answer in English.",
    }
    lang_instruction = lang_map.get(lang, "Answer in the same language as the question.")

    # ── answer cache (same question = instant return) ────────
    cached = cache_get(q)
    if cached:
        print(f"⚡ Cache hit for: {q}")
        add_turn(session_id, {"q": q, "a": cached["answer"]})
        return {**cached, "from_cache": True, "language": lang}

    # ── callup questions (predefined instant answers) ────────
    callup = match_callup(q)
    if callup:
        print(f"📋 Callup match for: {q}")
        result = {
            "answer":     callup["answer"],
            "language":   lang,
            "sources":    [],
            "images":     callup.get("images", []),
            "pdfs":       callup.get("pdfs", []),
            "videos":     callup.get("videos", []),
            "links":      callup.get("links", []),
            "from_cache": False,
        }
        cache_set(q, **{k: result[k] for k in ["answer","images","pdfs","videos","sources"]})
        add_turn(session_id, {"q": q, "a": callup["answer"]})
        return result

    # ── smart redirect check ─────────────────────────────────
    redirect = get_redirect(q)

    # ── agentic query decomposition ──────────────────────────
    sub_queries = decompose_query(q)
    print(f"🧠 Sub-queries: {sub_queries}")

    # ── retrieve from Qdrant for all sub-queries ─────────────
    all_contexts, all_sources, all_images, all_pdfs, all_videos = [], [], [], [], []

    for sq in sub_queries:
        try:
            ctx, src, imgs, pdfs, vids = retrieve(sq)
            all_contexts.extend(ctx)
            all_sources.extend(s for s in src if s not in all_sources)
            all_images.extend(i for i in imgs if i not in all_images)
            all_pdfs.extend(p for p in pdfs if p not in all_pdfs)
            all_videos.extend(v for v in vids if v not in all_videos)
        except Exception as e:
            print(f"⚠️ Retrieve error for '{sq}':", e)

    # ── fallback: Google Custom Search if Qdrant has nothing ─
    fallback_used = False
    if not all_contexts:
        print("🔍 No Qdrant results — trying Google fallback...")
        snippet, google_links = await google_search_fallback(q)
        if snippet:
            all_contexts = [snippet]
            all_sources.extend(l for l in google_links if l not in all_sources)
            fallback_used = True
            print(f"✅ Google fallback: {len(google_links)} links")

    # ── Moodle live announcements ────────────────────────────
    moodle_text = await fetch_moodle_announcements()

    # ── no context at all ────────────────────────────────────
    if not all_contexts:
        answer = (
            "I couldn't find specific information about this in APSIT's records. "
            "For accurate details, please visit the campus or contact the office directly.\n\n"
            "📞 Contact: +91-22-2895 5500 | 🌐 www.apsit.edu.in"
        )
        add_turn(session_id, {"q": q, "a": answer})
        return {
            "answer":     answer,
            "language":   lang,
            "sources":    [],
            "images":     [],
            "pdfs":       [],
            "videos":     [],
            "links":      redirect["links"] if redirect else [],
            "from_cache": False,
        }

    # ── build combined context ───────────────────────────────
    clean_contexts   = [c for c in all_contexts if len(c.strip()) > 30]
    combined_context = "\n\n".join(clean_contexts[:8])   # cap at 8 chunks

    history      = get_history(session_id)
    history_text = "\n".join(
        f"User: {h['q']}\nAssistant: {h['a']}" for h in history
    )

    # ── Gemini prompt ────────────────────────────────────────
    prompt = f"""
You are the official APSIT AI Assistant — a smart, helpful, human-like assistant for APSIT college students.

RULES:
- Answer using ONLY the context below. Do not hallucinate.
- Be warm, clear, and helpful — like a knowledgeable senior student.
- Use bullet points for lists. Keep answers concise but complete.
- Extract key dates, deadlines, fees, and names accurately.
- Do NOT mix languages. {lang_instruction}
- End every answer with: "For more queries, visit the college campus or contact us at +91-22-2895 5500."
- Do NOT use **, *, or markdown bold symbols.

CONVERSATION HISTORY:
{history_text if history_text else "No prior conversation."}

CONTEXT FROM APSIT WEBSITE:
{combined_context}

{"LIVE MOODLE ANNOUNCEMENTS:" + moodle_text if moodle_text else ""}

{"NOTE: Results from Google web search (APSIT site)." if fallback_used else ""}

STUDENT QUESTION:
{q}

ANSWER:
"""

    try:
        gemini  = get_gemini()
        resp    = gemini.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        answer  = getattr(resp, "text", "").strip() or "No response generated."
    except Exception as e:
        print("❌ Gemini error:", e)
        answer = "AI response failed. Please try again in a moment."

    # ── store in session + cache ─────────────────────────────
    add_turn(session_id, {"q": q, "a": answer})
    cache_set(q, answer=answer, images=all_images, pdfs=all_pdfs,
              videos=all_videos, sources=all_sources)

    # ── build response ───────────────────────────────────────
    extra_links = redirect["links"] if redirect else []
    if moodle_text:
        extra_links.append({
            "label": "📢 Check Moodle Announcements",
            "url":   "https://elearn.apsit.edu.in/moodle/"
        })

    return {
        "answer":     answer,
        "language":   lang,
        "sources":    all_sources,
        "images":     all_images[:6],
        "pdfs":       all_pdfs[:5],
        "videos":     all_videos[:3],
        "links":      extra_links,
        "from_cache": False,
    }


# ──────────────────────────────────────────────────────────
# ADMIN: CLEAR CACHE
# ──────────────────────────────────────────────────────────
@app.post("/admin/cache-clear")
def clear_cache(secret: str = ""):
    admin_secret = os.getenv("ADMIN_SECRET", "apsit-admin")
    if secret != admin_secret:
        raise HTTPException(status_code=403, detail="Forbidden")
    from app.memory.session_memory import cache_clear
    cache_clear()
    return {"status": "cache cleared"}
