from app import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid

# ---------------------------------------------------------
# 🟢 1. NEW CLASS: Add this somewhere near the top (e.g., before Property)
# ---------------------------------------------------------
class PropertyImage(db.Model):
    __tablename__ = 'property_images'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    property_id = db.Column(db.String(36), db.ForeignKey('properties.id'), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'image_url': self.image_url
        }

class User(db.Model):
    # ... (Keep your User class exactly as it is) ...
    __tablename__ = 'users'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    profile_image_url = db.Column(db.String(500), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(50), nullable=False)
    comment = db.Column(db.Text, nullable=True)
    national_id = db.Column(db.String(50), nullable=True)
    kra_pin = db.Column(db.String(50), nullable=True)
    evidence_of_identity = db.Column(db.String(500), nullable=True)
    show_welcome = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(500), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(500), nullable=True) # This remains the "Main Thumbnail"
    status = db.Column(db.String(50), nullable=False)
    comment = db.Column(db.Text, nullable=True)
    evidence_of_ownership = db.Column(db.String(500), nullable=True)
    lrn_no = db.Column(db.String(50), nullable=True)
    location = db.Column(db.String(255), nullable=True)
    
    state = db.Column(db.String(100))
    price = db.Column(db.Float, nullable=True)
    bedrooms = db.Column(db.Integer, nullable=True)
    bathrooms = db.Column(db.Integer, nullable=True)
    square_feet = db.Column(db.Integer, nullable=True)
    property_type = db.Column(db.String(50), default='apartment')
    amenities = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    units = db.relationship('Unit', backref='property', lazy=True, cascade='all, delete-orphan')
    
    # ---------------------------------------------------------
    # 🟢 2. NEW RELATIONSHIP: Link to the images table
    # ---------------------------------------------------------
    images = db.relationship('PropertyImage', backref='property', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
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
            'title': self.name,
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
            'state': self.state,
            'price': self.price,
            'bedrooms': self.bedrooms,
            'bathrooms': self.bathrooms,
            'square_feet': self.square_feet,
            'property_type': self.property_type,
            'amenities': self.amenities,
            
            # ---------------------------------------------------------
            # 🟢 3. NEW FIELD: Return the gallery URLs to the frontend
            # ---------------------------------------------------------
            'gallery_images': [img.image_url for img in self.images],

            **landlord_data,

            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

# ... (Keep Unit, Lease, RentInvoice, Payment, MaintenanceRequest, Notification exactly as they are) ...