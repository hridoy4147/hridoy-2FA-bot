import sqlite3

def get_db():
    conn = sqlite3.connect('hridoy_2fa.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS links 
                        (token TEXT PRIMARY KEY, user_id INTEGER, 
                         account TEXT, secret TEXT, expiry REAL)''')
        conn.commit()
