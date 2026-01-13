from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import Notification, User

notifications_bp = Blueprint('notifications', __name__)

# --- 1. GET MY NOTIFICATIONS ---
@notifications_bp.route('', methods=['GET'])
@jwt_required()
def get_notifications():
    current_user_id = get_jwt_identity()
    
    # Fetch notifications where I am the RECIPIENT
    notifications = Notification.query.filter_by(recipient_user_id=current_user_id)\
        .order_by(Notification.created_at.desc()).limit(20).all()
    
    return jsonify([notif.to_dict() for notif in notifications]), 200

# --- 2. GET UNREAD COUNT ---
@notifications_bp.route('/unread', methods=['GET'])
@jwt_required()
def get_unread_count():
    current_user_id = get_jwt_identity()
    # Count where I am recipient AND it is unread
    count = Notification.query.filter_by(recipient_user_id=current_user_id, is_read=False).count()
    return jsonify({'unread_count': count}), 200

# --- 3. MARK AS READ ---
@notifications_bp.route('/<notification_id>/read', methods=['PATCH'])
@jwt_required()
def mark_as_read(notification_id):
    current_user_id = get_jwt_identity()
    notification = Notification.query.get(notification_id)
    
    if not notification:
        return jsonify({'error': 'Not found'}), 404
    
    # Security check: Am I the recipient?
    if notification.recipient_user_id != current_user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    notification.is_read = True
    db.session.commit()
    
    return jsonify({'message': 'Marked as read'}), 200

# --- 4. DELETE NOTIFICATION ---
@notifications_bp.route('/<notification_id>', methods=['DELETE'])
@jwt_required()
def delete_notification(notification_id):
    current_user_id = get_jwt_identity()
    notification = Notification.query.get(notification_id)
    
    if not notification:
        return jsonify({'error': 'Not found'}), 404
    
    if notification.recipient_user_id != current_user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(notification)
    db.session.commit()
    
    return jsonify({'message': 'Deleted'}), 200