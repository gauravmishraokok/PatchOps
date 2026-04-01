import json

# Mock LLM call for component testing
def safe_call_llm_json(prompt, max_tokens=1000):
    # In a real scenario, this would call Groq/OpenAI
    # For demo purposes, we'll simulate logic
    if "auth.py" in prompt and "app.py" in prompt:
        # If app.py is fixed (SQLi fixed), auth.py might need update or be fine
        # Spec says auth.py has IDOR, but we're checking COMPATIBILITY
        # Let's say if we change get_profile signature it breaks.
        return {
            "is_compatible": False,
            "issues_found": ["Patched file changed get_profile call site logic"],
            "suggested_fix": "import db_utils\nimport config\nimport utils\n\ndef login(username, password):\n    return {\"status\": \"success\", \"token\": \"mock-token-123\"}\n\ndef get_profile(user_id):\n    # FIXED IDOR\n    return db_utils.safe_query(\"SELECT * FROM users WHERE id = ?\", (user_id,))[0] if db_utils.query_user(user_id) else None\n\ndef check_token(token):\n    return token == \"mock-token-123\"\n"
        }
    return {
        "is_compatible": True,
        "issues_found": [],
        "suggested_fix": ""
    }

def handler(event, context):
    patched_file_name = event.get("patched_file_name")
    original_code = event.get("original_code")
    patched_code = event.get("patched_code")
    completed_fixes = event.get("completed_fixes", [])
    neighbor_file_name = event.get("neighbor_file_name")
    neighbor_code = event.get("neighbor_code")

    COMPONENT_TEST_PROMPT = f"""
You are a code compatibility analyst.

PATCHED FILE: {patched_file_name}
CHANGES MADE:
{json.dumps(completed_fixes, indent=2)}

NEIGHBOR FILE: {neighbor_file_name}
{neighbor_code}

TASK: Does the neighbor file still work correctly given the changes made to the patched file?
Return ONLY JSON.
"""
    
    # In demo mode, we use the mock result
    result = safe_call_llm_json(COMPONENT_TEST_PROMPT)
    result["neighbor"] = neighbor_file_name
    return result
