import ssl
import time
import urllib.request
import certifi
import feedparser
from datetime import datetime, timedelta
from newsapi import NewsApiClient
from backend.config import NEWSAPI_KEY, OUTLETS, OUTLET_RSS
from backend import database as db

# SSL context that trusts certifi's CA bundle (fixes macOS Python SSL errors)
_SSL_CTX = ssl.create_default_context(cafile=certifi.where())


def fetch_from_newsapi() -> list[dict]:
    if not NEWSAPI_KEY:
        print("No NEWSAPI_KEY set — skipping NewsAPI fetch")
        return []

    client = NewsApiClient(api_key=NEWSAPI_KEY)
    from_date = (datetime.utcnow() - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S")
    articles = []

    for name, source_id in OUTLETS.items():
        try:
            resp = client.get_everything(
                sources=source_id,
                from_param=from_date,
                language="en",
                sort_by="publishedAt",
                page_size=20,
            )
            for a in resp.get("articles", []):
                articles.append({
                    "source": name,
                    "title": a.get("title") or "",
                    "description": a.get("description") or "",
                    "content": a.get("content") or "",
                    "url": a.get("url") or "",
                    "published_at": a.get("publishedAt") or "",
                    "fetched_at": datetime.utcnow(),
                })
        except Exception as e:
            print(f"NewsAPI error for {name}: {e}")
        time.sleep(0.5)

    return articles


def _fetch_rss_with_ssl(url: str):
    """Fetch RSS feed bytes using certifi SSL context, then parse."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; MediaLens/1.0; +https://github.com/medialens)"},
        )
        with urllib.request.urlopen(req, context=_SSL_CTX, timeout=10) as resp:
            data = resp.read()
        return feedparser.parse(data)
    except Exception:
        # Fallback: let feedparser handle it directly (works for http://)
        return feedparser.parse(url)


def fetch_from_rss() -> dict[str, dict]:
    """Returns dict keyed by URL with article data."""
    rss_articles = {}
    for name, rss_url in OUTLET_RSS.items():
        try:
            feed = _fetch_rss_with_ssl(rss_url)
            for entry in feed.entries[:20]:
                url = entry.get("link", "")
                if not url:
                    continue
                summary = entry.get("summary", "") or entry.get("description", "") or ""
                rss_articles[url] = {
                    "source": name,
                    "title": entry.get("title", ""),
                    "description": summary[:1000],
                    "content": summary[:2000],
                    "url": url,
                    "published_at": entry.get("published", ""),
                    "fetched_at": datetime.utcnow(),
                }
        except Exception as e:
            print(f"RSS error for {name}: {e}")
        time.sleep(0.2)
    return rss_articles


def store_articles(articles: list[dict]) -> int:
    stored = 0
    for article in articles:
        if not article.get("url"):
            continue
        try:
            db.articles().update_one(
                {"url": article["url"]},
                {"$setOnInsert": {
                    "cluster_id": None,
                    "sentiment_score": None,
                    "framing_features": None,
                    "embedding": None,
                }, "$set": article},
                upsert=True,
            )
            stored += 1
        except Exception as e:
            print(f"Store error: {e}")
    return stored


def run_ingestion() -> int:
    print("Starting ingestion...")
    rss_by_url = fetch_from_rss()
    api_articles = fetch_from_newsapi()

    # Merge: API articles take priority; fill missing body from RSS
    merged: dict[str, dict] = dict(rss_by_url)
    for a in api_articles:
        url = a["url"]
        if url in merged:
            if not a["content"] and merged[url].get("content"):
                a["content"] = merged[url]["content"]
            if not a["description"] and merged[url].get("description"):
                a["description"] = merged[url]["description"]
        merged[url] = a

    count = store_articles(list(merged.values()))
    print(f"Ingestion complete: {count} articles stored/updated")
    db.log_pipeline_run(count)
    return count
