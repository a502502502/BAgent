import sys
sys.path.insert(0, ".")
import scripts.live_ticket_daemon as daemon
p = daemon.run_sync_cycle()
print("=== SITUAZIONE AGGIORNATA TUTTE LE 7 GAMBE (Ore 15:43) ===")
for leg in p["legs"]:
    print(f"[{leg['id']}] {leg['match_name']}: {leg['score_home']}-{leg['score_away']} | Stato: {leg['status']} ({leg['minute_desc']}) | Leg: {leg['leg_status']} | Dettaglio: {leg['status_detail']}")
