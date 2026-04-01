import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import your handlers
from lambdas.patch_writer.handler import lambda_handler as patch_writer_handler
from lambdas.security_reviewer.handler import lambda_handler as security_reviewer_handler
from lambdas.pr_generator.handler import lambda_handler as pr_generator_handler

def run_local_tests():
    print("🚀 STARTING BLUE TEAM LOCAL INTEGRATION TEST...\n")

    # ---------------------------------------------------------
    # MOCK DATA (Simulating output from Person B's Red Team)
    # ---------------------------------------------------------
    mock_source_code = """
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

@app.route('/user')
def get_user():
    user_id = request.args.get('id')
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # VULNERABLE LINE BELOW
    query = f"SELECT username, email, role FROM users WHERE id = {user_id}"
    cursor.execute(query)
    users = cursor.fetchall()
    return jsonify({"users": users})

if __name__ == '__main__':
    app.run(port=5000)
"""

    mock_exploit_code = """
import requests
try:
    response = requests.get("http://localhost:5000/user?id=-1 UNION SELECT username, email, role FROM users")
    data = response.json()
    if len(data.get("users", [])) > 1:
        print("EXPLOIT_SUCCESS")
    else:
        print("EXPLOIT_FAILED")
except Exception as e:
    print(f"Error: {e}")
"""

    vulnerability_type = "SQL Injection"
    vulnerable_lines = ["query = f\"SELECT username, email, role FROM users WHERE id = {user_id}\""]
    cwe = "CWE-89"
    severity = "HIGH"

    # ---------------------------------------------------------
    # TEST 1: Patch Writer
    # ---------------------------------------------------------
    print("🧪 TEST 1: Invoking Patch Writer...")
    patch_event = {
        "source_code": mock_source_code,
        "vulnerability_type": vulnerability_type,
        "vulnerable_lines": vulnerable_lines,
        "exploit_code": mock_exploit_code,
        "previous_patch_failed": False
    }
    
    patch_result = patch_writer_handler(patch_event, None)
    
    # DEBUG: Print raw dictionary to see what's actually returned
    print(f"\n📋 RAW DICT RETURNED: {json.dumps(patch_result, indent=2)}\n")
    
    print("✅ Patch Writer completed.")
    print(f"Changes Made: {patch_result.get('changes_made')}")
    print(f"Root Cause: {patch_result.get('root_cause')}\n")
    
    patched_code = patch_result.get("patched_code")
    if not patched_code:
        print("❌ ERROR: Patch Writer did not return patched_code.")
        return

    # ---------------------------------------------------------
    # TEST 2: Security Reviewer
    # ---------------------------------------------------------
    print("🧪 TEST 2: Invoking Security Reviewer...")
    reviewer_event = {
        "original_code": mock_source_code,
        "patched_code": patched_code,
        "vulnerability_type": vulnerability_type,
        "exploit_code": mock_exploit_code
    }
    
    review_result = security_reviewer_handler(reviewer_event, None)
    print("✅ Security Reviewer completed.")
    print(f"Approved: {review_result.get('patch_approved')}")
    print(f"Feedback: {review_result.get('feedback')}\n")
    
    final_patch = review_result.get("final_patch", patched_code)

    # ---------------------------------------------------------
    # TEST 3: PR Generator (WARNING: THIS WILL HIT GITHUB)
    # ---------------------------------------------------------
    print("🧪 TEST 3: Invoking PR Generator...")
    pr_event = {
        "repo_full_name": "gauravmishraokok/PatchOps-Target", # Make sure this repo exists!
        "file_path": "app.py",
        "final_patch": final_patch,
        "vulnerability_type": vulnerability_type,
        "cwe": cwe,
        "severity": severity,
        "exploit_evidence": mock_exploit_code,
        "changes_made": patch_result.get("changes_made", ["Fixed SQL Injection"])
    }
    
    pr_result = pr_generator_handler(pr_event, None)
    
    if pr_result.get("status") == "SUCCESS":
        print("✅ PR Generator completed successfully!")
        print(f"🔗 PR URL: {pr_result.get('pr_url')}")
        print(f"🌿 Branch: {pr_result.get('branch_name')}")
    else:
        print(f"❌ PR Generator Failed: {pr_result.get('error_message')}")

if __name__ == "__main__":
    run_local_tests()