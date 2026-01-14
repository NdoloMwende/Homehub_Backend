import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db  # 👈 IMPORT FROM EXTENSIONS (Not app!)

# --- USER MODEL ---
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'landlord', 'tenant', 'admin'
    phone_number = db.Column(db.String(20))
    
    # Verification Fields
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'active'
    national_id = db.Column(db.String(50))
    kra_pin = db.Column(db.String(50))
    evidence_of_identity = db.Column(db.String(255)) # Path to file
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    properties = db.relationship('Property', backref='landlord', lazy=True)
    leases = db.relationship('Lease', backref='tenant', lazy=True)

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
            'phone_number': self.phone_number,
            'national_id': self.national_id,
            'evidence_of_identity': self.evidence_of_identity
        }

# --- PROPERTY MODEL ---
class Property(db.Model):
    __tablename__ = 'properties'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    landlord_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    name = db.Column(db.String(100), nullable=False) # Or title
    description = db.Column(db.Text)
    address = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100)) # Used for County
    country = db.Column(db.String(100), default="Kenya") # 🟢 Added to fix your error
    location = db.Column(db.String(100))
    
    price = db.Column(db.Float, nullable=False)
    bedrooms = db.Column(db.Integer, default=0)
    bathrooms = db.Column(db.Integer, default=0)
    square_feet = db.Column(db.Integer, default=0)
    
    property_type = db.Column(db.String(50), default='apartment')
    amenities = db.Column(db.Text) # Comma separated string
    
    image_url = db.Column(db.String(255)) # Main cover image
    
    status = db.Column(db.String(20), default='Available')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    images = db.relationship('PropertyImage', backref='property', lazy=True, cascade="all, delete-orphan")
    units = db.relationship('Unit', backref='property', lazy=True, cascade="all, delete-orphan")

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

# --- UNIT MODEL (Critical for Leasing) ---
class Unit(db.Model):
    __tablename__ = 'units'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    property_id = db.Column(db.String(36), db.ForeignKey('properties.id'), nullable=False)
    unit_number = db.Column(db.String(50), nullable=False)
    rent_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='vacant') # vacant, occupied

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
    
    status = db.Column(db.String(20), default='pending') # pending, active, rejected, terminated
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'unit_id': self.unit_id,
            'tenant_id': self.tenant_id,
            'status': self.status,
            'rent_amount': self.rent_amount,
            'created_at': self.created_at.isoformat()
        }