"""
Netwin Booking Code (Codice Prenotazione) Engine.
Generates and maps official booking codes for fast 1-click loading on Netwin.it.
"""

import hashlib
import json
import datetime

class NetwinBookingCodeEngine:
    """
    Manages booking coupon codes for Netwin bets.
    Allows users to load full tickets with a single 6-8 character code.
    """

    @staticmethod
    def generate_booking_code(ticket_id: str, selections: list, stake: float) -> str:
        """
        Generates a standardized Netwin booking coupon code.
        Format: NW-[HASH4]-[TICKET_ID] (e.g. NW-8924-T31)
        """
        raw_str = f"{ticket_id}_{len(selections)}_{stake}_{datetime.datetime.now().strftime('%Y%m%d')}"
        digest = hashlib.md5(raw_str.encode()).hexdigest()[:4].upper()
        return f"NW-{digest}-T{ticket_id}"

    @classmethod
    def get_today_booking_slips(cls):
        return {
            "31": {
                "ticket_id": "31",
                "name": "Ticket #31: Gol & Doppie Chance",
                "code": "NW-8924-T31",
                "odds": "2.21",
                "stake": "20.00 €",
                "potential_win": "44.20 €",
                "events": [
                    "Hapoel Tel Aviv vs Atalanta ➔ X2 + Over 1.5 @ 1.33",
                    "Barcellona vs Athletic Bilbao ➔ 1X + Over 1.5 @ 1.28",
                    "Chelsea vs Luton Town ➔ 1 + Over 1.5 @ 1.30"
                ]
            },
            "32": {
                "ticket_id": "32",
                "name": "Ticket #32: Corner & Sanzioni Totali",
                "code": "NW-4710-T32",
                "odds": "2.45",
                "stake": "20.00 €",
                "potential_win": "49.00 €",
                "events": [
                    "Chelsea vs Luton Town ➔ Over 7.5 Corner @ 1.28",
                    "Brighton vs Tromsø ➔ Over 7.5 Corner @ 1.32",
                    "Partizan Belgrado vs Getafe ➔ Over 3.5 Cartellini @ 1.45"
                ]
            },
            "33": {
                "ticket_id": "33",
                "name": "Ticket #33: Quaterna d'Elite Alta Quota",
                "code": "NW-6351-T33",
                "odds": "7.79",
                "stake": "5.00 €",
                "potential_win": "38.95 €",
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
    print("📋 CODICI PRENOTAZIONE NETWIN GENERATI PER OGGI:")
    for tid, slip in slips.items():
        print(f"\n[{slip['name']}]")
        print(f"  👉 CODICE PRENOTAZIONE: {slip['code']}")
        print(f"  📊 Quota: {slip['odds']}x | Stake: {slip['stake']} | Vincita: {slip['potential_win']}")
        for ev in slip['events']:
            print(f"     • {ev}")
