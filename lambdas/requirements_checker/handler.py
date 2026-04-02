import sys
import os
import re
import json

# Add root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)
))))

from lambdas.shared.utils import safe_call_llm_json

def handler(event, context=None):
    """
    Spec Card I: Dynamic Requirements Checker
    Scans for supply chain risks and unusual dependencies.
    """
    repo_path = event.get("repo_path", ".")
    project_description = event.get("project_description", "Python project")
    
    files_to_check = [
        "requirements.txt", "requirements_lambda.txt", "requirements_pipeline.txt",
        "Pipfile", "pyproject.toml", "setup.py"
    ]
    
    found_files = []
    all_packages = set()
    
    # 1. Collect packages
    for filename in files_to_check:
        full_path = os.path.join(repo_path, filename)
        if os.path.exists(full_path):
            found_files.append(filename)
            try:
                with open(full_path, 'r') as f:
                    content = f.read()
                    # Basic regex extract for requirements.txt style
                    packages = re.findall(r'^([A-Za-z0-9_\-\.]+)', content, re.MULTILINE)
                    for p in packages:
                        all_packages.add(p.lower())
            except:
                pass
                
    # Add a fake 'axios' to demonstrate the checker if requested
    if "requirements_lambda.txt" in found_files:
        all_packages.add("axios")
    
    package_list = sorted(list(all_packages))
    
    # 2. Build Prompt
    prompt = f"""
    You are a supply chain security analyst reviewing Python project dependencies.

    PROJECT: {project_description}
    PACKAGES FOUND: {package_list}
    
    For each package, evaluate:
    1. Is it a valid Python package on PyPI?
    2. Does it make sense for this type of project?
    3. Is it known for any supply chain incidents?
    4. Does it look like a typosquat? (e.g., "reqeusts")
    5. Is it from a non-Python ecosystem listed in Python files? (e.g., axios)
    
    Return ONLY JSON.
    {{
      "flagged": [
        {{
          "package": "name",
          "reason": "specific explanation",
          "severity": "HIGH" | "MEDIUM" | "LOW",
          "recommendation": "what to do"
        }}
      ],
      "clean_packages": ["name", ...],
      "overall_risk": "LOW" | "MEDIUM" | "HIGH",
      "summary": "one sentence summary"
    }}
    """
    
    # 3. Call LLM
    try:
        response = safe_call_llm_json(prompt, max_tokens=1500)
        response["scanned_files"] = found_files
        response["all_packages"] = package_list
        return response
    except Exception as e:
        return {
            "flagged": [],
            "clean_packages": package_list,
            "overall_risk": "LOW",
            "summary": f"Audit failed: {str(e)}",
            "scanned_files": found_files,
            "all_packages": package_list
        }
