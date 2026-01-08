from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import Property, User

properties_bp = Blueprint('properties', __name__)

@properties_bp.route('', methods=['GET'])
def get_all_properties():
    """
    Get all approved properties
    ---
    """
    # properties = Property.query.filter_by(status='approved').all()
    properties = Property.query.all()
    return jsonify([prop.to_dict() for prop in properties]), 200

@properties_bp.route('', methods=['POST'])
@jwt_required()
def create_property():
    """
    Create new property (Landlord only)
    ---
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          properties:
            name:
              type: string
            address:
              type: string
            city:
              type: string
            country:
              type: string
            description:
              type: string
            image_url:
              type: string
            evidence_of_ownership:
              type: string
            lrn_no:
              type: string
            location:
              type: string
    """
    current_user = User.query.get(get_jwt_identity())
    if current_user.role != 'landlord':
        return jsonify({'error': 'Only landlords can create properties'}), 403
    
    data = request.get_json()
    
    required_fields = ['name', 'address', 'city', 'country']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    property = Property(
        landlord_id=current_user.id,
        name=data['name'],
        address=data['address'],
        city=data['city'],
        country=data['country'],
        description=data.get('description'),
        image_url=data.get('image_url'),
        evidence_of_ownership=data.get('evidence_of_ownership'),
        lrn_no=data.get('lrn_no'),
        location=data.get('location'),
        status='pending'
    )
    
    db.session.add(property)
    db.session.commit()
    
    return jsonify({'message': 'Property created successfully', 'property': property.to_dict()}), 201

@properties_bp.route('/<property_id>', methods=['GET'])
def get_property(property_id):
    """
    Get property by ID
    ---
    parameters:
      - name: property_id
        in: path
        type: string
        required: true
    """
    property = Property.query.get(property_id)
    
    if not property:
        return jsonify({'error': 'Property not found'}), 404
    
    return jsonify(property.to_dict()), 200

@properties_bp.route('/<property_id>', methods=['PUT'])
@jwt_required()
def update_property(property_id):
    """
    Update property (Landlord owner only)
    ---
    security:
      - Bearer: []
    parameters:
      - name: property_id
        in: path
        type: string
        required: true
      - name: body
        in: body
        schema:
          properties:
            name:
              type: string
            address:
              type: string
            city:
              type: string
            country:
              type: string
            description:
              type: string
            image_url:
              type: string
    """
    current_user = User.query.get(get_jwt_identity())
    property = Property.query.get(property_id)
    
    if not property:
        return jsonify({'error': 'Property not found'}), 404
    
    if property.landlord_id != current_user.id and current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    if 'name' in data:
        property.name = data['name']
    if 'address' in data:
        property.address = data['address']
    if 'city' in data:
        property.city = data['city']
    if 'country' in data:
        property.country = data['country']
    if 'description' in data:
        property.description = data['description']
    if 'image_url' in data:
        property.image_url = data['image_url']
    
    db.session.commit()
    
    return jsonify({'message': 'Property updated successfully', 'property': property.to_dict()}), 200

@properties_bp.route('/<property_id>/approve', methods=['POST'])
@jwt_required()
def approve_property(property_id):
    """
    Approve property (Admin only)
    ---
    security:
      - Bearer: []
    parameters:
      - name: property_id
        in: path
        type: string
        required: true
      - name: body
        in: body
        schema:
          properties:
            comment:
              type: string
    """
    current_user = User.query.get(get_jwt_identity())
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    property = Property.query.get(property_id)
    if not property:
        return jsonify({'error': 'Property not found'}), 404
    
    data = request.get_json() or {}
    property.status = 'approved'
    property.comment = data.get('comment')
    
    db.session.commit()
    
    return jsonify({'message': 'Property approved successfully', 'property': property.to_dict()}), 200

@properties_bp.route('/<property_id>/reject', methods=['POST'])
@jwt_required()
def reject_property(property_id):
    """
    Reject property (Admin only)
    ---
    security:
      - Bearer: []
    parameters:
      - name: property_id
        in: path
        type: string
        required: true
      - name: body
        in: body
        schema:
          properties:
            comment:
              type: string
    """
    current_user = User.query.get(get_jwt_identity())
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    property = Property.query.get(property_id)
    if not property:
        return jsonify({'error': 'Property not found'}), 404
    
    data = request.get_json() or {}
    property.status = 'rejected'
    property.comment = data.get('comment')
    
    db.session.commit()
    
    return jsonify({'message': 'Property rejected', 'property': property.to_dict()}), 200

@properties_bp.route('/landlord/<landlord_id>', methods=['GET'])
def get_landlord_properties(landlord_id):
    """
    Get all properties for a landlord
    ---
    parameters:
      - name: landlord_id
        in: path
        type: string
        required: true
    """
    properties = Property.query.filter_by(landlord_id=landlord_id).all()
    return jsonify([prop.to_dict() for prop in properties]), 200
