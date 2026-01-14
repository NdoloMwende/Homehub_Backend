from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from extensions import db  # 🟢 Updated to use extensions
from models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # 1. Validate required fields
    if not data.get('email') or not data.get('password') or not data.get('full_name'):
        return jsonify({'error': 'Missing required fields'}), 400

    # 2. Check if email exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400

    # 3. Determine Role & Status
    role = data.get('role', 'tenant')
    status = 'active' # Default for tenants

    # --- 🔐 ADMIN SECRET CHECK 🔐 ---
    if data.get('admin_secret') == 'HomeHubAdmin2026':
        role = 'admin'
        status = 'active' 
    elif role == 'landlord':
        status = 'pending' # Landlords need verification
    # --------------------------------

    # 4. Create User with ALL model fields
    try:
        new_user = User(
            full_name=data['full_name'],
            email=data['email'],
            role=role,
            status=status,
            phone_number=data.get('phone_number') or data.get('phone'), # 🟢 Handles both naming styles
            national_id=data.get('national_id'), # 🟢 Added for verification
            kra_pin=data.get('kra_pin'),         # 🟢 Added for verification
            evidence_of_identity=data.get('evidence_of_identity')
        )
        new_user.set_password(data['password']) # Uses the helper method from models.py

        db.session.add(new_user)
        db.session.commit()

        return jsonify({'message': 'User registered successfully'}), 201
    except Exception as e:
        db.session.rollback()
        print(f"Registration Error: {str(e)}")
        return jsonify({'error': 'Registration failed. Ensure all fields are valid.'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # 1. Check if user exists
    user = User.query.filter_by(email=data.get('email')).first()
    
    # 2. Check password using the method in the User model
    if not user or not user.check_password(data.get('password')):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # 3. Generate Token (Uses UUID string as identity)
    access_token = create_access_token(identity=user.id)
    
    return jsonify({
        'message': 'Login successful',
        'access_token': access_token,
        'user': user.to_dict()
    }), 200