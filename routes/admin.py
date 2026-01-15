from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import User, Property, Notification

# 🟢 THIS WAS MISSING
admin_bp = Blueprint('admin', __name__)

# Helper: Check if current user is Admin
def verify_admin(user_id):
    user = User.query.get(user_id)
    return user and user.role == 'admin'

# --- 1. LANDLORD VERIFICATION ---

@admin_bp.route('/landlords/pending', methods=['GET'])
@jwt_required()
def get_pending_landlords():
    current_user_id = get_jwt_identity()
    if not verify_admin(current_user_id):
        return jsonify({'error': 'Unauthorized. Admin access only.'}), 403

    # Fetch landlords who are not yet active
    landlords = User.query.filter_by(role='landlord', status='pending').all()
    
    return jsonify([{
        'id': l.id,
        'full_name': l.full_name,
        'email': l.email,
        'phone': l.phone_number,
        'national_id': l.national_id,
        'kra_pin': l.kra_pin,
        'evidence_of_identity': l.evidence_of_identity, # URL to uploaded ID
        'created_at': l.created_at.isoformat()
    } for l in landlords]), 200

@admin_bp.route('/landlords/<user_id>/verify', methods=['PATCH'])
@jwt_required()
def verify_landlord(user_id):
    current_user_id = get_jwt_identity()
    if not verify_admin(current_user_id):
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    action = data.get('action') # 'approve' or 'reject'
    
    landlord = User.query.get(user_id)
    if not landlord: return jsonify({'error': 'User not found'}), 404

    if action == 'approve':
        landlord.status = 'active'
        msg = "Your Landlord account has been verified! You can now list properties."
    elif action == 'reject':
        landlord.status = 'rejected'
        msg = "Your Landlord verification failed. Please contact support."
    else:
        return jsonify({'error': 'Invalid action'}), 400

    # Notify Landlord
    db.session.add(Notification(user_id=landlord.id, message=msg))
    db.session.commit()

    return jsonify({'message': f'Landlord {action}d successfully'}), 200

# --- 2. PROPERTY VERIFICATION ---

@admin_bp.route('/properties/pending', methods=['GET'])
@jwt_required()
def get_pending_properties():
    current_user_id = get_jwt_identity()
    if not verify_admin(current_user_id):
        return jsonify({'error': 'Unauthorized'}), 403

    # Fetch properties that are 'pending' or 'Under Review'
    properties = Property.query.filter(Property.status.in_(['pending', 'Under Review'])).all()
    
    results = []
    for p in properties:
        landlord = User.query.get(p.landlord_id)
        results.append({
            'id': p.id,
            'name': p.name,
            'location': f"{p.city}, {p.address}",
            'price': p.price,
            'landlord_name': landlord.full_name if landlord else "Unknown",
            'image_url': p.image_url,
            'status': p.status
        })

    return jsonify(results), 200

@admin_bp.route('/properties/<property_id>/verify', methods=['PATCH'])
@jwt_required()
def verify_property(property_id):
    current_user_id = get_jwt_identity()
    if not verify_admin(current_user_id):
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    action = data.get('action') # 'approve' or 'reject'
    
    prop = Property.query.get(property_id)
    if not prop: return jsonify({'error': 'Property not found'}), 404

    if action == 'approve':
        prop.status = 'approved' 
        msg = f"Your property '{prop.name}' has been approved and is now live."
    elif action == 'reject':
        prop.status = 'rejected'
        msg = f"Your property '{prop.name}' was rejected. Please check guidelines."
    else:
        return jsonify({'error': 'Invalid action'}), 400

    # Notify Landlord
    db.session.add(Notification(user_id=prop.landlord_id, message=msg))
    db.session.commit()

    return jsonify({'message': f'Property {action}d successfully'}), 200