"""
APSIT AI — Session Memory (Redis-backed with in-memory fallback)
-----------------------------------------------------------------
- Session turns stored in Redis with 2-hour TTL
- Answer cache stored in Redis with 6-hour TTL
- Falls back to in-memory dicts if Redis is unavailable
- Use redis_available() to check connection status
"""

import os, json, time, re
from typing import Optional

# ──────────────────────────────────────────────────────────
# REDIS SETUP
# ──────────────────────────────────────────────────────────
try:
    import redis
    _redis = redis.Redis.from_url(
        os.getenv("REDIS_URL", "redis://localhost:6379"),
        decode_responses=True,
        socket_connect_timeout=3,
    )
    _redis.ping()
    _REDIS_OK = True
    print("✅ Redis connected")
except Exception as e:
    _REDIS_OK = False
    _redis = None
    print(f"⚠️ Redis unavailable — using in-memory fallback: {e}")

# In-memory fallbacks
_sessions: dict = {}
_cache:    dict = {}

MAX_TURNS   = 6
SESSION_TTL = 2 * 60 * 60    # 2 hours
CACHE_TTL   = 6 * 60 * 60    # 6 hours


def redis_available() -> bool:
    return _REDIS_OK


# ──────────────────────────────────────────────────────────
# SESSION HELPERS
# ──────────────────────────────────────────────────────────
def _session_key(session_id: str) -> str:
    return f"apsit:session:{session_id}"


def add_turn(session_id: str, data: dict):
    key = _session_key(session_id)
    if _REDIS_OK:
        try:
            raw   = _redis.get(key)
            turns = json.loads(raw) if raw else []
            turns.append(data)
            turns = turns[-MAX_TURNS:]
            _redis.setex(key, SESSION_TTL, json.dumps(turns))
            return
        except Exception as e:
            print("⚠️ Redis session write error:", e)

    # in-memory fallback
    _sessions.setdefault(session_id, []).append(data)
    if len(_sessions[session_id]) > MAX_TURNS:
        _sessions[session_id] = _sessions[session_id][-MAX_TURNS:]


def get_history(session_id: str) -> list:
    key = _session_key(session_id)
    if _REDIS_OK:
        try:
            raw = _redis.get(key)
            return json.loads(raw) if raw else []
        except Exception as e:
            print("⚠️ Redis session read error:", e)

    return _sessions.get(session_id, [])


# ──────────────────────────────────────────────────────────
# ANSWER CACHE
# ──────────────────────────────────────────────────────────
def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9\s]", "", text.lower().strip())


def _cache_key(question: str) -> str:
    return f"apsit:cache:{_normalize(question)}"


def cache_get(question: str) -> Optional[dict]:
    key = _cache_key(question)
    if _REDIS_OK:
        try:
            raw = _redis.get(key)
            return json.loads(raw) if raw else None
        except Exception as e:
            print("⚠️ Redis cache read error:", e)

    entry = _cache.get(key)
    if entry and (time.time() - entry["ts"]) < CACHE_TTL:
        return entry
    return None


def cache_set(question: str, answer: str, images: list,
              pdfs: list, videos: list, sources: list):
    key  = _cache_key(question)
    data = {
        "answer":  answer,
        "images":  images,
        "pdfs":    pdfs,
        "videos":  videos,
        "sources": sources,
        "ts":      time.time(),
    }
    if _REDIS_OK:
        try:
            _redis.setex(key, CACHE_TTL, json.dumps(data))
            return
        except Exception as e:
            print("⚠️ Redis cache write error:", e)

    _cache[key] = data


def cache_clear():
    if _REDIS_OK:
        try:
            keys = _redis.keys("apsit:cache:*")
            if keys:
                _redis.delete(*keys)
            print("✅ Redis cache cleared")
            return
        except Exception as e:
            print("⚠️ Redis cache clear error:", e)

    _cache.clear()
    print("✅ In-memory cache cleared")
