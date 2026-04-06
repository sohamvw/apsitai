import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
import json
import os
import time
import random

BASE_DOMAIN = "apsit.edu.in"
VISITED_FILE = "visited.json"


# =========================
# 📁 STORAGE
# =========================
def load_set(file):
    if os.path.exists(file):
        return set(json.load(open(file)))
    return set()


def save_set(file, data):
    json.dump(list(data), open(file, "w"))


# =========================
# 🔗 NORMALIZE
# =========================
def normalize(url):
    url, _ = urldefrag(url)
    return url.rstrip("/")


# =========================
# 🔗 EXTRACT LINKS
# =========================
def extract_links(soup, base_url):
    links = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        full = normalize(urljoin(base_url, href))
        parsed = urlparse(full)

        if BASE_DOMAIN in parsed.netloc:

            # ❌ skip junk
            if any(ext in full.lower() for ext in [
                ".jpg", ".jpeg", ".png", ".gif", ".svg",
                ".zip", ".rar", ".css", ".js"
            ]):
                continue

            links.add(full)

    return list(links)


# =========================
# 📸 MEDIA
# =========================
def extract_media(soup, base_url):
    images, pdfs, videos = [], [], []

    for img in soup.find_all("img"):
        if img.get("src"):
            images.append(urljoin(base_url, img["src"]))

    for a in soup.find_all("a", href=True):
        href = a["href"]
        full = urljoin(base_url, href)

        if ".pdf" in href.lower():
            pdfs.append(full)

        if "youtube.com" in href or "youtu.be" in href:
            videos.append(full)

    return images, pdfs, videos


# =========================
# 🌐 HUMAN-LIKE FETCH (BEST FIX)
# =========================
def fetch(url):
    try:
        session = requests.Session()

        headers = {
            "User-Agent": random.choice([
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/119 Safari/537.36",
            ]),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Referer": "https://www.google.com/"
        }

        res = session.get(url, headers=headers, timeout=15)

        if res.status_code == 200 and "text/html" in res.headers.get("Content-Type", ""):
            return res.text

        print("❌ Blocked:", res.status_code)

    except Exception as e:
        print("❌ Fetch error:", e)

    return None


# =========================
# 🚀 MAIN CRAWLER
# =========================
def crawl(start_url, max_pages=3000):

    queue = [start_url]
    visited = load_set(VISITED_FILE)

    results = []
    start_time = time.time()

    print(f"🚀 Starting crawl | visited={len(visited)}")

    while queue and len(visited) < max_pages:

        url = queue.pop(0)

        if url in visited:
            continue

        print(f"\n🌐 {len(visited)} → {url}")

        html = fetch(url)

        if not html:
            print("❌ No HTML")
            continue

        soup = BeautifulSoup(html, "html.parser")

        for tag in soup(["script", "style", "nav", "footer"]):
            tag.extract()

        text = soup.get_text(" ", strip=True)

        # 🔥 VERY IMPORTANT (don't skip small pages like HOD)
        if len(text) < 30:
            print("⚠️ Small page skipped")
            continue

        images, pdfs, videos = extract_media(soup, url)

        results.append({
            "url": url,
            "text": text,
            "images": images,
            "pdfs": pdfs,
            "videos": videos
        })

        links = extract_links(soup, url)

        print(f"➡ Found {len(links)} links")

        for link in links:
            if link not in visited and link not in queue:
                queue.append(link)

        visited.add(url)
        save_set(VISITED_FILE, visited)

        # ⏱ ETA
        elapsed = time.time() - start_time
        rate = len(visited) / elapsed if elapsed else 0
        eta = (max_pages - len(visited)) / rate if rate else 0

        print(f"📌 Queue: {len(queue)}")
        print(f"⏱ ETA ~ {int(eta/60)} min")

        time.sleep(random.uniform(0.5, 1.2))

    print(f"\n✅ Crawled {len(results)} pages")
    return results