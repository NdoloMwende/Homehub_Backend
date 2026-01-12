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
    current_user_id = get_jwt_identity() # This returns the UUID string
    
    # Fetch user object to check role
    current_user = User.query.get(current_user_id)
    
    if not current_user or current_user.role != 'landlord':
        return jsonify({'error': 'Only landlords can create properties'}), 403

    data = request.get_json()
    
    # Create Property with UUIDs and New Fields
    new_property = Property(
        landlord_id=current_user.id,
        name=data.get('title'),    # Map 'title' from frontend to 'name' in DB
        address=data.get('address'),
        city=data.get('city'),
        country='Kenya',           # Default
        state=data.get('state'),
        description=data.get('description'),
        
        # New Rental Details
        price=data.get('price'),
        bedrooms=data.get('bedrooms'),
        bathrooms=data.get('bathrooms'),
        square_feet=data.get('square_feet'),
        property_type=data.get('property_type'),
        image_url=data.get('image_url'),
        
        status='pending' 
    )
    
    db.session.add(new_property)
    db.session.commit()
    
    return jsonify({'message': 'Property created successfully', 'property': new_property.to_dict()}), 201

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
