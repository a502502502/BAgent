"""
Netwin Booking Code & Active Ticket Ledger Engine.
Updated with Monday 14 September 2026 tickets:
- Ticket #86: Sprint Mattina & Pranzo (12:00 - 14:30) @ 3.07x
- Ticket #83: Quaterna d'Oro Pomeridiana (14:30 - 18:00) @ 4.06x
- Ticket #84: Raddoppio Blindato (14:30 - 17:00) @ 2.38x
- Ticket #87: Serale d'Elite (18:30 - 22:30) @ 4.85x
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
            "88": {
                "ticket_id": "88",
                "name": "Ticket #88: Super Early Bird (Start Ore 11:30)",
                "code": "NW-1130-T88",
                "odds": "3.74",
                "stake": "15.00 €",
                "potential_win": "56.10 €",
                "status": "⏳ PRONTA AL PIAZZAMENTO (START 11:30)",
                "events": [
                    "East Bengal vs Mohammedan (11:30) ➔ 1X (Doppia Chance) @ 1.22",
                    "FC Osaka vs Ehime (12:00) ➔ 1X (Doppia Chance) @ 1.25",
                    "Geylang vs Tanjong Pagar (13:30) ➔ Over 2.5 Gol @ 1.35",
                    "Shan United vs Ezra (13:30) ➔ 1 (1X2) @ 1.30",
                    "Dynamo Kyiv vs Epitsentr (14:30) ➔ 1 + Over 1.5 Gol @ 1.40"
                ]
            },
            "86": {
                "ticket_id": "86",
                "name": "Ticket #86: Sprint Mattina & Pranzo (Start Ore 12:00)",
                "code": "NW-1200-T86",
                "odds": "3.07",
                "stake": "15.00 €",
                "potential_win": "46.05 €",
                "status": "⏳ PRONTA AL PIAZZAMENTO (START 12:00)",
                "events": [
                    "FC Osaka vs Ehime (12:00) ➔ 1X (Doppia Chance) @ 1.25",
                    "Geylang vs Tanjong Pagar (13:30) ➔ Over 2.5 Gol @ 1.35",
                    "Shan United vs Ezra (13:30) ➔ 1 (1X2) @ 1.30",
                    "Dynamo Kyiv vs Epitsentr (14:30) ➔ 1 + Over 1.5 Gol @ 1.40"
                ]
            },
            "83": {
                "ticket_id": "83",
                "name": "Ticket #83: Quaterna d'Oro Pomeridiana (Start Ore 14:30)",
                "code": "NW-1430-T83",
                "odds": "4.06",
                "stake": "15.00 €",
                "potential_win": "60.90 €",
                "status": "⏳ PRONTA AL PIAZZAMENTO (START 14:30)",
                "events": [
                    "Dynamo Kyiv vs Epitsentr (14:30) ➔ 1 + Over 1.5 Gol @ 1.40",
                    "Shakhtar Donetsk vs Ch. Odesa (17:00) ➔ 1 + Over 1.5 Gol @ 1.42",
                    "U. Cluj vs Otelul Galati (17:00) ➔ 1X + Under 3.5 Gol @ 1.48",
                    "Al Shamal vs Al Ittihad (18:00) ➔ X2 + Over 1.5 Gol @ 1.38"
                ]
            },
            "84": {
                "ticket_id": "84",
                "name": "Ticket #84: Raddoppio Blindato d'Acciaio (Start Ore 14:30)",
                "code": "NW-1430-T84",
                "odds": "2.38",
                "stake": "20.00 €",
                "potential_win": "47.60 €",
                "status": "⏳ PRONTA AL PIAZZAMENTO (START 14:30)",
                "events": [
                    "Dynamo Kyiv vs Epitsentr (14:30) ➔ 1 + Over 1.5 Gol @ 1.40",
                    "Shakhtar Donetsk vs Ch. Odesa (17:00) ➔ 1 + Over 1.5 Gol @ 1.42",
                    "U. Cluj vs Otelul Galati (17:00) ➔ 1X (Doppia Chance) @ 1.20"
                ]
            },
            "87": {
                "ticket_id": "87",
                "name": "Ticket #87: Quintina Serale d'Elite (Start Ore 18:30)",
                "code": "NW-1830-T87",
                "odds": "4.85",
                "stake": "15.00 €",
                "potential_win": "72.75 €",
                "status": "⏳ PRONTA AL PIAZZAMENTO (START 18:30)",
                "events": [
                    "Como vs Parma (18:30) ➔ 1X + Over 1.5 Gol @ 1.45",
                    "Bodo/Glimt vs Sandefjord (19:00) ➔ 1 + Over 1.5 Gol @ 1.45",
                    "Gaziantep vs Fenerbahce (19:00) ➔ X2 + Over 1.5 Gol @ 1.44",
                    "Inter vs Udinese (20:45) ➔ 1X + MultiGol 1-4 @ 1.44",
                    "Villarreal vs Betis (21:00) ➔ 1X + Over 1.5 Gol @ 1.48"
                ]
            }
        }

if __name__ == "__main__":
    engine = NetwinBookingCodeEngine()
    slips = engine.get_today_booking_slips()
    print("📋 ACTIVE BETS LEDGER CON LE NUOVE SCHEDINE DEL 14 SETTEMBRE:")
    for tid, slip in slips.items():
        print(f"[{slip['status']}] {slip['name']} | Quota: {slip['odds']}x | Stake: {slip['stake']} | Potenziale: {slip['potential_win']}")
