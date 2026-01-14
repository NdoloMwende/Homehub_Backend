from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Lease, Property, User, Notification, Unit
from datetime import datetime, timedelta

leases_bp = Blueprint('leases', __name__)

# --- 1. GET ALL LEASES ---
@leases_bp.route('', methods=['GET'])
@jwt_required()
def get_all_leases():
    current_user = User.query.get(get_jwt_identity())
    if current_user.role == 'admin':
        leases = Lease.query.all()
    elif current_user.role == 'landlord':
        leases = db.session.query(Lease).join(Unit, Lease.unit_id == Unit.id)\
            .join(Property, Unit.property_id == Property.id)\
            .filter(Property.landlord_id == current_user.id).all()
    else: # Tenant
        leases = Lease.query.filter_by(tenant_id=current_user.id).all()

    return jsonify([lease.to_dict() for lease in leases]), 200

# --- 2. CREATE APPLICATION ---
@leases_bp.route('', methods=['POST'])
@jwt_required()
def create_lease_application():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        prop_id = data.get('property_id')

        if not prop_id or prop_id == "undefined":
            return jsonify({'error': 'Invalid Property selection'}), 400

        property_obj = Property.query.get(prop_id)
        unit = Unit.query.filter_by(property_id=prop_id, status='vacant').first()
        
        if not unit:
            unit = Unit(property_id=prop_id, unit_number="Unit 1", rent_amount=property_obj.price, status="vacant")
            db.session.add(unit)
            db.session.commit()

        new_lease = Lease(
            unit_id=unit.id,
            tenant_id=current_user_id,
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=365),
            rent_amount=property_obj.price,
            status='pending'
        )
        db.session.add(new_lease)
        db.session.add(Notification(user_id=property_obj.landlord_id, message=f"New Lease Request: {property_obj.name}"))
        db.session.commit()
        return jsonify({'message': 'Lease application sent!'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# --- 3. STATUS UPDATES ---
@leases_bp.route('/<lease_id>/status', methods=['POST'])
@jwt_required()
def update_lease_status(lease_id):
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        action = data.get('status')

        lease = Lease.query.get(lease_id)
        unit = Unit.query.get(lease.unit_id)
        prop = Property.query.get(unit.property_id)
        
        # 🟢 CRITICAL: String conversion prevents 403 Forbidden errors
        if str(prop.landlord_id) != str(current_user_id):
            return jsonify({'error': 'Unauthorized'}), 403

        if action == 'approved':
            lease.status = 'active'
            unit.status = 'occupied'
        elif action == 'rejected':
            lease.status = 'rejected'
        
        db.session.add(Notification(user_id=lease.tenant_id, message=f"Your lease for {prop.name} was {action}."))
        db.session.commit()
        return jsonify({'message': f'Lease {action}'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500