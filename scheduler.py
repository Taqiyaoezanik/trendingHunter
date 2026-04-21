"""
scheduler.py — Loop internal setiap 6 jam.

Alternatif dari PM2 cron jika kamu mau satu proses yang terus berjalan.
Jalankan: python scheduler.py
Atau via PM2 tanpa cron_restart:
  pm2 start scheduler.py --name trend-hunter --interpreter python3
"""

import time
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Setup logging
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "scheduler.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("scheduler")

INTERVAL_HOURS = 6  # Ganti ke 1, 3, 12, dll sesuai kebutuhan
INTERVAL_SECONDS = INTERVAL_HOURS * 3600


def run_once():
    """Jalankan satu siklus trend hunting."""
    from dotenv import load_dotenv
    load_dotenv()

    from src.collector import collect_all
    from src.analyzer import analyze_trends
    from src.notifier import notify

    logger.info("=" * 50)
    logger.info(f"[SCHEDULER] Mulai siklus — {datetime.now().strftime('%Y-%m-%d %H:%M:%S WIB')}")
    logger.info("=" * 50)

    try:
        # Step 1: Kumpulkan data
        logger.info("STEP 1: Mengumpulkan data dari sumber...")
        raw_data = collect_all()
        total_signals = sum(len(v) for v in raw_data.values() if isinstance(v, list))
        logger.info(f"Total sinyal terkumpul: {total_signals}")

        # Step 2: Analisis dengan LLM
        logger.info("STEP 2: Menganalisis tren dengan LLM...")
        analysis = analyze_trends(raw_data)
        trends_found = len(analysis.get("trends", []))
        logger.info(f"Tren teridentifikasi: {trends_found}")

        # Step 3: Kirim notifikasi + simpan
        logger.info("STEP 3: Mengirim laporan...")
        result = notify(raw_data, analysis)

        logger.info("=" * 50)
        logger.info("Siklus selesai!")
        logger.info(f"  JSON: {result['json_saved']}")
        logger.info(f"  Telegram: {'✅ Terkirim' if result['telegram_sent'] else '⚠️  Skip (tidak dikonfigurasi)'}")
        logger.info("=" * 50)

        # Print summary
        print(f"\n=== RINGKASAN TREN — {datetime.now().strftime('%d %b %Y %H:%M')} ===")
        print(analysis.get("summary", ""))
        print()
        for t in analysis.get("trends", []):
            score = t.get("virality_score", 0)
            bar = "█" * (score // 10) + "░" * (10 - score // 10)
            print(f"  {t['rank']}. {t['topic']}")
            print(f"     [{bar}] {score}/100 — {t['hook']}")
        print()

        return True

    except Exception as e:
        logger.error(f"ERROR saat menjalankan agen: {e}", exc_info=True)
        return False


def main():
    logger.info(f"[SCHEDULER] Trend Hunter dimulai. Interval: setiap {INTERVAL_HOURS} jam.")
    logger.info(f"[SCHEDULER] Jadwal run: setiap {INTERVAL_HOURS} jam sekali dari sekarang.")

    while True:
        next_run = datetime.now() + timedelta(seconds=INTERVAL_SECONDS)

        # Jalankan sekarang
        success = run_once()

        # Hitung waktu tunggu
        wait_seconds = (next_run - datetime.now()).total_seconds()
        if wait_seconds < 0:
            wait_seconds = 0

        logger.info(
            f"[SCHEDULER] Run berikutnya: {next_run.strftime('%Y-%m-%d %H:%M:%S')} "
            f"(dalam {INTERVAL_HOURS} jam)"
        )

        # Tidur sampai jadwal berikutnya
        time.sleep(max(wait_seconds, 0))


if __name__ == "__main__":
    main()
