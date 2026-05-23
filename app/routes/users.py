"""User CRUD endpoints."""

from flask import Blueprint, jsonify, request

from app.services.user_service import (
    get_all_users,
    get_user_by_id,
    create_user,
    update_user,
    delete_user,
)

users_bp = Blueprint("users", __name__)


@users_bp.route("/", methods=["GET"])
def list_users():
    return jsonify(get_all_users()), 200


@users_bp.route("/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = get_user_by_id(user_id)
    if user is None:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user), 200


@users_bp.route("/", methods=["POST"])
def create():
    data = request.get_json(silent=True) or {}
    try:
        user = create_user(data.get("name", ""), data.get("email", ""))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(user), 201


@users_bp.route("/<int:user_id>", methods=["PUT"])
def update(user_id):
    data = request.get_json(silent=True) or {}
    updated = update_user(user_id, data.get("name"), data.get("email"))
    if updated is None:
        return jsonify({"error": "User not found"}), 404
    return jsonify(updated), 200


@users_bp.route("/<int:user_id>", methods=["DELETE"])
def delete(user_id):
    deleted = delete_user(user_id)
    if not deleted:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"message": "User deleted"}), 200
