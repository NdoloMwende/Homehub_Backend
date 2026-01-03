from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import Payment, Lease, User
from datetime import datetime

payments_bp = Blueprint('payments', __name__)

@payments_bp.route('', methods=['GET'])
@jwt_required()
def get_all_payments():
    """
    Get all payments
    ---
    security:
      - Bearer: []
    """
    current_user = User.query.get(get_jwt_identity())
    
    if current_user.role == 'admin':
        payments = Payment.query.all()
    else:
        # For tenants and landlords, restrict to relevant payments
        payments = Payment.query.all()
    
    return jsonify([payment.to_dict() for payment in payments]), 200

@payments_bp.route('', methods=['POST'])
@jwt_required()
def create_payment():
    """
    Create new payment
    ---
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          properties:
            lease_id:
              type: string
            invoice_id:
              type: string
            amount:
              type: number
            due_date:
              type: string
            payment_reference:
              type: string
            payment_method:
              type: string
    """
    data = request.get_json()
    
    lease = Lease.query.get(data.get('lease_id'))
    if not lease:
        return jsonify({'error': 'Lease not found'}), 404
    
    required_fields = ['lease_id', 'amount', 'due_date']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    payment = Payment(
        lease_id=data['lease_id'],
        invoice_id=data.get('invoice_id'),
        amount=data['amount'],
        due_date=datetime.fromisoformat(data['due_date']).date(),
        payment_reference=data.get('payment_reference'),
        payment_method=data.get('payment_method'),
        status='pending'
    )
    
    db.session.add(payment)
    db.session.commit()
    
    return jsonify({'message': 'Payment created successfully', 'payment': payment.to_dict()}), 201

@payments_bp.route('/<payment_id>', methods=['GET'])
@jwt_required()
def get_payment(payment_id):
    """
    Get payment by ID
    ---
    security:
      - Bearer: []
    parameters:
      - name: payment_id
        in: path
        type: string
        required: true
    """
    payment = Payment.query.get(payment_id)
    
    if not payment:
        return jsonify({'error': 'Payment not found'}), 404
    
    return jsonify(payment.to_dict()), 200

@payments_bp.route('/<payment_id>', methods=['PUT'])
@jwt_required()
def update_payment(payment_id):
    """
    Update payment status
    ---
    security:
      - Bearer: []
    parameters:
      - name: payment_id
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
    """
    payment = Payment.query.get(payment_id)
    
    if not payment:
        return jsonify({'error': 'Payment not found'}), 404
    
    data = request.get_json()
    
    if 'status' in data:
        payment.status = data['status']
    
    if 'paid_date' in data:
        payment.paid_date = datetime.fromisoformat(data['paid_date']).date()
    
    db.session.commit()
    
    return jsonify({'message': 'Payment updated successfully', 'payment': payment.to_dict()}), 200

@payments_bp.route('/lease/<lease_id>', methods=['GET'])
def get_lease_payments(lease_id):
    """
    Get all payments for a lease
    ---
    parameters:
      - name: lease_id
        in: path
        type: string
        required: true
    """
    payments = Payment.query.filter_by(lease_id=lease_id).all()
    return jsonify([payment.to_dict() for payment in payments]), 200
