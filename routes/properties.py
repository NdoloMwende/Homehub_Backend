from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import Property, User

properties_bp = Blueprint('properties', __name__)

# --- 1. GET ALL (Marketplace) ---
@properties_bp.route('', methods=['GET'])
def get_all_properties():
    """ Get all properties for the public marketplace """
    # Optionally filter by status='approved' if you want strictly vetted listings
    # properties = Property.query.filter_by(status='approved').all()
    properties = Property.query.all()
    return jsonify([prop.to_dict() for prop in properties]), 200

# --- 2. CREATE (Landlord Only) ---
@properties_bp.route('', methods=['POST'])
@jwt_required()
def create_property():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if not current_user or current_user.role != 'landlord':
        return jsonify({'error': 'Only landlords can create properties'}), 403

    data = request.get_json()
    
    # Validation (Basic)
    if not data.get('title') or not data.get('price'):
        return jsonify({'error': 'Title and Price are required'}), 400

    new_property = Property(
        landlord_id=current_user.id,
        name=data.get('title'),    # Map 'title' to 'name'
        address=data.get('address'),
        city=data.get('city'),
        country='Kenya',
        state=data.get('state'),
        description=data.get('description'),
        
        # New Rental Details
        price=data.get('price'),
        bedrooms=data.get('bedrooms'),
        bathrooms=data.get('bathrooms'),
        square_feet=data.get('square_feet'),
        property_type=data.get('property_type'),
        amenities=data.get('amenities'), # Store as string
        image_url=data.get('image_url'),
        
        status='pending' 
    )
    
    db.session.add(new_property)
    db.session.commit()
    
    return jsonify({'message': 'Property created successfully', 'property': new_property.to_dict()}), 201

# --- 3. GET SINGLE (Details Page) ---
@properties_bp.route('/<property_id>', methods=['GET'])
def get_property(property_id):
    property = Property.query.get(property_id)
    if not property:
        return jsonify({'error': 'Property not found'}), 404
    return jsonify(property.to_dict()), 200

# --- 4. UPDATE (Edit Page) ---
@properties_bp.route('/<property_id>', methods=['PUT'])
@jwt_required()
def update_property(property_id):
    current_user = User.query.get(get_jwt_identity())
    property = Property.query.get(property_id)
    
    if not property:
        return jsonify({'error': 'Property not found'}), 404
    
    # Security: Only Owner or Admin can edit
    if property.landlord_id != current_user.id and current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Update Basic Fields
    if 'title' in data: property.name = data['title']
    if 'address' in data: property.address = data['address']
    if 'city' in data: property.city = data['city']
    if 'state' in data: property.state = data['state']
    if 'description' in data: property.description = data['description']
    if 'image_url' in data: property.image_url = data['image_url']
    
    # Update Rental Details (NEW)
    if 'price' in data: property.price = data['price']
    if 'bedrooms' in data: property.bedrooms = data['bedrooms']
    if 'bathrooms' in data: property.bathrooms = data['bathrooms']
    if 'square_feet' in data: property.square_feet = data['square_feet']
    if 'property_type' in data: property.property_type = data['property_type']
    if 'amenities' in data: property.amenities = data['amenities']

    db.session.commit()
    
    return jsonify({'message': 'Property updated successfully', 'property': property.to_dict()}), 200

# --- 5. DELETE (My Properties Page) ---
@properties_bp.route('/<property_id>', methods=['DELETE'])
@jwt_required()
def delete_property(property_id):
    current_user = User.query.get(get_jwt_identity())
    property = Property.query.get(property_id)

    if not property:
        return jsonify({'error': 'Property not found'}), 404

    # Security: Only Owner or Admin can delete
    if property.landlord_id != current_user.id and current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    db.session.delete(property)
    db.session.commit()

    return jsonify({'message': 'Property deleted successfully'}), 200

# --- 6. APPROVE/REJECT (Admin Dashboard) ---
@properties_bp.route('/<property_id>/approve', methods=['POST'])
@jwt_required()
def approve_property(property_id):
    current_user = User.query.get(get_jwt_identity())
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    property = Property.query.get(property_id)
    if not property: return jsonify({'error': 'Property not found'}), 404
    
    data = request.get_json() or {}
    property.status = 'approved'
    property.comment = data.get('comment')
    db.session.commit()
    return jsonify({'message': 'Property approved', 'property': property.to_dict()}), 200

@properties_bp.route('/<property_id>/reject', methods=['POST'])
@jwt_required()
def reject_property(property_id):
    current_user = User.query.get(get_jwt_identity())
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    property = Property.query.get(property_id)
    if not property: return jsonify({'error': 'Property not found'}), 404
    
    data = request.get_json() or {}
    property.status = 'rejected'
    property.comment = data.get('comment')
    db.session.commit()
    return jsonify({'message': 'Property rejected', 'property': property.to_dict()}), 200

# --- 7. GET LANDLORD PROPERTIES (My Properties Page) ---
@properties_bp.route('/landlord/<landlord_id>', methods=['GET'])
def get_landlord_properties(landlord_id):
    properties = Property.query.filter_by(landlord_id=landlord_id).all()
    return jsonify([prop.to_dict() for prop in properties]), 200