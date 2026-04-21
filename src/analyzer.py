"""
LLM Analyzer — kirim raw data ke LLM via OpenRouter,
minta analisis tren + scoring + hook suggestion.
"""

import json
import logging
import os
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek/deepseek-chat")  # DeepSeek V3
API_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = """Kamu adalah trend analyst senior untuk konten kreator Indonesia.
Spesialisasi kamu: Tech/AI dan Finance/Crypto.
Tugasmu: menganalisis raw data sinyal tren dan mengidentifikasi mana yang paling potensial untuk dijadikan konten viral.
Selalu respond dalam Bahasa Indonesia yang natural.
Output HANYA berupa JSON valid, tanpa preamble atau markdown backtick."""

ANALYSIS_PROMPT = """Berikut adalah raw data sinyal tren hari ini dari berbagai platform:

{raw_data}

Analisis data ini dan identifikasi TOP 5 tren yang paling relevan dan potensial untuk konten kreator niche Tech/AI dan Finance/Crypto di Indonesia.

Untuk setiap tren, berikan output dalam format JSON berikut:
{{
  "trends": [
    {{
      "rank": 1,
      "topic": "Judul topik singkat dan menarik",
      "niche": "tech_ai" atau "finance_crypto",
      "sources": ["sumber1", "sumber2"],
      "virality_score": angka 0-100,
      "momentum": "hot" atau "rising" atau "stable",
      "hook": "1 kalimat hook pembuka yang powerful untuk konten",
      "angle": "Sudut pandang unik atau controversial yang bisa diambil",
      "content_formats": ["short_video", "thread", "carousel"],
      "why_now": "Kenapa topik ini relevan SEKARANG, dalam 1 kalimat"
    }}
  ],
  "summary": "Ringkasan singkat kondisi tren hari ini dalam 2 kalimat",
  "best_pick": 1
}}

Pastikan:
- Hook dalam Bahasa Indonesia yang natural, bukan terjemahan kaku
- Virality score realistis berdasarkan data, bukan asal tinggi
- Pilih tren yang benar-benar ada di data, bukan rekaan
"""


def analyze_trends(raw_data: dict) -> dict:
    """Kirim raw data ke LLM, terima analisis terstruktur."""
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY belum di-set di environment variable")

    # Kompres data agar tidak terlalu panjang
    compressed = {
        "google_trends_top": raw_data.get("google_trends", [])[:15],
        "reddit_top": [
            {"title": r["title"], "source": r["source"]}
            for r in raw_data.get("reddit", [])[:15]
        ],
        "youtube_top": [
            {"title": r["title"], "channel": r.get("channel", "")}
            for r in raw_data.get("youtube", [])[:10]
        ],
    }

    prompt = ANALYSIS_PROMPT.format(
        raw_data=json.dumps(compressed, ensure_ascii=False, indent=2)
    )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/trend-hunter-agent",
    }

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.4,
        "max_tokens": 2000,
    }

    logger.info(f"Mengirim ke LLM: {LLM_MODEL}")
    response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
    response.raise_for_status()

    raw_response = response.json()
    content = raw_response["choices"][0]["message"]["content"].strip()

    # Parse JSON dari response
    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        # Fallback: coba ekstrak JSON dari dalam teks
        import re
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            result = json.loads(match.group())
        else:
            raise ValueError(f"LLM tidak return JSON valid: {content[:200]}")

    result["analyzed_at"] = datetime.now().isoformat()
    result["model_used"] = LLM_MODEL
    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Test dengan dummy data
    dummy = {
        "google_trends": [{"title": "AI coding tools", "source": "Google Trends"}],
        "reddit": [{"title": "Solana price prediction 2025", "source": "Reddit"}],
        "youtube": [{"title": "Tutorial Python AI terbaru", "channel": "Tech Indo"}],
    }
    result = analyze_trends(dummy)
    print(json.dumps(result, indent=2, ensure_ascii=False))
