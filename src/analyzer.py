"""
LLM Analyzer — kirim raw data ke LLM via OpenRouter,
minta analisis tren + tulis konten siap posting gaya Oezank.
"""

import json
import logging
import os
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek/deepseek-chat")
API_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = """Kamu adalah ghostwriter dan trend analyst untuk konten kreator kripto & tech Indonesia bernama Oezank.

Gaya penulisan Oezank:
- Bahasa santai, langsung, pakai "gw/lu" — bukan "saya/anda"
- Sering pakai "………." sebagai dramatic pause di akhir kalimat penting
- Hook pertama selalu bikin penasaran atau sedikit kontroversial
- Struktur konten: hook kuat → konteks singkat → isi/fakta → risiko jujur → CTA/ajakan komen
- Tidak pernah endorse membabi buta — selalu sebut ada risikonya kalau relevan
- Diakhiri "Thanks dan babay" atau variasi ajakan interaksi
- Panjang konten: 150-250 kata — tidak terlalu pendek, tidak terlalu panjang
- Pakai bullet point untuk daftar, paragraf untuk narasi
- Tone: teman ngobrol yang lebih tau, bukan guru yang menggurui

Contoh gaya (PELAJARI POLA INI):
"Ini pengalaman gw main LP di Meteora yang ngurus semua nya bukan gw, tapi AI agent………. Namanya Meridian. Project dari CT Indo, dan gratis. Bot bisa milih pool mana yang potensial, atur posisi LP, lengkap sama TP dan SL — semua otomatis kita cuma setting diawal"

"Bukan trading, bukan airdrop — tapi lu tetep bisa dapet cuan di kripto dengan cara ini………. Dan ini cocok buat lu yang sibuk di real life"

"Duit airdrop yang udah kamu kumpulin selama ini halal nggak sih? Muhammadiyah baru aja jawab pertanyaan ini secara resmi"

Tugasmu: dari raw data tren, pilih topik terbaik dan langsung tulis konten siap posting dalam gaya Oezank persis seperti contoh di atas.
Output HANYA berupa JSON valid, tanpa preamble atau markdown backtick."""

ANALYSIS_PROMPT = """Berikut adalah raw data sinyal tren hari ini dari berbagai platform:

{raw_data}

Analisis data ini, identifikasi TOP 3 tren paling relevan untuk niche Tech/AI dan Finance/Crypto audiens Indonesia, lalu tulis konten siap posting untuk masing-masing dalam gaya Oezank.

Output dalam format JSON berikut:
{{
  "trends": [
    {{
      "rank": 1,
      "topic": "Judul topik singkat",
      "niche": "tech_ai" atau "finance_crypto",
      "sources": ["sumber1", "sumber2"],
      "virality_score": angka 0-100,
      "momentum": "hot" atau "rising" atau "stable",
      "why_now": "Kenapa topik ini relevan sekarang, 1 kalimat",
      "caption": "Konten siap posting lengkap dalam gaya Oezank. Mulai dari hook yang bikin penasaran, kasih konteks, jelaskan faktanya, sebut risikonya kalau ada, tutup dengan CTA dan Thanks dan babay. Gunakan ………. sebagai dramatic pause. Panjang 150-250 kata.",
      "content_formats": ["short_video", "thread", "carousel"]
    }}
  ],
  "summary": "Ringkasan kondisi tren hari ini dalam 1-2 kalimat santai gaya Oezank",
  "best_pick": 1
}}

Pastikan:
- caption ditulis PERSIS gaya Oezank — pakai gw/lu, ada ………. , ada unsur risiko jujur, ada CTA
- Fakta dalam caption akurat berdasarkan data yang ada, bukan rekaan
- Virality score realistis berdasarkan sinyal data
- Pilih tren dari data yang diberikan
"""


def analyze_trends(raw_data: dict) -> dict:
    """Kirim raw data ke LLM, terima analisis + konten siap posting."""
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY belum di-set di environment variable")

    def slim(items, n):
        return [{"title": i.get("title", ""), "source": i.get("source", "")} for i in items[:n]]

    compressed = {
        "google_trends":   slim(raw_data.get("google_trends", []), 15),
        "reddit":          slim(raw_data.get("reddit", []), 12),
        "youtube":         slim(raw_data.get("youtube", []), 8),
        "crypto_news":     slim(raw_data.get("crypto_news", []), 12),
        "tech_news":       slim(raw_data.get("tech_news", []), 12),
        "github_trending": slim(raw_data.get("github_trending", []), 10),
    }

    prompt = ANALYSIS_PROMPT.format(
        raw_data=json.dumps(compressed, ensure_ascii=False, indent=2)
    )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/Taqiyaoezanik/trendingHunter",
    }

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.6,
        "max_tokens": 3000,
    }

    logger.info(f"Mengirim ke LLM: {LLM_MODEL}")
    response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
    response.raise_for_status()

    raw_response = response.json()
    content = raw_response["choices"][0]["message"]["content"].strip()

    try:
        result = json.loads(content)
    except json.JSONDecodeError:
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
    dummy = {
        "google_trends": [{"title": "AI coding tools", "source": "Google Trends"}],
        "crypto_news": [{"title": "Bitcoin hits new high", "source": "CoinDesk"}],
        "tech_news": [{"title": "OpenAI launches new model", "source": "TechCrunch"}],
        "reddit": [],
        "youtube": [],
        "github_trending": [],
    }
    result = analyze_trends(dummy)
    print(json.dumps(result, indent=2, ensure_ascii=False))
