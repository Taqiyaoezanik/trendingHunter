module.exports = {
  apps: [
    {
      name: "trend-hunter",
      script: "main.py",
      interpreter: "python3",

      // Jalankan setiap 6 jam: jam 00:00, 06:00, 12:00, 18:00 WIB
      // (WIB = UTC+7, jadi UTC: 17:00, 23:00, 05:00, 11:00)
      cron_restart: "0 17,23,5,11 * * *",

      // Setelah cron selesai, proses berhenti (bukan daemon terus-menerus)
      autorestart: false,

      // Jangan restart kalau crash di luar jadwal
      watch: false,

      // Environment variables (backup jika .env tidak ter-load)
      env: {
        NODE_ENV: "production",
        PYTHONUNBUFFERED: "1",
      },

      // Log output
      out_file: "./logs/pm2_out.log",
      error_file: "./logs/pm2_err.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss",

      // Merge semua log jadi satu file per app
      merge_logs: true,
    },
  ],
};
