from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import Notification, User

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('', methods=['GET'])
@jwt_required()
def get_notifications():
    """
    Get all notifications for current user
    ---
    security:
      - Bearer: []
    """
    current_user_id = get_jwt_identity()
    notifications = Notification.query.filter_by(recipient_user_id=current_user_id).order_by(Notification.created_at.desc()).all()
    
    return jsonify([notif.to_dict() for notif in notifications]), 200

@notifications_bp.route('', methods=['POST'])
@jwt_required()
def create_notification():
    """
    Create new notification
    ---
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          properties:
            recipient_user_id:
              type: string
            message:
              type: string
    """
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    recipient = User.query.get(data.get('recipient_user_id'))
    if not recipient:
        return jsonify({'error': 'Recipient not found'}), 404
    
    required_fields = ['recipient_user_id', 'message']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    notification = Notification(
        user_id=current_user_id,
        recipient_user_id=data['recipient_user_id'],
        message=data['message'],
        is_read=False
    )
    
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({'message': 'Notification sent successfully', 'notification': notification.to_dict()}), 201

@notifications_bp.route('/<notification_id>/read', methods=['PUT'])
@jwt_required()
def mark_as_read(notification_id):
    """
    Mark notification as read
    ---
    security:
      - Bearer: []
    parameters:
      - name: notification_id
        in: path
        type: string
        required: true
    """
    current_user_id = get_jwt_identity()
    notification = Notification.query.get(notification_id)
    
    if not notification:
        return jsonify({'error': 'Notification not found'}), 404
    
    if notification.recipient_user_id != current_user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    notification.is_read = True
    db.session.commit()
    
    return jsonify({'message': 'Notification marked as read', 'notification': notification.to_dict()}), 200

@notifications_bp.route('/unread', methods=['GET'])
@jwt_required()
def get_unread_count():
    """
    Get unread notification count
    ---
    security:
      - Bearer: []
    """
    current_user_id = get_jwt_identity()
    count = Notification.query.filter_by(recipient_user_id=current_user_id, is_read=False).count()
    
    return jsonify({'unread_count': count}), 200

@notifications_bp.route('/<notification_id>', methods=['DELETE'])
@jwt_required()
def delete_notification(notification_id):
    """
    Delete notification
    ---
    security:
      - Bearer: []
    parameters:
      - name: notification_id
        in: path
        type: string
        required: true
    """
    current_user_id = get_jwt_identity()
    notification = Notification.query.get(notification_id)
    
    if not notification:
        return jsonify({'error': 'Notification not found'}), 404
    
    if notification.recipient_user_id != current_user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(notification)
    db.session.commit()
    
    return jsonify({'message': 'Notification deleted'}), 200
