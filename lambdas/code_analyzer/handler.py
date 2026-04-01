import sys
import os

# Works both locally (from repo root) and in Lambda
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)
))))
from lambdas.shared.utils import safe_call_llm_json, call_llm, extract_code_block


ANALYZER_PROMPT = """You are a security vulnerability analyst.

Analyze the following Python source code and identify the most critical security vulnerability.

CVE hint: {cve_description}

Source code:
{source_code}

Return a JSON object with this exact structure. No explanation outside the JSON. No markdown fences. Start your response with {{ and end with }}:

{{
  "vulnerable_lines": ["the exact line of code that is vulnerable"],
  "line_numbers": [<line number as integer>],
  "vulnerability_type": "<specific type e.g. SQL Injection, Command Injection, Path Traversal>",
  "explanation": "<2-3 sentences explaining why this is vulnerable and what an attacker can do>",
  "attack_vector": "<concrete example: HTTP method, path, parameter, and payload>",
  "severity": "<HIGH or MEDIUM or LOW>",
  "cwe": "<CWE number e.g. CWE-89>"
}}"""


def handler(event, context):
    try:
        # 1. Validate input
        if not event or "source_code" not in event:
            return {"error": "No source_code provided"}

        source_code = event.get("source_code", "")
        cve_description = event.get("cve_description", "")

        # 2. Format prompt
        prompt = ANALYZER_PROMPT.format(
            source_code=source_code,
            cve_description=cve_description
        )

        # 3. Call LLM
        result = safe_call_llm_json(prompt, max_tokens=1000)

        # 4. Handle LLM error
        if not isinstance(result, dict):
            return {"error": "Invalid response from LLM"}

        if "error" in result:
            return result

        # 5. Validate required keys
        required_keys = ["vulnerability_type", "attack_vector", "vulnerable_lines"]
        missing_keys = [k for k in required_keys if k not in result or not result.get(k)]

        if missing_keys:
            return {"error": f"Response missing required keys: {missing_keys}"}

        # 6. Soft validation rule
        attack_vector = result.get("attack_vector", "")
        vulnerability_type = result.get("vulnerability_type", "")

        warning = None

        if not vulnerability_type:
            warning = "vulnerability_type is empty"

        if not any(x in attack_vector for x in ["GET", "POST", "/"]):
            warning = (warning + "; " if warning else "") + "attack_vector may not be a valid HTTP pattern"

        if warning:
            result["warning"] = warning

        # 7. Return final structured result
        return result

    except Exception as e:
        return {"error": str(e)}