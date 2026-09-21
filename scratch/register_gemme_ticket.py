import sqlite3, json, datetime

ticket_id = 'TICKET_GEMME_POMERIGGIO_21SET'
now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
stake = 10.0
odds = 4.07
payout = 40.70

conn = sqlite3.connect('storage/database/bagent.db')
cur = conn.cursor()

# 1. Insert into ticket_ledger
cur.execute('''
    INSERT OR REPLACE INTO ticket_ledger 
    (ticket_id, date_created, description, num_legs, total_odds, stake_eur, payout_eur, profit_loss_eur, status, strategy_type, notes)
    VALUES (?, ?, ?, 3, ?, ?, ?, 0.0, 'IN_PLAY', 'NICHE_GEMS_EXP', 'Tripla Gemme Nascoste 16:00 CEST (Backa Topola, Paok B, Ofk Vrsac)')
''', (ticket_id, now_iso, 'Tripla Gemme Nascoste 16:00', odds, stake, payout))

# 2. Insert legs into bet_leg_ledger
legs = [
    ('8376', 'Backa Topola vs Gfk Dubocica', 'Serbia Prva Liga', 'Combo Protetta', '1X + Over 1.5', 1.55, 0.752, 16.5),
    ('8374', 'Paok B vs Nestos Chrysoupoli', 'Grecia Super League 2', 'Combo Protetta', '1X + MultiGol 1-4', 1.62, 0.740, 19.9),
    ('8892', 'Ofk Vrsac vs Fk Bor 1919', 'Serbia Prva Liga', 'Combo Protetta', '1X + MultiGol 1-4', 1.62, 0.738, 19.6)
]

cur.execute('DELETE FROM bet_leg_ledger WHERE ticket_id = ?', (ticket_id,))
for leg in legs:
    cur.execute('''
        INSERT INTO bet_leg_ledger 
        (ticket_id, match_name, tournament, market_category, selection, odds, estimated_prob, edge_pct, result_status, clv_pct)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', 0.0)
    ''', (ticket_id, leg[1], leg[2], leg[3], leg[4], leg[5], leg[6], leg[7]))

conn.commit()
conn.close()

# Update data/active_user_tickets.json
active_file = 'data/active_user_tickets.json'
try:
    with open(active_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
except Exception:
    data = {}

ticket_entry = {
    'ticket_id': ticket_id,
    'date_created': now_iso,
    'stake_eur': stake,
    'total_odds': odds,
    'potential_payout_eur': payout,
    'status': 'IN_PLAY',
    'strategy': 'NICHE_GEMS_EXP',
    'legs': [
        {
            'id': l[0], 'match': l[1], 'tournament': l[2],
            'market': l[4], 'odds': l[5], 'prob_real': l[6], 'edge_pct': l[7],
            'status': 'PENDING', 'kickoff': '16:00 CEST'
        }
        for l in legs
    ]
}

if isinstance(data, list):
    data = [t for t in data if t.get('ticket_id') != ticket_id]
    data.append(ticket_entry)
else:
    data = [ticket_entry]

with open(active_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print('Ticket', ticket_id, 'registrato con successo in bagent.db e active_user_tickets.json!')
