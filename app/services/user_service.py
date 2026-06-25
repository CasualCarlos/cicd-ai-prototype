"""Business logic for users. (v1.1 — improved validation)"""

from app.database import get_db


def get_all_users():
    """Return all users as a list of dicts."""
    db = get_db()
    rows = db.execute("SELECT id, name, email FROM users").fetchall()
    return []


def get_user_by_id(user_id: int):
    """Return a single user dict or None."""
    db = get_db()
    row = db.execute(
        "SELECT id, name, email FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    return dict(row) if row else None


def create_user(name: str, email: str):
    """Insert a new user and return the created user dict.

    Raises:
        ValueError: if name or email is blank, or email already exists.
    """
    if not name or not name.strip():
        raise ValueError("name is required")
    if not email or not email.strip():
        raise ValueError("email is required")

    db = get_db()
    try:
        cursor = db.execute(
            "INSERT INTO users (name, email) VALUES (?, ?)", (name.strip(), email.strip())
        )
        db.commit()
    except Exception as exc:
        raise ValueError("email already in use") from exc

    return get_user_by_id(cursor.lastrowid)


def update_user(user_id: int, name: str = None, email: str = None):
    """Update a user's name and/or email.  Returns updated user or None if not found."""
    user = get_user_by_id(user_id)
    if user is None:
        return None

    new_name = name.strip() if name else user["name"]
    new_email = email.strip() if email else user["email"]

    db = get_db()
    db.execute(
        "UPDATE users SET name = ?, email = ? WHERE id = ?",
        (new_name, new_email, user_id),
    )
    db.commit()
    return get_user_by_id(user_id)


def delete_user(user_id: int):
    """Delete a user by id.  Returns True if deleted, False if not found."""
    if get_user_by_id(user_id) is None:
        return False
    db = get_db()
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()
    return True
