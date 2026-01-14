from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Lease, Property, User, Notification, Unit
from datetime import datetime, timedelta

# 🟢 THIS WAS MISSING: Define the Blueprint
leases_bp = Blueprint('leases', __name__)

# --- 1. GET ALL LEASES (NUCLEAR DEBUG VERSION) ---
@leases_bp.route('', methods=['GET'])
# @jwt_required() # 🟢 Temporarily commented out to test raw DB access
def get_all_leases():
    try:
        # 🟢 NUCLEAR DEBUG: Fetch EVERYTHING ignoring User IDs
        leases = Lease.query.all()
        
        print(f"\n☢️ NUCLEAR DEBUG: Found {len(leases)} total leases in DB.")
        for l in leases:
            print(f"   - ID: {l.id} | Status: {l.status} | TenantID: {l.tenant_id} | Prop: {l.property_name}")

        return jsonify([lease.to_dict() for lease in leases]), 200
    except Exception as e:
        print(f"❌ DB ERROR: {e}")
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

        # Create Lease
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