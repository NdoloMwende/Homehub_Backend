from flask import Blueprint, request, jsonify, abort
from app.models.property import Property
from app import db

properties_bp = Blueprint("properties", __name__)

# GET ALL PROPERTIES
@properties_bp.route("", methods=["GET"])
def get_properties():
    properties = Property.query.all()
    return jsonify(properties=[p.to_dict() for p in properties])

# GET PROPERTY BY ID
@properties_bp.route("/<int:property_id>", methods=["GET"])
def get_property(property_id):
    prop = Property.query.get_or_404(property_id)
    return jsonify(prop.to_dict())

# CREATE PROPERTY
@properties_bp.route("", methods=["POST"])
def create_property():
    data = request.get_json()
    required_fields = ["landlord_id", "name"]
    for field in required_fields:
        if field not in data:
            abort(400, f"{field} is required")

    prop = Property(
        landlord_id=data["landlord_id"],
        name=data["name"],
        address=data.get("address"),
        city=data.get("city"),
        country=data.get("country"),
        description=data.get("description"),
        image_url=data.get("image_url"),
        status=data.get("status", "pending"),
        comment=data.get("comment"),
        evidence_of_ownership=data.get("evidence_of_ownership"),
        lrn_no=data.get("lrn_no"),
        location=data.get("location")
    )
    db.session.add(prop)
    db.session.commit()
    return jsonify(prop.to_dict()), 201

# UPDATE PROPERTY
@properties_bp.route("/<int:property_id>", methods=["PATCH"])
def update_property(property_id):
    prop = Property.query.get_or_404(property_id)
    data = request.get_json()
    for field, value in data.items():
        if hasattr(prop, field):
            setattr(prop, field, value)
    db.session.commit()
    return jsonify(prop.to_dict())

# DELETE PROPERTY
@properties_bp.route("/<int:property_id>", methods=["DELETE"])
def delete_property(property_id):
    prop = Property.query.get_or_404(property_id)
    db.session.delete(prop)
    db.session.commit()
    return jsonify({"message": "Property deleted"})
