from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import MaintenanceRequest, Lease, Property, User, Notification, Unit
from sqlalchemy import cast, String  # 🟢 IMPORT REQUIRED FOR ID FIX

maintenance_bp = Blueprint('maintenance', __name__)

# --- 1. GET ALL REQUESTS (Auto-filtered by Role) ---
@maintenance_bp.route('', methods=['GET'])
@jwt_required()
def get_requests():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({'error': 'User not found'}), 404

        if user.role == 'landlord':
            # Landlords see requests for THEIR properties only
            # 🟢 FIX: Cast to String to ensure match
            requests = db.session.query(MaintenanceRequest).join(Unit).join(Property)\
                .filter(cast(Property.landlord_id, String) == str(current_user_id))\
                .order_by(MaintenanceRequest.created_at.desc()).all()
        else:
            # Tenants see their own requests
            # 🟢 FIX: Cast to String to ensure match
            requests = MaintenanceRequest.query.filter(
                cast(MaintenanceRequest.tenant_id, String) == str(current_user_id)
            ).order_by(MaintenanceRequest.created_at.desc()).all()

        return jsonify([req.to_dict() for req in requests]), 200

    except Exception as e:
        print(f"❌ Error fetching maintenance: {e}")
        return jsonify({'error': str(e)}), 500


# --- 2. CREATE NEW REQUEST (Auto-detects Lease) ---
@maintenance_bp.route('', methods=['POST'])
@jwt_required()
def create_request():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()

        # 1. Validate Input
        title = data.get('title')
        description = data.get('description')
        priority = data.get('priority', 'medium')

        if not title or not description:
            return jsonify({'error': 'Title and description are required'}), 400

        # 2. 🟢 CRITICAL FIX: Find Active Lease using String Cast
        # We need to find the lease to know which Unit/Property this is for.
        active_lease = Lease.query.filter(
            cast(Lease.tenant_id, String) == str(current_user_id),
            Lease.status == 'active'
        ).first()

        if not active_lease:
            return jsonify({'error': 'You must have an Active Lease to submit maintenance requests.'}), 403

        # 3. Create the Request
        new_request = MaintenanceRequest(
            tenant_id=current_user_id,
            unit_id=active_lease.unit_id,  # Auto-linked from lease
            title=title,
            description=description,
            priority=priority,
            status='pending'
        )

        db.session.add(new_request)
        
        # 4. Notify Landlord
        # We need to fetch the property to get the landlord's ID
        unit = Unit.query.get(active_lease.unit_id)
        prop = Property.query.get(unit.property_id)
        
        db.session.add(Notification(
            user_id=prop.landlord_id,
            message=f"New Maintenance Request: {title} ({priority})"
        ))

        db.session.commit()
        return jsonify({
            'message': 'Maintenance request submitted successfully!',
            'request': new_request.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error creating maintenance: {e}")
        return jsonify({'error': str(e)}), 500


# --- 3. UPDATE REQUEST STATUS (Landlord Only) ---
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

        # Verify Landlord Ownership
        unit = Unit.query.get(req.unit_id)
        prop = Property.query.get(unit.property_id)

        if str(prop.landlord_id) != str(current_user_id):
            return jsonify({'error': 'Unauthorized'}), 403

        req.status = new_status
        
        # Notify Tenant
        db.session.add(Notification(
            user_id=req.tenant_id,
            message=f"Maintenance Update: Your request '{req.title}' is now {new_status}."
        ))

        db.session.commit()
        return jsonify({'message': 'Status updated successfully', 'request': req.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500