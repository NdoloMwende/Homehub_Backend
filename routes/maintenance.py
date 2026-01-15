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
        if not user: return jsonify({'error': 'User not found'}), 404

        if user.role == 'landlord':
            requests = db.session.query(MaintenanceRequest).join(Unit).join(Property)\
                .filter(cast(Property.landlord_id, String) == str(current_user_id))\
                .order_by(MaintenanceRequest.created_at.desc()).all()
        else:
            requests = MaintenanceRequest.query.filter(
                cast(MaintenanceRequest.tenant_id, String) == str(current_user_id)
            ).order_by(MaintenanceRequest.created_at.desc()).all()

        result = []
        for req in requests:
            r_dict = req.to_dict()
            unit = Unit.query.get(req.unit_id)
            prop = Property.query.get(unit.property_id) if unit else None
            r_dict['property_name'] = prop.name if prop else "Unknown"
            result.append(r_dict)

        return jsonify(result), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# --- 2. CREATE REQUEST (The Bulletproof Logic) ---
@maintenance_bp.route('', methods=['POST'])
@jwt_required()
def create_request():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        provided_unit_id = data.get('unit_id')
        
        print(f"🔍 DEBUG: New Request from {current_user_id} for Unit {provided_unit_id}")

        # 🟢 STEP 1: Fetch ALL leases (Ignore status filter for now)
        all_leases = Lease.query.filter(
            cast(Lease.tenant_id, String) == str(current_user_id)
        ).all()
        
        # 🟢 STEP 2: Filter for 'Active' in Python (Ignores Case & Spaces)
        active_leases = []
        for lease in all_leases:
            # Clean the status string
            status_clean = str(lease.status).strip().lower()
            print(f"   - Checking Lease {lease.id} (Unit {lease.unit_id}): Status='{lease.status}'")
            
            if status_clean == 'active':
                active_leases.append(lease)

        # Check if we found anything
        if not active_leases:
            print("❌ DEBUG: No active leases found after filtering.")
            return jsonify({'error': 'No active leases found. You cannot submit maintenance requests.'}), 403

        # 🟢 STEP 3: Match the Unit ID
        target_lease = None
        
        # Scenario A: User Selected a Property (Dropdown)
        if provided_unit_id:
            # Look for ID match inside active leases
            target_lease = next((l for l in active_leases if str(l.unit_id) == str(provided_unit_id)), None)
            
            if not target_lease:
                print(f"❌ DEBUG: Unit ID {provided_unit_id} not found in user's active leases.")
                return jsonify({'error': 'Invalid Property Selected. Ensure you have an Active lease for this specific unit.'}), 403
        
        # Scenario B: Auto-Select (Only 1 Active Lease)
        else:
            if len(active_leases) == 1:
                target_lease = active_leases[0]
                print(f"✅ DEBUG: Auto-selected Lease {target_lease.id}")
            else:
                return jsonify({'error': 'You have multiple active properties. Please select one from the list.'}), 400

        # 🟢 STEP 4: Create
        new_request = MaintenanceRequest(
            tenant_id=current_user_id,
            unit_id=target_lease.unit_id,
            title=data.get('title'),
            description=data.get('description'),
            priority=data.get('priority', 'medium'),
            status='pending'
        )

        db.session.add(new_request)
        
        # Notify Landlord
        unit = Unit.query.get(target_lease.unit_id)
        if unit:
            prop = Property.query.get(unit.property_id)
            if prop:
                db.session.add(Notification(user_id=prop.landlord_id, message=f"Maintenance: {data.get('title')}"))

        db.session.commit()
        return jsonify({'message': 'Request submitted successfully!', 'request': new_request.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        print(f"❌ ERROR: {e}")
        return jsonify({'error': str(e)}), 500


# --- 3. UPDATE STATUS ---
@maintenance_bp.route('/<int:request_id>', methods=['PATCH'])
@jwt_required()
def update_request_status(request_id):
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        req = MaintenanceRequest.query.get(request_id)
        if not req: return jsonify({'error': 'Not found'}), 404
        
        unit = Unit.query.get(req.unit_id)
        prop = Property.query.get(unit.property_id)
        if str(prop.landlord_id) != str(current_user_id): return jsonify({'error': 'Unauthorized'}), 403

        req.status = data.get('status')
        db.session.commit()
        return jsonify({'message': 'Updated'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500