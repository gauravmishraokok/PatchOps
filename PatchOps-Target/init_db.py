import sqlite3
import os
# Removed cross-imports

def init(app=None):
    if os.path.exists("users.db"):
        os.remove("users.db")
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, email TEXT, role TEXT, password TEXT)")
    cursor.execute("INSERT INTO users VALUES (1, 'alice', 'alice@example.com', 'admin', 'password123')")
    cursor.execute("INSERT INTO users VALUES (2, 'bob', 'bob@example.com', 'user', 'password456')")
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init()
