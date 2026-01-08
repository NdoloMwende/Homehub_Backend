import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from models import Unit, Property, User

app = create_app()

# -------------------------
# Units to seed
# -------------------------
units = [
    {
        "property_name": "Green Villa",
        "unit_number": "101",
        "floor_number": "1",
        "rent_amount": 50000,
        "status": "vacant"
    },
    {
        "property_name": "Green Villa",
        "unit_number": "102",
        "floor_number": "1",
        "rent_amount": 55000,
        "status": "occupied"
    },
    {
        "property_name": "Blue Apartment",
        "unit_number": "201",
        "floor_number": "2",
        "rent_amount": 40000,
        "status": "vacant"
    },
    {
        "property_name": "Red House",
        "unit_number": "301",
        "floor_number": "3",
        "rent_amount": 60000,
        "status": "vacant"
    },
    {
        "property_name": "Sunshine Flats",
        "unit_number": "401",
        "floor_number": "4",
        "rent_amount": 35000,
        "status": "vacant"
    },
]

with app.app_context():
    for u in units:
        property = Property.query.filter_by(name=u["property_name"]).first()
        if not property:
            print(f"Property {u['property_name']} not found. Skipping unit {u['unit_number']}.")
            continue

        # Avoid duplicate units
        if Unit.query.filter_by(property_id=property.id, unit_number=u["unit_number"]).first():
            continue

        unit = Unit(
            property_id=property.id,
            unit_number=u["unit_number"],
            floor_number=u.get("floor_number"),
            rent_amount=u["rent_amount"],
            status=u["status"]
        )
        db.session.add(unit)

    db.session.commit()
    print("Units seeded successfully!")
