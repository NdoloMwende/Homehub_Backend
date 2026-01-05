from app import db
from datetime import datetime

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    full_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(50), nullable=False)  # admin, landlord, tenant
    phone = db.Column(db.String(20))

    profile_image_url = db.Column(db.Text)

    is_active = db.Column(db.Boolean, default=True)
    status = db.Column(db.String(50))  # approved, pending, active

    show_welcome = db.Column(db.Boolean, default=True)
    comment = db.Column(db.Text)

    national_id = db.Column(db.String(50))
    kra_pin = db.Column(db.String(50))

    evidence_of_identity = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "password_hash": self.password_hash,
            "role": self.role,
            "phone": self.phone,
            "profile_image_url": self.profile_image_url,
            "is_active": self.is_active,
            "status": self.status,
            "show_welcome": self.show_welcome,
            "comment": self.comment,
            "national_id": self.national_id,
            "kra_pin": self.kra_pin,
            "evidence_of_identity": self.evidence_of_identity,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
