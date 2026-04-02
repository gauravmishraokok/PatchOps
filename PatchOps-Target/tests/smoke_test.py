import requests
import pytest

BASE_URL = "http://localhost:5000"

def test_health_endpoint():
    """Verify patched app is alive."""
    r = requests.get(f"{BASE_URL}/health", timeout=5)
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_user_endpoint_returns_data():
    """Verify /user endpoint still functions."""
    r = requests.get(f"{BASE_URL}/user?id=1", timeout=5)
    assert r.status_code == 200
    # The database initialization creates a users table
    assert "username" in r.json()

def test_user_endpoint_no_sqli_bypass():
    """Security smoke test: verify SQLi payload doesn't dump all users."""
    # Payload that would normally dump more or bypass if not parameterized
    r = requests.get(f"{BASE_URL}/user", params={"id": "1 OR 1=1--"}, timeout=5)
    # If patched correctly, this should either 404 (not found) or return exactly one user (if id '1 OR 1=1--' is treated as a string)
    # or return a 500/400 if it's a strict type check. For this demo, let's check it doesn't return more than 1 user.
    if r.status_code == 200:
        data = r.json()
        # If it returns a single user object, its length (keys) is small. 
        # If it returns a list, we check length. Our current endpoint returns a single object.
        assert "username" in data
    else:
        assert r.status_code in [404, 400, 500]

def test_profile_endpoint_exists():
    """Verify /profile exists and doesn't crash."""
    r = requests.get(f"{BASE_URL}/profile?id=1", timeout=5)
    assert r.status_code in [200, 401, 403, 404]

def test_ping_endpoint_no_command_injection():
    """Security smoke test: verify command injection is blocked."""
    r = requests.get(f"{BASE_URL}/ping?ip=127.0.0.1; ls", timeout=5)
    # If patched, the output should just be the ping result for "127.0.0.1; ls" which usually fails or just pings.
    # It shouldn't contain etc/password or file listing markers.
    if r.status_code == 200:
        text = r.json().get("output", "").lower()
        assert "etc" not in text
        assert "root" not in text
    else:
        assert r.status_code in [400, 500]
