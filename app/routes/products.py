"""Product endpoints. (v2.0 — added search)"""

from flask import Blueprint, jsonify, request

from app.services.product_service import (
    get_all_products,
    get_product_by_id,
    create_product,
)

products_bp = Blueprint("products", __name__)


@products_bp.route("/", methods=["GET"])
def list_products():
    return jsonify(get_all_products()), 200


@products_bp.route("/<int:product_id>", methods=["GET"])
def get_product(product_id):
    product = get_product_by_id(product_id)
    if product is None:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(product), 200


@products_bp.route("/", methods=["POST"])
def create():
    data = request.get_json(silent=True) or {}
    try:
        product = create_product(
            data.get("name", ""),
            data.get("price"),
            data.get("description"),
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(product), 201
