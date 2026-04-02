import os
import subprocess
from flask import Flask, request, jsonify
import auth
import config
import db_utils
import reports

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

@app.get('/user')
def get_user():
    # CWE-89 SQL Injection: Directly inserting user input into query string
    user_id = request.args.get('id')
    conn = db_utils.get_connection()
    cursor = conn.cursor()
    # Vulnerable line: f-string insertion
    query = cursor.execute("SELECT username, email, role FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return jsonify({"username": user[0], "email": user[1], "role": user[2]})
    return jsonify({"error": "User not found"}), 404

@app.get('/ping')
def ping():
    # CWE-78 Command Injection: Unsafe shell execution of user input
    ip = request.args.get('ip')
    try:
        # Vulnerable line: shell=True and f-string
        output = subprocess.check_output(f"ping -n 1 {ip}", shell=True)
        return jsonify({"output": output.decode()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.get('/profile')
def profile():
    user_id = request.args.get('id')
    profile_data = auth.get_profile(user_id)
    if profile_data:
        return jsonify({"profile": profile_data})
    return jsonify({"error": "Profile not found"}), 404

if __name__ == '__main__':
    import init_db
    init_db.init()
    app.run(port=5000)
