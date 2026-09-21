import sqlite3
from datetime import datetime

local_db = 'storage/database/bagent.db'
remote_db = 'scratch/remote_bagent.db'

lconn = sqlite3.connect(local_db)
rconn = sqlite3.connect(remote_db)
lc = lconn.cursor()
rc = rconn.cursor()

# 1. Ensure tactical_lessons table exists in local_db
lc.execute("""
CREATE TABLE IF NOT EXISTS tactical_lessons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    match_name TEXT NOT NULL,
    market_name TEXT NOT NULL,
    odds REAL NOT NULL,
    outcome TEXT NOT NULL,
    failure_category TEXT NOT NULL,
    actual_stats TEXT NOT NULL,
    tactical_lesson TEXT NOT NULL,
    applied_rule TEXT
)
""")

# Copy tactical_lessons from remote
remote_lessons = rc.execute("SELECT timestamp, match_name, market_name, odds, outcome, failure_category, actual_stats, tactical_lesson, applied_rule FROM tactical_lessons").fetchall()
for lesson in remote_lessons:
    # check if exists
    exists = lc.execute("SELECT id FROM tactical_lessons WHERE match_name = ? AND market_name = ?", (lesson[1], lesson[2])).fetchone()
    if not exists:
        lc.execute("""
            INSERT INTO tactical_lessons (timestamp, match_name, market_name, odds, outcome, failure_category, actual_stats, tactical_lesson, applied_rule)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, lesson)
print("Copied tactical lessons.")

# 2. Insert TICKET_90_NOTTE_BLINDATA
t90 = rc.execute("SELECT ticket_id, date_created, description, num_legs, total_odds, stake_eur, payout_eur, profit_loss_eur, status, strategy_type, notes FROM ticket_ledger WHERE ticket_id = 'TICKET_90_NOTTE_BLINDATA'").fetchone()
if t90:
    exists = lc.execute("SELECT ticket_id FROM ticket_ledger WHERE ticket_id = 'TICKET_90_NOTTE_BLINDATA'").fetchone()
    if not exists:
        lc.execute("""
            INSERT INTO ticket_ledger (ticket_id, date_created, description, num_legs, total_odds, stake_eur, payout_eur, profit_loss_eur, status, strategy_type, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, t90)
        print("Inserted TICKET_90_NOTTE_BLINDATA")

# 3. Insert TICKET_91_RECUPERO_CORAZZATO with updated status = 'LOST', payout = 0.0, profit = -20.0
t91 = rc.execute("SELECT ticket_id, date_created, description, num_legs, total_odds, stake_eur, payout_eur, profit_loss_eur, status, strategy_type, notes FROM ticket_ledger WHERE ticket_id = 'TICKET_91_RECUPERO_CORAZZATO'").fetchone()
if t91:
    exists = lc.execute("SELECT ticket_id FROM ticket_ledger WHERE ticket_id = 'TICKET_91_RECUPERO_CORAZZATO'").fetchone()
    if not exists:
        lc.execute("""
            INSERT INTO ticket_ledger (ticket_id, date_created, description, num_legs, total_odds, stake_eur, payout_eur, profit_loss_eur, status, strategy_type, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (t91[0], t91[1], t91[2], t91[3], t91[4], t91[5], 0.0, -20.0, 'LOST', t91[9], 'Persa per corner Miami (5 corner totali su Over 7.5; Belgrano 2-1 void; Velez 3-2 won)'))
        print("Inserted TICKET_91_RECUPERO_CORAZZATO (as LOST)")

# 4. Copy and update legs for Ticket 90 and 91
for tid in ['TICKET_90_NOTTE_BLINDATA', 'TICKET_91_RECUPERO_CORAZZATO']:
    legs = rc.execute("SELECT ticket_id, match_name, tournament, market_category, selection, odds, estimated_prob, edge_pct, result_status, clv_pct FROM bet_leg_ledger WHERE ticket_id = ?", (tid,)).fetchall()
    for leg in legs:
        exists = lc.execute("SELECT id FROM bet_leg_ledger WHERE ticket_id = ? AND match_name = ?", (leg[0], leg[1])).fetchone()
        if not exists:
            # update result_status if needed
            r_status = leg[8]
            if leg[0] == 'TICKET_90_NOTTE_BLINDATA':
                if 'Porto' in leg[1]:
                    r_status = 'LOST' # 3-1
                elif 'Platense' in leg[1]:
                    r_status = 'WON' # 0-1
                elif 'Valencia' in leg[1]:
                    r_status = 'LOST' # 2-3
            elif leg[0] == 'TICKET_91_RECUPERO_CORAZZATO':
                if 'Belgrano' in leg[1]:
                    r_status = 'VOID' # 2-1 on Under 3.0 Asian
                elif 'Miami' in leg[1]:
                    r_status = 'LOST' # 5 corners on Over 7.5
                elif 'Velez' in leg[1]:
                    r_status = 'WON' # 3-2 on 1X
            
            lc.execute("""
                INSERT INTO bet_leg_ledger (ticket_id, match_name, tournament, market_category, selection, odds, estimated_prob, edge_pct, result_status, clv_pct)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (leg[0], leg[1], leg[2], leg[3], leg[4], leg[5], leg[6], leg[7], r_status, leg[9]))
            print(f"Inserted leg {leg[1]} for {leg[0]} with status {r_status}")

# 5. Add tactical lessons for Porto-Benfica and Inter Miami
lessons_to_add = [
    (
        datetime.now().isoformat(),
        "Porto vs Benfica",
        "Under 3.5 Gol Totali",
        1.33,
        "LOST",
        "TITAN_ATTACKING_CLASH",
        "4 gol (3-1 FT, Porto 3, Benfica 1)",
        "Scontro tra due giganti offensivi d'elite (>2.3 gol/gara). In Portogallo o grandi leghe, quando due dominanti si scontrano, la tensione genera errori ed espulsioni che aprono a goleada. Gli Under < 4.5 sono vietati.",
        "Regola #74 - Divieto Under tra Giganti Offensivi"
    ),
    (
        datetime.now().isoformat(),
        "Inter Miami vs San Diego FC",
        "Over 7.5 Corner Totali",
        1.24,
        "LOST",
        "MLS_CORNER_FLOW_TRAP",
        "5 corner totali (Miami 4, San Diego 1)",
        "L'Inter Miami gioca molto per vie centrali palla al piede senza ali pure che crossano sul fondo a ripetizione; match ad alto possesso e transizioni centrali producono pochi corner anche con tanti gol (2-2). Vietato forzare corner generici in MLS senza ali ad alto volume.",
        "Regola #72 / Regola #75 - MLS Corner Flow Trap"
    )
]

for lesson in lessons_to_add:
    exists = lc.execute("SELECT id FROM tactical_lessons WHERE match_name = ? AND failure_category = ?", (lesson[1], lesson[5])).fetchone()
    if not exists:
        lc.execute("""
            INSERT INTO tactical_lessons (timestamp, match_name, market_name, odds, outcome, failure_category, actual_stats, tactical_lesson, applied_rule)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, lesson)
        print(f"Added tactical lesson for {lesson[1]}")

# 6. Update bankroll_history
# Current balance is 204.18
b90_exists = lc.execute("SELECT id FROM bankroll_history WHERE ticket_id = 'TICKET_90_NOTTE_BLINDATA'").fetchone()
if not b90_exists:
    lc.execute("""
        INSERT INTO bankroll_history (timestamp, balance_eur, change_eur, reason, ticket_id)
        VALUES (?, ?, ?, ?, ?)
    """, ('2026-09-20T20:51:00', 184.18, -20.0, 'LOSS_TICKET_90_NOTTE_BLINDATA', 'TICKET_90_NOTTE_BLINDATA'))
    print("Recorded bankroll for Ticket 90: 184.18")

b91_exists = lc.execute("SELECT id FROM bankroll_history WHERE ticket_id = 'TICKET_91_RECUPERO_CORAZZATO'").fetchone()
if not b91_exists:
    lc.execute("""
        INSERT INTO bankroll_history (timestamp, balance_eur, change_eur, reason, ticket_id)
        VALUES (?, ?, ?, ?, ?)
    """, ('2026-09-21T00:07:00', 164.18, -20.0, 'LOSS_TICKET_91_RECUPERO_CORAZZATO', 'TICKET_91_RECUPERO_CORAZZATO'))
    print("Recorded bankroll for Ticket 91: 164.18")

lconn.commit()
print("Database merge completed successfully!")
