from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import MaintenanceRequest, Unit, User, Notification, Lease # 👈 Added Notification & Lease imports

maintenance_bp = Blueprint('maintenance', __name__)

# --- 1. GET ALL REQUESTS ---
@maintenance_bp.route('', methods=['GET'])
@jwt_required()
def get_all_requests():
    current_user = User.query.get(get_jwt_identity())
    
    if current_user.role == 'admin':
        requests = MaintenanceRequest.query.all()
    elif current_user.role == 'landlord':
        requests = MaintenanceRequest.query.filter_by(landlord_id=current_user.id).all()
    else:  # tenant
        requests = MaintenanceRequest.query.filter_by(tenant_id=current_user.id).all()
    
    return jsonify([req.to_dict() for req in requests]), 200

# --- 2. CREATE REQUEST (With Notification Trigger) ---
@maintenance_bp.route('', methods=['POST'])
@jwt_required()
def create_request():
    current_user = User.query.get(get_jwt_identity())
    data = request.get_json()
    
    unit = Unit.query.get(data.get('unit_id'))
    if not unit:
        return jsonify({'error': 'Unit not found'}), 404
    
    # Get active lease for this tenant and unit
    lease = Lease.query.filter_by(unit_id=unit.id, tenant_id=current_user.id, status='active').first()
    if not lease:
        return jsonify({'error': 'No active lease found for this unit'}), 403
    
    required_fields = ['unit_id', 'title', 'description']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    maintenance_request = MaintenanceRequest(
        unit_id=data['unit_id'],
        tenant_id=current_user.id,
        landlord_id=unit.property.landlord_id,
        title=data['title'],
        description=data['description'],
        image_url=data.get('image_url'),
        status='pending'
    )
    
    db.session.add(maintenance_request)
    
    # 🔔 TRIGGER: Notify Landlord
    alert_landlord = Notification(
        user_id=current_user.id,                # Sender: Tenant
        recipient_user_id=unit.property.landlord_id, # Recipient: Landlord
        type='alert',
        message=f"Maintenance: New request '{data['title']}' for Unit {unit.unit_number}"
    )
    db.session.add(alert_landlord)

    db.session.commit()
    
    return jsonify({'message': 'Maintenance request created successfully', 'request': maintenance_request.to_dict()}), 201

# --- 3. GET SINGLE REQUEST ---
@maintenance_bp.route('/<request_id>', methods=['GET'])
@jwt_required()
def get_request(request_id):
    maintenance_request = MaintenanceRequest.query.get(request_id)
    
    if not maintenance_request:
        return jsonify({'error': 'Request not found'}), 404
    
    return jsonify(maintenance_request.to_dict()), 200

# --- 4. UPDATE STATUS (With Notification Trigger) ---
@maintenance_bp.route('/<request_id>', methods=['PUT']) # User kept PUT, so we keep PUT
@jwt_required()
def update_request(request_id):
    current_user = User.query.get(get_jwt_identity())
    maintenance_request = MaintenanceRequest.query.get(request_id)
    
    if not maintenance_request:
        return jsonify({'error': 'Request not found'}), 404
    
    if maintenance_request.landlord_id != current_user.id and current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    if 'status' in data:
        maintenance_request.status = data['status']
        
        # 🔔 TRIGGER: Notify Tenant
        # Only notify if status actually changed
        alert_tenant = Notification(
            user_id=current_user.id,               # Sender: Landlord
            recipient_user_id=maintenance_request.tenant_id, # Recipient: Tenant
            type='info',
            message=f"Maintenance Update: Your request '{maintenance_request.title}' is now {data['status']}"
        )
        db.session.add(alert_tenant)
    
    db.session.commit()
    
    return jsonify({'message': 'Request updated successfully', 'request': maintenance_request.to_dict()}), 200

# --- 5. HELPER ROUTES ---
@maintenance_bp.route('/unit/<unit_id>', methods=['GET'])
def get_unit_requests(unit_id):
    requests = MaintenanceRequest.query.filter_by(unit_id=unit_id).all()
    return jsonify([req.to_dict() for req in requests]), 200

@maintenance_bp.route('/tenant/<tenant_id>', methods=['GET'])
def get_tenant_requests(tenant_id):
    requests = MaintenanceRequest.query.filter_by(tenant_id=tenant_id).all()
    return jsonify([req.to_dict() for req in requests]), 200