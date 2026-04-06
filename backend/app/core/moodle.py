"""
APSIT AI — Moodle Announcements Fetcher
-----------------------------------------
Scrapes the APSIT Moodle landing page every 6 hours.
Returns a short text summary of announcements to inject into AI prompt.
Caches result in memory to avoid hammering Moodle on every query.
"""

import httpx
import time
from bs4 import BeautifulSoup

MOODLE_URL  = "https://elearn.apsit.edu.in/moodle/"
CACHE_TTL   = 6 * 60 * 60   # 6 hours

_cached_text: str  = ""
_last_fetch:  float = 0.0


async def fetch_moodle_announcements() -> str:
    """
    Returns a short text of latest Moodle announcements.
    Refreshes every 6 hours. Returns empty string on failure.
    """
    global _cached_text, _last_fetch

    # serve from cache if fresh
    if _cached_text and (time.time() - _last_fetch) < CACHE_TTL:
        return _cached_text

    print("🔄 Fetching Moodle announcements...")

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(MOODLE_URL, follow_redirects=True)

        if r.status_code != 200:
            print(f"⚠️ Moodle fetch returned {r.status_code}")
            return _cached_text   # return stale cache on error

        soup = BeautifulSoup(r.text, "html.parser")

        # Extract visible text from announcement/news blocks
        # Moodle uses various class names — try common ones
        texts = []

        for selector in [
            ".news-item", ".announcement", ".forumpost",
            ".coursebox", ".notice", "h3", "h4"
        ]:
            for el in soup.select(selector)[:10]:
                t = el.get_text(" ", strip=True)
                if t and len(t) > 20:
                    texts.append(t)

        if not texts:
            # fallback: grab all paragraph text
            for p in soup.find_all("p")[:15]:
                t = p.get_text(" ", strip=True)
                if t and len(t) > 20:
                    texts.append(t)

        if texts:
            summary = "\n- ".join(texts[:8])
            _cached_text = f"Latest APSIT Moodle Announcements:\n- {summary}"
            _last_fetch  = time.time()
            print(f"✅ Moodle: {len(texts)} items fetched")
        else:
            print("⚠️ Moodle: No announcements found")
            _cached_text = ""

    except Exception as e:
        print(f"❌ Moodle fetch error: {e}")

    return _cached_text
