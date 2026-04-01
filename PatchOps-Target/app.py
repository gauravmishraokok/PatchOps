from flask import Flask, request, jsonify, redirect, abort
import sqlite3
import subprocess
import json
import os
import logging
import ipaddress

app = Flask(__name__)

# ✅ Load secrets from environment (NO hardcoding)
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "")
API_KEY = os.getenv("API_KEY", "")
SECRET_TOKEN = os.getenv("SECRET_TOKEN", "")

DB_PATH = "users.db"

logging.basicConfig(filename='app.log', level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route('/health')
def health():
    return jsonify({"status": "ok"})


# ✅ FIXED: SQL Injection (use parameterized queries)
@app.route('/user')
def get_user():
    user_id = request.args.get('id')

    if not user_id or not user_id.isdigit():
        return jsonify({"error": "Invalid user id"}), 400

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT username, email, role FROM users WHERE id = ?",
        (user_id,)
    )

    users = cursor.fetchall()
    conn.close()

    return jsonify({"users": users})


# ✅ FIXED: Command Injection
@app.route('/ping')
def ping_host():
    target_ip = request.args.get('ip')

    try:
        # Validate IP strictly
        ipaddress.ip_address(target_ip)
    except:
        return jsonify({"error": "Invalid IP"}), 400

    try:
        output = subprocess.check_output(
            ["ping", "-c", "1", target_ip],
            text=True
        )
        return jsonify({"result": output})
    except subprocess.CalledProcessError:
        return jsonify({"error": "Ping failed"}), 500


# ✅ FIXED: Unsafe Deserialization (use JSON instead of pickle)
@app.route('/deserialize')
def deserialize_data():
    data = request.args.get('data')

    try:
        obj = json.loads(data)
    except:
        return jsonify({"error": "Invalid JSON"}), 400

    return jsonify({"object": obj})


# ✅ FIXED: IDOR (basic authorization check placeholder)
@app.route('/profile/<user_id>')
def get_profile(user_id):
    auth_user = request.headers.get("X-USER-ID")

    if auth_user != user_id:
        return jsonify({"error": "Unauthorized"}), 403

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT username, email FROM users WHERE id = ?",
        (user_id,)
    )

    profile = cursor.fetchone()
    conn.close()

    return jsonify({"profile": profile})


# ✅ FIXED: Open Redirect
@app.route('/redirect')
def open_redirect():
    redirect_url = request.args.get('url')

    allowed_domains = ["example.com", "yourapp.com"]

    if not redirect_url or not any(domain in redirect_url for domain in allowed_domains):
        return jsonify({"error": "Invalid redirect URL"}), 400

    return redirect(redirect_url)


# ✅ FIXED: Sensitive Data Exposure
@app.route('/logs')
def get_logs():
    # Do NOT log secrets
    logger.info(f"User accessed logs from IP: {request.remote_addr}")

    if not os.path.exists('app.log'):
        return jsonify({"logs": ""})

    with open('app.log', 'r') as f:
        logs = f.read()

    return jsonify({"logs": logs})


if __name__ == '__main__':
    app.run(port=5000, debug=False)
