from app import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # admin, landlord, tenant
    phone = db.Column(db.String(20), nullable=True)
    profile_image_url = db.Column(db.String(500), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(50), nullable=False)  # approved, pending, rejected, active
    comment = db.Column(db.Text, nullable=True)
    national_id = db.Column(db.String(50), nullable=True)
    kra_pin = db.Column(db.String(50), nullable=True)
    evidence_of_identity = db.Column(db.String(500), nullable=True)
    show_welcome = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    properties = db.relationship('Property', backref='landlord', lazy=True, foreign_keys='Property.landlord_id')
    leases = db.relationship('Lease', backref='tenant', lazy=True, foreign_keys='Lease.tenant_id')
    maintenance_requests_tenant = db.relationship('MaintenanceRequest', backref='tenant_req', lazy=True, foreign_keys='MaintenanceRequest.tenant_id')
    maintenance_requests_landlord = db.relationship('MaintenanceRequest', backref='landlord_req', lazy=True, foreign_keys='MaintenanceRequest.landlord_id')
    
    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'role': self.role,
            'phone': self.phone,
            'profile_image_url': self.profile_image_url,
            'is_active': self.is_active,
            'status': self.status,
            'comment': self.comment,
            'national_id': self.national_id,
            'kra_pin': self.kra_pin,
            'evidence_of_identity': self.evidence_of_identity,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class Property(db.Model):
    __tablename__ = 'properties'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    landlord_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # --- EXISTING FIELDS ---
    name = db.Column(db.String(255), nullable=False) # Maps to 'title' in frontend
    address = db.Column(db.String(500), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    status = db.Column(db.String(50), nullable=False)  # approved, pending, rejected
    comment = db.Column(db.Text, nullable=True)
    evidence_of_ownership = db.Column(db.String(500), nullable=True)
    lrn_no = db.Column(db.String(50), nullable=True)
    location = db.Column(db.String(255), nullable=True)
    
    # --- NEW FIELDS (Required for Frontend) ---
    state = db.Column(db.String(100)) # County
    price = db.Column(db.Float, nullable=True) # Rent Amount
    bedrooms = db.Column(db.Integer, nullable=True)
    bathrooms = db.Column(db.Integer, nullable=True)
    square_feet = db.Column(db.Integer, nullable=True)
    property_type = db.Column(db.String(50), default='apartment')
    amenities = db.Column(db.Text, nullable=True)
    # ------------------------------------------

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    units = db.relationship('Unit', backref='property', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        # 🟢 NEW: Fetch Landlord details safely using the 'landlord' backref from User model
        landlord_data = {}
        if self.landlord:
            landlord_data = {
                'landlord_name': self.landlord.full_name,
                'landlord_email': self.landlord.email,
                'landlord_phone': self.landlord.phone
            }

        return {
            'id': self.id,
            'landlord_id': self.landlord_id,
            'title': self.name, # FRONTEND expects 'title', DB has 'name'
            'name': self.name,
            'address': self.address,
            'city': self.city,
            'country': self.country,
            'description': self.description,
            'image_url': self.image_url,
            'status': self.status,
            'comment': self.comment,
            'evidence_of_ownership': self.evidence_of_ownership,
            'lrn_no': self.lrn_no,
            'location': self.location,
            
            # Add new fields to dictionary
            'state': self.state,
            'price': self.price,
            'bedrooms': self.bedrooms,
            'bathrooms': self.bathrooms,
            'square_feet': self.square_feet,
            'property_type': self.property_type,
            'amenities': self.amenities,
            
            # 🟢 Include Landlord Info
            **landlord_data,

            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class Unit(db.Model):
    __tablename__ = 'units'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    property_id = db.Column(db.String(36), db.ForeignKey('properties.id'), nullable=False)
    unit_number = db.Column(db.String(50), nullable=False)
    floor_number = db.Column(db.String(50), nullable=True)
    rent_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False)  # occupied, vacant, under-maintenance
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    leases = db.relationship('Lease', backref='unit', lazy=True, cascade='all, delete-orphan')
    rent_invoices = db.relationship('RentInvoice', backref='unit_ref', lazy=True)
    maintenance_requests = db.relationship('MaintenanceRequest', backref='unit_req', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'property_id': self.property_id,
            'unit_number': self.unit_number,
            'floor_number': self.floor_number,
            'rent_amount': self.rent_amount,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class Lease(db.Model):
    __tablename__ = 'leases'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    unit_id = db.Column(db.String(36), db.ForeignKey('units.id'), nullable=False)
    tenant_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    monthly_rent = db.Column(db.Float, nullable=False)
    deposit = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False)  # active, expired, terminated
    document_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    rent_invoices = db.relationship('RentInvoice', backref='lease_ref', lazy=True)
    payments = db.relationship('Payment', backref='lease_ref', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'unit_id': self.unit_id,
            'tenant_id': self.tenant_id,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'monthly_rent': self.monthly_rent,
            'deposit': self.deposit,
            'status': self.status,
            'document_url': self.document_url,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class RentInvoice(db.Model):
    __tablename__ = 'rentinvoices'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    unit_id = db.Column(db.String(36), db.ForeignKey('units.id'), nullable=False)
    landlord_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    tenant_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    lease_id = db.Column(db.String(36), db.ForeignKey('leases.id'), nullable=False)
    invoice_date = db.Column(db.Date, nullable=False)
    invoice_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False)  # pending, paid, overdue
    paid_date = db.Column(db.Date, nullable=True)
    payment_id = db.Column(db.String(36), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign Keys
    landlord = db.relationship('User', foreign_keys=[landlord_id], backref='rent_invoices_as_landlord')
    tenant = db.relationship('User', foreign_keys=[tenant_id], backref='rent_invoices_as_tenant')
    
    def to_dict(self):
        return {
            'id': self.id,
            'unit_id': self.unit_id,
            'landlord_id': self.landlord_id,
            'tenant_id': self.tenant_id,
            'lease_id': self.lease_id,
            'invoice_date': self.invoice_date.isoformat(),
            'invoice_amount': self.invoice_amount,
            'status': self.status,
            'paid_date': self.paid_date.isoformat() if self.paid_date else None,
            'payment_id': self.payment_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lease_id = db.Column(db.String(36), db.ForeignKey('leases.id'), nullable=False)
    invoice_id = db.Column(db.String(36), db.ForeignKey('rentinvoices.id'), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    paid_date = db.Column(db.Date, nullable=True)
    payment_reference = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(50), nullable=False)  # pending, paid, failed
    payment_method = db.Column(db.String(50), nullable=True)  # mpesa, card, bank_transfer
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'lease_id': self.lease_id,
            'invoice_id': self.invoice_id,
            'amount': self.amount,
            'due_date': self.due_date.isoformat(),
            'paid_date': self.paid_date.isoformat() if self.paid_date else None,
            'payment_reference': self.payment_reference,
            'status': self.status,
            'payment_method': self.payment_method,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class MaintenanceRequest(db.Model):
    __tablename__ = 'maintenance_requests'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    unit_id = db.Column(db.String(36), db.ForeignKey('units.id'), nullable=False)
    tenant_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    landlord_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    status = db.Column(db.String(50), nullable=False)  # pending, in-progress, completed, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'unit_id': self.unit_id,
            'tenant_id': self.tenant_id,
            'landlord_id': self.landlord_id,
            'title': self.title,
            'description': self.description,
            'image_url': self.image_url,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    recipient_user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sender = db.relationship('User', foreign_keys=[user_id], backref='notifications_sent')
    recipient = db.relationship('User', foreign_keys=[recipient_user_id], backref='notifications_received')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'recipient_user_id': self.recipient_user_id,
            'message': self.message,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat()
        }
