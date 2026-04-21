"""
Data Collector — mengambil sinyal tren dari berbagai sumber.
Sources: Google Trends (pytrends), Reddit RSS, YouTube RSS
"""

import feedparser
import json
import logging
from datetime import datetime, timedelta
from pytrends.request import TrendReq
import time

logger = logging.getLogger(__name__)

NICHES = {
    "tech_ai": [
        "artificial intelligence", "AI tools", "machine learning", "ChatGPT",
        "coding assistant", "teknologi AI", "AI Indonesia", "developer tools"
    ],
    "finance_crypto": [
        "crypto Indonesia", "Bitcoin", "saham Indonesia", "investasi", "IHSG",
        "DeFi", "Solana", "altcoin", "reksadana", "finansial"
    ]
}

YOUTUBE_RSS_CHANNELS = [
    "https://www.youtube.com/feeds/videos.xml?channel_id=UCVHkE6tPwQEgNj3LqJZ6WUg",  # Tech Indo
]

REDDIT_RSS_FEEDS = [
    "https://www.reddit.com/r/Indonesia/.rss",
    "https://www.reddit.com/r/CryptoCurrency/.rss",
    "https://www.reddit.com/r/technology/.rss",
    "https://www.reddit.com/r/artificial/.rss",
]


def fetch_google_trends(niche_keywords: list, geo: str = "ID") -> list:
    """Ambil trending queries dari Google Trends."""
    results = []
    try:
        pytrends = TrendReq(hl="id-ID", tz=420, timeout=(10, 25))
        # Ambil realtime trending searches
        trending = pytrends.trending_searches(pn="indonesia")
        for term in trending[0].tolist()[:20]:
            results.append({
                "title": term,
                "source": "Google Trends",
                "type": "trending_search",
                "url": f"https://trends.google.com/trends/explore?q={term}&geo=ID"
            })
        time.sleep(1)

        # Interest over time untuk niche keywords
        chunks = [niche_keywords[i:i+5] for i in range(0, len(niche_keywords), 5)]
        for chunk in chunks[:2]:
            try:
                pytrends.build_payload(chunk, timeframe="now 1-d", geo=geo)
                interest = pytrends.interest_over_time()
                if not interest.empty:
                    latest = interest.iloc[-1]
                    for kw in chunk:
                        if kw in latest and latest[kw] > 50:
                            results.append({
                                "title": kw,
                                "source": "Google Trends",
                                "type": "rising_keyword",
                                "score": int(latest[kw]),
                                "url": f"https://trends.google.com/trends/explore?q={kw}&geo=ID"
                            })
                time.sleep(2)
            except Exception as e:
                logger.warning(f"Trends chunk error: {e}")
    except Exception as e:
        logger.error(f"Google Trends error: {e}")
    return results


def fetch_reddit_rss() -> list:
    """Ambil post terpopuler dari subreddit relevan via RSS."""
    results = []
    for feed_url in REDDIT_RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]:
                results.append({
                    "title": entry.get("title", ""),
                    "source": "Reddit",
                    "url": entry.get("link", ""),
                    "summary": entry.get("summary", "")[:200],
                    "published": entry.get("published", "")
                })
            time.sleep(0.5)
        except Exception as e:
            logger.warning(f"Reddit RSS error {feed_url}: {e}")
    return results


def fetch_youtube_rss() -> list:
    """Ambil video terbaru dari channel YouTube relevan via RSS."""
    results = []
    for feed_url in YOUTUBE_RSS_CHANNELS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:5]:
                results.append({
                    "title": entry.get("title", ""),
                    "source": "YouTube",
                    "url": entry.get("link", ""),
                    "channel": feed.feed.get("title", ""),
                    "published": entry.get("published", "")
                })
        except Exception as e:
            logger.warning(f"YouTube RSS error {feed_url}: {e}")
    return results


def collect_all() -> dict:
    """Jalankan semua collector dan return data mentah."""
    logger.info("Mulai pengumpulan data...")

    all_keywords = NICHES["tech_ai"] + NICHES["finance_crypto"]

    data = {
        "collected_at": datetime.now().isoformat(),
        "google_trends": fetch_google_trends(all_keywords),
        "reddit": fetch_reddit_rss(),
        "youtube": fetch_youtube_rss(),
    }

    total = sum(len(v) for v in data.values() if isinstance(v, list))
    logger.info(f"Total sinyal terkumpul: {total}")
    return data


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raw = collect_all()
    print(json.dumps(raw, indent=2, ensure_ascii=False))
