import sys
import os

# Works both locally (from repo root) and in Lambda
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)
))))
from lambdas.shared.utils import safe_call_llm_json, call_llm

REVIEW_PROMPT = """You are an unforgiving AppSec code reviewer. Your job is to validate security patches.

ORIGINAL CODE (vulnerable):
{original_code}

PATCHED CODE (proposed fix):
{patched_code}

VULNERABILITY_TYPE: {vulnerability_type}

EXPLOIT_CODE (proof-of-concept):
{exploit_code}

Your strict validation checklist:

1. EXPLOIT NEUTRALIZATION: Does the patched code actually prevent the exploit? Trace through the exploit logic step-by-step.
2. IMPORTS PRESERVED: Are all necessary imports (Flask, request, jsonify, sqlite3) still present? No removal of critical dependencies?
3. /HEALTH ENDPOINT: Is the /health endpoint still intact and functional for health checks?
4. SYNTAX & RUNTIME: Is the patched code syntactically correct Python? Will it run without TypeError/SyntaxError?
5. NO NEW VULNS: Does the patch introduce new security issues (e.g., worse SQL injection, XSS, etc.)?
6. MINIMAL CHANGES: Does the patch make only the necessary changes to fix the bug, or does it refactor unnecessarily?

Return ONLY a JSON object with this structure. No explanation outside JSON. No markdown fences.

{{
  "patch_approved": <true or false>,
  "feedback": "<detailed reasoning covering all 6 points above. Be critical and specific.>",
  "final_patch": "<if patch_approved is true, return the patched_code as-is. If false, provide your own corrected patch_code here that fixes all issues>"
}}

CRITICAL: If you find ANY issue, set patch_approved to false and provide a corrected version in final_patch.
Be unforgiving — security is not optional."""


def lambda_handler(event, context=None):
    """
    Security Reviewer Lambda Handler.
    Validates that patch_writer's output is safe and correct.
    """
    try:
        original_code = event.get("original_code", "")
        patched_code = event.get("patched_code", "")
        vulnerability_type = event.get("vulnerability_type", "")
        exploit_code = event.get("exploit_code", "")

        if not all([original_code, patched_code, vulnerability_type]):
            return {
                "error": "Missing required fields: original_code, patched_code, vulnerability_type",
                "patch_approved": False,
                "feedback": "Invalid input",
                "final_patch": ""
            }

        # Construct the review prompt
        prompt = REVIEW_PROMPT.format(
            original_code=original_code,
            patched_code=patched_code,
            vulnerability_type=vulnerability_type,
            exploit_code=exploit_code
        )

        # Get LLM review
        review_result = safe_call_llm_json(prompt=prompt, max_tokens=3000, retries=2)

        if "error" in review_result:
            return {
                "error": f"Review failed: {review_result.get('error')}",
                "patch_approved": False,
                "feedback": review_result.get("error", "Unknown error"),
                "final_patch": patched_code
            }

        # Extract review fields
        patch_approved = review_result.get("patch_approved", False)
        feedback = review_result.get("feedback", "")
        final_patch = review_result.get("final_patch", patched_code if patch_approved else "")

        return {
            "patch_approved": patch_approved,
            "feedback": feedback,
            "final_patch": final_patch
        }

    except Exception as e:
        return {
            "error": f"Security review exception: {str(e)}",
            "patch_approved": False,
            "feedback": str(e),
            "final_patch": ""
        }
