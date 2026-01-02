from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import RentInvoice, Lease, User, Unit, Property

rent_invoices_bp = Blueprint('rent_invoices', __name__)

@rent_invoices_bp.route('', methods=['GET'])
@jwt_required()
def get_all_invoices():
    """
    Get all rent invoices
    ---
    security:
      - Bearer: []
    """
    current_user = User.query.get(get_jwt_identity())
    
    if current_user.role == 'admin':
        invoices = RentInvoice.query.all()
    elif current_user.role == 'landlord':
        invoices = RentInvoice.query.filter_by(landlord_id=current_user.id).all()
    else:  # tenant
        invoices = RentInvoice.query.filter_by(tenant_id=current_user.id).all()
    
    return jsonify([invoice.to_dict() for invoice in invoices]), 200

@rent_invoices_bp.route('', methods=['POST'])
@jwt_required()
def create_invoice():
    """
    Create new rent invoice (Landlord only)
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
            landlord_id:
              type: string
            tenant_id:
              type: string
            lease_id:
              type: string
            invoice_date:
              type: string
            invoice_amount:
              type: number
            status:
              type: string
    """
    current_user = User.query.get(get_jwt_identity())
    data = request.get_json()
    
    lease = Lease.query.get(data.get('lease_id'))
    if not lease:
        return jsonify({'error': 'Lease not found'}), 404
    
    unit = lease.unit
    property = unit.property
    if property.landlord_id != current_user.id and current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    required_fields = ['unit_id', 'landlord_id', 'tenant_id', 'lease_id', 'invoice_date', 'invoice_amount']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    from datetime import datetime
    invoice = RentInvoice(
        unit_id=data['unit_id'],
        landlord_id=data['landlord_id'],
        tenant_id=data['tenant_id'],
        lease_id=data['lease_id'],
        invoice_date=datetime.fromisoformat(data['invoice_date']).date(),
        invoice_amount=data['invoice_amount'],
        status=data.get('status', 'pending')
    )
    
    db.session.add(invoice)
    db.session.commit()
    
    return jsonify({'message': 'Invoice created successfully', 'invoice': invoice.to_dict()}), 201

@rent_invoices_bp.route('/<invoice_id>', methods=['GET'])
@jwt_required()
def get_invoice(invoice_id):
    """
    Get invoice by ID
    ---
    security:
      - Bearer: []
    parameters:
      - name: invoice_id
        in: path
        type: string
        required: true
    """
    invoice = RentInvoice.query.get(invoice_id)
    
    if not invoice:
        return jsonify({'error': 'Invoice not found'}), 404
    
    return jsonify(invoice.to_dict()), 200

@rent_invoices_bp.route('/<invoice_id>', methods=['PUT'])
@jwt_required()
def update_invoice(invoice_id):
    """
    Update invoice status
    ---
    security:
      - Bearer: []
    parameters:
      - name: invoice_id
        in: path
        type: string
        required: true
      - name: body
        in: body
        schema:
          properties:
            status:
              type: string
            paid_date:
              type: string
            payment_id:
              type: string
    """
    current_user = User.query.get(get_jwt_identity())
    invoice = RentInvoice.query.get(invoice_id)
    
    if not invoice:
        return jsonify({'error': 'Invoice not found'}), 404
    
    if invoice.landlord_id != current_user.id and current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    if 'status' in data:
        invoice.status = data['status']
    
    if 'paid_date' in data:
        from datetime import datetime
        invoice.paid_date = datetime.fromisoformat(data['paid_date']).date()
    
    if 'payment_id' in data:
        invoice.payment_id = data['payment_id']
    
    db.session.commit()
    
    return jsonify({'message': 'Invoice updated successfully', 'invoice': invoice.to_dict()}), 200

@rent_invoices_bp.route('/tenant/<tenant_id>', methods=['GET'])
def get_tenant_invoices(tenant_id):
    """
    Get all invoices for a tenant
    ---
    parameters:
      - name: tenant_id
        in: path
        type: string
        required: true
    """
    invoices = RentInvoice.query.filter_by(tenant_id=tenant_id).all()
    return jsonify([invoice.to_dict() for invoice in invoices]), 200

@rent_invoices_bp.route('/landlord/<landlord_id>', methods=['GET'])
def get_landlord_invoices(landlord_id):
    """
    Get all invoices for a landlord
    ---
    parameters:
      - name: landlord_id
        in: path
        type: string
        required: true
    """
    invoices = RentInvoice.query.filter_by(landlord_id=landlord_id).all()
    return jsonify([invoice.to_dict() for invoice in invoices]), 200
