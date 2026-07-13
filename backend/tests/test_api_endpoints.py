"""
Integration tests for FastAPI routers, validation, and security headers.
"""

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health_check_and_headers():
    """Verify health endpoint works and returns standard security headers."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    
    # Check security headers
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-XSS-Protection") == "1; mode=block"
    assert resp.headers.get("Referrer-Policy") == "no-referrer"


def test_validation_malformed_username():
    """Verify that malformed usernames are rejected by the Pydantic schema."""
    resp = client.post("/api/wrapped", json={"username": "user!name", "year": 2025})
    assert resp.status_code == 422
    assert "Invalid GitHub username" in resp.text

    resp2 = client.post("/api/wrapped", json={"username": "user; rm -rf /", "year": 2025})
    assert resp2.status_code == 422
    assert "Invalid GitHub username" in resp2.text

    resp3 = client.post("/api/wrapped", json={"username": "a" * 40, "year": 2025})
    assert resp3.status_code == 422


def test_validation_invalid_token():
    """Verify that invalid github token formats are rejected."""
    resp = client.post(
        "/api/wrapped", 
        json={"username": "torvalds", "github_token": "short", "year": 2025}
    )
    assert resp.status_code == 422
    assert "Invalid GitHub token format" in resp.text

    resp2 = client.post(
        "/api/wrapped", 
        json={"username": "torvalds", "github_token": "token-with-invalid-chars!@#", "year": 2025}
    )
    assert resp2.status_code == 422
    assert "Invalid GitHub token format" in resp2.text


def test_path_parameter_validation_image():
    """Verify path parameter username validation on the GET /image route."""
    # Malformed username parameter
    resp = client.get("/api/wrapped/user!name/image")
    assert resp.status_code == 422

    # Directory traversal/invalid username parameter
    resp2 = client.get("/api/wrapped/invalid.user/image")
    assert resp2.status_code == 422


def test_path_parameter_validation_personality():
    """Verify path parameter username validation on the GET /personality route."""
    # Malformed username parameter
    resp = client.get("/api/wrapped/user!name/personality")
    assert resp.status_code == 422
