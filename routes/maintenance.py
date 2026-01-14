from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db  # 🟢 FIX: Use extensions to prevent circular imports
from models import MaintenanceRequest, Unit, User, Notification, Lease, Property

maintenance_bp = Blueprint('maintenance', __name__)

# --- 1. GET ALL REQUESTS ---
@maintenance_bp.route('', methods=['GET'])
@jwt_required()
def get_all_requests():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if current_user.role == 'admin':
        requests = MaintenanceRequest.query.all()
    elif current_user.role == 'landlord':
        # 🟢 FIX: Join with Property to find requests for this landlord
        requests = MaintenanceRequest.query.join(Property)\
            .filter(Property.landlord_id == current_user.id)\
            .order_by(MaintenanceRequest.created_at.desc()).all()
    else:  # tenant
        requests = MaintenanceRequest.query.filter_by(tenant_id=current_user.id)\
            .order_by(MaintenanceRequest.created_at.desc()).all()
    
    return jsonify([req.to_dict() for req in requests]), 200

# --- 2. CREATE REQUEST (Automated Unit Detection) ---
@maintenance_bp.route('', methods=['POST'])
@jwt_required()
def create_request():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    # 🟢 AUTOMATION FIX: Find the tenant's active lease automatically
    # This removes the need for the tenant to send 'unit_id' manually
    active_lease = Lease.query.filter_by(tenant_id=current_user_id, status='active').first()
    
    if not active_lease:
        return jsonify({'error': 'You must have an active lease to report maintenance issues.'}), 403
    
    # Get details from the lease
    unit = Unit.query.get(active_lease.unit_id)
    prop = Property.query.get(unit.property_id)
    
    if not data.get('title') or not data.get('description'):
        return jsonify({'error': 'Title and Description are required'}), 400
    
    # Create the request linked to the Property
    maintenance_request = MaintenanceRequest(
        property_id=prop.id,      # 🟢 Auto-linked
        tenant_id=current_user_id,
        title=data['title'],
        description=data['description'],
        priority=data.get('priority', 'medium'),
        status='pending'
    )
    
    db.session.add(maintenance_request)
    
    # 🔔 TRIGGER: Notify Landlord (Using the simplified Notification model)
    alert_msg = f"Maintenance Alert: {data['title']} at {prop.name} (Unit {unit.unit_number})"
    alert_landlord = Notification(
        user_id=prop.landlord_id,  # Recipient
        message=alert_msg
    )
    db.session.add(alert_landlord)

    db.session.commit()
    
    return jsonify({'message': 'Maintenance request submitted successfully', 'request': maintenance_request.to_dict()}), 201

# --- 3. GET SINGLE REQUEST ---
@maintenance_bp.route('/<request_id>', methods=['GET'])
@jwt_required()
def get_request(request_id):
    maintenance_request = MaintenanceRequest.query.get(request_id)
    
    if not maintenance_request:
        return jsonify({'error': 'Request not found'}), 404
    
    return jsonify(maintenance_request.to_dict()), 200

# --- 4. UPDATE STATUS (With Notification Trigger) ---
@maintenance_bp.route('/<request_id>', methods=['PUT'])
@jwt_required()
def update_request(request_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    maintenance_request = MaintenanceRequest.query.get(request_id)
    
    if not maintenance_request:
        return jsonify({'error': 'Request not found'}), 404
    
    # Verify ownership via Property
    prop = Property.query.get(maintenance_request.property_id)
    
    if str(prop.landlord_id) != str(current_user_id) and current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    if 'status' in data:
        maintenance_request.status = data['status']
        
        # 🔔 TRIGGER: Notify Tenant
        alert_msg = f"Update: Your maintenance request '{maintenance_request.title}' is now {data['status']}"
        alert_tenant = Notification(
            user_id=maintenance_request.tenant_id, # Recipient
            message=alert_msg
        )
        db.session.add(alert_tenant)
    
    db.session.commit()
    
    return jsonify({'message': 'Request updated successfully', 'request': maintenance_request.to_dict()}), 200

# --- 5. HELPER ROUTES ---
@maintenance_bp.route('/property/<property_id>', methods=['GET'])
def get_property_requests(property_id):
    requests = MaintenanceRequest.query.filter_by(property_id=property_id).all()
    return jsonify([req.to_dict() for req in requests]), 200

@maintenance_bp.route('/tenant/<tenant_id>', methods=['GET'])
def get_tenant_requests(tenant_id):
    requests = MaintenanceRequest.query.filter_by(tenant_id=tenant_id).all()
    return jsonify([req.to_dict() for req in requests]), 200