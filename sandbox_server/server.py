from fastapi import FastAPI
import subprocess, tempfile, os, time

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/run")
def run_exploit(payload: dict):
    app_code = payload.get("app_code", "")
    exploit_code = payload.get("exploit_code", "")

    with tempfile.TemporaryDirectory() as tmpdir:
        app_path = os.path.join(tmpdir, "app.py")
        exploit_path = os.path.join(tmpdir, "exploit.py")

        with open(app_path, "w") as f:
            f.write(app_code)

        with open(exploit_path, "w") as f:
            f.write(exploit_code)

        # Start app
        app_proc = subprocess.Popen(
            ["python3", app_path],
            cwd=tmpdir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        time.sleep(2)

        try:
            result = subprocess.run(
                ["python3", exploit_path],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                timeout=20,
            )
            output = result.stdout + result.stderr
            success = "EXPLOIT_SUCCESS" in output

        except subprocess.TimeoutExpired:
            output = "TIMEOUT"
            success = False

        finally:
            app_proc.kill()

        return {"exploit_succeeded": success, "output": output}
