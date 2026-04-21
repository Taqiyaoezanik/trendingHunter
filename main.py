"""
Trend Hunter Agent — main runner.
Jalankan manual: python main.py
Atau via cron / PM2 (lihat README).
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

# Setup logging
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
today = datetime.now().strftime("%Y-%m-%d")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / f"agent_{today}.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("main")


def run():
    from src.collector import collect_all
    from src.analyzer import analyze_trends
    from src.notifier import notify

    logger.info("=" * 50)
    logger.info("Trend Hunter Agent mulai berjalan")
    logger.info("=" * 50)

    # Step 1: Kumpulkan data
    logger.info("STEP 1: Mengumpulkan data dari sumber...")
    raw_data = collect_all()
    total_signals = sum(
        len(v) for v in raw_data.values() if isinstance(v, list)
    )
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
    logger.info("Selesai!")
    logger.info(f"  JSON: {result['json_saved']}")
    logger.info(f"  Telegram: {'OK' if result['telegram_sent'] else 'Skip (tidak dikonfigurasi)'}")
    logger.info("=" * 50)

    # Print summary ke stdout
    print("\n=== RINGKASAN TREN HARI INI ===")
    print(analysis.get("summary", ""))
    print()
    for t in analysis.get("trends", []):
        score = t.get("virality_score", 0)
        bar = "█" * (score // 10) + "░" * (10 - score // 10)
        print(f"  {t['rank']}. {t['topic']}")
        print(f"     [{bar}] {score}/100  —  {t['hook']}")
        print()


if __name__ == "__main__":
    run()
