from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Lease, Property, User, Notification, Unit
from datetime import datetime, timedelta
from sqlalchemy import cast, String  # 🟢 IMPORT REQUIRED FOR ID FIX

leases_bp = Blueprint('leases', __name__)

# --- 1. GET ALL LEASES ---
@leases_bp.route('', methods=['GET'])
@jwt_required()
def get_all_leases():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User session not found'}), 404

        print(f"🔍 Fetching leases for User ID: {current_user_id} (Role: {user.role})")

        if user.role == 'landlord':
            # 🟢 FIX: Use SQLAlchemy 'cast' instead of Python 'str'
            # This safely converts the DB UUID to a string for comparison
            leases = db.session.query(Lease).join(Unit).join(Property)\
                .filter(cast(Property.landlord_id, String) == str(current_user_id))\
                .order_by(Lease.created_at.desc()).all()
        else:
            # 🟢 FIX: Same here for Tenant
            leases = Lease.query.filter(cast(Lease.tenant_id, String) == str(current_user_id))\
                .order_by(Lease.created_at.desc()).all()
        
        print(f"✅ Found {len(leases)} leases.")
        return jsonify([lease.to_dict() for lease in leases]), 200

    except Exception as e:
        print(f"❌ Error fetching leases: {e}")
        # Return the actual error message so the frontend debug box can see it
        return jsonify({'error': str(e)}), 500


# --- 2. CREATE LEASE APPLICATION ---
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
            return jsonify({'error': 'Property not found'}), 404

        # Auto-create unit if missing
        unit = Unit.query.filter_by(property_id=prop_id, status='vacant').first()
        if not unit:
            unit = Unit(
                property_id=prop_id, 
                unit_number="Main Unit", 
                rent_amount=property_obj.price, 
                status='vacant'
            )
            db.session.add(unit)
            db.session.commit()

        new_lease = Lease(
            unit_id=unit.id,
            tenant_id=current_user_id,
            rent_amount=property_obj.price,
            status='pending',
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=365)
        )
        
        db.session.add(new_lease)
        
        # Notify Landlord
        db.session.add(Notification(
            user_id=property_obj.landlord_id, 
            message=f"New application received for {property_obj.name}."
        ))
        
        db.session.commit()
        return jsonify({'message': 'Lease application sent successfully!'}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# --- 3. UPDATE LEASE STATUS ---
@leases_bp.route('/<lease_id>/status', methods=['POST'])
@jwt_required()
def update_lease_status(lease_id):
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        action = data.get('status') 

        lease = Lease.query.get(lease_id)
        if not lease:
            return jsonify({'error': 'Lease not found'}), 404

        unit = Unit.query.get(lease.unit_id)
        prop = Property.query.get(unit.property_id)
        
        # Security Check using Cast
        if str(prop.landlord_id) != str(current_user_id):
            return jsonify({'error': 'Unauthorized'}), 403

        if action == 'approved':
            lease.status = 'active'
            unit.status = 'occupied'
        elif action == 'rejected':
            lease.status = 'rejected'
            unit.status = 'vacant'
        
        db.session.add(Notification(user_id=lease.tenant_id, message=f"Application {action}."))
        db.session.commit()
        return jsonify({'message': f'Lease marked as {action}'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500