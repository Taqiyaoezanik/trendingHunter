"""
Notifier — kirim laporan tren ke Telegram dan simpan ke JSON.
"""

import json
import logging
import os
import requests
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "output"))

MOMENTUM_EMOJI = {
    "hot": "🔥",
    "rising": "📈",
    "stable": "➡️",
}

NICHE_LABEL = {
    "tech_ai": "Tech / AI",
    "finance_crypto": "Finance / Crypto",
}


def format_telegram_message(analysis: dict) -> str:
    """Format hasil analisis menjadi pesan Telegram yang rapi."""
    now = datetime.now().strftime("%A, %d %b %Y · %H:%M WIB")
    trends = analysis.get("trends", [])
    summary = analysis.get("summary", "")
    best_pick = analysis.get("best_pick", 1)

    lines = [
        f"*Trend Hunter — Laporan Harian*",
        f"_{now}_",
        f"",
        f"{summary}",
        f"",
        f"*Top {len(trends)} Tren Hari Ini:*",
        f"",
    ]

    for t in trends:
        rank = t.get("rank", 0)
        emoji = MOMENTUM_EMOJI.get(t.get("momentum", "stable"), "➡️")
        star = " ⭐ *Best Pick*" if rank == best_pick else ""
        niche = NICHE_LABEL.get(t.get("niche", ""), t.get("niche", ""))
        score = t.get("virality_score", 0)
        formats = " · ".join(t.get("content_formats", []))

        lines += [
            f"{emoji} *{rank}. {t.get('topic', '')}*{star}",
            f"   Niche: {niche} · Score: {score}/100",
            f"   Hook: _{t.get('hook', '')}_",
            f"   Angle: {t.get('angle', '')}",
            f"   Format: {formats}",
            f"   Kenapa sekarang: {t.get('why_now', '')}",
            f"",
        ]

    lines += [
        f"---",
        f"_Model: {analysis.get('model_used', 'N/A')}_",
    ]

    return "\n".join(lines)


def send_telegram(message: str) -> bool:
    """Kirim pesan ke Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram credentials belum di-set, skip notifikasi.")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }

    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        logger.info("Pesan Telegram berhasil dikirim.")
        return True
    except Exception as e:
        logger.error(f"Gagal kirim Telegram: {e}")
        return False


def save_json(raw_data: dict, analysis: dict) -> Path:
    """Simpan raw data + analisis ke file JSON harian."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    filepath = OUTPUT_DIR / f"trends_{today}.json"

    output = {
        "date": today,
        "raw_data": raw_data,
        "analysis": analysis,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    logger.info(f"Laporan disimpan: {filepath}")
    return filepath


def notify(raw_data: dict, analysis: dict):
    """Entry point: simpan JSON + kirim Telegram."""
    # Selalu simpan JSON
    json_path = save_json(raw_data, analysis)

    # Kirim Telegram
    message = format_telegram_message(analysis)
    telegram_ok = send_telegram(message)

    return {
        "json_saved": str(json_path),
        "telegram_sent": telegram_ok,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    dummy_analysis = {
        "trends": [
            {
                "rank": 1,
                "topic": "AI Coding Assistant Populer di Indonesia",
                "niche": "tech_ai",
                "sources": ["Google Trends", "Reddit"],
                "virality_score": 88,
                "momentum": "hot",
                "hook": "Gue coding 10x lebih cepat sejak pakai ini — dan gratis.",
                "angle": "Review jujur dari developer Indonesia yang sudah coba semua tools",
                "content_formats": ["short_video", "thread"],
                "why_now": "Minggu ini Google merilis Gemini Code Assist gratis untuk semua user.",
            }
        ],
        "summary": "Tren tech AI mendominasi hari ini, terutama tools coding dan privasi data.",
        "best_pick": 1,
        "model_used": "deepseek/deepseek-chat",
    }
    result = notify({}, dummy_analysis)
    print(result)
