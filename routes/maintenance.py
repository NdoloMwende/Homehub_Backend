from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import MaintenanceRequest, Lease, Property, User, Notification, Unit
from sqlalchemy import cast, String, func # 🟢 Added func for lowercase check

maintenance_bp = Blueprint('maintenance', __name__)

# --- 1. GET REQUESTS ---
@maintenance_bp.route('', methods=['GET'])
@jwt_required()
def get_requests():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({'error': 'User not found'}), 404

        if user.role == 'landlord':
            requests = db.session.query(MaintenanceRequest).join(Unit).join(Property)\
                .filter(cast(Property.landlord_id, String) == str(current_user_id))\
                .order_by(MaintenanceRequest.created_at.desc()).all()
        else:
            requests = MaintenanceRequest.query.filter(
                cast(MaintenanceRequest.tenant_id, String) == str(current_user_id)
            ).order_by(MaintenanceRequest.created_at.desc()).all()

        return jsonify([req.to_dict() for req in requests]), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- 2. CREATE REQUEST ---
@maintenance_bp.route('', methods=['POST'])
@jwt_required()
def create_request():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        print(f"🔍 DEBUG: Attempting to find active lease for Tenant {current_user_id}")

        # 🟢 CRITICAL FIX: Case-Insensitive Status Check
        # Uses func.lower() to match 'Active', 'active', or 'ACTIVE'
        active_lease = Lease.query.filter(
            cast(Lease.tenant_id, String) == str(current_user_id),
            func.lower(Lease.status) == 'active' 
        ).first()

        if not active_lease:
            # 🟢 DEBUG: If it fails, print why to the terminal
            print("❌ DEBUG: No active lease found. Checking DB contents...")
            all_leases = Lease.query.filter(cast(Lease.tenant_id, String) == str(current_user_id)).all()
            for l in all_leases:
                print(f"   - Found Lease ID: {l.id} | Status: '{l.status}' (Match Failed)")
            
            return jsonify({'error': 'Failed. Ensure you have an active lease.'}), 403

        print(f"✅ DEBUG: Found Active Lease {active_lease.id}")

        new_request = MaintenanceRequest(
            tenant_id=current_user_id,
            unit_id=active_lease.unit_id,
            title=data.get('title'),
            description=data.get('description'),
            priority=data.get('priority', 'medium'),
            status='pending'
        )

        db.session.add(new_request)
        
        # Notify Landlord logic
        unit = Unit.query.get(active_lease.unit_id)
        if unit:
            prop = Property.query.get(unit.property_id)
            if prop:
                db.session.add(Notification(
                    user_id=prop.landlord_id, 
                    message=f"New Request: {data.get('title')}"
                ))

        db.session.commit()
        return jsonify({'message': 'Request submitted successfully', 'request': new_request.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        print(f"❌ ERROR: {str(e)}")
        return jsonify({'error': str(e)}), 500

# --- 3. UPDATE REQUEST (Landlord) ---
@maintenance_bp.route('/<int:request_id>', methods=['PATCH'])
@jwt_required()
def update_request_status(request_id):
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        new_status = data.get('status')

        req = MaintenanceRequest.query.get(request_id)
        if not req:
            return jsonify({'error': 'Request not found'}), 404

        unit = Unit.query.get(req.unit_id)
        prop = Property.query.get(unit.property_id)

        if str(prop.landlord_id) != str(current_user_id):
            return jsonify({'error': 'Unauthorized'}), 403

        req.status = new_status
        db.session.add(Notification(user_id=req.tenant_id, message=f"Maintenance Update: {new_status}"))
        db.session.commit()
        return jsonify({'message': 'Status updated', 'request': req.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500