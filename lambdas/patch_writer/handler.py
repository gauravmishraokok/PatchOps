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
    Batch Patch Writer Lambda Handler.
    Accepts an array of vulnerabilities and fixes ALL of them in a single LLM call.
    """
    try:
        source_code = event.get("source_code", "")
        vulnerabilities = event.get("vulnerabilities", [])

        if not source_code:
            return {
                "error": "Missing source_code",
                "patched_code": "",
                "completed_fixes": []
            }

        if not vulnerabilities:
            return {
                "patched_code": source_code,
                "completed_fixes": []
            }

        # Format vulnerabilities for the prompt
        vulns_str = json.dumps(vulnerabilities, indent=2)

        # Build the batch patcher prompt
        prompt = f"""You are an elite Application Security Engineer.
You have been handed a source file containing multiple vulnerabilities. You must fix ALL of them in a single response.

ORIGINAL CODE:
```python
{source_code}
```

VULNERABILITIES TO FIX:
{vulns_str}

CRITICAL RULES:
1. DO NOT rewrite the entire file. Use surgical Search & Replace blocks only.
2. You must provide EXACTLY ONE fix object per vulnerability listed. If there are 8 vulnerabilities in the input, return exactly 8 fix objects in the fixes array.
3. The search text must EXACTLY match the original code, including all whitespace and indentation.
4. All newlines in strings MUST be escaped as \\n and all quotes as \\".
5. Group each vulnerability's modifications together in the fixes array.
6. Be exhaustive but ONLY within the scope of what's provided. Do not create extra fixes.

STRICT JSON SCHEMA (EXACTLY {len(vulnerabilities)} FIXES):
{{
    "fixes": [
        {{
            "vulnerability_type": "<e.g., SQL Injection>",
            "cwe": "<e.g., CWE-89>",
            "changes_made": ["Change 1", "Change 2"],
            "modifications": [
                {{
                    "search": "<EXACT text block from original code, escaped properly>",
                    "replace": "<Secure replacement code, escaped properly>"
                }}
            ]
        }}
    ]
}}

You MUST return exactly {len(vulnerabilities)} objects in the fixes array, no more, no less.
Return ONLY the JSON object. Start with {{ and end with }}. No other text."""

        # Call LLM for batch patching
        batch_result = safe_call_llm_json(prompt, max_tokens=8000, retries=2)

        if "error" in batch_result:
            return {
                "error": f"Batch patch generation failed: {batch_result.get('error')}",
                "patched_code": "",
                "completed_fixes": []
            }

        current_code = source_code
        completed_fixes = []
        failed_fixes = []

        # Process each fix from the batch
        for fix in batch_result.get("fixes", []):
            vuln_type = fix.get("vulnerability_type", "Unknown")
            cwe = fix.get("cwe", "")
            modifications = fix.get("modifications", [])
            changes_made = fix.get("changes_made", [])

            fix_successful = True
            applied_modifications = []

            for mod in modifications:
                search_text = mod.get("search", "")
                replace_text = mod.get("replace", "")

                if not search_text:
                    continue

                # 🔨 TRY EXACT MATCH FIRST
                if search_text in current_code:
                    current_code = current_code.replace(search_text, replace_text, 1)  # Replace ONE instance at a time
                    applied_modifications.append(mod)
                # 🔨 FALLBACK: TRY STRIP WHITESPACE
                elif search_text.strip() and search_text.strip() in current_code:
                    current_code = current_code.replace(search_text.strip(), replace_text.strip(), 1)
                    applied_modifications.append(mod)
                else:
                    # ⚠️ Could not find the exact string - mark as partially failed
                    fix_successful = False
                    print(f"⚠️  WARNING: Could not apply patch for {vuln_type} - Search string not found in current code.")
                    break

            if fix_successful and applied_modifications:
                completed_fixes.append({
                    "type": vuln_type,
                    "cwe": cwe,
                    "changes_made": changes_made,
                    "exploit_evidence": next((v.get("attack_vector", "N/A") for v in vulnerabilities if v.get("cwe") == cwe), "N/A")
                })
            else:
                failed_fixes.append({
                    "type": vuln_type,
                    "cwe": cwe,
                    "reason": "Could not locate search string in code"
                })

        return {
            "patched_code": current_code,
            "completed_fixes": completed_fixes,
            "failed_fixes": failed_fixes if failed_fixes else None,
            "total_vulnerabilities": len(vulnerabilities),
            "successful_patches": len(completed_fixes)
        }

    except Exception as e:
        return {
            "error": f"Batch patch writer exception: {str(e)}",
            "patched_code": "",
            "completed_fixes": []
        }

