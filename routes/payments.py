from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
# 🟢 UPDATED: Added Notification to imports
from models import Invoice, Payment, Lease, User, Unit, Property, Notification
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
        
        # Trigger STK Push
        mpesa = MpesaHandler()
        # We pass invoice ID in AccountReference so we can track it (in a real app)
        res = mpesa.initiate_stk_push(phone, invoice.amount, f"INV-{invoice.id}")
        
        return jsonify({'message': 'STK Push sent. Check your phone.', 'mpesa_response': res}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- 4. MPESA CALLBACK (The Logic Engine) ---
@payments_bp.route('/callback', methods=['POST'])
def mpesa_callback():
    try:
        data = request.get_json()
        print("🔴 MPESA CALLBACK RECEIVED:", data)

        # 1. Parse the M-Pesa Response
        stk_callback = data.get('Body', {}).get('stkCallback', {})
        result_code = stk_callback.get('ResultCode')
        
        # ResultCode 0 means SUCCESS
        if result_code != 0:
            print("❌ Payment Failed or Cancelled by User")
            return jsonify({'result': 'failed'}), 200

        # 2. Extract Metadata (Amount, Receipt, Phone)
        metadata = stk_callback.get('CallbackMetadata', {}).get('Item', [])
        
        amount = None
        receipt = None
        phone = None

        for item in metadata:
            if item['Name'] == 'Amount': amount = item['Value']
            if item['Name'] == 'MpesaReceiptNumber': receipt = item['Value']
            if item['Name'] == 'PhoneNumber': phone = str(item['Value'])

        if not amount or not receipt:
            return jsonify({'error': 'Invalid metadata'}), 400

        # 3. Find the Matching Invoice
        # In a production app, we would match via CheckoutRequestID. 
        # For this prototype, we match the First Pending Invoice with the exact Amount.
        invoice = Invoice.query.filter_by(amount=amount, status='pending').first()

        if invoice:
            # A. Mark Invoice as Paid
            invoice.status = 'paid'
            
            # B. Record the Payment
            new_payment = Payment(
                invoice_id=invoice.id,
                transaction_code=receipt,
                amount=amount,
                phone_number=phone
            )
            db.session.add(new_payment)

            # C. Notify the Landlord (🟢 NEW LOGIC)
            # Find the landlord via Lease -> Unit -> Property -> Landlord
            lease = Lease.query.get(invoice.lease_id)
            if lease:
                unit = Unit.query.get(lease.unit_id)
                prop = Property.query.get(unit.property_id)
                
                notification_msg = f"💰 Payment Received: KSh {amount} for {prop.name} (Unit {unit.unit_number}). Ref: {receipt}"
                
                # Add notification
                db.session.add(Notification(
                    user_id=prop.landlord_id,
                    message=notification_msg,
                    is_read=False
                ))

            db.session.commit()
            print(f"✅ Payment {receipt} processed successfully for Invoice #{invoice.id}")

        else:
            print("⚠️ Payment received but no matching pending invoice found.")

        return jsonify({'result': 'success'}), 200

    except Exception as e:
        print("Callback Error:", str(e))
        return jsonify({'error': str(e)}), 500