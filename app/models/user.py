from app import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # admin / landlord / tenant
    phone = db.Column(db.String(50))
    profile_image_url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(50))
    comment = db.Column(db.Text)
    national_id = db.Column(db.String(50))
    kra_pin = db.Column(db.String(50))
    evidence_of_identity = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.full_name}>"
