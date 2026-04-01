from flask import Flask, request, jsonify, redirect
import sqlite3
import subprocess
import pickle
import os
import logging

app = Flask(__name__)

# CWE-798: Hardcoded Secrets
DATABASE_PASSWORD = "admin123"
API_KEY = "sk-1234567890abcdef"
SECRET_TOKEN = "supersecrettoken2024"

# Database connection
DB_PATH = "users.db"

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

# CWE-89: SQL Injection
@app.route('/user')
def get_user():
    user_id = request.args.get('id')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = f"SELECT username, email, role FROM users WHERE id = {user_id}"
    cursor.execute(query)
    users = cursor.fetchall()
    conn.close()
    return jsonify({"users": users})

# CWE-78: Command Injection
@app.route('/ping')
def ping_host():
    target_ip = request.args.get('ip')
    command = f"ping -c 1 {target_ip}"
    output = subprocess.check_output(command, shell=True, text=True)
    return jsonify({"result": output})

# CWE-502: Unsafe Deserialization
@app.route('/deserialize')
def deserialize_data():
    data = request.args.get('data')
    obj = pickle.loads(bytes.fromhex(data))
    return jsonify({"object": str(obj)})

# CWE-639: Insecure Direct Object Reference (IDOR)
@app.route('/profile/<user_id>')
def get_profile(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT username, email, ssn FROM users WHERE id = ?", (user_id,))
    profile = cursor.fetchone()
    conn.close()
    return jsonify({"profile": profile})

# CWE-601: Open Redirect
@app.route('/redirect')
def open_redirect():
    redirect_url = request.args.get('url')
    return redirect(redirect_url)

# CWE-200: Sensitive Data Exposure
@app.route('/logs')
def get_logs():
    logging.basicConfig(filename='app.log', level=logging.DEBUG)
    logger = logging.getLogger()
    logger.debug(f"User login attempt with IP: {request.remote_addr}")
    logger.debug(f"Database password: {DATABASE_PASSWORD}")
    logger.debug(f"API key: {API_KEY}")
    with open('app.log', 'r') as f:
        logs = f.read()
    return jsonify({"logs": logs})

# CWE-287: Broken Authentication
@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    # Plaintext password comparison, no salt/hash
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    if user:
        return jsonify({"token": SECRET_TOKEN})
    return jsonify({"error": "Invalid credentials"}), 401

# CWE-862: Missing Authorization
@app.route('/admin/delete_user/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    # No authorization check!
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "deleted"})

# CWE-434: Unrestricted File Upload
@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    filename = file.filename
    file.save(os.path.join('/tmp', filename))
    return jsonify({"filename": filename})

# CWE-22: Path Traversal
@app.route('/download')
def download_file():
    filename = request.args.get('file')
    filepath = os.path.join('/var/www/files', filename)
    with open(filepath, 'r') as f:
        content = f.read()
    return jsonify({"content": content})

if __name__ == '__main__':
    app.run(port=5000, debug=True)
