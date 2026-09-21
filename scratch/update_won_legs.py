import sqlite3

conn = sqlite3.connect('storage/database/bagent.db')
c = conn.cursor()

ticket_id = 'TICKET_TENNIS_CINQUINA_21SET'

# Update legs
c.execute("UPDATE bet_leg_ledger SET result_status = 'WON' WHERE ticket_id = ? AND match_name LIKE '%Walltin%'", (ticket_id,))
c.execute("UPDATE bet_leg_ledger SET result_status = 'WON' WHERE ticket_id = ? AND match_name LIKE '%Rocco%'", (ticket_id,))
c.execute("UPDATE bet_leg_ledger SET result_status = 'VOID', odds = 1.00 WHERE ticket_id = ? AND match_name LIKE '%Avdeeva%'", (ticket_id,))

# Update ticket total odds: 1.08 * 1.20 * 1.00 * 2.15 * 1.40 = 3.90
# Payout: 10.00 * 3.90 = 39.00
c.execute("""
    UPDATE ticket_ledger 
    SET total_odds = 3.90, payout_eur = 39.00, notes = 'Prime 2 VINTE (Lane + Dessi), Avdeeva VOID. Restano Rus e Hercog/Romero Over 18.5'
    WHERE ticket_id = ?
""", (ticket_id,))

conn.commit()
print("Updated legs and ticket in database!")
