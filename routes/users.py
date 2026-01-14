from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import User, Lease, Property
from werkzeug.utils import secure_filename # 👈 Required for file uploads
import os # 👈 Required for file paths

users_bp = Blueprint('users', __name__)

# --- 1. GET CURRENT USER (For Settings Page) ---
@users_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get the currently logged-in user's profile"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(user.to_dict()), 200

# --- 2. DELETE ACCOUNT (New Feature) ---
@users_bp.route('/me', methods=['DELETE'])
@jwt_required()
def delete_account():
    """
    Permanently delete account.
    - Landlords cannot delete if they own active properties.
    - Tenants cannot delete if they have active leases.
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # SAFETY CHECK: Prevent breaking data integrity
    if user.role == 'landlord':
        # Check if they own properties
        active_props = Property.query.filter_by(landlord_id=user.id).first()
        if active_props:
            return jsonify({'error': 'Cannot delete account while you have listed properties. Please delete them first.'}), 400
            
    elif user.role == 'tenant':
        # Check if they have an active lease
        active_lease = Lease.query.filter_by(tenant_id=user.id, status='active').first()
        if active_lease:
            return jsonify({'error': 'Cannot delete account with an active lease. Please contact your landlord.'}), 400

    # If safe, delete user
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'message': 'Account deleted successfully'}), 200

# --- 3. GET ALL USERS (Admin Only) ---
@users_bp.route('', methods=['GET'])
@jwt_required()
def get_all_users():
    current_user = User.query.get(get_jwt_identity())
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    users = User.query.all()
    return jsonify([user.to_dict() for user in users]), 200

# --- 4. GET USER BY ID ---
@users_bp.route('/<user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(user.to_dict()), 200

# --- 5. UPDATE USER PROFILE ---
@users_bp.route('/<user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Users can only update their own profile (unless admin)
    current_user = User.query.get(current_user_id)
    if current_user_id != user_id and current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    if 'full_name' in data: user.full_name = data['full_name']
    if 'phone' in data: user.phone = data['phone']
    if 'profile_image_url' in data: user.profile_image_url = data['profile_image_url']
    if 'national_id' in data: user.national_id = data['national_id']
    if 'kra_pin' in data: user.kra_pin = data['kra_pin']
    
    db.session.commit()
    return jsonify({'message': 'User updated successfully', 'user': user.to_dict()}), 200

# --- 6. APPROVE USER (Admin Only) ---
@users_bp.route('/<user_id>/approve', methods=['POST'])
@jwt_required()
def approve_user(user_id):
    current_user = User.query.get(get_jwt_identity())
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get(user_id)
    if not user: return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json() or {}
    user.status = 'approved'
    user.comment = data.get('comment')
    
    db.session.commit()
    return jsonify({'message': 'User approved successfully', 'user': user.to_dict()}), 200

# --- 7. REJECT USER (Admin Only) ---
@users_bp.route('/<user_id>/reject', methods=['POST'])
@jwt_required()
def reject_user(user_id):
    current_user = User.query.get(get_jwt_identity())
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get(user_id)
    if not user: return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json() or {}
    user.status = 'rejected'
    user.comment = data.get('comment')
    user.is_active = False
    
    db.session.commit()
    return jsonify({'message': 'User rejected', 'user': user.to_dict()}), 200

# --- 8. UPLOAD VERIFICATION DOCS (The Missing Piece!) ---
@users_bp.route('/verify-upload', methods=['POST'])
@jwt_required()
def upload_verification():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # 1. Update Text Data (ID and PIN)
    if request.form.get('national_id'):
        user.national_id = request.form.get('national_id')
    if request.form.get('kra_pin'):
        user.kra_pin = request.form.get('kra_pin')

    # 2. Handle File Upload (The ID Document)
    file = request.files.get('document')
    if file:
        filename = secure_filename(file.filename)
        
        # Ensure upload folder exists
        upload_folder = current_app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
            
        # Save File
        upload_path = os.path.join(upload_folder, filename)
        file.save(upload_path)
        
        # Update Database
        user.evidence_of_identity = f"/uploads/{filename}"
        
        # Optional: Set status to 'pending' so Admin sees it needs review
        user.status = 'pending'

    db.session.commit()
    
    return jsonify({'message': 'Verification documents uploaded successfully'}), 200