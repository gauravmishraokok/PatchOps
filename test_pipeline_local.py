import os
import sys
import json
import time
import subprocess
import tempfile
import signal

# Ensure repo root is in path
sys.path.insert(0, os.path.abspath("."))

# =========================
# STEP 1: LOAD ENV
# =========================
print("\n=== STEP 0: LOAD ENV ===")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("❌ ERROR: GROQ_API_KEY not set in environment")
    sys.exit(1)

# =========================
# STEP 2: DEFINE VULNERABLE APP
# =========================
print("\n=== STEP 1: LOAD VULNERABLE APP SOURCE ===")

VULNERABLE_APP_SOURCE = """
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.execute("CREATE TABLE users (username TEXT, email TEXT, role TEXT)")
    conn.execute("INSERT INTO users VALUES ('alice', 'alice@example.com', 'user')")
    conn.execute("INSERT INTO users VALUES ('bob', 'bob@example.com', 'admin')")
    conn.commit()
    return conn

db = get_db()

@app.route('/user')
def get_user():
    user_id = request.args.get('id', '')
    query = f"SELECT username, email, role FROM users WHERE rowid = {user_id}"
    cursor = db.execute(query)
    results = cursor.fetchall()
    return jsonify({"users": results})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
"""

# =========================
# STEP 3: RUN CODE ANALYZER
# =========================
print("\n=== STEP 2: CODE ANALYZER ===")

try:
    from lambdas.code_analyzer.handler import handler as analyzer_handler

    analyzer_event = {
        "source_code": VULNERABLE_APP_SOURCE,
        "cve_description": "SQL Injection via unsanitized GET parameter id"
    }

    analyzer_result = analyzer_handler(analyzer_event)

    print(json.dumps(analyzer_result, indent=2))

    if "error" in analyzer_result:
        print("❌ Analyzer failed")
        sys.exit(1)

except Exception as e:
    print(f"❌ Analyzer exception: {e}")
    sys.exit(1)

# =========================
# STEP 4: RUN EXPLOIT CRAFTER
# =========================
print("\n=== STEP 3: EXPLOIT CRAFTER ===")

try:
    from lambdas.exploit_crafter.handler import handler as exploit_handler

    exploit_event = {
        "source_code": VULNERABLE_APP_SOURCE,
        "vulnerable_lines": analyzer_result.get("vulnerable_lines", []),
        "vulnerability_type": analyzer_result.get("vulnerability_type"),
        "attack_vector": analyzer_result.get("attack_vector")
    }

    exploit_result = exploit_handler(exploit_event)

    exploit_code = exploit_result.get("exploit_code", "")

    print("\n--- GENERATED EXPLOIT ---\n")
    print(exploit_code)

    if "error" in exploit_result:
        print("❌ Exploit crafter returned error")

except Exception as e:
    print(f"❌ Exploit crafter exception: {e}")
    sys.exit(1)

# =========================
# STEP 5: START FLASK APP
# =========================
print("\n=== STEP 4: START TARGET APP ===")

app_file = os.path.join(tempfile.gettempdir(), "patchops_target_test.py")

with open(app_file, "w") as f:
    f.write(VULNERABLE_APP_SOURCE)

proc = subprocess.Popen(
    ["python", app_file],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

time.sleep(3)

if proc.poll() is not None:
    stdout, stderr = proc.communicate()
    print("❌ Flask app failed to start")
    print("STDOUT:\n", stdout)
    print("STDERR:\n", stderr)
    sys.exit(1)

print("✅ Flask app running on http://localhost:5000")

# =========================
# STEP 6: RUN EXPLOIT
# =========================
print("\n=== STEP 5: RUN EXPLOIT ===")

exploit_file = os.path.join(tempfile.gettempdir(), "patchops_exploit_test.py")

with open(exploit_file, "w") as f:
    f.write(exploit_code)

try:
    result = subprocess.run(
        ["python", exploit_file],
        capture_output=True,
        text=True,
        timeout=30
    )

    print("\n--- EXPLOIT STDOUT ---\n")
    print(result.stdout)

    print("\n--- EXPLOIT STDERR ---\n")
    print(result.stderr)

except subprocess.TimeoutExpired:
    print("❌ Exploit execution timed out")
    proc.terminate()
    sys.exit(1)

# =========================
# STEP 7: CHECK RESULT
# =========================
print("\n=== STEP 6: RESULT ===")

if "EXPLOIT_SUCCESS" in result.stdout:
    print("✅ RED TEAM PIPELINE WORKING")
else:
    print("❌ EXPLOIT DID NOT SUCCEED — check exploit code above")

# =========================
# STEP 8: CLEANUP
# =========================
print("\n=== STEP 7: CLEANUP ===")

try:
    proc.terminate()
    proc.wait(timeout=5)
except Exception:
    proc.kill()

for path in [app_file, exploit_file]:
    try:
        os.remove(path)
    except Exception:
        pass

print("🧹 Cleanup complete")