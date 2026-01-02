from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import MaintenanceRequest, Unit, User

maintenance_bp = Blueprint('maintenance', __name__)

@maintenance_bp.route('', methods=['GET'])
@jwt_required()
def get_all_requests():
    """
    Get all maintenance requests
    ---
    security:
      - Bearer: []
    """
    current_user = User.query.get(get_jwt_identity())
    
    if current_user.role == 'admin':
        requests = MaintenanceRequest.query.all()
    elif current_user.role == 'landlord':
        requests = MaintenanceRequest.query.filter_by(landlord_id=current_user.id).all()
    else:  # tenant
        requests = MaintenanceRequest.query.filter_by(tenant_id=current_user.id).all()
    
    return jsonify([req.to_dict() for req in requests]), 200

@maintenance_bp.route('', methods=['POST'])
@jwt_required()
def create_request():
    """
    Create new maintenance request (Tenant only)
    ---
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          properties:
            unit_id:
              type: string
            title:
              type: string
            description:
              type: string
            image_url:
              type: string
    """
    current_user = User.query.get(get_jwt_identity())
    data = request.get_json()
    
    unit = Unit.query.get(data.get('unit_id'))
    if not unit:
        return jsonify({'error': 'Unit not found'}), 404
    
    # Get active lease for this tenant and unit
    from models import Lease
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
    db.session.commit()
    
    return jsonify({'message': 'Maintenance request created successfully', 'request': maintenance_request.to_dict()}), 201

@maintenance_bp.route('/<request_id>', methods=['GET'])
@jwt_required()
def get_request(request_id):
    """
    Get maintenance request by ID
    ---
    security:
      - Bearer: []
    parameters:
      - name: request_id
        in: path
        type: string
        required: true
    """
    maintenance_request = MaintenanceRequest.query.get(request_id)
    
    if not maintenance_request:
        return jsonify({'error': 'Request not found'}), 404
    
    return jsonify(maintenance_request.to_dict()), 200

@maintenance_bp.route('/<request_id>', methods=['PUT'])
@jwt_required()
def update_request(request_id):
    """
    Update maintenance request status (Landlord/Admin only)
    ---
    security:
      - Bearer: []
    parameters:
      - name: request_id
        in: path
        type: string
        required: true
      - name: body
        in: body
        schema:
          properties:
            status:
              type: string
    """
    current_user = User.query.get(get_jwt_identity())
    maintenance_request = MaintenanceRequest.query.get(request_id)
    
    if not maintenance_request:
        return jsonify({'error': 'Request not found'}), 404
    
    if maintenance_request.landlord_id != current_user.id and current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    if 'status' in data:
        maintenance_request.status = data['status']
    
    db.session.commit()
    
    return jsonify({'message': 'Request updated successfully', 'request': maintenance_request.to_dict()}), 200

@maintenance_bp.route('/unit/<unit_id>', methods=['GET'])
def get_unit_requests(unit_id):
    """
    Get all maintenance requests for a unit
    ---
    parameters:
      - name: unit_id
        in: path
        type: string
        required: true
    """
    requests = MaintenanceRequest.query.filter_by(unit_id=unit_id).all()
    return jsonify([req.to_dict() for req in requests]), 200

@maintenance_bp.route('/tenant/<tenant_id>', methods=['GET'])
def get_tenant_requests(tenant_id):
    """
    Get all maintenance requests by a tenant
    ---
    parameters:
      - name: tenant_id
        in: path
        type: string
        required: true
    """
    requests = MaintenanceRequest.query.filter_by(tenant_id=tenant_id).all()
    return jsonify([req.to_dict() for req in requests]), 200
