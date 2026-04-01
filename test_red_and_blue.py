import os
import json
from dotenv import load_dotenv

load_dotenv()

from lambdas.code_analyzer.handler import handler as code_analyzer_handler
from lambdas.patch_writer.handler import lambda_handler as patch_writer_handler
from lambdas.pr_generator.handler import lambda_handler as pr_generator_handler

def run_local_tests():
    print("🚀 STARTING BATCH-PROCESSING PIPELINE (Optimized for Rate Limits)...\n")

    # 1. READ THE REAL VULNERABLE FILE
    target_file_path = "PatchOps-Target/app.py"
    try:
        with open(target_file_path, "r") as f:
            live_source_code = f.read()
        print(f"✅ Successfully loaded {target_file_path}\n")
    except FileNotFoundError:
        print(f"❌ ERROR: Could not find {target_file_path}. Make sure the path is correct.")
        return

    # 2. INVOKE THE LIVE ANALYZER (LLM CALL #1)
    print("🔍 ANALYZER: Exhaustive Vulnerability Sweep...")
    analyzer_event = {"source_code": live_source_code}
    analyzer_result = code_analyzer_handler(analyzer_event, None)
    
    if "error" in analyzer_result:
        print(f"❌ Analyzer Failed: {analyzer_result['error']}")
        return

    vulnerabilities = analyzer_result.get("vulnerabilities", [])
    print(f"✅ Found {len(vulnerabilities)} vulnerabilities:\n")
    for i, v in enumerate(vulnerabilities, 1):
        vuln_type = v.get('vulnerability_type', 'Unknown')
        cwe = v.get('cwe', 'CWE-Unknown')
        severity = v.get('severity', 'UNKNOWN')
        print(f"  {i}. {vuln_type} ({cwe}) [{severity}]")

    if not vulnerabilities:
        print("\n🎉 Code is secure! No patches needed.")
        return

    # 3. INVOKE BATCH PATCHER (LLM CALL #2) - FIX ALL IN ONE SHOT
    print(f"\n{'='*60}")
    print(f"🛠️  BATCH PATCHER: Fixing all {len(vulnerabilities)} vulnerabilities...")
    print(f"{'='*60}\n")
    
    patch_event = {
        "source_code": live_source_code,
        "vulnerabilities": vulnerabilities  # Pass entire array!
    }
    
    patch_result = patch_writer_handler(patch_event, None)
    
    if "error" in patch_result:
        print(f"❌ Batch Patcher Failed: {patch_result['error']}")
        return
        
    completed_fixes = patch_result.get("completed_fixes", [])
    failed_fixes = patch_result.get("failed_fixes", [])
    current_source_code = patch_result.get("patched_code")
    
    print(f"✅ Batch Patching Complete:")
    print(f"   ✓ Successfully fixed: {patch_result.get('successful_patches')}/{patch_result.get('total_vulnerabilities')}")
    
    if failed_fixes:
        print(f"   ✗ Failed to fix: {len(failed_fixes)}")
        for fail in failed_fixes:
            print(f"      - {fail['type']} ({fail['cwe']}): {fail['reason']}")

    if not completed_fixes:
        print("\n⚠️  No patches were successfully applied.")
        return

    # 4. PR GENERATION (LLM CALL #3 - GitHub API)
    print(f"\n{'='*60}")
    print(f"📝 PR GENERATOR: Creating pull request with {len(completed_fixes)} fixes...")
    print(f"{'='*60}\n")
    
    pr_event = {
        "repo_full_name": "gauravmishraokok/PatchOps-Target",
        "file_path": "app.py",
        "final_patch": current_source_code,
        "fixed_vulnerabilities": completed_fixes  # NEW SCHEMA: Pass array directly
    }
    
    pr_result = pr_generator_handler(pr_event, None)
    
    if pr_result.get("status") == "SUCCESS":
        print("✅ Pull Request Created Successfully!")
        print(f"🔗 PR URL: {pr_result.get('pr_url')}")
        print(f"🌿 Branch: {pr_result.get('branch_name')}\n")
        print(f"📊 SUMMARY:")
        print(f"   • Vulnerabilities Found: {len(vulnerabilities)}")
        print(f"   • Vulnerabilities Fixed: {len(completed_fixes)}")
        print(f"   • LLM Calls Made: 3 (Analyzer → Batch Patcher → PR Generator)")
        print(f"   • Pipeline Status: ✅ SUCCESS")
    else:
        print(f"❌ PR Generator Failed: {pr_result.get('error_message')}")

if __name__ == "__main__":
    run_local_tests()
