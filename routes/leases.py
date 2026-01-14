from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Lease, Property, User, Notification, Unit
from datetime import datetime, timedelta

leases_bp = Blueprint('leases', __name__)

# --- 1. GET ALL LEASES (Dynamic History for both roles) ---
@leases_bp.route('', methods=['GET'])
@jwt_required()
def get_all_leases():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User session not found'}), 404

    if user.role == 'landlord':
        # John sees history for all his properties to update his "Active Tenants" count
        leases = db.session.query(Lease).join(Unit).join(Property)\
            .filter(Property.landlord_id == current_user_id)\
            .order_by(Lease.created_at.desc()).all()
    else:
        # Tom sees his personal history (Pending, Active, Rejected)
        leases = Lease.query.filter_by(tenant_id=current_user_id)\
            .order_by(Lease.created_at.desc()).all()

    return jsonify([lease.to_dict() for lease in leases]), 200


# --- 2. CREATE LEASE APPLICATION (The "Lease Now" Logic) ---
@leases_bp.route('', methods=['POST'])
@jwt_required()
def create_lease_application():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        prop_id = data.get('property_id')

        if not prop_id:
            return jsonify({'error': 'Invalid Property selection'}), 400

        property_obj = Property.query.get(prop_id)
        if not property_obj:
            return jsonify({'error': 'Property not found in database'}), 404

        # 🟢 AUTO-UNIT CREATOR: Ensures application succeeds even if no units exist yet
        unit = Unit.query.filter_by(property_id=prop_id, status='vacant').first()
        
        if not unit:
            unit = Unit(
                property_id=prop_id, 
                unit_number="Main Unit", 
                rent_amount=property_obj.price, 
                status='vacant'
            )
            db.session.add(unit)
            db.session.commit() # Save to get the unit.id

        # Create the initial pending lease
        new_lease = Lease(
            unit_id=unit.id,
            tenant_id=current_user_id,
            rent_amount=property_obj.price,
            status='pending'
        )
        
        db.session.add(new_lease)
        
        # Landlord Notification
        db.session.add(Notification(
            user_id=property_obj.landlord_id, 
            message=f"New application received for {property_obj.name}."
        ))
        
        db.session.commit()
        return jsonify({'message': 'Lease application sent successfully!'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# --- 3. UPDATE LEASE STATUS (Approval/Rejection Logic) ---
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
        
        # Security & UUID String Check
        if str(prop.landlord_id) != str(current_user_id):
            return jsonify({'error': 'Unauthorized: Ownership check failed'}), 403

        if action == 'approved':
            lease.status = 'active'
            unit.status = 'occupied'
            # 🟢 DYNAMIC DATES: Set upon approval for 1 year
            lease.start_date = datetime.utcnow()
            lease.end_date = lease.start_date + timedelta(days=365)
        elif action == 'rejected':
            lease.status = 'rejected'
            unit.status = 'vacant'
        
        # Notify Tenant
        msg = f"Your lease application for {prop.name} has been {action}."
        db.session.add(Notification(user_id=lease.tenant_id, message=msg))
        
        db.session.commit()
        return jsonify({'message': f'Lease marked as {action}'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500