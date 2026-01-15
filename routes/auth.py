from flask import Blueprint, request, jsonify
from extensions import db
from models import User
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # 1. Check for missing fields
    required = ['full_name', 'email', 'password', 'role']
    if not all(k in data for k in required):
        return jsonify({'error': 'Missing required fields'}), 400

    # 2. Check if user exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400

    # 3. 🟢 CRITICAL FIX: Enforce "Pending" status for Landlords
    # Tenants are active immediately, Landlords must wait for Admin
    initial_status = 'pending' if data['role'] == 'landlord' else 'active'

    # 4. Create User
    new_user = User(
        full_name=data['full_name'],
        email=data['email'],
        role=data['role'],
        phone_number=data.get('phone_number'),
        status=initial_status, # <--- Uses the logic above
        national_id=data.get('national_id'), # Optional at start
        kra_pin=data.get('kra_pin')          # Optional at start
    )
    new_user.set_password(data['password'])
    
    try:
        db.session.add(new_user)
        db.session.commit()
        
        # 5. Return success message (customize based on role)
        if data['role'] == 'landlord':
            return jsonify({
                'message': 'Account created! Please wait for Admin approval before logging in.',
                'require_approval': True 
            }), 201
        else:
            return jsonify({'message': 'User registered successfully'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # 1. Find User
    user = User.query.filter_by(email=data['email']).first()
    
    # 2. Validate Password
    if user and user.check_password(data['password']):
        
        # 3. 🟢 CRITICAL FIX: Block login if Pending or Rejected
        if user.status == 'pending':
            return jsonify({'error': 'Your account is still under review by an Admin.'}), 403
        if user.status == 'rejected':
            return jsonify({'error': 'Your account verification failed. Contact support.'}), 403

        # 4. Generate Token
        access_token = create_access_token(identity=user.id)
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': user.to_dict()
        }), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(user.to_dict()), 200