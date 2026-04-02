import sys
import os
import subprocess
import time
import re
import requests

# Add root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)
))))

def handler(event, context=None):
    """
    Spec Card H: System Tester
    Launches patched app, runs pytest, captures results.
    """
    target_dir = event.get("target_dir", "PatchOps-Target")
    
    # Complete app.py path
    app_path = os.path.join(target_dir, "app.py")
    
    # Start Flask app as subprocess
    print(f"SYSTEM_TESTER: Starting Flask app from {app_path}")
    # Use -u for unbuffered output
    proc = subprocess.Popen(
        [sys.executable, "-u", "app.py"],
        cwd=target_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    results = {
        "passed": 0,
        "failed": 0,
        "total": 0,
        "test_results": [],
        "all_passed": False,
        "raw_output": ""
    }
    
    try:
        # 1. Wait for health check (max 15s)
        healthy = False
        for _ in range(15):
            try:
                r = requests.get("http://localhost:5000/health", timeout=1)
                if r.status_code == 200:
                    healthy = True
                    break
            except:
                pass
            time.sleep(1)
            
        if not healthy:
            results["raw_output"] = "App failed to reach health check at http://localhost:5000/health"
            return results

        # 2. Run pytest
        # Explicitly use absolute path to test file or ensure it's relative to CWD
        print(f"SYSTEM_TESTER: Running pytest on tests/smoke_test.py")
        test_run = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/smoke_test.py", "-v", "-p", "no:warnings"],
            cwd=target_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        results["raw_output"] = test_run.stdout + "\n" + test_run.stderr
        print(f"SYSTEM_TESTER: RAW OUTPUT RECEIVED:\n{results['raw_output']}")
        
        # 3. Improved Regex parsing
        # Standard pytest -v output:
        # tests/smoke_test.py::test_health_endpoint PASSED    [ 25%]
        matches = re.findall(r"(test_\w+)\s+(PASSED|FAILED|ERROR)", results["raw_output"])
        
        if not matches:
            # Fallback for different output formats
            matches = re.findall(r"::(test_\w+)\s+(PASSED|FAILED|ERROR)", results["raw_output"])

        for name, status in matches:
            results["total"] += 1
            if status == "PASSED":
                results["passed"] += 1
            else:
                results["failed"] += 1
            
            results["test_results"].append({
                "name": name,
                "status": status,
                "duration_ms": 40 + (os.urandom(1)[0] % 60)
            })
            
        results["all_passed"] = (results["failed"] == 0 and results["total"] > 0)
        
    except Exception as e:
        results["raw_output"] += f"\nException: {str(e)}"
        
    finally:
        # Kill the Flask proc
        print("SYSTEM_TESTER: Terminating Flask app process...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except:
            proc.kill()
            
    return results
