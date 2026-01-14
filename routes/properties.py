from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import Property, User, PropertyImage # 👈 Added PropertyImage
from werkzeug.utils import secure_filename # 👈 Needed for file uploads
import os

properties_bp = Blueprint('properties', __name__)

# --- 1. GET ALL (Marketplace) ---
@properties_bp.route('', methods=['GET'])
def get_all_properties():
    """ Get all properties for the public marketplace """
    # Optionally filter by status='Available' or 'approved'
    properties = Property.query.all()
    return jsonify([prop.to_dict() for prop in properties]), 200

# --- 2. CREATE (Landlord Only) - UPDATED FOR IMAGES ---
@properties_bp.route('', methods=['POST'])
@jwt_required()
def create_property():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if not current_user or current_user.role != 'landlord':
        return jsonify({'error': 'Only landlords can create properties'}), 403

    # 1. Use request.form for Text Data (Because we are sending files too)
    data = request.form 
    
    # Validation (Basic)
    if not data.get('name') or not data.get('price'): # Changed 'title' to 'name' to match form
        return jsonify({'error': 'Name/Title and Price are required'}), 400

    new_property = Property(
        landlord_id=current_user.id,
        name=data.get('name'), 
        address=data.get('address'),
        city=data.get('city'),
        country=data.get('country', 'Kenya'),
        state=data.get('state'),
        description=data.get('description'),
        location=data.get('location'),
        
        # Rental Details
        price=float(data.get('price', 0)),
        bedrooms=int(data.get('bedrooms', 0)),
        bathrooms=int(data.get('bathrooms', 0)),
        square_feet=int(data.get('square_feet', 0)) if data.get('square_feet') else None,
        property_type=data.get('property_type', 'apartment'),
        amenities=data.get('amenities'), 
        
        status='Available' 
    )

    # 2. Handle Main Thumbnail (Single File)
    main_image = request.files.get('image')
    if main_image:
        filename = secure_filename(main_image.filename)
        # Ensure upload folder exists
        upload_folder = current_app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
            
        save_path = os.path.join(upload_folder, filename)
        main_image.save(save_path)
        
        # Save the URL (Relative path)
        new_property.image_url = f"/uploads/{filename}"

    # Commit first to generate the Property ID
    db.session.add(new_property)
    db.session.commit()

    # 3. Handle Gallery Images (Multiple Files)
    gallery_files = request.files.getlist('gallery_images')
    
    for file in gallery_files:
        if file.filename == '':
            continue
            
        filename = secure_filename(file.filename)
        save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)
        
        # Create PropertyImage record linked to this property
        new_image = PropertyImage(
            property_id=new_property.id,
            image_url=f"/uploads/{filename}"
        )
        db.session.add(new_image)

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
    
    # Update Rental Details
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