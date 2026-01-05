from flask import Blueprint, request, jsonify, abort
from app.models.unit import Unit
from app import db

units_bp = Blueprint("units", __name__)

# GET ALL UNITS
@units_bp.route("", methods=["GET"])
def get_units():
    units = Unit.query.all()
    return jsonify(units=[u.to_dict() for u in units])

# GET UNIT BY ID
@units_bp.route("/<int:unit_id>", methods=["GET"])
def get_unit(unit_id):
    unit = Unit.query.get_or_404(unit_id)
    return jsonify(unit.to_dict())

# CREATE UNIT
@units_bp.route("", methods=["POST"])
def create_unit():
    data = request.get_json()
    required_fields = ["property_id", "unit_number"]
    for field in required_fields:
        if field not in data:
            abort(400, f"{field} is required")

    unit = Unit(
        property_id=data["property_id"],
        unit_number=data["unit_number"],
        floor_number=data.get("floor_number"),
        rent_amount=data.get("rent_amount"),
        status=data.get("status", "available")
    )
    db.session.add(unit)
    db.session.commit()
    return jsonify(unit.to_dict()), 201

# UPDATE UNIT
@units_bp.route("/<int:unit_id>", methods=["PATCH"])
def update_unit(unit_id):
    unit = Unit.query.get_or_404(unit_id)
    data = request.get_json()
    for field, value in data.items():
        if hasattr(unit, field):
            setattr(unit, field, value)
    db.session.commit()
    return jsonify(unit.to_dict())

# DELETE UNIT
@units_bp.route("/<int:unit_id>", methods=["DELETE"])
def delete_unit(unit_id):
    unit = Unit.query.get_or_404(unit_id)
    db.session.delete(unit)
    db.session.commit()
    return jsonify({"message": "Unit deleted"})
