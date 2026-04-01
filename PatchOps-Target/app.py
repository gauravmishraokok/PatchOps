from flask import Flask, request, jsonify, redirect
import sqlite3
import subprocess
import pickle
import os

app = Flask(__name__)

# 🔥 Hardcoded secrets (easy detection)
DATABASE_PASSWORD = "admin123"
API_KEY = "sk-test-abcdef"
SECRET_TOKEN = "super-secret-token"

DB_PATH = "users.db"


@app.route('/health')
def health():
    return jsonify({"status": "ok"})


# 🔥 SQL Injection (fully exploitable)
@app.route('/user')
def get_user():
    user_id = request.args.get('id')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = f"SELECT id, username, email, role FROM users WHERE id = {user_id}"
    cursor.execute(query)

    data = cursor.fetchall()
    conn.close()

    return jsonify({"result": data})


# 🔥 Command Injection (very obvious exploit)
@app.route('/exec')
def exec_cmd():
    cmd = request.args.get('cmd')

    output = subprocess.getoutput(cmd)  # no filtering at all

    return jsonify({"output": output})


# 🔥 Unsafe Deserialization (RCE possible)
@app.route('/deserialize', methods=["POST"])
def deserialize():
    raw = request.data

    obj = pickle.loads(raw)  # direct RCE vector

    return jsonify({"data": str(obj)})


# 🔥 IDOR (no auth at all + sensitive fields)
@app.route('/profile')
def profile():
    user_id = request.args.get('id')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(f"SELECT username, email, password, ssn FROM users WHERE id = {user_id}")
    user = cursor.fetchone()

    conn.close()

    return jsonify({"profile": user})


# 🔥 Open Redirect
@app.route('/redirect')
def open_redirect():
    url = request.args.get('url')
    return redirect(url)


# 🔥 Arbitrary File Read (VERY GOOD for agents)
@app.route('/read')
def read_file():
    path = request.args.get('path')

    with open(path, 'r') as f:
        content = f.read()

    return jsonify({"content": content})


# 🔥 Debug endpoint (info leak)
@app.route('/debug')
def debug():
    return jsonify({
        "env": dict(os.environ),
        "cwd": os.getcwd()
    })


if __name__ == '__main__':
    app.run(port=5000, debug=True)
