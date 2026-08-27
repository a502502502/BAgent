@echo off
title BAgent Telegram Live Schedine Notifier
color 0A
echo ======================================================================
echo          ROBOT BAGENT TELEGRAM LIVE NOTIFIER - SERIE LIVE
echo ======================================================================
echo  Questo batch controlla in tempo reale le tue schedine giocate
echo  e ti invia notifiche istantanee su Telegram per:
echo    * Gol e avanzamento eventi
echo    * Corner e Cartellini raggiunti
echo    * Alert di Copertura Matematica (Dutching Profit-Lock) al 75'-80'
echo    * Notifica finale di CASSA e VINCITA!
echo ======================================================================
echo.
cd /d "%~dp0"
python scripts/telegram_live_betslip_notifier.py
echo.
echo ======================================================================
echo  Avvio loop continuo in background...
echo  Premi CTRL+C per fermare il notifier in qualsiasi momento.
echo ======================================================================
python scripts/live_lineup_sentinel_5min.py
pause
