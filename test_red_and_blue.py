import asyncio
import json
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Add current directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lambdas.graph_builder.handler import handler as graph_builder_handler
from lambdas.code_analyzer.handler import handler as code_analyzer_handler
from lambdas.exploit_crafter.handler import handler as exploit_crafter_handler
from lambdas.patch_writer.handler import lambda_handler as patch_writer_handler
from lambdas.security_reviewer.handler import lambda_handler as security_reviewer_handler
from lambdas.neighbor_resolver.handler import handler as neighbor_resolver_handler
from lambdas.component_tester.handler import handler as component_tester_handler

async def run_cli_pipeline():
    TARGET_DIR = "PatchOps-Target"
    PRIMARY_TARGET = "app.py"
    
    print("\n[STEP 0] Building Graph...")
    graph = graph_builder_handler({"repo_path": TARGET_DIR}, None)
    print(f"Found {len(graph['nodes'])} files, {len(graph['edges'])} dependencies")
    
    print(f"\n[STEP 1] Analyzing {PRIMARY_TARGET}...")
    with open(os.path.join(TARGET_DIR, PRIMARY_TARGET), 'r') as f:
        source_code = f.read()
    
    analyzer_result = code_analyzer_handler({"source_code": source_code}, None)
    vulnerabilities = analyzer_result.get("vulnerabilities", [])
    print(f"Found {len(vulnerabilities)} vulnerabilities")
    
    if not vulnerabilities:
        return

    print("\n[STEP 2] Crafting Exploit...")
    sqli_vuln = next((v for v in vulnerabilities if "89" in v.get("cwe", "")), vulnerabilities[0])
    exploit_result = exploit_crafter_handler({
        "vulnerability_type": sqli_vuln["vulnerability_type"],
        "attack_vector": sqli_vuln["attack_vector"],
        "vulnerable_lines": sqli_vuln["vulnerable_lines"]
    }, None)
    print("Exploit ready.")
    
    print("\n[STEP 4] Writing Patch...")
    patch_result = patch_writer_handler({
        "source_code": source_code,
        "vulnerabilities": vulnerabilities
    }, None)
    patched_code = patch_result.get("patched_code")
    print(f"Applied {len(patch_result.get('completed_fixes', []))} fixes.")
    
    print("\n[STEP 5] Reviewing Patch...")
    review_result = security_reviewer_handler({
        "original_code": source_code,
        "patched_code": patched_code,
        "vulnerability_type": "Batch Fix",
        "exploit_code": exploit_result.get("exploit_code")
    }, None)
    final_patched_code = review_result.get("final_patch")
    print(f"Patch approved: {review_result.get('patch_approved')}")
    
    print("\n[STEP 7] Resolving Neighbors...")
    neighbor_result = neighbor_resolver_handler({
        "patched_file": PRIMARY_TARGET,
        "graph": graph
    }, None)
    neighbors = neighbor_result.get("neighbors")
    print(f"Neighbors to check: {neighbors}")
    
    print("\n[STEP 8] Testing Components...")
    for neighbor in neighbors:
        print(f"Checking {neighbor}...")
        with open(os.path.join(TARGET_DIR, neighbor), 'r') as f:
            neighbor_code = f.read()
        
        test_result = component_tester_handler({
            "patched_file_name": PRIMARY_TARGET,
            "original_code": source_code,
            "patched_code": final_patched_code,
            "neighbor_file_name": neighbor,
            "neighbor_code": neighbor_code
        }, None)
        
        if test_result.get("is_compatible"):
            print(f"  ✓ {neighbor} OK")
        else:
            print(f"  ⚠ {neighbor} INCOMPATIBLE")
            if test_result.get("suggested_fix"):
                print(f"  Applying fix to {neighbor}...")
                with open(os.path.join(TARGET_DIR, neighbor), "w") as f:
                    f.write(test_result["suggested_fix"])
                    
    # Save final app.py
    with open(os.path.join(TARGET_DIR, PRIMARY_TARGET), "w") as f:
        f.write(final_patched_code)
        
    print("\nPipeline Complete!")

if __name__ == "__main__":
    asyncio.run(run_cli_pipeline())
