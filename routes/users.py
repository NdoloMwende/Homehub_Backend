from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import User

users_bp = Blueprint('users', __name__)

@users_bp.route('', methods=['GET'])
@jwt_required()
def get_all_users():
    """
    Get all users (Admin only)
    ---
    security:
      - Bearer: []
    """
    current_user = User.query.get(get_jwt_identity())
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    users = User.query.all()
    return jsonify([user.to_dict() for user in users]), 200

@users_bp.route('/<user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """
    Get user by ID
    ---
    security:
      - Bearer: []
    parameters:
      - name: user_id
        in: path
        type: string
        required: true
    """
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(user.to_dict()), 200

@users_bp.route('/<user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """
    Update user profile
    ---
    security:
      - Bearer: []
    parameters:
      - name: user_id
        in: path
        type: string
        required: true
      - name: body
        in: body
        schema:
          properties:
            full_name:
              type: string
            phone:
              type: string
            profile_image_url:
              type: string
            national_id:
              type: string
            kra_pin:
              type: string
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Users can only update their own profile
    current_user = User.query.get(current_user_id)
    if current_user_id != user_id and current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    if 'full_name' in data:
        user.full_name = data['full_name']
    if 'phone' in data:
        user.phone = data['phone']
    if 'profile_image_url' in data:
        user.profile_image_url = data['profile_image_url']
    if 'national_id' in data:
        user.national_id = data['national_id']
    if 'kra_pin' in data:
        user.kra_pin = data['kra_pin']
    
    db.session.commit()
    
    return jsonify({'message': 'User updated successfully', 'user': user.to_dict()}), 200

@users_bp.route('/<user_id>/approve', methods=['POST'])
@jwt_required()
def approve_user(user_id):
    """
    Approve user (Admin only)
    ---
    security:
      - Bearer: []
    parameters:
      - name: user_id
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
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json() or {}
    user.status = 'approved'
    user.comment = data.get('comment')
    
    db.session.commit()
    
    return jsonify({'message': 'User approved successfully', 'user': user.to_dict()}), 200

@users_bp.route('/<user_id>/reject', methods=['POST'])
@jwt_required()
def reject_user(user_id):
    """
    Reject user (Admin only)
    ---
    security:
      - Bearer: []
    parameters:
      - name: user_id
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
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json() or {}
    user.status = 'rejected'
    user.comment = data.get('comment')
    user.is_active = False
    
    db.session.commit()
    
    return jsonify({'message': 'User rejected', 'user': user.to_dict()}), 200
