from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import Property, User, PropertyImage
from werkzeug.utils import secure_filename
import os

properties_bp = Blueprint('properties', __name__)

# --- 🔍 DEBUGGER: Print everything coming in ---
@properties_bp.before_request
def log_request_info():
    if request.method == 'POST':
        print(f"🔹 [DEBUG] Headers: {request.headers}")
        print(f"🔹 [DEBUG] Form Data: {request.form}")
        print(f"🔹 [DEBUG] Files: {request.files}")

# --- CREATE PROPERTY (Robust) ---
@properties_bp.route('', methods=['POST'])
@jwt_required()
def create_property():
    try:
        current_user_id = get_jwt_identity()
        print(f"✅ [DEBUG] User Identified: {current_user_id}")

        # 1. SMART DATA EXTRACTION
        # Try to get data from Form (Multipart) OR JSON
        data = {}
        if request.content_type and 'multipart/form-data' in request.content_type:
            data = request.form.to_dict() # Convert to regular dict
        else:
            data = request.get_json(silent=True) or {}

        print(f"🔹 [DEBUG] Extracted Data: {data}")

        # 2. VALIDATION (Accept 'title' OR 'name')
        title = data.get('name') or data.get('title')
        price = data.get('price')

        if not title or not price:
            print("❌ [ERROR] Missing Title or Price")
            return jsonify({'error': 'Title and Price are required'}), 400

        # 3. CREATE PROPERTY OBJECT
        new_property = Property(
            landlord_id=current_user_id,
            name=title,
            description=data.get('description', ''),
            address=data.get('address', ''),
            city=data.get('city', ''),
            state=data.get('state', ''),
            price=float(price) if price else 0.0,
            bedrooms=int(data.get('bedrooms', 0)) if data.get('bedrooms') else 0,
            bathrooms=int(data.get('bathrooms', 0)) if data.get('bathrooms') else 0,
            square_feet=int(data.get('square_feet', 0)) if data.get('square_feet') else 0,
            property_type=data.get('property_type', 'apartment'),
            status='Available' 
        )

        # 4. HANDLE MAIN IMAGE
        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                filename = secure_filename(file.filename)
                # Ensure upload folder exists
                upload_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                
                file.save(os.path.join(upload_dir, filename))
                new_property.image_url = f"/uploads/{filename}"
                print(f"✅ [DEBUG] Saved Main Image: {filename}")

        db.session.add(new_property)
        db.session.commit()

        # 5. HANDLE GALLERY IMAGES
        if 'gallery_images' in request.files:
            gallery_files = request.files.getlist('gallery_images')
            for file in gallery_files:
                if file.filename == '': continue
                
                filename = secure_filename(file.filename)
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                
                new_image = PropertyImage(
                    property_id=new_property.id,
                    image_url=f"/uploads/{filename}"
                )
                db.session.add(new_image)
            db.session.commit()
            print(f"✅ [DEBUG] Saved {len(gallery_files)} Gallery Images")

        return jsonify({'message': 'Property created!', 'property': new_property.to_dict()}), 201

    except Exception as e:
        print(f"❌ [CRITICAL ERROR]: {str(e)}")
        # Return 500 with the specific error so we can fix it
        return jsonify({'error': str(e)}), 500

# --- KEEP OTHER ROUTES ---
@properties_bp.route('', methods=['GET'])
def get_all_properties():
    properties = Property.query.all()
    return jsonify([prop.to_dict() for prop in properties]), 200

@properties_bp.route('/<property_id>', methods=['GET'])
def get_property(property_id):
    property = Property.query.get(property_id)
    if not property: return jsonify({'error': 'Property not found'}), 404
    return jsonify(property.to_dict()), 200

@properties_bp.route('/landlord/<landlord_id>', methods=['GET'])
def get_landlord_properties(landlord_id):
    properties = Property.query.filter_by(landlord_id=landlord_id).all()
    return jsonify([prop.to_dict() for prop in properties]), 200