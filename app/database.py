"""SQLite database setup.

In-memory database is used during testing; a file-based database is used in production.
"""

import sqlite3
from flask import g, current_app


def get_db():
    """Return a database connection for the current request context."""
    if "db" not in g:
        database = current_app.config["DATABASE"]
        # Support URI-style connection strings (e.g. shared in-memory for tests)
        use_uri = database.startswith("file:")
        g.db = sqlite3.connect(
            database,
            detect_types=sqlite3.PARSE_DECLTYPES,
            uri=use_uri,
        )
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    """Close the database connection at the end of a request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app):
    """Create tables if they do not exist yet."""
    with app.app_context():
        db = get_db()
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                name    TEXT    NOT NULL,
                email   TEXT    NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS products (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT    NOT NULL,
                price       REAL    NOT NULL,
                description TEXT
            );
            """
        )
        db.commit()
