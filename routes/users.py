import os
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from extensions import db  # 🟢 FIX: Use extensions to prevent circular import crashes
from models import User

users_bp = Blueprint('users', __name__)

# --- 1. GET CURRENT USER PROFILE ---
@users_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        return jsonify(user.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- 2. THE VERIFICATION ROUTE (Your Logic + Safety Fixes) ---
@users_bp.route('/verify-upload', methods=['POST'])
@jwt_required()
def upload_verification():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # 1. Update Text Data (National ID & KRA)
        if request.form.get('national_id'):
            user.national_id = request.form.get('national_id')
        if request.form.get('kra_pin'):
            user.kra_pin = request.form.get('kra_pin')

        # 2. Handle File Upload
        # Check for 'document' (your code) OR 'file' (generic fallback)
        file = request.files.get('document') or request.files.get('file')
        
        if file:
            filename = secure_filename(f"verify_{user.id}_{file.filename}")
            
            # Ensure upload folder exists
            upload_folder = current_app.config['UPLOAD_FOLDER']
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
                
            # Save File
            upload_path = os.path.join(upload_folder, filename)
            file.save(upload_path)
            
            # Save Path to DB
            user.evidence_of_identity = f"/uploads/{filename}"
            
            # 3. CRITICAL: Auto-approve logic
            user.status = 'approved'
            # user.is_active = True # (Optional: depending on if you use this flag)

        db.session.commit()
        
        return jsonify({
            'message': 'Verification successful. You can now add properties!', 
            'user': user.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# --- 3. DELETE ACCOUNT (New Feature) ---
@users_bp.route('/me', methods=['DELETE'])
@jwt_required()
def delete_account():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        # SQLAlchemy cascade rules in models.py should handle 
        # deleting linked leases/properties automatically.
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'message': 'Account deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500