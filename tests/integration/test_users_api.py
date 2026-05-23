"""Integration tests for the users API.

Uses a real in-memory SQLite DB and the Flask test client.
These tests are naturally slower than unit tests because each test
rebuilds the database schema and performs real I/O.
"""

import json
import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clean_db(app):
    """Wipe the users table between tests so they are independent."""
    with app.app_context():
        from app.database import get_db
        db = get_db()
        db.execute("DELETE FROM users")
        db.commit()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_list_users_empty(client):
    """GET /users/ returns an empty list when no users exist."""
    response = client.get("/users/")
    assert response.status_code == 200
    assert response.get_json() == []


def test_create_user(client):
    """POST /users/ creates a user and returns 201 with the new resource."""
    payload = {"name": "Alice", "email": "alice@example.com"}
    response = client.post("/users/", json=payload)
    data = response.get_json()

    assert response.status_code == 201
    assert data["name"] == "Alice"
    assert data["email"] == "alice@example.com"
    assert "id" in data


def test_get_user_by_id(client):
    """GET /users/<id> returns the correct user."""
    created = client.post("/users/", json={"name": "Bob", "email": "bob@example.com"}).get_json()
    user_id = created["id"]

    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200
    assert response.get_json()["name"] == "Bob"


def test_get_user_not_found(client):
    """GET /users/<id> returns 404 for a non-existent user."""
    response = client.get("/users/9999")
    assert response.status_code == 404


def test_update_user(client):
    """PUT /users/<id> updates the user's fields."""
    created = client.post("/users/", json={"name": "Carol", "email": "carol@example.com"}).get_json()
    user_id = created["id"]

    response = client.put(f"/users/{user_id}", json={"name": "Caroline"})
    data = response.get_json()

    assert response.status_code == 200
    assert data["name"] == "Caroline"
    assert data["email"] == "carol@example.com"


def test_delete_user(client):
    """DELETE /users/<id> removes the user; subsequent GET returns 404."""
    created = client.post("/users/", json={"name": "Dave", "email": "dave@example.com"}).get_json()
    user_id = created["id"]

    delete_response = client.delete(f"/users/{user_id}")
    assert delete_response.status_code == 200

    get_response = client.get(f"/users/{user_id}")
    assert get_response.status_code == 404


def test_create_user_missing_email(client):
    """POST /users/ with no email returns 400."""
    response = client.post("/users/", json={"name": "Eve"})
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_list_users_after_inserts(client):
    """GET /users/ returns all created users."""
    client.post("/users/", json={"name": "Frank", "email": "frank@example.com"})
    client.post("/users/", json={"name": "Grace", "email": "grace@example.com"})

    response = client.get("/users/")
    data = response.get_json()

    assert response.status_code == 200
    assert len(data) == 2
    names = {u["name"] for u in data}
    assert names == {"Frank", "Grace"}
