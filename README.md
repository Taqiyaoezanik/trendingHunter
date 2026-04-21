# Trend Hunter Agent

Agent Python yang otomatis memantau tren harian dari X/Twitter, TikTok, Google Trends, Reddit, dan YouTube — lalu menganalisisnya dengan LLM (DeepSeek V3 via OpenRouter) dan mengirim laporan ke Telegram + menyimpan ke JSON.

**Niche default:** Tech/AI dan Finance/Crypto (bisa dikustomisasi di `src/collector.py`)

---

## Fitur

- Kumpulkan sinyal tren dari Google Trends, Reddit RSS, YouTube RSS
- Analisis dan scoring otomatis via LLM (DeepSeek V3 / GPT-4o-mini)
- Hook konten siap pakai untuk setiap tren
- Laporan harian ke Telegram + file JSON
- Bisa dijadwalkan via PM2 atau cron

---

## Cara Pakai

### 1. Clone repo

```bash
git clone https://github.com/YOUR_USERNAME/trend-hunter-agent.git
cd trend-hunter-agent
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Setup environment

```bash
cp .env.example .env
nano .env   # Isi API key kamu
```

Isi minimal:
- `OPENROUTER_API_KEY` — dari [openrouter.ai/keys](https://openrouter.ai/keys)
- `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` (opsional, untuk notifikasi)

### 4. Jalankan manual

```bash
python main.py
```

Output akan tampil di terminal + tersimpan di folder `output/trends_YYYY-MM-DD.json`.

---

## Setup Telegram Bot

1. Chat `@BotFather` di Telegram → `/newbot` → ikuti instruksi
2. Copy token yang diberikan → paste ke `TELEGRAM_BOT_TOKEN`
3. Chat `@userinfobot` → copy ID kamu → paste ke `TELEGRAM_CHAT_ID`
4. Kirim pesan dulu ke bot kamu agar bot bisa membalas

---

## Jadwal Otomatis dengan PM2 (untuk VPS)

```bash
# Install PM2 jika belum ada
npm install -g pm2

# Jalankan dengan jadwal harian jam 07:00 WIB
pm2 start ecosystem.config.js

# Simpan agar jalan setelah reboot
pm2 save
pm2 startup

# Monitor log
pm2 logs trend-hunter
```

Atau pakai cron langsung:

```bash
crontab -e
# Tambahkan baris ini (jam 07:00 WIB = 00:00 UTC):
0 0 * * * cd /path/to/trend-hunter-agent && python3 main.py >> logs/cron.log 2>&1
```

---

## Struktur Proyek

```
trend-hunter-agent/
├── main.py               # Entry point utama
├── src/
│   ├── collector.py      # Ambil data dari semua sumber
│   ├── analyzer.py       # Analisis tren via LLM (OpenRouter)
│   └── notifier.py       # Kirim ke Telegram + simpan JSON
├── output/               # Laporan harian JSON (di-gitignore)
├── logs/                 # Log harian (di-gitignore)
├── ecosystem.config.js   # Config PM2
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Kustomisasi Niche

Edit `src/collector.py`, bagian `NICHES`:

```python
NICHES = {
    "tech_ai": ["AI tools", "machine learning", ...],
    "finance_crypto": ["crypto Indonesia", "saham", ...],
    # Tambah niche baru:
    "lifestyle": ["gaya hidup", "self improvement", ...],
}
```

---

## Ganti Model LLM

Di `.env`, ubah `LLM_MODEL`:

| Model | Kecepatan | Biaya | Cocok untuk |
|-------|-----------|-------|-------------|
| `deepseek/deepseek-chat` | Cepat | ~$0.01/hari | **Default, terbaik** |
| `openai/gpt-4o-mini` | Sedang | ~$0.03/hari | Alternatif |
| `openai/gpt-4o` | Lambat | ~$0.20/hari | Kalau mau premium |

---

## Contoh Output JSON

```json
{
  "date": "2025-04-21",
  "analysis": {
    "trends": [
      {
        "rank": 1,
        "topic": "AI Coding Assistant Populer di Indonesia",
        "niche": "tech_ai",
        "virality_score": 88,
        "momentum": "hot",
        "hook": "Gue coding 10x lebih cepat sejak pakai ini — dan gratis.",
        "angle": "Review jujur dari developer Indonesia yang sudah coba semua tools",
        "content_formats": ["short_video", "thread"],
        "why_now": "Google baru rilis Gemini Code Assist gratis untuk semua user."
      }
    ],
    "summary": "Tren tech AI mendominasi hari ini.",
    "best_pick": 1
  }
}
```

---

## Integrasi ke Script Writer Agent

Output JSON dari agent ini bisa langsung di-feed ke Script Writer Agent:

```python
import json
from pathlib import Path
from datetime import datetime

today = datetime.now().strftime("%Y-%m-%d")
with open(f"output/trends_{today}.json") as f:
    data = json.load(f)

best = data["analysis"]["trends"][0]
print(f"Topik: {best['topic']}")
print(f"Hook: {best['hook']}")
# Feed ke Script Writer...
```

---

## License

MIT — bebas dipakai, dimodifikasi, dan didistribusikan.
