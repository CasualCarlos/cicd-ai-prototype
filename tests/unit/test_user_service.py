"""Unit tests for user_service — the DB is mocked so these run fast."""

from unittest.mock import MagicMock, patch, call
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_row(id, name, email):
    """Create a sqlite3.Row-like dict."""
    return {"id": id, "name": name, "email": email}


# ---------------------------------------------------------------------------
# get_all_users
# ---------------------------------------------------------------------------

@patch("app.services.user_service.get_db")
def test_get_all_users_returns_list(mock_get_db):
    """get_all_users returns every row from the DB as a list of dicts."""
    mock_db = MagicMock()
    mock_db.execute.return_value.fetchall.return_value = [
        _make_row(1, "Alice", "alice@example.com"),
        _make_row(2, "Bob", "bob@example.com"),
    ]
    mock_get_db.return_value = mock_db

    from app.services.user_service import get_all_users
    result = get_all_users()

    assert len(result) == 2
    assert result[0]["name"] == "Alice"


@patch("app.services.user_service.get_db")
def test_get_all_users_empty(mock_get_db):
    """get_all_users returns an empty list when the table is empty."""
    mock_db = MagicMock()
    mock_db.execute.return_value.fetchall.return_value = []
    mock_get_db.return_value = mock_db

    from app.services.user_service import get_all_users
    assert get_all_users() == []


# ---------------------------------------------------------------------------
# get_user_by_id
# ---------------------------------------------------------------------------

@patch("app.services.user_service.get_db")
def test_get_user_by_id_found(mock_get_db):
    """get_user_by_id returns the user when it exists."""
    mock_db = MagicMock()
    mock_db.execute.return_value.fetchone.return_value = _make_row(1, "Alice", "alice@example.com")
    mock_get_db.return_value = mock_db

    from app.services.user_service import get_user_by_id
    user = get_user_by_id(1)

    assert user is not None
    assert user["email"] == "alice@example.com"


@patch("app.services.user_service.get_db")
def test_get_user_by_id_not_found(mock_get_db):
    """get_user_by_id returns None when the user does not exist."""
    mock_db = MagicMock()
    mock_db.execute.return_value.fetchone.return_value = None
    mock_get_db.return_value = mock_db

    from app.services.user_service import get_user_by_id
    assert get_user_by_id(999) is None


# ---------------------------------------------------------------------------
# create_user validation
# ---------------------------------------------------------------------------

@patch("app.services.user_service.get_db")
def test_create_user_raises_on_blank_name(mock_get_db):
    """create_user raises ValueError when name is blank."""
    from app.services.user_service import create_user
    with pytest.raises(ValueError, match="name is required"):
        create_user("", "valid@example.com")


@patch("app.services.user_service.get_db")
def test_create_user_raises_on_blank_email(mock_get_db):
    """create_user raises ValueError when email is blank."""
    from app.services.user_service import create_user
    with pytest.raises(ValueError, match="email is required"):
        create_user("Alice", "")


# ---------------------------------------------------------------------------
# delete_user
# ---------------------------------------------------------------------------

@patch("app.services.user_service.get_db")
@patch("app.services.user_service.get_user_by_id", return_value=None)
def test_delete_user_not_found(mock_get_by_id, mock_get_db):
    """delete_user returns False when the user does not exist."""
    from app.services.user_service import delete_user
    assert delete_user(999) is False


@patch("app.services.user_service.get_db")
@patch(
    "app.services.user_service.get_user_by_id",
    return_value={"id": 1, "name": "Alice", "email": "alice@example.com"},
)
def test_delete_user_existing(mock_get_by_id, mock_get_db):
    """delete_user returns True and executes DELETE when user exists."""
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db

    from app.services.user_service import delete_user
    result = delete_user(1)

    assert result is True
    mock_db.execute.assert_called_once()
    mock_db.commit.assert_called_once()
