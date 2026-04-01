import db_utils
import config

def login(username, password):
    # Mock login
    return {"status": "success", "token": "mock-token-123"}

def get_profile(user_id):
    # CWE-639 IDOR: no ownership check, directly queries DB with user-supplied ID
    conn = db_utils.get_connection()
    cursor = conn.cursor()
    # Vulnerable line: direct execution with user_id
    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
    profile = cursor.fetchone()
    conn.close()
    return profile

def check_token(token):
    return token == "mock-token-123"
