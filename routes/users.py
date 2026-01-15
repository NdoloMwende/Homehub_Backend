from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import User, Notification, Lease, MaintenanceRequest, Property, Unit

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

# --- 2. GET NOTIFICATIONS ---
@users_bp.route('/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    try:
        current_user_id = get_jwt_identity()
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

# --- 3. MARK NOTIFICATION READ ---
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

# --- 4. CLEAR ALL NOTIFICATIONS ---
@users_bp.route('/notifications/clear', methods=['DELETE'])
@jwt_required()
def clear_all_notifications():
    try:
        current_user_id = get_jwt_identity()
        Notification.query.filter_by(user_id=current_user_id).delete()
        db.session.commit()
        return jsonify({'message': 'All notifications cleared'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# --- 5. DELETE ACCOUNT (🟢 NEW & CRITICAL) ---
@users_bp.route('/profile', methods=['DELETE'])
@jwt_required()
def delete_account():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # 🟢 MANUAL CLEANUP (Prevent Foreign Key Errors)
        
        # 1. Delete Notifications
        Notification.query.filter_by(user_id=current_user_id).delete()

        # 2. Delete Maintenance Requests (Tenant or Landlord side handled via relationships usually, but explicit is safer)
        if user.role == 'tenant':
            MaintenanceRequest.query.filter_by(tenant_id=current_user_id).delete()
            Lease.query.filter_by(tenant_id=current_user_id).delete()
        
        elif user.role == 'landlord':
            # This is destructive: Deleting a landlord deletes their Properties -> Units -> Leases -> Requests
            properties = Property.query.filter_by(landlord_id=current_user_id).all()
            for prop in properties:
                # Get all units for this property
                units = Unit.query.filter_by(property_id=prop.id).all()
                for unit in units:
                    # Delete requests & leases for unit
                    MaintenanceRequest.query.filter_by(unit_id=unit.id).delete()
                    Lease.query.filter_by(unit_id=unit.id).delete()
                    db.session.delete(unit)
                db.session.delete(prop)

        # 3. Finally, Delete the User
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'message': 'Account and all associated data deleted successfully'}), 200

    except Exception as e:
        db.session.rollback()
        print(f"Delete Error: {str(e)}") # Print error to terminal for debugging
        return jsonify({'error': f"Failed to delete account: {str(e)}"}), 500