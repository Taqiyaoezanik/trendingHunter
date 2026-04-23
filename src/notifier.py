"""
Notifier — kirim laporan tren ke Telegram dan simpan ke JSON.
Pakai parse_mode HTML agar karakter ………. tidak bikin error Markdown.
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

MOMENTUM_EMOJI = {"hot": "🔥", "rising": "📈", "stable": "➡️"}
NICHE_LABEL = {"tech_ai": "Tech / AI", "finance_crypto": "Finance / Crypto"}


def escape_html(text: str) -> str:
    """Escape karakter HTML yang bisa bikin error."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def format_telegram_messages(analysis: dict) -> list:
    """
    Return list of messages — satu per tren.
    Pakai HTML formatting, bukan Markdown, agar ………. tidak error.
    """
    now = datetime.now().strftime("%A, %d %b %Y · %H:%M WIB")
    trends = analysis.get("trends", [])
    summary = analysis.get("summary", "")
    best_pick = analysis.get("best_pick", 1)
    messages = []

    # Pesan 1: header
    header = (
        f"<b>Trend Hunter — {now}</b>\n\n"
        f"{escape_html(summary)}\n\n"
        f"Ada <b>{len(trends)} konten siap posting</b> buat hari ini 👇"
    )
    messages.append(header)

    # Satu pesan per tren
    for t in trends:
        rank = t.get("rank", 0)
        emoji = MOMENTUM_EMOJI.get(t.get("momentum", "stable"), "➡️")
        star = " ⭐ <b>Best Pick</b>" if rank == best_pick else ""
        niche = NICHE_LABEL.get(t.get("niche", ""), t.get("niche", ""))
        score = t.get("virality_score", 0)
        formats = " · ".join(t.get("content_formats", []))
        caption = escape_html(t.get("caption", ""))
        why_now = escape_html(t.get("why_now", ""))
        topic = escape_html(t.get("topic", ""))
        sources = escape_html(", ".join(t.get("sources", [])))

        msg = (
            f"{emoji} <b>Tren #{rank} — {topic}</b>{star}\n"
            f"<i>{niche}</i> · Score: <b>{score}/100</b> · {formats}\n"
            f"Kenapa sekarang: <i>{why_now}</i>\n\n"
            f"— <b>CAPTION SIAP POSTING</b> —\n\n"
            f"{caption}\n\n"
            f"<i>Sumber: {sources}</i>"
        )
        messages.append(msg)

    return messages


def send_telegram(message: str) -> bool:
    """Kirim satu pesan ke Telegram dengan HTML parse mode."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram credentials belum di-set, skip.")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Gagal kirim HTML: {e}")
        # Fallback: kirim plain text
        try:
            plain = message.replace("<b>", "").replace("</b>", "") \
                           .replace("<i>", "").replace("</i>", "") \
                           .replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
            payload2 = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": plain,
                "disable_web_page_preview": True,
            }
            resp2 = requests.post(url, json=payload2, timeout=15)
            resp2.raise_for_status()
            logger.info("Terkirim sebagai plain text.")
            return True
        except Exception as e2:
            logger.error(f"Gagal kirim plain text juga: {e2}")
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


def notify(raw_data: dict, analysis: dict) -> dict:
    """Entry point: simpan JSON + kirim semua pesan ke Telegram."""
    json_path = save_json(raw_data, analysis)
    messages = format_telegram_messages(analysis)
    sent_count = 0

    import time
    for i, msg in enumerate(messages):
        ok = send_telegram(msg)
        if ok:
            sent_count += 1
            logger.info(f"Pesan {i+1}/{len(messages)} terkirim")
        time.sleep(0.5)

    return {
        "json_saved": str(json_path),
        "telegram_sent": sent_count > 0,
        "messages_sent": sent_count,
        "messages_total": len(messages),
    }
