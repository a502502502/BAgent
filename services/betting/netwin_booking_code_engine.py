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
            "34": {
                "ticket_id": "34",
                "name": "Ticket #34: Quintina d'Elite Serale (Ref: DF07EA081B31840F2C06)",
                "code": "DF07EA081B31840F2C06",
                "odds": "4.80",
                "stake": "20.00 €",
                "potential_win": "96.07 €",
                "status": "🟢 ATTIVO / GIOCATO A SISTEMA",
                "events": [
                    "Ajax vs Sion (20:00) ➔ 1X + Over 1.5 Gol @ 1.22",
                    "Hapoel Tel Aviv vs Atalanta (20:00) ➔ X2 + Over 1.5 Gol @ 1.41",
                    "Chelsea vs Luton Town (20:30) ➔ 1 (1X2) @ 1.09",
                    "Partizan Belgrade vs Getafe (21:00) ➔ Over 4.5 Cartellini @ 1.83",
                    "Barcellona vs Athletic Bilbao (21:00) ➔ 1X + Over 2.5 Gol @ 1.40"
                ]
            },
            "30": {
                "ticket_id": "30",
                "name": "Ticket #30: Pomeridiana d'Elite (Ore 18:00 & 19:00)",
                "code": "NW-1800-T30",
                "odds": "3.75",
                "stake": "20.00 €",
                "potential_win": "75.00 €",
                "status": "🟢 ATTIVO / IN CORSO",
                "events": [
                    "Qarabag vs Twente (18:00) ➔ Over 4.5 Cartellini Totali @ 1.80",
                    "Kauno Zalgiris vs Besiktas (19:00) ➔ Besiktas Over 1.5 Gol @ 1.50",
                    "Brann vs PAOK (19:00) ➔ PAOK Over 3.5 Corner @ 1.39"
                ]
            },
            "32": {
                "ticket_id": "32",
                "name": "Ticket #32: Corner & Sanzioni Totali (Ore 20:30 - 21:00)",
                "code": "NW-4710-T32",
                "odds": "2.45",
                "stake": "20.00 €",
                "potential_win": "49.00 €",
                "status": "⏳ OPZIONE AGGIUNTIVA",
                "events": [
                    "Chelsea vs Luton Town ➔ Over 7.5 Corner @ 1.28",
                    "Brighton vs Tromsø ➔ Over 7.5 Corner @ 1.32",
                    "Partizan Belgrado vs Getafe ➔ Over 3.5 Cartellini @ 1.45"
                ]
            }
        }

if __name__ == "__main__":
    engine = NetwinBookingCodeEngine()
    slips = engine.get_today_booking_slips()
    print("📋 ACTIVE BETS LEDGER CON TICKET #34 REGISTRATO:")
    for tid, slip in slips.items():
        print(f"[{slip['status']}] {slip['name']} | Quota: {slip['odds']}x | Stake: {slip['stake']} | Potenziale: {slip['potential_win']}")
