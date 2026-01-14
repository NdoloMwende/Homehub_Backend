from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import MaintenanceRequest, Lease, Property, User, Notification, Unit
from sqlalchemy import cast, String

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


# --- 2. CREATE REQUEST (The Fuzzy Fix) ---
@maintenance_bp.route('', methods=['POST'])
@jwt_required()
def create_request():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        print(f"🔍 DEBUG: Maintenance submit from Tenant {current_user_id}")

        # 🟢 STEP 1: Fetch ALL leases for this tenant (Ignore status for now)
        all_leases = Lease.query.filter(
            cast(Lease.tenant_id, String) == str(current_user_id)
        ).all()

        print(f"   - Found {len(all_leases)} total leases.")

        # 🟢 STEP 2: Python "Fuzzy Search" for the Active Lease
        # This handles 'Active', 'active', 'ACTIVE', ' active ', etc.
        active_lease = None
        for lease in all_leases:
            # Clean up the status string
            status_clean = str(lease.status).strip().lower()
            print(f"   - Checking Lease {lease.id}: Status='{lease.status}' (Clean='{status_clean}')")
            
            if status_clean == 'active':
                active_lease = lease
                break
        
        # 🟢 STEP 3: Handle "No Lease Found"
        if not active_lease:
            # If we fail, tell the user exactly what we found (Debug help)
            found_statuses = [l.status for l in all_leases]
            error_msg = f"No Active Lease found. Your leases are: {found_statuses}"
            print(f"❌ {error_msg}")
            return jsonify({'error': error_msg}), 403

        print(f"✅ FOUND ACTIVE LEASE: {active_lease.id} (Unit {active_lease.unit_id})")

        # 🟢 STEP 4: Create Request (Backend provides the Unit ID automatically)
        new_request = MaintenanceRequest(
            tenant_id=current_user_id,
            unit_id=active_lease.unit_id, # INFERRED from the lease
            title=data.get('title'),
            description=data.get('description'),
            priority=data.get('priority', 'medium'),
            status='pending'
        )

        db.session.add(new_request)
        
        # Notify Landlord
        unit = Unit.query.get(active_lease.unit_id)
        if unit:
            prop = Property.query.get(unit.property_id)
            if prop:
                db.session.add(Notification(
                    user_id=prop.landlord_id, 
                    message=f"New Request: {data.get('title')}"
                ))

        db.session.commit()
        return jsonify({
            'message': 'Request submitted successfully!', 
            'request': new_request.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"❌ SYSTEM ERROR: {str(e)}")
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