// PM2 config — jalankan agent setiap pagi jam 07:00 WIB
// Setup: pm2 start ecosystem.config.js
// Monitor: pm2 logs trend-hunter

module.exports = {
  apps: [
    {
      name: "trend-hunter",
      script: "main.py",
      interpreter: "python3",
      cron_restart: "0 0 * * *",   // Jam 00:00 UTC = 07:00 WIB
      autorestart: false,
      watch: false,
      env: {
        PYTHONUNBUFFERED: "1",
      },
    },
  ],
};
