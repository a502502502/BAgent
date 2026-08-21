#!/bin/bash
# ==============================================================================
# BAgent Raspberry Pi 24/7 Auto-Deploy & Systemd Setup Script
# Esegue il tracker live Telegram 24 ore su 24 anche a PC spento
# ==============================================================================

set -e

echo "🚀 [1/4] Aggiornamento del repository BAgent da GitHub..."
git pull origin main

echo "📦 [2/4] Installazione dipendenze Python..."
python3 -m venv venv || true
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "⚙️ [3/4] Creazione del servizio Systemd (bagent-live.service)..."
SERVICE_FILE="/etc/systemd/system/bagent-live.service"
CURRENT_DIR=$(pwd)
USER_NAME=$(whoami)

sudo bash -c "cat <<EOF > $SERVICE_FILE
[Unit]
Description=BAgent 24/7 Telegram Live Tracker & Sports Engine
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER_NAME
WorkingDirectory=$CURRENT_DIR
ExecStart=$CURRENT_DIR/venv/bin/python $CURRENT_DIR/scripts/night_live_daemon.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF"

echo "🔄 [4/4] Abilitazione e avvio del servizio automatico al boot..."
sudo systemctl daemon-reload
sudo systemctl enable bagent-live.service
sudo systemctl restart bagent-live.service

echo ""
echo "=============================================================================="
echo "✅ BAgent è ora attivo 24/7 sul tuo Raspberry Pi!"
echo "   • Stato del servizio: sudo systemctl status bagent-live"
echo "   • Log in tempo reale: sudo journalctl -u bagent-live -f"
echo "   • Si riavvia automaticamente se il Raspberry si riaccende o va via la corrente!"
echo "=============================================================================="
