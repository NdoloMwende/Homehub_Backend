import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

# --- USER MODEL ---
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'landlord', 'tenant', 'admin'
    phone_number = db.Column(db.String(20))
    
    # Verification Fields (Maintained)
    status = db.Column(db.String(20), default='pending')
    national_id = db.Column(db.String(50))
    kra_pin = db.Column(db.String(50))
    evidence_of_identity = db.Column(db.String(255))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    properties = db.relationship('Property', backref='landlord', lazy=True)
    leases = db.relationship('Lease', backref='tenant', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)
    maintenance_requests = db.relationship('MaintenanceRequest', backref='tenant', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'status': self.status,
            'phone_number': self.phone_number
        }

# --- PROPERTY MODEL ---
class Property(db.Model):
    __tablename__ = 'properties'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    landlord_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    address = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    country = db.Column(db.String(100), default="Kenya")
    location = db.Column(db.String(100))
    
    price = db.Column(db.Float, nullable=False)
    bedrooms = db.Column(db.Integer, default=0)
    bathrooms = db.Column(db.Integer, default=0)
    square_feet = db.Column(db.Integer, default=0)
    
    property_type = db.Column(db.String(50), default='apartment')
    amenities = db.Column(db.Text)
    
    image_url = db.Column(db.String(255))
    
    status = db.Column(db.String(20), default='Available')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    images = db.relationship('PropertyImage', backref='property', lazy=True, cascade="all, delete-orphan")
    units = db.relationship('Unit', backref='property', lazy=True, cascade="all, delete-orphan")
    maintenance_requests = db.relationship('MaintenanceRequest', backref='property', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'landlord_id': self.landlord_id,
            'name': self.name,
            'description': self.description,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'country': self.country,
            'price': self.price,
            'bedrooms': self.bedrooms,
            'bathrooms': self.bathrooms,
            'square_feet': self.square_feet,
            'property_type': self.property_type,
            'image_url': self.image_url,
            'images': [img.to_dict() for img in self.images],
            'status': self.status
        }

# --- PROPERTY IMAGE MODEL ---
class PropertyImage(db.Model):
    __tablename__ = 'property_images'
    
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.String(36), db.ForeignKey('properties.id'), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)

    def to_dict(self):
        return {'id': self.id, 'image_url': self.image_url}

# --- UNIT MODEL ---
class Unit(db.Model):
    __tablename__ = 'units'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    property_id = db.Column(db.String(36), db.ForeignKey('properties.id'), nullable=False)
    unit_number = db.Column(db.String(50), nullable=False)
    rent_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='vacant')

    leases = db.relationship('Lease', backref='unit', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'unit_number': self.unit_number,
            'rent_amount': self.rent_amount,
            'status': self.status
        }

# --- LEASE MODEL ---
class Lease(db.Model):
    __tablename__ = 'leases'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    unit_id = db.Column(db.String(36), db.ForeignKey('units.id'), nullable=False)
    tenant_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    rent_amount = db.Column(db.Float)
    
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    invoices = db.relationship('RentInvoice', backref='lease', lazy=True)
    payments = db.relationship('Payment', backref='lease', lazy=True)

    def to_dict(self):
        # 🟢 UPDATED: Resolving Property info for Tenant history
        prop = self.unit.property if self.unit and self.unit.property else None
        
        return {
            'id': self.id,
            'unit_id': self.unit_id,
            'tenant_id': self.tenant_id,
            'property_name': prop.name if prop else "Unknown Property",
            'unit_number': self.unit.unit_number if self.unit else "Main",
            'status': self.status,
            'rent_amount': self.rent_amount,
            # 🟢 UPDATED: Formatting dates for React
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'created_at': self.created_at.isoformat()
        }

# --- NOTIFICATION MODEL ---
class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'message': self.message,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat()
        }

# --- MAINTENANCE REQUEST MODEL ---
class MaintenanceRequest(db.Model):
    __tablename__ = 'maintenance_requests'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    property_id = db.Column(db.String(36), db.ForeignKey('properties.id'), nullable=False)
    tenant_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default='medium')
    status = db.Column(db.String(20), default='pending')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'property_id': self.property_id,
            'tenant_id': self.tenant_id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }

# --- RENT INVOICE MODEL ---
class RentInvoice(db.Model):
    __tablename__ = 'rent_invoices'

    id = db.Column(db.Integer, primary_key=True)
    lease_id = db.Column(db.String(36), db.ForeignKey('leases.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'lease_id': self.lease_id,
            'amount': self.amount,
            'due_date': self.due_date.isoformat(),
            'status': self.status
        }

# --- PAYMENT MODEL ---
class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    lease_id = db.Column(db.String(36), db.ForeignKey('leases.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date_paid = db.Column(db.DateTime, default=datetime.utcnow)
    method = db.Column(db.String(50)) # e.g., M-Pesa, Cash

    def to_dict(self):
        return {
            'id': self.id,
            'amount': self.amount,
            'date_paid': self.date_paid.isoformat(),
            'method': self.method
        }