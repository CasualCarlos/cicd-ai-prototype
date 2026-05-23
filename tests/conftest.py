"""Shared pytest fixtures."""

import os
import tempfile
import pytest
from app.main import create_app


@pytest.fixture
def app():
    """Create an application backed by a temporary file-based SQLite database.

    Using a file (not :memory:) ensures every connection within the same test
    sees the same schema, even when opened in separate app contexts.  The file
    is deleted after the test finishes.
    """
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    application = create_app({"TESTING": True, "DATABASE": db_path})
    yield application

    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()
