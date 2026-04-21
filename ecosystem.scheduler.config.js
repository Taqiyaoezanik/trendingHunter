/**
 * ecosystem.scheduler.config.js
 *
 * Gunakan file ini jika kamu ingin PM2 menjalankan scheduler.py
 * (proses terus berjalan, bukan cron_restart).
 *
 * Cara pakai:
 *   pm2 start ecosystem.scheduler.config.js
 *   pm2 save
 */

module.exports = {
  apps: [
    {
      name: "trend-hunter",
      script: "scheduler.py",
      interpreter: "python3",

      // Restart otomatis jika crash
      autorestart: true,
      watch: false,

      // Maksimal restart dalam 10 menit (anti infinite restart loop)
      max_restarts: 5,
      min_uptime: "10m",

      env: {
        NODE_ENV: "production",
        PYTHONUNBUFFERED: "1",
      },

      out_file: "./logs/pm2_scheduler_out.log",
      error_file: "./logs/pm2_scheduler_err.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss",
      merge_logs: true,
    },
  ],
};
