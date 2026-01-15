from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import User, Notification

users_bp = Blueprint('users', __name__)

# --- 1. GET PROFILE ---
@users_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({
        'id': user.id,
        'full_name': user.full_name,
        'email': user.email,
        'role': user.role,
        'phone_number': user.phone_number
    }), 200

# --- 2. GET NOTIFICATIONS (🟢 NEW) ---
@users_bp.route('/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    try:
        current_user_id = get_jwt_identity()
        # Fetch notifications, newest first
        notifications = Notification.query.filter_by(user_id=current_user_id)\
            .order_by(Notification.created_at.desc()).all()
        
        result = [{
            'id': n.id,
            'message': n.message,
            'is_read': n.is_read,
            'created_at': n.created_at.isoformat()
        } for n in notifications]
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- 3. MARK NOTIFICATION READ (🟢 NEW) ---
@users_bp.route('/notifications/<int:notification_id>/read', methods=['PATCH'])
@jwt_required()
def mark_read(notification_id):
    try:
        current_user_id = get_jwt_identity()
        notification = Notification.query.get(notification_id)
        
        if not notification or str(notification.user_id) != str(current_user_id):
            return jsonify({'error': 'Notification not found'}), 404
            
        notification.is_read = True
        db.session.commit()
        return jsonify({'message': 'Marked as read'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- 4. CLEAR ALL NOTIFICATIONS (🟢 NEW) ---
@users_bp.route('/notifications/clear', methods=['DELETE'])
@jwt_required()
def clear_all_notifications():
    try:
        current_user_id = get_jwt_identity()
        # Delete all notifications for this user
        Notification.query.filter_by(user_id=current_user_id).delete()
        db.session.commit()
        return jsonify({'message': 'All notifications cleared'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500