from flask import Blueprint, request, jsonify, abort
from app.models.user import User
from app import db

users_bp = Blueprint("users", __name__)

# --------------------
# GET ALL USERS
# --------------------
@users_bp.route("", methods=["GET"])
def get_users():
    users = User.query.all()
    return jsonify(users=[u.to_dict() for u in users])

# --------------------
# GET USER BY ID
# --------------------
@users_bp.route("/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

# --------------------
# CREATE USER
# --------------------
@users_bp.route("", methods=["POST"])
def create_user():
    data = request.get_json()

    required_fields = ["full_name", "email", "password_hash", "role"]
    for field in required_fields:
        if field not in data:
            abort(400, f"{field} is required")

    user = User(
        full_name=data["full_name"],
        email=data["email"],
        password_hash=data["password_hash"],
        role=data["role"],
        phone=data.get("phone"),
        profile_image_url=data.get("profile_image_url"),
        is_active=data.get("is_active", True),
        status=data.get("status"),
        show_welcome=data.get("show_welcome", True),
        comment=data.get("comment"),
        national_id=data.get("national_id"),
        kra_pin=data.get("kra_pin"),
        evidence_of_identity=data.get("evidence_of_identity")
    )

    db.session.add(user)
    db.session.commit()

    return jsonify(user.to_dict()), 201

# --------------------
# UPDATE USER (PATCH)
# --------------------
@users_bp.route("/<int:user_id>", methods=["PATCH"])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()

    for field, value in data.items():
        if hasattr(user, field):
            setattr(user, field, value)

    db.session.commit()
    return jsonify(user.to_dict())

# --------------------
# SOFT DELETE USER
# --------------------
@users_bp.route("/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = False
    db.session.commit()

    return jsonify({"message": "User deactivated"})
