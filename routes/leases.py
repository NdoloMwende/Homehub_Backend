from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import Lease, Unit, User
from datetime import datetime

leases_bp = Blueprint('leases', __name__)

@leases_bp.route('', methods=['GET'])
@jwt_required()
def get_all_leases():
    """
    Get all leases
    ---
    security:
      - Bearer: []
    """
    current_user = User.query.get(get_jwt_identity())
    
    if current_user.role == 'admin':
        leases = Lease.query.all()
    elif current_user.role == 'landlord':
        leases = Lease.query.join(Unit).join(Property).filter(Property.landlord_id == current_user.id).all()
    else:  # tenant
        leases = Lease.query.filter_by(tenant_id=current_user.id).all()
    
    return jsonify([lease.to_dict() for lease in leases]), 200

@leases_bp.route('', methods=['POST'])
@jwt_required()
def create_lease():
    """
    Create new lease
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
            tenant_id:
              type: string
            start_date:
              type: string
            end_date:
              type: string
            monthly_rent:
              type: number
            deposit:
              type: number
            document_url:
              type: string
    """
    current_user = User.query.get(get_jwt_identity())
    data = request.get_json()
    
    unit = Unit.query.get(data.get('unit_id'))
    if not unit:
        return jsonify({'error': 'Unit not found'}), 404
    
    property = unit.property
    if property.landlord_id != current_user.id and current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    required_fields = ['unit_id', 'tenant_id', 'start_date', 'end_date', 'monthly_rent', 'deposit']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    lease = Lease(
        unit_id=data['unit_id'],
        tenant_id=data['tenant_id'],
        start_date=datetime.fromisoformat(data['start_date']).date(),
        end_date=datetime.fromisoformat(data['end_date']).date(),
        monthly_rent=data['monthly_rent'],
        deposit=data['deposit'],
        document_url=data.get('document_url'),
        status='active'
    )
    
    db.session.add(lease)
    unit.status = 'occupied'
    db.session.commit()
    
    return jsonify({'message': 'Lease created successfully', 'lease': lease.to_dict()}), 201

@leases_bp.route('/<lease_id>', methods=['GET'])
@jwt_required()
def get_lease(lease_id):
    """
    Get lease by ID
    ---
    security:
      - Bearer: []
    parameters:
      - name: lease_id
        in: path
        type: string
        required: true
    """
    lease = Lease.query.get(lease_id)
    
    if not lease:
        return jsonify({'error': 'Lease not found'}), 404
    
    return jsonify(lease.to_dict()), 200

@leases_bp.route('/<lease_id>', methods=['PUT'])
@jwt_required()
def update_lease(lease_id):
    """
    Update lease
    ---
    security:
      - Bearer: []
    parameters:
      - name: lease_id
        in: path
        type: string
        required: true
      - name: body
        in: body
        schema:
          properties:
            status:
              type: string
            end_date:
              type: string
    """
    current_user = User.query.get(get_jwt_identity())
    lease = Lease.query.get(lease_id)
    
    if not lease:
        return jsonify({'error': 'Lease not found'}), 404
    
    unit = lease.unit
    property = unit.property
    if property.landlord_id != current_user.id and current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    if 'status' in data:
        lease.status = data['status']
        if data['status'] == 'terminated' or data['status'] == 'expired':
            unit.status = 'vacant'
    
    if 'end_date' in data:
        lease.end_date = datetime.fromisoformat(data['end_date']).date()
    
    db.session.commit()
    
    return jsonify({'message': 'Lease updated successfully', 'lease': lease.to_dict()}), 200

@leases_bp.route('/tenant/<tenant_id>', methods=['GET'])
def get_tenant_leases(tenant_id):
    """
    Get all leases for a tenant
    ---
    parameters:
      - name: tenant_id
        in: path
        type: string
        required: true
    """
    leases = Lease.query.filter_by(tenant_id=tenant_id).all()
    return jsonify([lease.to_dict() for lease in leases]), 200

@leases_bp.route('/unit/<unit_id>', methods=['GET'])
def get_unit_leases(unit_id):
    """
    Get all leases for a unit
    ---
    parameters:
      - name: unit_id
        in: path
        type: string
        required: true
    """
    leases = Lease.query.filter_by(unit_id=unit_id).all()
    return jsonify([lease.to_dict() for lease in leases]), 200
