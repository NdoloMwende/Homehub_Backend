import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from extensions import db
from models import Property, PropertyImage, Unit, User

properties_bp = Blueprint('properties', __name__)

# Allowed image extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- 1. CREATE PROPERTY (With Admin Verification Logic) ---
@properties_bp.route('/', methods=['POST'])
@jwt_required()
def create_property():
    try:
        current_user_id = get_jwt_identity()
        
        # 1. Check if user is a VALID Landlord
        landlord = User.query.get(current_user_id)
        if landlord.role != 'landlord':
            return jsonify({'error': 'Only landlords can list properties'}), 403
        if landlord.status != 'active':
            return jsonify({'error': 'You must be a verified landlord to list properties'}), 403

        # 2. Handle Text Data
        data = request.form
        
        # 3. Handle Main Image
        if 'image' not in request.files:
            return jsonify({'error': 'Main property image is required'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No image selected'}), 400
            
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            # In production, you would upload to Cloudinary here
            image_url = f"https://homehub-project.onrender.com/uploads/{filename}"
        else:
            return jsonify({'error': 'Invalid file type'}), 400

        # 4. 🟢 CRITICAL FIX: Set status to 'pending'
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
            status='pending'  # <--- Forces Admin Approval
        )
        
        db.session.add(new_property)
        db.session.commit() # Commit to get ID for gallery images

        # 5. Handle Extra Gallery Images
        files = request.files.getlist('extra_images')
        for f in files:
            if f and allowed_file(f.filename):
                fname = secure_filename(f"{uuid.uuid4()}_{f.filename}")
                f.save(os.path.join(current_app.config['UPLOAD_FOLDER'], fname))
                extra_url = f"https://homehub-project.onrender.com/uploads/{fname}"
                
                gallery_img = PropertyImage(property_id=new_property.id, image_url=extra_url)
                db.session.add(gallery_img)
        
        db.session.commit()

        return jsonify({
            'message': 'Property submitted for review. An Admin will approve it shortly.',
            'property': new_property.to_dict()
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- 2. GET ALL PROPERTIES (Public Marketplace) ---
@properties_bp.route('/', methods=['GET'])
def get_properties():
    # Only show APPROVED properties to the public
    properties = Property.query.filter_by(status='approved').all()
    # (Or 'Available' if you use that status in your seed, but 'approved' is safer for new logic)
    
    # Fallback: If your seed data uses 'Available' and you want to show those too:
    # properties = Property.query.filter(Property.status.in_(['approved', 'Available'])).all()
    
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
    # Landlords should see ALL their properties, even pending ones
    properties = Property.query.filter_by(landlord_id=current_user_id).all()
    return jsonify([p.to_dict() for p in properties]), 200