"""
Notifier — kirim laporan tren ke Telegram dan simpan ke JSON.
Format pesan: konten siap posting gaya Oezank, bukan sekadar ide.
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


def format_telegram_message(analysis: dict) -> list:
    """
    Return list of messages — satu pesan per tren.
    Telegram punya limit 4096 karakter per pesan,
    jadi kita split per tren agar caption tidak kepotong.
    """
    now = datetime.now().strftime("%A, %d %b %Y · %H:%M WIB")
    trends = analysis.get("trends", [])
    summary = analysis.get("summary", "")
    best_pick = analysis.get("best_pick", 1)
    messages = []

    # Pesan pertama: header + summary
    header = (
        f"*Trend Hunter — {now}*\n\n"
        f"{summary}\n\n"
        f"Ada *{len(trends)} konten siap posting* buat hari ini 👇"
    )
    messages.append(header)

    # Satu pesan per tren — isi caption lengkap
    for t in trends:
        rank = t.get("rank", 0)
        emoji = MOMENTUM_EMOJI.get(t.get("momentum", "stable"), "➡️")
        star = " ⭐ *Best Pick*" if rank == best_pick else ""
        niche = NICHE_LABEL.get(t.get("niche", ""), t.get("niche", ""))
        score = t.get("virality_score", 0)
        formats = " · ".join(t.get("content_formats", []))
        caption = t.get("caption", "").replace("……….", "\\.\\.\\.\\.\\.")

        msg = (
            f"{emoji} *Tren #{rank} — {t.get('topic', '')}*{star}\n"
            f"_{niche}_ · Score: *{score}/100* · {formats}\n"
            f"Kenapa sekarang: _{t.get('why_now', '')}_\n\n"
            f"*— CAPTION SIAP POSTING —*\n\n"
            f"{t.get('caption', '')}\n\n"
            f"Sumber: {', '.join(t.get('sources', []))}"
        )
        messages.append(msg)

    return messages


def send_telegram(message: str) -> bool:
    """Kirim satu pesan ke Telegram."""
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
        return True
    except Exception as e:
        logger.error(f"Gagal kirim Telegram: {e}")
        # Coba kirim tanpa markdown kalau format error
        try:
            payload["parse_mode"] = None
            payload["text"] = message.replace("*", "").replace("_", "")
            resp = requests.post(url, json=payload, timeout=15)
            resp.raise_for_status()
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

    messages = format_telegram_message(analysis)
    sent_count = 0

    for i, msg in enumerate(messages):
        ok = send_telegram(msg)
        if ok:
            sent_count += 1
            logger.info(f"Pesan {i+1}/{len(messages)} terkirim")
        import time
        time.sleep(0.5)  # hindari rate limit Telegram

    logger.info(f"Telegram: {sent_count}/{len(messages)} pesan terkirim")

    return {
        "json_saved": str(json_path),
        "telegram_sent": sent_count > 0,
        "messages_sent": sent_count,
        "messages_total": len(messages),
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    dummy_analysis = {
        "trends": [
            {
                "rank": 1,
                "topic": "AI Coding Assistant Gratis dari Google",
                "niche": "tech_ai",
                "sources": ["TechCrunch", "HackerNews"],
                "virality_score": 88,
                "momentum": "hot",
                "why_now": "Google baru rilis Gemini Code Assist gratis untuk semua developer.",
                "caption": (
                    "Google baru aja ngasih sesuatu yang bikin developer seneng……….\n\n"
                    "Gemini Code Assist sekarang gratis buat semua orang. Bukan trial, bukan limited — gratis beneran.\n\n"
                    "Gw udah coba sendiri. Kemampuan autocomplete nya lumayan, bisa ngerti konteks code yang panjang, "
                    "dan yang paling berguna — bisa explain error langsung di dalam IDE.\n\n"
                    "Tapi tetep ada catatannya:\n"
                    "- Data code lu bisa dipakai Google buat training (baca privacy policy nya)\n"
                    "- Untuk project sensitif atau company code, pikir dua kali dulu\n"
                    "- Masih kalah di beberapa aspek dibanding GitHub Copilot yang berbayar\n\n"
                    "Kalau lu developer atau lagi belajar coding, worth banget buat dicoba — gratis soalnya……….\n\n"
                    "Udah ada yang nyoba? Drop di komen, lebih suka tools mana.\n"
                    "Thanks dan babay"
                ),
                "content_formats": ["short_video", "carousel"],
            }
        ],
        "summary": "Hari ini banyak noise dari dunia AI — yang paling worth dibahas buat audiens lu ada di bawah.",
        "best_pick": 1,
        "model_used": "deepseek/deepseek-chat",
    }
    result = notify({}, dummy_analysis)
    print(result)
