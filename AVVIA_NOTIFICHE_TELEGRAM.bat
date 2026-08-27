@echo off
title BAgent Telegram Real-Time In-Play Live Notifier
color 0A
echo ======================================================================
echo          ROBOT BAGENT TELEGRAM LIVE NOTIFIER (LOOP 60 SECONDI)
echo ======================================================================
echo  Fonti Dati: UEFA.com MatchCenter + Sofascore Feed + Netwin Live
echo.
echo  Notifiche inviate automaticamente sul tuo smartphone per:
echo    [1] Ogni Gol segnato (Besiktas, Atalanta, Barcellona, Chelsea)
echo    [2] Corner del PAOK (1/4, 2/4, 3/4, 4/4)
echo    [3] Alert di Copertura Matematica Dutching al 75'-80'
echo    [4] Notifica di CASSA VINTA!
echo ======================================================================
echo.
cd /d "%~dp0"
python scripts/telegram_live_inplay_poller.py
pause
