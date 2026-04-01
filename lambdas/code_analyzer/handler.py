import sys
import os

# Works both locally (from repo root) and in Lambda
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)
))))
from lambdas.shared.utils import safe_call_llm_json


def handler(event, context=None):
    """
    Hard Boundary Code Analyzer Lambda Handler.
    Strictly limited to Top 8 vulnerability categories with consolidation.
    """
    try:
        if not event or "source_code" not in event:
            return {"error": "No source_code provided"}

        source_code = event.get("source_code", "")

        # The Hard Boundary Vulnerability Scanning Prompt
        prompt = f"""You are an Elite Static Application Security Testing (SAST) engine.
You are evaluating this Python Flask application.

SOURCE CODE:
```python
{source_code}
```

CRITICAL BOUNDARY DIRECTIVE:
You must perform an exhaustive sweep for EXACTLY these 8 vulnerability categories:

1. Hardcoded Secrets (CWE-798)
2. SQL Injection (CWE-89)
3. Command Injection (CWE-78)
4. Path Traversal (CWE-22)
5. Cross-Site Scripting / XSS (CWE-79)
6. Broken Access Control / IDOR (CWE-284)
7. Unsafe Deserialization (CWE-502)
8. Server-Side Request Forgery / SSRF (CWE-918)

RULES:

1. You MUST return an array of exactly 8 objects, one for each category above.
2. For each category, evaluate logically if it is genuinely present in the given code. Set "is_present" to true or false.
3. If "is_present" is true, provide the severity, vulnerable_lines (exact match of the code), and an attack_vector explanation.
4. If "is_present" is false, leave vulnerable_lines as an empty array and attack_vector as empty string.
5. If the same vulnerability appears multiple times, CONSOLIDATE them into the single object.

STRICT JSON SCHEMA:
{{
    "analysis": [
        {{
            "vulnerability_type": "<Type, e.g., SQL Injection>",
            "cwe": "<CWE number, e.g., CWE-89>",
            "is_present": <true/false boolean value only>,
            "severity": "<CRITICAL/HIGH/MEDIUM/NONE>",
            "vulnerable_lines": ["<exact string 1>", "<exact string 2>"],
            "attack_vector": "<Comprehensive attack explanation>"
        }}
    ]
}}

Return ONLY the JSON object. Start with {{ and end with }}. No other text. Every field must be present."""

        # Call LLM with consolidated findings
        result = safe_call_llm_json(prompt, max_tokens=3000, retries=2)

        # Validate and clean the response
        if "error" in result:
            return result

        analysis = result.get("analysis", [])
        
        # Filter to ensure we only return genuinely present vulnerabilities
        validated_vulns = []
        for vuln in analysis:
            is_present = vuln.get("is_present")
            if is_present is True or str(is_present).lower() == "true":
                if all(key in vuln for key in ["vulnerability_type", "cwe", "severity", "vulnerable_lines", "attack_vector"]):
                    validated_vulns.append(vuln)
        
        return {"vulnerabilities": validated_vulns}

    except Exception as e:
        return {"error": f"Code analyzer exception: {str(e)}"}