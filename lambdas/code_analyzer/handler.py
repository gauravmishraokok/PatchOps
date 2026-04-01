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
You are strictly limited to identifying ONLY the following 8 vulnerability categories:

1. Hardcoded Secrets (CWE-798)
2. SQL Injection (CWE-89)
3. Command Injection (CWE-78)
4. Path Traversal (CWE-22)
5. Cross-Site Scripting / XSS (CWE-79)
6. Broken Access Control / IDOR (CWE-284)
7. Unsafe Deserialization (CWE-502)
8. Server-Side Request Forgery / SSRF (CWE-918)

RULES:

1. If you find a vulnerability that is NOT on this exact list of 8, YOU MUST IGNORE IT.
2. If you find multiple instances of the same vulnerability type (e.g., SQL Injection in 3 different routes), CONSOLIDATE them into a single JSON object for that category, listing all affected lines in the vulnerable_lines array.
3. You must NEVER return more than 8 objects in the vulnerabilities array.
4. Each vulnerability MUST include ALL required fields: vulnerability_type, cwe, severity, vulnerable_lines, attack_vector.

STRICT JSON SCHEMA:
{{
    "vulnerabilities": [
        {{
            "vulnerability_type": "<Type, e.g., SQL Injection>",
            "cwe": "<CWE number, e.g., CWE-89>",
            "severity": "<CRITICAL/HIGH/MEDIUM>",
            "vulnerable_lines": ["<exact string 1>", "<exact string 2>", "<exact string 3>"],
            "attack_vector": "<Comprehensive attack explanation covering all instances>"
        }}
    ]
}}

Return ONLY the JSON object. Start with {{ and end with }}. No other text. Every field must be present."""

        # Call LLM with consolidated findings
        result = safe_call_llm_json(prompt, max_tokens=6000, retries=2)

        # Validate and clean the response
        if "error" in result:
            return result

        vulnerabilities = result.get("vulnerabilities", [])
        
        # Filter to ensure all required fields are present
        validated_vulns = []
        for vuln in vulnerabilities:
            if all(key in vuln for key in ["vulnerability_type", "cwe", "severity", "vulnerable_lines", "attack_vector"]):
                validated_vulns.append(vuln)
        
        return {"vulnerabilities": validated_vulns}

    except Exception as e:
        return {"error": f"Code analyzer exception: {str(e)}"}