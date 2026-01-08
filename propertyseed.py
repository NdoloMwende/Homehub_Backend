import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from models import Property, User

app = create_app()

# Properties with mixed status
properties = [
    {
        "name": "Green Villa",
        "address": "123 Green St",
        "city": "Nairobi",
        "country": "Kenya",
        "landlord_email": "john.landlord@homehub.com",
        "status": "approved"
    },
    {
        "name": "Blue Apartment",
        "address": "45 Blue Ave",
        "city": "Nairobi",
        "country": "Kenya",
        "landlord_email": "john.landlord@homehub.com",
        "status": "pending"
    },
    {
        "name": "Red House",
        "address": "78 Red Rd",
        "city": "Mombasa",
        "country": "Kenya",
        "landlord_email": "mary.landlord@homehub.com",
        "status": "approved"
    },
    {
        "name": "Sunshine Flats",
        "address": "22 Sunshine Ln",
        "city": "Kisumu",
        "country": "Kenya",
        "landlord_email": "mary.landlord@homehub.com",
        "status": "pending"
    },
]

with app.app_context():
    for p in properties:
        landlord = User.query.filter_by(email=p["landlord_email"]).first()
        if not landlord:
            print(f"Landlord {p['landlord_email']} not found. Skipping property {p['name']}.")
            continue

        # Avoid duplicates
        if Property.query.filter_by(name=p["name"], landlord_id=landlord.id).first():
            continue

        prop = Property(
            landlord_id=landlord.id,
            name=p["name"],
            address=p["address"],
            city=p["city"],
            country=p["country"],
            status=p["status"]  # use the mixed status
        )
        db.session.add(prop)

    db.session.commit()
    print("Properties seeded with mixed status successfully!")
