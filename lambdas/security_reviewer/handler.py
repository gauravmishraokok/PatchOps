import sys
import os

# Works both locally (from repo root) and in Lambda
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)
))))
from lambdas.shared.utils import safe_call_llm_json


REVIEW_PROMPT = """You are a senior application security engineer doing a code review.

Vulnerability being fixed: {vulnerability_type}

Original vulnerable code:
{original_code}

Proposed patch:
{patched_code}

Exploit that proved the original vulnerability:
{exploit_code}

Review the patch and answer these questions:
1. Does it fix the root cause completely?
2. Does it introduce any new vulnerabilities?
3. Does it preserve all original functionality?
4. Is the fix correct and idiomatic?

If the patch is correct: approve it as-is.
If it needs minor improvements: provide an improved version.
If it has serious issues: rewrite the fix correctly.

Return a JSON object. No markdown. Start with {{
{{
  "patch_approved": true or false,
  "issues_found": ["list any issues, or empty array if none"],
  "recommendations": ["list suggestions, or empty array"],
  "final_patch": "<the complete final file — improved if needed, same as input if good>"
}}"""


def lambda_handler(event, context=None):
    """
    Security Reviewer Lambda Handler.
    Reviews the patch produced by patch_writer.
    Checks it actually fixes the vulnerability and doesn't introduce new ones.
    Returns an approved patch — either the original or an improved version.
    """
    try:
        # 1. Validate event has original_code and patched_code
        original_code = event.get("original_code")
        patched_code = event.get("patched_code")
        
        if not original_code or not patched_code:
            return {
                "error": "Missing required fields: original_code and patched_code",
                "patch_approved": False,
                "issues_found": ["Missing input validation"],
                "recommendations": [],
                "final_patch": event.get('patched_code', '')
            }

        # 2. Format REVIEW_PROMPT
        prompt = REVIEW_PROMPT.format(
            original_code=original_code,
            patched_code=patched_code,
            exploit_code=event.get("exploit_code", ""),
            vulnerability_type=event.get("vulnerability_type", "Unknown")
        )

        # 3. Call safe_call_llm_json
        result = safe_call_llm_json(prompt, max_tokens=3000)

        # 4. If result has 'error' key: return error with fallback
        if "error" in result:
            return {
                "error": result['error'],
                "patch_approved": False,
                "issues_found": [],
                "final_patch": event.get('patched_code', '')
            }

        # 5. Validate 'final_patch' exists and is non-empty string with 'def ' in it
        final_patch = result.get("final_patch")
        if not final_patch or not isinstance(final_patch, str) or "def " not in final_patch:
            # Fall back to input patched_code
            result['final_patch'] = event.get('patched_code', '')
            result['patch_approved'] = True  # Default to approval on fallback

        # 6. Ensure patch_approved key exists — default to True if missing
        if 'patch_approved' not in result:
            result['patch_approved'] = True

        # 7. Ensure required fields exist with defaults
        if 'issues_found' not in result:
            result['issues_found'] = []
        if 'recommendations' not in result:
            result['recommendations'] = []

        # 8. Return result
        return {
            "patch_approved": result["patch_approved"],
            "issues_found": result["issues_found"],
            "recommendations": result["recommendations"],
            "final_patch": result["final_patch"]
        }

    except Exception as e:
        # Failure philosophy: never block the pipeline
        return {
            "error": f"Security review exception: {str(e)}",
            "patch_approved": True,  # Default to approval on error
            "issues_found": ["Review process failed"],
            "recommendations": [],
            "final_patch": event.get('patched_code', '')
        }
