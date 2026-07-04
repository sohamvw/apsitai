"""
APSIT AI — Moodle Announcements Fetcher
---------------------------------------
Scrapes the APSIT Moodle landing page every 6 hours.
Returns a short text summary of announcements to inject into the AI prompt.
Uses an in-memory cache to reduce requests.
"""

import asyncio
import time

import httpx
from bs4 import BeautifulSoup

MOODLE_URL = "https://elearn.apsit.edu.in/moodle/"
CACHE_TTL = 6 * 60 * 60  # 6 hours

_cached_text = ""
_last_fetch = 0.0

_fetch_lock = asyncio.Lock()

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/137.0 Safari/537.36"
    )
}


async def fetch_moodle_announcements() -> str:
    """
    Returns cached Moodle announcements.

    Cache refreshes every 6 hours.
    """

    global _cached_text, _last_fetch

    # ---------------------------------------------------------
    # Fresh cache
    # ---------------------------------------------------------

    if _cached_text and (time.time() - _last_fetch) < CACHE_TTL:
        return _cached_text

    # Prevent multiple simultaneous fetches
    async with _fetch_lock:

        # Maybe another request already refreshed it
        if _cached_text and (time.time() - _last_fetch) < CACHE_TTL:
            return _cached_text

        print("🔄 Fetching Moodle announcements...")

        try:

            async with httpx.AsyncClient(
                timeout=10,
                follow_redirects=True,
                headers=HEADERS,
            ) as client:

                response = await client.get(MOODLE_URL)

            if response.status_code != 200:
                print(f"⚠️ Moodle returned HTTP {response.status_code}")
                return _cached_text

            soup = BeautifulSoup(response.text, "html.parser")

            texts = []

            selectors = [
                ".news-item",
                ".announcement",
                ".forumpost",
                ".coursebox",
                ".notice",
                "h3",
                "h4",
            ]

            for selector in selectors:

                for element in soup.select(selector)[:10]:

                    text = element.get_text(" ", strip=True)

                    if (
                        text
                        and len(text) > 20
                        and text not in texts
                    ):
                        texts.append(text)

            # -------------------------------------------------
            # Fallback
            # -------------------------------------------------

            if not texts:

                for paragraph in soup.find_all("p")[:15]:

                    text = paragraph.get_text(" ", strip=True)

                    if (
                        text
                        and len(text) > 20
                        and text not in texts
                    ):
                        texts.append(text)

            # -------------------------------------------------
            # Update cache
            # -------------------------------------------------

            if texts:

                summary = "\n- ".join(texts[:8])

                _cached_text = (
                    "Latest APSIT Moodle Announcements:\n- "
                    + summary
                )

                _last_fetch = time.time()

                print(
                    f"✅ Moodle cache refreshed ({len(texts)} announcements)"
                )

            else:

                print("⚠️ No Moodle announcements found.")

                _cached_text = ""

        except Exception as e:

            print(f"❌ Moodle fetch error: {e}")

    return _cached_text