import sqlite3
from datetime import datetime

db_path = 'storage/database/bagent.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

ticket_id = 'TICKET_TENNIS_CINQUINA_21SET'
date_now = '2026-09-21 11:04:00'
description = 'Cinquina Tennis Sesto Senso (Lane + Dessi + Avdeeva + Rus + Hercog/Romero Over 18.5)'
stake = 10.00
total_odds = 5.93
payout = 59.29

# 1. Insert into ticket_ledger
c.execute("""
    INSERT OR REPLACE INTO ticket_ledger (
        ticket_id, date_created, description, num_legs, total_odds, 
        stake_eur, payout_eur, profit_loss_eur, status, strategy_type, notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    ticket_id, date_now, description, 5, total_odds, 
    stake, payout, 0.0, 'IN_PLAY', 'TENNIS_SIXTH_SENSE_VALUE',
    'Netwin ticket: Lane 1.08 + Dessi 1.20 + Avdeeva 1.52 + Rus 2.15 + Hercog Over 18.5 1.40'
))

# 2. Insert legs into bet_leg_ledger
legs = [
    (ticket_id, "Kelvin Walltin vs Lewie Lane", "ITF Sweden M25", "TENNIS_MONEYLINE", "2 (Lewie Lane)", 1.08, 0.92, 0.05, "IN_PLAY", None),
    (ticket_id, "Lorenzo Rocco vs Marco Dessi", "ITF Italy M25", "TENNIS_MONEYLINE", "2 (Marco Dessi)", 1.20, 0.83, 0.04, "IN_PLAY", None),
    (ticket_id, "Yuki Naito vs Julia Avdeeva", "WTA 125 Ankara", "TENNIS_MONEYLINE", "2 (Julia Avdeeva)", 1.52, 0.66, 0.06, "IN_PLAY", None),
    (ticket_id, "Mia Ristic vs Arantxa Rus", "WTA 125 Tolentino", "TENNIS_MONEYLINE", "2 (Arantxa Rus)", 2.15, 0.55, 0.18, "IN_PLAY", None),
    (ticket_id, "Polona Hercog vs Leyre Romero Gormaz", "WTA 125 Tolentino", "TENNIS_GAMES_OVER", "Over 18.5 Game Totali", 1.40, 0.74, 0.08, "IN_PLAY", None),
]

for leg in legs:
    c.execute("""
        INSERT INTO bet_leg_ledger (
            ticket_id, match_name, tournament, market_category, selection,
            odds, estimated_prob, edge_pct, result_status, clv_pct
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, leg)

# 3. Update bankroll_history
# Current balance was 164.18, minus 10.00 stake = 154.18
c.execute("""
    INSERT INTO bankroll_history (timestamp, balance_eur, change_eur, reason, ticket_id)
    VALUES (?, ?, ?, ?, ?)
""", (datetime.now().isoformat(), 154.18, -10.00, 'STAKE_TICKET_TENNIS_CINQUINA_21SET', ticket_id))

conn.commit()
print("Ticket logged successfully into bagent.db!")
