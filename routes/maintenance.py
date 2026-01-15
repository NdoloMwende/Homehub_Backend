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

        # Add Property Name for Context
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

# --- 2. CREATE REQUEST (Smart Logic) ---
@maintenance_bp.route('', methods=['POST'])
@jwt_required()
def create_request():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        provided_unit_id = data.get('unit_id')
        
        # 🟢 SCENARIO 1: Fetch ALL Active Leases
        active_leases = Lease.query.filter(
            cast(Lease.tenant_id, String) == str(current_user_id),
            Lease.status == 'active'
        ).all()
        
        if not active_leases:
             return jsonify({'error': 'No active leases found.'}), 403

        target_lease = None

        # 🟢 SCENARIO 2: If User selected a Property (Dropdown)
        if provided_unit_id:
            target_lease = next((l for l in active_leases if str(l.unit_id) == str(provided_unit_id)), None)
            if not target_lease:
                return jsonify({'error': 'Invalid Property Selected.'}), 403
        
        # 🟢 SCENARIO 3: Auto-Detect (Single Property)
        else:
            if len(active_leases) == 1:
                target_lease = active_leases[0]
            else:
                return jsonify({'error': 'Multiple properties found. Please select one.'}), 400

        new_request = MaintenanceRequest(
            tenant_id=current_user_id,
            unit_id=target_lease.unit_id, # 🟢 Uses specific Unit ID
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
        return jsonify({'message': 'Submitted', 'request': new_request.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# --- 3. UPDATE REQUEST ---
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