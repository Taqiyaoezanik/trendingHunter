"""
Data Collector — mengambil sinyal tren dari berbagai sumber gratis.
Sources: Google Trends, Reddit RSS, YouTube RSS, Hacker News,
         CoinDesk, CoinTelegraph, TechInAsia, Katadata, GitHub Trending
"""

import feedparser
import requests
import json
import logging
import re
from datetime import datetime
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

# === RSS FEEDS — semua gratis, tidak butuh API key ===

REDDIT_FEEDS = [
    ("Indonesia",       "https://www.reddit.com/r/Indonesia/.rss"),
    ("CryptoCurrency",  "https://www.reddit.com/r/CryptoCurrency/.rss"),
    ("technology",      "https://www.reddit.com/r/technology/.rss"),
    ("artificial",      "https://www.reddit.com/r/artificial/.rss"),
    ("LocalLLaMA",      "https://www.reddit.com/r/LocalLLaMA/.rss"),
    ("investing",       "https://www.reddit.com/r/investing/.rss"),
]

YOUTUBE_FEEDS = [
    ("Fireship",        "https://www.youtube.com/feeds/videos.xml?channel_id=UCsBjURrPoezykLs9EqgamOA"),
    ("TED",             "https://www.youtube.com/feeds/videos.xml?channel_id=UCAuUUnT6oDeKwE6v1NGQxug"),
    ("Modus",           "https://www.youtube.com/feeds/videos.xml?channel_id=UCiGm_E4Ze-UqADzGmBKSDtQ"),
]

CRYPTO_FEEDS = [
    ("CoinDesk",        "https://www.coindesk.com/arc/outboundfeeds/rss/"),
    ("CoinTelegraph",   "https://cointelegraph.com/rss"),
    ("Decrypt",         "https://decrypt.co/feed"),
    ("TheBlock",        "https://www.theblock.co/rss.xml"),
]

TECH_FEEDS = [
    ("TechCrunch",      "https://techcrunch.com/feed/"),
    ("TheVerge",        "https://www.theverge.com/rss/index.xml"),
    ("VentureBeat AI",  "https://venturebeat.com/category/ai/feed/"),
    ("TechInAsia",      "https://www.techinasia.com/feed"),
    ("Katadata",        "https://katadata.co.id/feed"),
    ("HackerNews",      "https://hnrss.org/frontpage"),
    ("HN Ask",          "https://hnrss.org/ask"),
]


def fetch_google_trends(niche_keywords: list, geo: str = "ID") -> list:
    """Ambil trending queries dari Google Trends Indonesia."""
    results = []
    try:
        pytrends = TrendReq(hl="id-ID", tz=420, timeout=(10, 25))

        # Realtime trending searches Indonesia
        try:
            trending = pytrends.trending_searches(pn="indonesia")
            for term in trending[0].tolist()[:20]:
                results.append({
                    "title": term,
                    "source": "Google Trends",
                    "type": "trending_search",
                    "url": f"https://trends.google.com/trends/explore?q={term}&geo=ID"
                })
            time.sleep(1)
        except Exception as e:
            logger.warning(f"Google Trends realtime error: {e}")

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

    logger.info(f"Google Trends: {len(results)} sinyal")
    return results


def fetch_rss_feeds(feeds: list, category: str, max_per_feed: int = 8) -> list:
    """Generic RSS fetcher untuk semua kategori."""
    results = []
    for name, url in feeds:
        try:
            feed = feedparser.parse(url)
            count = 0
            for entry in feed.entries[:max_per_feed]:
                title = entry.get("title", "").strip()
                if not title:
                    continue
                results.append({
                    "title": title,
                    "source": name,
                    "category": category,
                    "url": entry.get("link", ""),
                    "summary": entry.get("summary", "")[:200].strip(),
                    "published": entry.get("published", "")
                })
                count += 1
            logger.info(f"  {name}: {count} artikel")
            time.sleep(0.3)
        except Exception as e:
            logger.warning(f"RSS error [{name}]: {e}")
    return results


def fetch_github_trending() -> list:
    """Scrape GitHub Trending page untuk tech topics."""
    results = []
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; TrendHunter/1.0)"}
        resp = requests.get("https://github.com/trending", headers=headers, timeout=10)
        if resp.status_code == 200:
            matches = re.findall(
                r'<h2[^>]*>\s*<a[^>]*href="/([^"]+)"[^>]*>',
                resp.text
            )
            for repo_path in matches[:15]:
                repo_path = repo_path.strip()
                if "/" in repo_path and len(repo_path) < 60:
                    results.append({
                        "title": repo_path,
                        "source": "GitHub Trending",
                        "category": "tech_ai",
                        "url": f"https://github.com/{repo_path}",
                        "summary": "Trending repository di GitHub hari ini"
                    })
            logger.info(f"  GitHub Trending: {len(results)} repo")
    except Exception as e:
        logger.warning(f"GitHub Trending error: {e}")
    return results


def collect_all() -> dict:
    """Jalankan semua collector dan return data mentah."""
    logger.info("=" * 40)
    logger.info("Mulai pengumpulan data dari semua sumber...")
    logger.info("=" * 40)

    all_keywords = NICHES["tech_ai"] + NICHES["finance_crypto"]

    logger.info("[ Google Trends ]")
    google = fetch_google_trends(all_keywords)

    logger.info("[ Reddit ]")
    reddit = fetch_rss_feeds(REDDIT_FEEDS, "social", max_per_feed=8)

    logger.info("[ YouTube ]")
    youtube = fetch_rss_feeds(YOUTUBE_FEEDS, "video", max_per_feed=5)

    logger.info("[ Crypto News ]")
    crypto_news = fetch_rss_feeds(CRYPTO_FEEDS, "finance_crypto", max_per_feed=8)

    logger.info("[ Tech News ]")
    tech_news = fetch_rss_feeds(TECH_FEEDS, "tech_ai", max_per_feed=8)

    logger.info("[ GitHub Trending ]")
    github = fetch_github_trending()

    data = {
        "collected_at": datetime.now().isoformat(),
        "google_trends": google,
        "reddit": reddit,
        "youtube": youtube,
        "crypto_news": crypto_news,
        "tech_news": tech_news,
        "github_trending": github,
    }

    total = sum(len(v) for v in data.values() if isinstance(v, list))
    logger.info("=" * 40)
    logger.info(f"Total sinyal terkumpul: {total}")
    logger.info("=" * 40)
    return data


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raw = collect_all()
    print(json.dumps(raw, indent=2, ensure_ascii=False))
