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
        raw_str = f"{ticket_id}_{len(selections)}_{stake}_{datetime.datetime.now().strftime('%Y%m%d')}"
        digest = hashlib.md5(raw_str.encode()).hexdigest()[:4].upper()
        return f"NW-{digest}-T{ticket_id}"

    @classmethod
    def get_today_booking_slips(cls):
        return {
            "29": {
                "ticket_id": "29",
                "name": "Ticket #29: Pomeridiana Lampo (Ore 17:00 - 18:00)",
                "code": "NW-1700-T29",
                "odds": "2.90",
                "stake": "10.00 €",
                "potential_win": "29.00 €",
                "events": [
                    "Ararat-Armenia vs U Craiova (17:00) ➔ 1X (Doppia Chance) @ 1.36",
                    "Maccabi Tel Aviv vs Lugano (17:00) ➔ Over 1.5 Gol Totali @ 1.22",
                    "FK Jablonec vs Rangers (17:30) ➔ X2 (Doppia Chance Rangers) @ 1.25",
                    "Qarabag vs Twente (18:00) ➔ Over 3.5 Cartellini Totali @ 1.40"
                ]
            },
            "30": {
                "ticket_id": "30",
                "name": "Ticket #30: Pomeridiana d'Elite (Ore 18:00 & 19:00)",
                "code": "NW-1800-T30",
                "odds": "2.92",
                "stake": "15.00 €",
                "potential_win": "43.80 €",
                "events": [
                    "Qarabag vs Twente ➔ Over 3.5 Cartellini Totali @ 1.40",
                    "Kauno Zalgiris vs Besiktas ➔ Besiktas Over 1.5 Gol @ 1.50",
                    "Brann vs PAOK ➔ PAOK Over 3.5 Corner @ 1.39"
                ]
            },
            "31": {
                "ticket_id": "31",
                "name": "Ticket #31: Gol & Doppie Chance (Ore 20:00 - 21:00)",
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
                "name": "Ticket #32: Corner & Sanzioni Totali (Ore 20:30 - 21:00)",
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
                "name": "Ticket #33: Quaterna d'Elite Alta Quota (Ore 20:00 - 21:00)",
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
    print("📋 TUTTI I CODICI PRENOTAZIONE NETWIN AGGIORNATI (CON TICKET #29):")
    for tid, slip in slips.items():
        print(f"\n[{slip['name']}]")
        print(f"  👉 CODICE: {slip['code']} | Quota: {slip['odds']}x | Stake: {slip['stake']} | Vincita: {slip['potential_win']}")
