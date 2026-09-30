import time
from services.notifications.telegram_service import TelegramService
from services.live.siege_engine import SiegeEngine
from utils.logger import logger

def main():
    logger.info("🤖 Avvio del Telegram Poller & Live Monitor...")
    bot = TelegramService()
    engine = SiegeEngine()
    
    # Simulazione di un ciclo di monitoraggio live
    while True:
        # Qui andrebbe la logica reale di fetching dei match live
        # Per demo, simuliamo un trigger di assedio
        logger.info("🔍 Scansione match live in corso...")
        
        # Esempio: se ci fosse un match in assedio
        # opportunities = engine.check_siege_trigger(...)
        # if opportunities:
        #     bot.send_siege_alert("Real Madrid vs Underdog", opportunities)
            
        time.sleep(60) # Polling ogni 60 secondi come da Regola

if __name__ == "__main__":
    main()
