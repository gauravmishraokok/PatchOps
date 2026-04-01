import os, sys

# Cross-platform Python executable
PYTHON = sys.executable

# ==========================
# ENVIRONMENT SETUP
# ==========================
api_key = os.environ.get('GROQ_API_KEY')
if not api_key:
    print("ERROR: GROQ_API_KEY environment variable not set")
    print("Run: export GROQ_API_KEY=gsk_your_key_here")
    sys.exit(1)

VULNERABLE_APP_SOURCE = """
from flask import Flask, request, jsonify
import sqlite3
import tempfile
import os

app = Flask(__name__)
DB_PATH = os.path.join(tempfile.gettempdir(), "users.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(\"\"\"CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY, username TEXT, email TEXT, role TEXT
    )\"\"\")
    conn.execute("DELETE FROM users")
    conn.execute("INSERT INTO users VALUES (1, 'alice', 'alice@corp.com', 'admin')")
    conn.execute("INSERT INTO users VALUES (2, 'bob', 'bob@corp.com', 'user')")
    conn.commit()
    conn.close()

@app.route('/user')
def get_user():
    user_id = request.args.get('id', '')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = f"SELECT username, email, role FROM users WHERE id = {user_id}"
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return jsonify({"users": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)
"""

# ==========================
# IMPORT HANDLERS
# ==========================
sys.path.insert(0, os.path.dirname(__file__))
from lambdas.code_analyzer.handler import handler as analyze
from lambdas.exploit_crafter.handler import handler as craft_exploit

import subprocess
import time
import requests
import pprint
import tempfile
import shutil

pp = pprint.PrettyPrinter(indent=2)

# ==========================
# STEP 0 — HEALTH CHECK
# ==========================
print("Checking Groq API connection...")
try:
    from lambdas.shared.utils import call_llm
    response = call_llm(prompt="Reply with the single word: READY")
    if "READY" in response.upper():
        print("✅ Groq API connected")
    else:
        print("⚠ Groq API responded:", response)
except Exception as e:
    print("⚠ Health check failed:", str(e))

# ==========================
# STEP 1 — CODE ANALYZER
# ==========================
print("\n=== STEP 1: CODE ANALYZER ===")
analyzer_event = {"source_code": VULNERABLE_APP_SOURCE}
try:
    analyzer_result = analyze(analyzer_event, None)
    pp.pprint(analyzer_result)
    if "error" in analyzer_result:
        print("Analyzer error:", analyzer_result["error"])
        sys.exit(1)
except Exception as e:
    print("Analyzer failed:", str(e))
    sys.exit(1)

# ==========================
# STEP 2 — EXPLOIT CRAFTER
# ==========================
print("\n=== STEP 2: EXPLOIT CRAFTER ===")
try:
    craft_result = craft_exploit(analyzer_result, None)
    exploit_code = craft_result.get("exploit_code", "")
    if exploit_code:
        print(exploit_code)
    if "error" in craft_result and not exploit_code:
        print("Exploit crafting failed:", craft_result["error"])
        sys.exit(1)
    if "warnings" in craft_result:
        for w in craft_result["warnings"]:
            print(f"\033[93mWarning: {w}\033[0m")
except Exception as e:
    print("Exploit crafting exception:", str(e))
    sys.exit(1)

# ==========================
# STEPS 3-8 — RUN APP AND EXPLOIT
# ==========================
flask_proc = None
tmp_app_file = os.path.join(tempfile.gettempdir(), "patchops_app_test.py")
tmp_exploit_file = os.path.join(tempfile.gettempdir(), "patchops_exploit_test.py")

try:
    # STEP 3 — START FLASK APP
    print("\n=== STEP 3: STARTING TARGET APP ===")
    with open(tmp_app_file, "w") as f:
        f.write(VULNERABLE_APP_SOURCE)
    flask_proc = subprocess.Popen([PYTHON, tmp_app_file],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  text=True)
    time.sleep(3)
    try:
        r = requests.get('http://localhost:5000/health', timeout=5)
        if r.status_code == 200 and r.json().get("status") == "ok":
            print("✅ Target app running on :5000")
        else:
            raise RuntimeError("Health check failed")
    except Exception as e:
        print("App failed to start:", str(e))
        if flask_proc:
            out, err = flask_proc.communicate(timeout=5)
            print("stdout:", out)
            print("stderr:", err)
        sys.exit(1)

    # STEP 4 — NORMAL REQUEST
    print("\n=== STEP 4: BASELINE REQUEST (no injection) ===")
    try:
        r = requests.get("http://localhost:5000/user?id=1")
        print(r.json())
    except Exception as e:
        print("⚠ Baseline request failed:", str(e))

    # STEP 5 — RUN EXPLOIT
    print("\n=== STEP 5: RUNNING EXPLOIT ===")
    with open(tmp_exploit_file, "w") as f:
        f.write(exploit_code)
    result = subprocess.run([PYTHON, tmp_exploit_file],
                            capture_output=True, text=True, timeout=30)
    print("=== EXPLOIT STDOUT ===")
    print(result.stdout)
    print("=== EXPLOIT STDERR ===")
    print(result.stderr)

    # STEP 6 — RESULT
    if "EXPLOIT_SUCCESS" in result.stdout:
        print("\n✅ RED TEAM PIPELINE WORKING — exploit confirmed SQL injection")
    else:
        print("\n❌ EXPLOIT DID NOT PRINT EXPLOIT_SUCCESS")
        print("Possible reasons:")
        print("  1. Groq generated a wrong exploit — re-run to try a different generation")
        print("  2. The EXPLOIT_SUCCESS string is missing — check exploit code above")
        print("  3. The app didn't start correctly — check Step 3 output")

finally:
    # STEP 7 — CLEANUP
    print("\n=== STEP 7: CLEANUP ===")
    if flask_proc:
        flask_proc.terminate()
        flask_proc.wait()
    for fpath in [tmp_app_file, tmp_exploit_file]:
        try:
            if os.path.exists(fpath):
                os.remove(fpath)
        except Exception:
            pass
    print("Cleanup done")