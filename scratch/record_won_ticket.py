import sqlite3

conn = sqlite3.connect("storage/database/bagent.db")
c = conn.cursor()

# Aggiorna ticket_ledger
c.execute("""
    UPDATE ticket_ledger
    SET status = 'WON',
        profit_loss_eur = 166.86,
        notes = 'VINTA! En plein storico 7 su 7: Chernomorets 1-1, Arabia U23 2-0, Yavne 0-0, Zhejiang 4-1, Polissya 1-0, H. Tel Aviv 3-0, Highbury 0-0'
    WHERE ticket_id = 'TICKET_CASSAFORTE_23EUR_18SET';
""")

# Aggiorna bet_leg_ledger
c.execute("""
    UPDATE bet_leg_ledger
    SET result_status = 'WON'
    WHERE ticket_id = 'TICKET_CASSAFORTE_23EUR_18SET';
""")

conn.commit()

c.execute("SELECT ticket_id, total_odds, stake_eur, payout_eur, profit_loss_eur, status, notes FROM ticket_ledger WHERE ticket_id = 'TICKET_CASSAFORTE_23EUR_18SET';")
row = c.fetchone()
print("Ticket aggiornato:", row)

c.execute("SELECT id, match_name, selection, odds, result_status FROM bet_leg_ledger WHERE ticket_id = 'TICKET_CASSAFORTE_23EUR_18SET';")
legs = c.fetchall()
print(f"Legs aggiornate ({len(legs)}):")
for l in legs:
    print(" ", l)

conn.close()
