from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import Property, User, PropertyImage, Unit # 👈 Added Unit import
from werkzeug.utils import secure_filename
import os

properties_bp = Blueprint('properties', __name__)

# --- 1. GET ALL (Marketplace) ---
@properties_bp.route('', methods=['GET'])
def get_all_properties():
    """ Get all properties for the public marketplace """
    try:
        properties = Property.query.all()
        return jsonify([prop.to_dict() for prop in properties]), 200
    except Exception as e:
        print(f"Error fetching properties: {e}")
        return jsonify({'error': 'Failed to fetch properties'}), 500

# --- 2. CREATE (Landlord Only) ---
@properties_bp.route('', methods=['POST'])
@jwt_required()
def create_property():
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        # Get Form Data
        data = request.form 
        
        # Validation
        title = data.get('name') or data.get('title')
        price = data.get('price')

        if not title or not price:
            return jsonify({'error': 'Title and Price are required'}), 400

        # Create Property Object
        new_property = Property(
            landlord_id=current_user_id,
            name=title,
            description=data.get('description', ''),
            address=data.get('address', ''),
            city=data.get('city', ''),
            country=data.get('country', 'Kenya'), # 🟢 Fix 1: Default to Kenya
            state=data.get('state', ''), 
            location=data.get('location', ''),
            price=float(price) if price else 0.0,
            bedrooms=int(data.get('bedrooms', 0)) if data.get('bedrooms') else 0,
            bathrooms=int(data.get('bathrooms', 0)) if data.get('bathrooms') else 0,
            square_feet=int(data.get('square_feet', 0)) if data.get('square_feet') else 0,
            property_type=data.get('property_type', 'apartment'),
            amenities=data.get('amenities', ''),
            status='Available' 
        )

        # Handle Main Image
        main_image = request.files.get('image')
        if main_image:
            filename = secure_filename(main_image.filename)
            upload_folder = current_app.config['UPLOAD_FOLDER']
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            
            save_path = os.path.join(upload_folder, filename)
            main_image.save(save_path)
            new_property.image_url = f"/uploads/{filename}"

        # Commit Property first to get ID
        db.session.add(new_property)
        db.session.commit()

        # 🟢 Fix 2: Auto-Create a Unit so Leasing works
        new_unit = Unit(
            property_id=new_property.id,
            unit_number="Main Unit", # Default name
            rent_amount=new_property.price,
            status='vacant'
        )
        db.session.add(new_unit)

        # Handle Gallery Images
        gallery_files = request.files.getlist('gallery_images')
        for file in gallery_files:
            if file.filename == '': continue
            
            filename = secure_filename(file.filename)
            save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            
            new_image = PropertyImage(
                property_id=new_property.id,
                image_url=f"/uploads/{filename}"
            )
            db.session.add(new_image)

        db.session.commit()
        
        print(f"✅ Property '{title}' and Unit created successfully!")
        return jsonify({'message': 'Property created successfully', 'property': new_property.to_dict()}), 201

    except Exception as e:
        print(f"❌ CRITICAL ERROR in create_property: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

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
    current_user_id = get_jwt_identity()
    property = Property.query.get(property_id)
    
    if not property:
        return jsonify({'error': 'Property not found'}), 404
    
    current_user = User.query.get(current_user_id)
    if property.landlord_id != current_user_id and current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json() or {}
    
    if 'title' in data: property.name = data['title']
    if 'name' in data: property.name = data['name']
    if 'price' in data: property.price = data['price']
    if 'description' in data: property.description = data['description']

    db.session.commit()
    return jsonify({'message': 'Property updated successfully', 'property': property.to_dict()}), 200

# --- 5. DELETE (My Properties Page) ---
@properties_bp.route('/<property_id>', methods=['DELETE'])
@jwt_required()
def delete_property(property_id):
    current_user_id = get_jwt_identity()
    property = Property.query.get(property_id)

    if not property:
        return jsonify({'error': 'Property not found'}), 404

    current_user = User.query.get(current_user_id)
    if property.landlord_id != current_user_id and current_user.role != 'admin':
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
    
    property.status = 'approved'
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
    
    property.status = 'rejected'
    db.session.commit()
    return jsonify({'message': 'Property rejected', 'property': property.to_dict()}), 200

# --- 7. GET LANDLORD PROPERTIES (My Properties Page) ---
@properties_bp.route('/landlord/<landlord_id>', methods=['GET'])
def get_landlord_properties(landlord_id):
    properties = Property.query.filter_by(landlord_id=landlord_id).all()
    return jsonify([prop.to_dict() for prop in properties]), 200