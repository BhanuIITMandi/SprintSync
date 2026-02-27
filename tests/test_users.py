"""Unit tests for user endpoints."""


def test_register_user_happy_path(client):
    """User registration returns 200 with correct email."""
    resp = client.post("/users/", json={
        "email": "newuser@example.com",
        "password": "securepass"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "newuser@example.com"
    assert data["is_admin"] is False
    assert "id" in data


def test_register_duplicate_email(client):
    """Registering with an existing email returns 400."""
    payload = {"email": "dup@example.com", "password": "pass123"}
    client.post("/users/", json=payload)
    resp = client.post("/users/", json=payload)
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"].lower()
