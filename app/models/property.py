from app import db
from datetime import datetime

class Property(db.Model):
    __tablename__ = "properties"

    id = db.Column(db.Integer, primary_key=True)
    landlord_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255))
    city = db.Column(db.String(100))
    country = db.Column(db.String(100))
    description = db.Column(db.Text)
    image_url = db.Column(db.Text)
    status = db.Column(db.String(50))  # approved, pending
    comment = db.Column(db.Text)
    evidence_of_ownership = db.Column(db.Text)
    lrn_no = db.Column(db.String(50))
    location = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to units
    units = db.relationship("Unit", backref="property", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "landlord_id": self.landlord_id,
            "name": self.name,
            "address": self.address,
            "city": self.city,
            "country": self.country,
            "description": self.description,
            "image_url": self.image_url,
            "status": self.status,
            "comment": self.comment,
            "evidence_of_ownership": self.evidence_of_ownership,
            "lrn_no": self.lrn_no,
            "location": self.location,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
