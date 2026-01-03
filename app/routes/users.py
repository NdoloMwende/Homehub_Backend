from flask import Blueprint, jsonify
from app.models import User
from app import db

bp = Blueprint("users", __name__)
@bp.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "users_count": User.query.count()})

@bp.route("/", methods=["GET"])
def get_users():
    users = User.query.all()
    return jsonify([{
        "id": u.id,
        "full_name": u.full_name,
        "email": u.email,
        "role": u.role,
        "phone": u.phone
    } for u in users])
