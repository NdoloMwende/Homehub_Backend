from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import Unit, Property, User

units_bp = Blueprint('units', __name__)

@units_bp.route('', methods=['GET'])
def get_all_units():
    """
    Get all units
    ---
    """
    units = Unit.query.all()
    return jsonify([unit.to_dict() for unit in units]), 200

@units_bp.route('', methods=['POST'])
@jwt_required()
def create_unit():
    """
    Create new unit (Landlord owner only)
    ---
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          properties:
            property_id:
              type: string
            unit_number:
              type: string
            floor_number:
              type: string
            rent_amount:
              type: number
    """
    current_user = User.query.get(get_jwt_identity())
    data = request.get_json()
    
    property = Property.query.get(data.get('property_id'))
    if not property:
        return jsonify({'error': 'Property not found'}), 404
    
    if property.landlord_id != current_user.id and current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    required_fields = ['property_id', 'unit_number', 'rent_amount']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    unit = Unit(
        property_id=data['property_id'],
        unit_number=data['unit_number'],
        floor_number=data.get('floor_number'),
        rent_amount=data['rent_amount'],
        status='vacant'
    )
    
    db.session.add(unit)
    db.session.commit()
    
    return jsonify({'message': 'Unit created successfully', 'unit': unit.to_dict()}), 201

@units_bp.route('/<unit_id>', methods=['GET'])
def get_unit(unit_id):
    """
    Get unit by ID
    ---
    parameters:
      - name: unit_id
        in: path
        type: string
        required: true
    """
    unit = Unit.query.get(unit_id)
    
    if not unit:
        return jsonify({'error': 'Unit not found'}), 404
    
    return jsonify(unit.to_dict()), 200

@units_bp.route('/<unit_id>', methods=['PUT'])
@jwt_required()
def update_unit(unit_id):
    """
    Update unit
    ---
    security:
      - Bearer: []
    parameters:
      - name: unit_id
        in: path
        type: string
        required: true
      - name: body
        in: body
        schema:
          properties:
            unit_number:
              type: string
            floor_number:
              type: string
            rent_amount:
              type: number
            status:
              type: string
    """
    current_user = User.query.get(get_jwt_identity())
    unit = Unit.query.get(unit_id)
    
    if not unit:
        return jsonify({'error': 'Unit not found'}), 404
    
    property = unit.property
    if property.landlord_id != current_user.id and current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    if 'unit_number' in data:
        unit.unit_number = data['unit_number']
    if 'floor_number' in data:
        unit.floor_number = data['floor_number']
    if 'rent_amount' in data:
        unit.rent_amount = data['rent_amount']
    if 'status' in data:
        unit.status = data['status']
    
    db.session.commit()
    
    return jsonify({'message': 'Unit updated successfully', 'unit': unit.to_dict()}), 200

@units_bp.route('/property/<property_id>', methods=['GET'])
def get_property_units(property_id):
    """
    Get all units for a property
    ---
    parameters:
      - name: property_id
        in: path
        type: string
        required: true
    """
    units = Unit.query.filter_by(property_id=property_id).all()
    return jsonify([unit.to_dict() for unit in units]), 200
