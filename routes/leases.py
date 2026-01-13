from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import Lease, Property, User
from datetime import datetime, timedelta

leases_bp = Blueprint('leases', __name__)

# --- 1. GET ALL LEASES (Smart Filter) ---
@leases_bp.route('', methods=['GET'])
@jwt_required()
def get_all_leases():
    current_user = User.query.get(get_jwt_identity())
    
    if current_user.role == 'admin':
        leases = Lease.query.all()
    elif current_user.role == 'landlord':
        # Find leases for properties owned by this landlord
        leases = db.session.query(Lease).join(Property, Lease.unit_id == Property.id)\
            .filter(Property.landlord_id == current_user.id).all()
    else: # Tenant
        leases = Lease.query.filter_by(tenant_id=current_user.id).all()

    # Enhance data with Property Titles
    output = []
    for lease in leases:
        data = lease.to_dict()
        prop = Property.query.get(lease.unit_id)
        if prop:
            data['property_title'] = prop.name
            data['property_city'] = prop.city
            
            # If Landlord, include Tenant Name
            if current_user.role == 'landlord':
                tenant = User.query.get(lease.tenant_id)
                data['tenant_name'] = tenant.full_name if tenant else "Unknown"
                
        output.append(data)
    
    return jsonify(output), 200

# --- 2. CREATE APPLICATION (The "Apply" Button) ---
@leases_bp.route('', methods=['POST'])
@jwt_required()
def create_lease_application():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    # 1. Validate Property
    # Note: We use property_id as unit_id for now
    prop_id = data.get('property_id') or data.get('unit_id')
    if not prop_id:
        return jsonify({'error': 'Property ID is required'}), 400

    property = Property.query.get(prop_id)
    if not property: return jsonify({'error': 'Property not found'}), 404

    # 2. Check for Duplicates
    existing = Lease.query.filter_by(tenant_id=current_user_id, unit_id=property.id, status='pending').first()
    if existing:
        return jsonify({'error': 'Application already pending'}), 400

    # 3. Create Lease with DEFAULTS (Smart Logic)
    # We set default dates to "Today" + "1 Year"
    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=365)

    new_lease = Lease(
        unit_id=property.id,
        tenant_id=current_user_id,
        start_date=start_date,
        end_date=end_date,
        monthly_rent=property.price,
        deposit=property.price, 
        status='pending' # Important: It is just a request
    )
    
    db.session.add(new_lease)
    db.session.commit()
    
    return jsonify({'message': 'Application submitted', 'lease': new_lease.to_dict()}), 201

# --- 3. LANDLORD ACTIONS (Approve/Reject) ---
@leases_bp.route('/<lease_id>/status', methods=['POST'])
@jwt_required()
def update_lease_status(lease_id):
    current_user = User.query.get(get_jwt_identity())
    data = request.get_json()
    action = data.get('status') # 'approved' or 'rejected'

    lease = Lease.query.get(lease_id)
    if not lease: return jsonify({'error': 'Lease not found'}), 404

    # Verify Landlord owns the property
    prop = Property.query.get(lease.unit_id)
    if prop.landlord_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    if action == 'approved':
        lease.status = 'active'
        prop.status = 'occupied' # Mark house as taken
    elif action == 'rejected':
        lease.status = 'rejected'
    
    db.session.commit()
    return jsonify({'message': f'Lease {action}'}), 200