import sys
import os
import json

# Works both locally (from repo root) and in Lambda
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)
))))
from lambdas.shared.utils import safe_call_llm_json, extract_code_block


def lambda_handler(event, context=None):
    """
    Patch Writer Lambda Handler.
    Rewrites vulnerable code to safely neutralize exploits.
    """
    try:
        source_code = event.get("source_code", "")
        vulnerability_type = event.get("vulnerability_type", "")
        vulnerable_lines = event.get("vulnerable_lines", [])
        exploit_code = event.get("exploit_code", "")
        previous_patch_failed = event.get("previous_patch_failed", False)

        if not all([source_code, vulnerability_type, exploit_code]):
            return {
                "error": "Missing required fields: source_code, vulnerability_type, exploit_code",
                "patched_code": "",
                "changes_made": [],
                "root_cause": ""
            }

        # Format vulnerable lines for the prompt
        vulnerable_lines_str = "\n".join(vulnerable_lines) if vulnerable_lines else "(analysis required)"

        # Build the strict system prompt with JSON contract
        prompt = f"""You are an elite Application Security Engineer.
Your task is to rewrite the provided Python file to fix a {vulnerability_type} vulnerability.

ORIGINAL CODE:
{source_code}

VULNERABLE LINES:
{vulnerable_lines_str}

EXPLOIT EVIDENCE (This exploit successfully bypassed the original code. Your fix MUST prevent this):
{exploit_code}
"""

        if previous_patch_failed:
            prompt += "\nWARNING: Your previous patch attempt FAILED the regression tests. You must try a fundamentally different approach. Do not repeat the same failed fix.\n"

        # THE JSON CONTRACT (Critical for reliability)
        prompt += """\nYou must output ONLY a valid JSON object. Do not wrap the JSON in markdown fences. Do not include any conversational text before or after the JSON.

CRITICAL JSON FORMATTING RULES:
You are returning a large block of Python code inside a JSON string. You MUST adhere to standard JSON escaping rules:
1. You MUST escape all newlines in the Python code as `\\n`. DO NOT output actual raw, physical line breaks inside the `patched_code` string.
2. You MUST escape all double quotes inside the Python code as `\\"`.
3. You MUST escape all tabs as `\\t`.
4. Your output must be parseable by Python's standard `json.loads()` function.

Example of CORRECT escaping:
{
    "patched_code": "import sqlite3\\nfrom flask import Flask\\n\\napp = Flask(__name__)\\ndef get_user():\\n    user_id = request.args.get(\\"id\\")\\n    ...",
    "changes_made": ["Use parameterized queries instead of f-strings", "Remove raw SQL substitution"],
    "root_cause": "Unsanitized user input was directly interpolated into SQL query using f-string"
}

You must strictly adhere to this exact JSON schema with proper escaping:
{
    "patched_code": "<string containing the complete, executable, patched Python file with all newlines as \\n and quotes as \\">",
    "changes_made": ["<string bullet point 1>", "<string bullet point 2>"],
    "root_cause": "<string briefly explaining the original flaw>"
}

Return ONLY the JSON object. Start with { and end with }. No other text."""

        # Execute with higher token limit (code rewrites need more tokens)
        patch_result = safe_call_llm_json(prompt=prompt, max_tokens=6000, retries=2)

        if "error" in patch_result:
            return {
                "error": f"Patch generation failed: {patch_result.get('error')}",
                "patched_code": "",
                "changes_made": [],
                "root_cause": ""
            }

        # Extract patch fields
        patched_code = patch_result.get("patched_code", "")
        changes_made = patch_result.get("changes_made", [])
        root_cause = patch_result.get("root_cause", "")

        # Validate we got actual code back
        if not patched_code or patched_code.strip() == "":
            return {
                "error": "LLM failed to generate patched code",
                "patched_code": "",
                "changes_made": changes_made,
                "root_cause": root_cause
            }

        return {
            "patched_code": patched_code,
            "changes_made": changes_made,
            "root_cause": root_cause
        }

    except Exception as e:
        return {
            "error": f"Patch writer exception: {str(e)}",
            "patched_code": "",
            "changes_made": [],
            "root_cause": ""
        }
