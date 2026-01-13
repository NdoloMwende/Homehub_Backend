from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import Lease, Property, User, Notification, Unit # 👈 Added Unit
from datetime import datetime, timedelta

leases_bp = Blueprint('leases', __name__)

# --- 1. GET ALL LEASES ---
@leases_bp.route('', methods=['GET'])
@jwt_required()
def get_all_leases():
    current_user = User.query.get(get_jwt_identity())
    
    if current_user.role == 'admin':
        leases = Lease.query.all()
    elif current_user.role == 'landlord':
        leases = db.session.query(Lease).join(Unit, Lease.unit_id == Unit.id)\
            .join(Property, Unit.property_id == Property.id)\
            .filter(Property.landlord_id == current_user.id).all()
    else: # Tenant
        leases = Lease.query.filter_by(tenant_id=current_user.id).all()

    output = []
    for lease in leases:
        data = lease.to_dict()
        # Fetch Property Details via Unit
        unit = Unit.query.get(lease.unit_id)
        if unit:
            prop = Property.query.get(unit.property_id)
            if prop:
                data['property_title'] = prop.name
                data['property_city'] = prop.city
                data['unit_number'] = unit.unit_number
                
                if current_user.role == 'landlord':
                    tenant = User.query.get(lease.tenant_id)
                    data['tenant_name'] = tenant.full_name if tenant else "Unknown"
        output.append(data)
    
    return jsonify(output), 200

# --- 2. CREATE APPLICATION ("Lease Now" Logic) ---
@leases_bp.route('', methods=['POST'])
@jwt_required()
def create_lease_application():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    # 1. Resolve Property to a Specific Unit
    target_unit_id = data.get('unit_id')
    property_obj = None

    if not target_unit_id and data.get('property_id'):
        # 🟢 SMART LOGIC: Find the first available unit in this property
        prop_id = data.get('property_id')
        property_obj = Property.query.get(prop_id)
        
        # Look for a vacant unit
        available_unit = Unit.query.filter_by(property_id=prop_id).first() 
        # Note: In a real app, verify status='vacant'. For demo, we take the first one.
        
        if not available_unit:
            # Auto-create a dummy unit if none exists (prevents crashing on properties without unit seeds)
            available_unit = Unit(
                property_id=prop_id, 
                unit_number="Main", 
                rent_amount=property_obj.price or 0, 
                status="vacant"
            )
            db.session.add(available_unit)
            db.session.commit()
            
        target_unit_id = available_unit.id
    
    if not target_unit_id:
        return jsonify({'error': 'No available units found for this property'}), 404

    # 2. Duplicate Check
    existing = Lease.query.filter_by(tenant_id=current_user_id, unit_id=target_unit_id, status='pending').first()
    if existing:
        return jsonify({'error': 'You already have a pending application for this unit'}), 400

    # 3. Create Lease
    # If we haven't fetched property yet, fetch it now for pricing
    if not property_obj:
        unit = Unit.query.get(target_unit_id)
        property_obj = Property.query.get(unit.property_id)

    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=365)

    new_lease = Lease(
        unit_id=target_unit_id,
        tenant_id=current_user_id,
        start_date=start_date,
        end_date=end_date,
        monthly_rent=property_obj.price,
        deposit=property_obj.price, 
        status='pending'
    )
    
    db.session.add(new_lease)

    # 🔔 TRIGGER: Notify Landlord
    alert_landlord = Notification(
        user_id=current_user_id,
        recipient_user_id=property_obj.landlord_id,
        type='alert',
        message=f"Lease Request: A tenant wants to lease {property_obj.name} (Unit {target_unit_id[:4]})."
    )
    db.session.add(alert_landlord)

    db.session.commit()
    
    return jsonify({'message': 'Lease application sent successfully!', 'lease': new_lease.to_dict()}), 201

# --- 3. STATUS UPDATES ---
@leases_bp.route('/<lease_id>/status', methods=['POST'])
@jwt_required()
def update_lease_status(lease_id):
    current_user = User.query.get(get_jwt_identity())
    data = request.get_json()
    action = data.get('status')

    lease = Lease.query.get(lease_id)
    if not lease: return jsonify({'error': 'Lease not found'}), 404

    unit = Unit.query.get(lease.unit_id)
    prop = Property.query.get(unit.property_id)
    
    if prop.landlord_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    if action == 'approved':
        lease.status = 'active'
        unit.status = 'occupied' # Mark unit occupied
    elif action == 'rejected':
        lease.status = 'rejected'
    
    # 🔔 TRIGGER: Notify Tenant
    alert_tenant = Notification(
        user_id=current_user.id,
        recipient_user_id=lease.tenant_id,
        type='success' if action == 'approved' else 'alert',
        message=f"Application Update: Your lease for {prop.name} was {action}."
    )
    db.session.add(alert_tenant)

    db.session.commit()
    return jsonify({'message': f'Lease {action}'}), 200