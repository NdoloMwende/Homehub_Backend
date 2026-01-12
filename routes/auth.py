from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from app import db
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
        status = 'active' # Admins are auto-verified
        print(f"🎉 Creating new ADMIN: {data['email']}")
    elif role == 'landlord':
        status = 'pending' # Landlords need verification
    # --------------------------------

    # 4. Create User
    new_user = User(
        full_name=data['full_name'],
        email=data['email'],
        password_hash=generate_password_hash(data['password']),
        role=role,
        status=status,
        phone=data.get('phone')
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # 1. Check if user exists
    user = User.query.filter_by(email=data.get('email')).first()
    
    # 2. Check password
    if not user or not check_password_hash(user.password_hash, data.get('password')):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # 3. Generate Token
    access_token = create_access_token(identity=user.id)
    
    return jsonify({
        'message': 'Login successful',
        'access_token': access_token,
        'user': user.to_dict()
    }), 200