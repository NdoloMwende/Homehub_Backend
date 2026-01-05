from app import db
from datetime import datetime

class Unit(db.Model):
    __tablename__ = "units"

    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey("properties.id"), nullable=False)
    unit_number = db.Column(db.String(50), nullable=False)
    floor_number = db.Column(db.String(50))
    rent_amount = db.Column(db.Integer)
    status = db.Column(db.String(50))  # available, occupied
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "property_id": self.property_id,
            "unit_number": self.unit_number,
            "floor_number": self.floor_number,
            "rent_amount": self.rent_amount,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
