from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Invoice, Payment, Lease, User, Unit, Property
from utils.mpesa import MpesaHandler
from datetime import datetime

payments_bp = Blueprint('payments', __name__)

# --- 1. LANDLORD: CREATE INVOICE ---
@payments_bp.route('/invoices', methods=['POST'])
@jwt_required()
def create_invoice():
    try:
        data = request.get_json()
        current_user_id = get_jwt_identity()
        
        lease = Lease.query.get(data['lease_id'])
        if not lease: return jsonify({'error': 'Lease not found'}), 404

        # Validate Landlord Ownership
        unit = Unit.query.get(lease.unit_id)
        prop = Property.query.get(unit.property_id)
        if str(prop.landlord_id) != str(current_user_id):
            return jsonify({'error': 'Unauthorized'}), 403

        new_invoice = Invoice(
            lease_id=lease.id,
            tenant_id=lease.tenant_id,
            amount=data['amount'],
            description=data['description'],
            due_date=datetime.strptime(data['due_date'], '%Y-%m-%d'),
            status='pending'
        )
        
        db.session.add(new_invoice)
        db.session.commit()
        return jsonify({'message': 'Invoice created', 'invoice': new_invoice.to_dict()}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- 2. TENANT: GET MY INVOICES ---
@payments_bp.route('/my-invoices', methods=['GET'])
@jwt_required()
def get_my_invoices():
    current_user_id = get_jwt_identity()
    invoices = Invoice.query.filter_by(tenant_id=current_user_id).order_by(Invoice.created_at.desc()).all()
    return jsonify([i.to_dict() for i in invoices]), 200

# --- 3. INITIATE MPESA PAYMENT ---
@payments_bp.route('/pay', methods=['POST'])
@jwt_required()
def pay_invoice():
    try:
        data = request.get_json()
        invoice_id = data.get('invoice_id')
        phone = data.get('phone_number') # 2547...
        
        invoice = Invoice.query.get(invoice_id)
        if not invoice: return jsonify({'error': 'Invoice not found'}), 404
        
        mpesa = MpesaHandler()
        res = mpesa.initiate_stk_push(phone, invoice.amount, f"INV-{invoice.id}")
        
        return jsonify({'message': 'STK Push sent.', 'mpesa_response': res}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- 4. CALLBACK (Webhook) ---
@payments_bp.route('/callback', methods=['POST'])
def mpesa_callback():
    # In a real app, you parse the JSON to confirm payment and mark invoice as 'paid'
    data = request.get_json()
    print("🔴 MPESA CALLBACK RECEIVED:", data)
    return jsonify({'result': 'received'}), 200