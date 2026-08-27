"""
Netwin Booking Code & Active Ticket Ledger Engine.
Tracks live active bets and bankroll utilization.
"""

import hashlib
import json
import datetime

class NetwinBookingCodeEngine:
    @staticmethod
    def generate_booking_code(ticket_id: str, selections: list, stake: float) -> str:
        raw_str = f"{ticket_id}_{len(selections)}_{stake}_{datetime.datetime.now().strftime('%Y%m%d')}"
        digest = hashlib.md5(raw_str.encode()).hexdigest()[:4].upper()
        return f"NW-{digest}-T{ticket_id}"

    @classmethod
    def get_today_booking_slips(cls):
        return {
            "30": {
                "ticket_id": "30",
                "name": "Ticket #30: Pomeridiana d'Elite (Ore 18:00 & 19:00)",
                "code": "NW-1800-T30",
                "odds": "3.65",
                "stake": "20.00 €",
                "potential_win": "73.00 €",
                "status": "🟢 ATTIVO / IN CORSO",
                "events": [
                    "Qarabag vs Twente (18:00) ➔ 1X (Doppia Chance Qarabag) @ 1.75",
                    "Kauno Zalgiris vs Besiktas (19:00) ➔ Besiktas Over 1.5 Gol @ 1.50",
                    "Brann vs PAOK (19:00) ➔ PAOK Over 3.5 Corner @ 1.39"
                ]
            },
            "31": {
                "ticket_id": "31",
                "name": "Ticket #31: Gol & Doppie Chance (Ore 20:00 - 21:00)",
                "code": "NW-8924-T31",
                "odds": "2.21",
                "stake": "20.00 €",
                "potential_win": "44.20 €",
                "status": "⏳ IN ATTESA DISTINTE (19:00)",
                "events": [
                    "Hapoel Tel Aviv vs Atalanta ➔ X2 + Over 1.5 @ 1.33",
                    "Barcellona vs Athletic Bilbao ➔ 1X + Over 1.5 @ 1.28",
                    "Chelsea vs Luton Town ➔ 1 + Over 1.5 @ 1.30"
                ]
            },
            "32": {
                "ticket_id": "32",
                "name": "Ticket #32: Corner & Sanzioni Totali (Ore 20:30 - 21:00)",
                "code": "NW-4710-T32",
                "odds": "2.45",
                "stake": "20.00 €",
                "potential_win": "49.00 €",
                "status": "⏳ IN ATTESA DISTINTE (19:30)",
                "events": [
                    "Chelsea vs Luton Town ➔ Over 7.5 Corner @ 1.28",
                    "Brighton vs Tromsø ➔ Over 7.5 Corner @ 1.32",
                    "Partizan Belgrado vs Getafe ➔ Over 3.5 Cartellini @ 1.45"
                ]
            },
            "33": {
                "ticket_id": "33",
                "name": "Ticket #33: Quaterna d'Elite Alta Quota (Ore 20:00 - 21:00)",
                "code": "NW-6351-T33",
                "odds": "7.79",
                "stake": "5.00 €",
                "potential_win": "38.95 €",
                "status": "⏳ IN ATTESA DISTINTE (19:00)",
                "events": [
                    "Hapoel vs Atalanta ➔ 2 + Over 1.5 @ 1.55",
                    "Barcellona vs Athletic ➔ 1 + Over 2.5 @ 1.72",
                    "Chelsea vs Luton Town ➔ 1 + Over 2.5 @ 1.58",
                    "Partizan vs Getafe ➔ Over 4.5 Cartellini @ 1.85"
                ]
            }
        }

if __name__ == "__main__":
    engine = NetwinBookingCodeEngine()
    slips = engine.get_today_booking_slips()
    print("📋 ACTIVE BETS LEDGER:")
    for tid, slip in slips.items():
        print(f"[{slip['status']}] {slip['name']} | Quota: {slip['odds']}x | Stake: {slip['stake']} | Potenziale: {slip['potential_win']}")
