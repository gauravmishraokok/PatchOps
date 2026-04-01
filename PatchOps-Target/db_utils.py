import sqlite3
import config

def get_connection():
    # In a real app, DB_PASSWORD would be used here
    return sqlite3.connect(DB_PATH)

def safe_query(query, params=()):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    result = cursor.fetchall()
    conn.close()
    return result

def query_user(user_id):
    return safe_query("SELECT * FROM users WHERE id = ?", (user_id,))

def query_report(report_id):
    return safe_query("SELECT * FROM reports WHERE id = ?", (report_id,))
