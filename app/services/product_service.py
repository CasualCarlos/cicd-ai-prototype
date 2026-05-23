"""Business logic for products. (v2.0 — search support)"""

from app.database import get_db


def get_all_products():
    """Return all products as a list of dicts."""
    db = get_db()
    rows = db.execute("SELECT id, name, price, description FROM products").fetchall()
    return [dict(row) for row in rows]


def get_product_by_id(product_id: int):
    """Return a single product dict or None."""
    db = get_db()
    row = db.execute(
        "SELECT id, name, price, description FROM products WHERE id = ?", (product_id,)
    ).fetchone()
    return dict(row) if row else None


def create_product(name: str, price: float, description: str = None):
    """Insert a new product and return the created product dict.

    Raises:
        ValueError: if name is blank or price is invalid.
    """
    if not name or not name.strip():
        raise ValueError("name is required")
    try:
        price = float(price)
    except (TypeError, ValueError) as exc:
        raise ValueError("price must be a number") from exc
    if price < 0:
        raise ValueError("price must be non-negative")

    db = get_db()
    cursor = db.execute(
        "INSERT INTO products (name, price, description) VALUES (?, ?, ?)",
        (name.strip(), price, description),
    )
    db.commit()
    return get_product_by_id(cursor.lastrowid)


def delete_product(product_id: int):
    """Delete a product by id.  Returns True if deleted, False if not found."""
    if get_product_by_id(product_id) is None:
        return False
    db = get_db()
    db.execute("DELETE FROM products WHERE id = ?", (product_id,))
    db.commit()
    return True
