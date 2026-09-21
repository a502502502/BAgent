import sqlite3

local_conn = sqlite3.connect('storage/database/bagent.db')
remote_conn = sqlite3.connect('scratch/remote_bagent.db')
lc = local_conn.cursor()
rc = remote_conn.cursor()

tables = [t[0] for t in rc.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print('Remote tables:', tables)

local_tickets = set(r[0] for r in lc.execute('SELECT ticket_id FROM ticket_ledger').fetchall())
remote_tickets = set(r[0] for r in rc.execute('SELECT ticket_id FROM ticket_ledger').fetchall())
print('Tickets only in remote:', remote_tickets - local_tickets)
print('Tickets only in local:', local_tickets - remote_tickets)
