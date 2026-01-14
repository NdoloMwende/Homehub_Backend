from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Lease, Property, User, Notification, Unit
from datetime import datetime, timedelta

leases_bp = Blueprint('leases', __name__)

# --- 🟢 GET ALL LEASES (Tenant & Landlord History) ---
@leases_bp.route('', methods=['GET'])
@jwt_required()
def get_all_leases():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if user.role == 'landlord':
        # Fetches only leases belonging to properties owned by this landlord
        leases = db.session.query(Lease).join(Unit).join(Property)\
            .filter(Property.landlord_id == current_user_id)\
            .order_by(Lease.created_at.desc()).all()
    else:
        # Fetches the personal history for the tenant
        leases = Lease.query.filter_by(tenant_id=current_user_id)\
            .order_by(Lease.created_at.desc()).all()

    return jsonify([lease.to_dict() for lease in leases]), 200

# --- 🟢 UPDATE LEASE STATUS (Approval/Rejection) ---
@leases_bp.route('/<lease_id>/status', methods=['POST'])
@jwt_required()
def update_lease_status(lease_id):
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        action = data.get('status') # 'approved' or 'rejected'

        lease = Lease.query.get(lease_id)
        if not lease:
            return jsonify({'error': 'Lease record not found'}), 404

        unit = Unit.query.get(lease.unit_id)
        prop = Property.query.get(unit.property_id)
        
        # Security Check: Ensure only the owner can approve
        if str(prop.landlord_id) != str(current_user_id):
            return jsonify({'error': 'Unauthorized access to this property'}), 403

        if action == 'approved':
            lease.status = 'active'
            unit.status = 'occupied'
            # 🟢 DYNAMIC DATES: Set move-in as today and expiry in 1 year
            lease.start_date = datetime.utcnow()
            lease.end_date = lease.start_date + timedelta(days=365)
        elif action == 'rejected':
            lease.status = 'rejected'
            unit.status = 'vacant'
        
        # Notification logic
        msg = f"Your lease application for {prop.name} has been {action}."
        db.session.add(Notification(user_id=lease.tenant_id, message=msg))
        
        db.session.commit()
        return jsonify({'message': f'Lease marked as {action}'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500