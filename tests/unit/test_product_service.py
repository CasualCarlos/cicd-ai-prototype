"""Unit tests for product_service — the DB is mocked so these run fast."""

from unittest.mock import MagicMock, patch
import pytest


def _make_row(id, name, price, description=None):
    return {"id": id, "name": name, "price": price, "description": description}


# ---------------------------------------------------------------------------
# get_all_products
# ---------------------------------------------------------------------------

@patch("app.services.product_service.get_db")
def test_get_all_products_returns_list(mock_get_db):
    """get_all_products returns all rows from the DB."""
    mock_db = MagicMock()
    mock_db.execute.return_value.fetchall.return_value = [
        _make_row(1, "Widget", 9.99),
        _make_row(2, "Gadget", 19.99, "A cool gadget"),
    ]
    mock_get_db.return_value = mock_db

    from app.services.product_service import get_all_products
    result = get_all_products()

    assert len(result) == 2
    assert result[1]["name"] == "Gadget"


@patch("app.services.product_service.get_db")
def test_get_all_products_empty(mock_get_db):
    """get_all_products returns an empty list when table is empty."""
    mock_db = MagicMock()
    mock_db.execute.return_value.fetchall.return_value = []
    mock_get_db.return_value = mock_db

    from app.services.product_service import get_all_products
    assert get_all_products() == []


# ---------------------------------------------------------------------------
# get_product_by_id
# ---------------------------------------------------------------------------

@patch("app.services.product_service.get_db")
def test_get_product_by_id_found(mock_get_db):
    """get_product_by_id returns the product dict when found."""
    mock_db = MagicMock()
    mock_db.execute.return_value.fetchone.return_value = _make_row(1, "Widget", 9.99)
    mock_get_db.return_value = mock_db

    from app.services.product_service import get_product_by_id
    product = get_product_by_id(1)

    assert product is not None
    assert product["price"] == 9.99


@patch("app.services.product_service.get_db")
def test_get_product_by_id_not_found(mock_get_db):
    """get_product_by_id returns None when product does not exist."""
    mock_db = MagicMock()
    mock_db.execute.return_value.fetchone.return_value = None
    mock_get_db.return_value = mock_db

    from app.services.product_service import get_product_by_id
    assert get_product_by_id(999) is None


# ---------------------------------------------------------------------------
# create_product validation
# ---------------------------------------------------------------------------

@patch("app.services.product_service.get_db")
def test_create_product_raises_on_blank_name(mock_get_db):
    """create_product raises ValueError when name is blank."""
    from app.services.product_service import create_product
    with pytest.raises(ValueError, match="name is required"):
        create_product("", 9.99)


@patch("app.services.product_service.get_db")
def test_create_product_raises_on_invalid_price(mock_get_db):
    """create_product raises ValueError when price is not a number."""
    from app.services.product_service import create_product
    with pytest.raises(ValueError, match="price must be a number"):
        create_product("Widget", "free")


@patch("app.services.product_service.get_db")
def test_create_product_raises_on_negative_price(mock_get_db):
    """create_product raises ValueError when price is negative."""
    from app.services.product_service import create_product
    with pytest.raises(ValueError, match="price must be non-negative"):
        create_product("Widget", -1.0)


# ---------------------------------------------------------------------------
# delete_product
# ---------------------------------------------------------------------------

@patch("app.services.product_service.get_db")
@patch("app.services.product_service.get_product_by_id", return_value=None)
def test_delete_product_not_found(mock_get_by_id, mock_get_db):
    """delete_product returns False when the product does not exist."""
    from app.services.product_service import delete_product
    assert delete_product(999) is False
