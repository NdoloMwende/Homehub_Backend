from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User
from werkzeug.utils import secure_filename
import os

users_bp = Blueprint('users', __name__)

# ... (Keep your other routes like /me, /delete, etc.) ...

# --- THE VERIFICATION ROUTE ---
@users_bp.route('/verify-upload', methods=['POST'])
@jwt_required()
def upload_verification():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # 1. Update Text Data
    if request.form.get('national_id'):
        user.national_id = request.form.get('national_id')
    if request.form.get('kra_pin'):
        user.kra_pin = request.form.get('kra_pin')

    # 2. Handle File Upload
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
        
        # Save Path
        user.evidence_of_identity = f"/uploads/{filename}"
        
        # 3. CRITICAL: Auto-approve so they can add properties immediately
        user.status = 'approved'
        user.is_active = True

    db.session.commit()
    
    return jsonify({
        'message': 'Verification successful', 
        'user': user.to_dict() # Return updated user data
    }), 200