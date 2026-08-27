#!/bin/bash
# scripts/deploy_pi.sh — Script di installazione & attivazione del demone 24/7 su Raspberry Pi

set -e

echo "=== 🍓 Deploy BAgent 24/7 Portal & Bot su Raspberry Pi ==="

# 1. Pull ultimi aggiornamenti
git pull origin main

# 2. Attiva virtualenv e installa dipendenze
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi
pip install -r requirements.txt

# 3. Installa servizio systemd
sudo cp systemd/bagent-portal.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable bagent-portal.service
sudo systemctl restart bagent-portal.service

echo "✅ Servizio bagent-portal.service ATTIVO e in esecuzione 24/7!"
echo "🌐 Portale Web: http://100.120.216.25:8080"
echo "🤖 Telegram Bot: @A502502_bot"
sudo systemctl status bagent-portal.service --no-pager
