import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding='utf-8')
from services.betting.netwin_automator import NetwinAutomator

def test_full_pipeline():
    automator = NetwinAutomator(headless=True)
    # Test con match disponibile su Netwin (es. Criciuma)
    test_selections = [
        {
            "home": "Criciuma",
            "match": "Criciuma vs Operario",
            "market": "1X2",
            "pick": "1",
            "netwin_odds": 1.98
        }
    ]
    print("Avvio test inserimento e generazione codice...")
    res = automator.build_ticket_and_book(test_selections, stake=25.0)
    print("Risultato test:", res)

if __name__ == "__main__":
    test_full_pipeline()
