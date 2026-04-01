import os
import re

def handler(event, context):
    repo_path = event.get("repo_path", "PatchOps-Target")
    nodes = []
    edges = []
    found_files = set()

    for root, dirs, files in os.walk(repo_path):
        for file in files:
            if file.endswith(".py"):
                rel_path = os.path.relpath(os.path.join(root, file), repo_path)
                # Use forward slashes for IDs
                file_id = rel_path.replace("\\", "/")
                found_files.add(file_id.replace(".py", ""))
                
                with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    nodes.append({
                        "id": file_id,
                        "path": os.path.join(root, file),
                        "lines": len(lines),
                        "status": "neutral"
                    })

    # Regex for imports
    import_pattern = re.compile(r'^(?:import\s+(\w+)|from\s+(\w+)\s+import)')

    for node in nodes:
        with open(node["path"], 'r', encoding='utf-8') as f:
            content = f.read()
            # Simple line-by-line regex for top-level imports
            for line in content.splitlines():
                match = import_pattern.match(line)
                if match:
                    # Group 1 is 'import X', Group 2 is 'from X import Y'
                    imported_module = match.group(1) or match.group(2)
                    # Check if it's a file in our repo
                    if imported_module in found_files:
                        target_id = f"{imported_module}.py"
                        # Handle potential subdirectories in IDs if needed, but for now simple
                        edges.append({
                            "source": node["id"],
                            "target": target_id,
                            "type": "imports"
                        })
                    # Special case for subdirectories like 'tests/test_suite.py' importing 'app'
                    # The regex might only catch 'app'
                    # If we have 'import app', and app.py is in root, it works.

    return {"nodes": nodes, "edges": edges}
