"""Integration tests for the products API.

Uses a real in-memory SQLite DB and the Flask test client.
"""

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clean_db(app):
    """Wipe the products table between tests so they are independent."""
    with app.app_context():
        from app.database import get_db
        db = get_db()
        db.execute("DELETE FROM products")
        db.commit()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_list_products_empty(client):
    """GET /products/ returns an empty list when no products exist."""
    response = client.get("/products/")
    assert response.status_code == 200
    assert response.get_json() == []


def test_create_product(client):
    """POST /products/ creates a product and returns 201."""
    payload = {"name": "Widget", "price": 9.99, "description": "A small widget"}
    response = client.post("/products/", json=payload)
    data = response.get_json()

    assert response.status_code == 201
    assert data["name"] == "Widget"
    assert data["price"] == 9.99
    assert data["description"] == "A small widget"
    assert "id" in data


def test_get_product_by_id(client):
    """GET /products/<id> returns the correct product."""
    created = client.post("/products/", json={"name": "Gadget", "price": 19.99}).get_json()
    product_id = created["id"]

    response = client.get(f"/products/{product_id}")
    assert response.status_code == 200
    assert response.get_json()["name"] == "Gadget"


def test_get_product_not_found(client):
    """GET /products/<id> returns 404 for a non-existent product."""
    response = client.get("/products/9999")
    assert response.status_code == 404


def test_create_product_invalid_price(client):
    """POST /products/ with a non-numeric price returns 400."""
    response = client.post("/products/", json={"name": "Thing", "price": "expensive"})
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_create_product_missing_name(client):
    """POST /products/ with no name returns 400."""
    response = client.post("/products/", json={"price": 5.00})
    assert response.status_code == 400


def test_list_products_after_inserts(client):
    """GET /products/ returns all created products."""
    client.post("/products/", json={"name": "Alpha", "price": 1.00})
    client.post("/products/", json={"name": "Beta", "price": 2.00})
    client.post("/products/", json={"name": "Gamma", "price": 3.00})

    response = client.get("/products/")
    data = response.get_json()

    assert response.status_code == 200
    assert len(data) == 3
