import os
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Property, PropertyImage, User

# 🟢 NEW: Cloudinary Imports
import cloudinary
import cloudinary.uploader
import cloudinary.api

properties_bp = Blueprint('properties', __name__)

# 🟢 NEW: Configure Cloudinary
cloudinary.config( 
  cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME'), 
  api_key = os.getenv('CLOUDINARY_API_KEY'), 
  api_secret = os.getenv('CLOUDINARY_API_SECRET') 
)

# Allowed image extensions (Basic validation)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- 1. CREATE PROPERTY (Cloudinary + Admin Verification) ---
@properties_bp.route('/', methods=['POST'])
@jwt_required()
def create_property():
    try:
        current_user_id = get_jwt_identity()
        
        # 1. Validate Landlord
        landlord = User.query.get(current_user_id)
        if landlord.role != 'landlord':
            return jsonify({'error': 'Only landlords can list properties'}), 403
        if landlord.status != 'active':
            return jsonify({'error': 'You must be a verified landlord to list properties'}), 403

        # 2. Get Text Data
        data = request.form
        
        # 3. 🟢 NEW: Upload Main Image to Cloudinary
        if 'image' not in request.files:
            return jsonify({'error': 'Main property image is required'}), 400
        
        file = request.files['image']
        
        if file and allowed_file(file.filename):
            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(file)
            image_url = upload_result['secure_url'] # <--- The Permanent Cloud URL
        else:
            return jsonify({'error': 'Invalid file type or no file'}), 400

        # 4. Create Property (Status = Pending for Admin Review)
        new_property = Property(
            landlord_id=current_user_id,
            name=data['name'],
            description=data['description'],
            address=data['address'],
            city=data['city'],
            price=float(data['price']),
            bedrooms=int(data['bedrooms']),
            bathrooms=int(data['bathrooms']),
            image_url=image_url,
            status='pending'  # <--- Admin must approve this!
        )
        
        db.session.add(new_property)
        db.session.commit()

        # 5. 🟢 NEW: Upload Extra Gallery Images to Cloudinary
        files = request.files.getlist('extra_images')
        for f in files:
            if f and allowed_file(f.filename):
                # Upload each extra image to Cloudinary
                res = cloudinary.uploader.upload(f)
                extra_url = res['secure_url']
                
                gallery_img = PropertyImage(property_id=new_property.id, image_url=extra_url)
                db.session.add(gallery_img)
        
        db.session.commit()

        return jsonify({
            'message': 'Property submitted for review. An Admin will approve it shortly.',
            'property': new_property.to_dict()
        }), 201

    except Exception as e:
        print("Upload Error:", e)
        return jsonify({'error': str(e)}), 500

# --- 2. GET ALL PROPERTIES (Public Marketplace) ---
@properties_bp.route('/', methods=['GET'])
def get_properties():
    # Only show APPROVED properties
    properties = Property.query.filter_by(status='approved').all()
    return jsonify([p.to_dict() for p in properties]), 200

# --- 3. GET SINGLE PROPERTY ---
@properties_bp.route('/<property_id>', methods=['GET'])
def get_property(property_id):
    prop = Property.query.get(property_id)
    if not prop: return jsonify({'error': 'Property not found'}), 404
    return jsonify(prop.to_dict()), 200

# --- 4. LANDLORD: GET MY PROPERTIES ---
@properties_bp.route('/my-properties', methods=['GET'])
@jwt_required()
def get_my_properties():
    current_user_id = get_jwt_identity()
    # Landlords see ALL their properties (pending, rejected, approved)
    properties = Property.query.filter_by(landlord_id=current_user_id).all()
    return jsonify([p.to_dict() for p in properties]), 200
    