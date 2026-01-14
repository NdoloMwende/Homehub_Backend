import os
from app import create_app
from extensions import db
from models import User, Property, Unit
from werkzeug.security import generate_password_hash

app = create_app()

def seed_database():
    with app.app_context():
        print("🚀 Initializing Perfect Seed...")
        
        # 1. RESET DATABASE
        db.drop_all()
        db.create_all()

        # 2. SEED USERS
        print("👤 Seeding Users...")
        users_data = [
            {"full_name": "System Admin", "email": "admin@homehub.com", "password": "admin123", "role": "admin", "phone": "0700000000"},
            {"full_name": "John Landlord", "email": "john.landlord@homehub.com", "password": "landlord123", "role": "landlord", "phone": "0711111111"},
            {"full_name": "Mary Landlord", "email": "mary.landlord@homehub.com", "password": "landlord123", "role": "landlord", "phone": "0712222222"},
            {"full_name": "Tom Tenant", "email": "tom.tenant@homehub.com", "password": "tenant123", "role": "tenant", "phone": "0721111111"},
            {"full_name": "Jane Tenant", "email": "jane.tenant@homehub.com", "password": "tenant123", "role": "tenant", "phone": "0722222222"},
            {"full_name": "Peter Tenant", "email": "peter.tenant@homehub.com", "password": "tenant123", "role": "tenant", "phone": "0723333333"},
        ]

        for u in users_data:
            user = User(
                full_name=u["full_name"],
                email=u["email"],
                password_hash=generate_password_hash(u["password"]),
                role=u["role"],
                phone_number=u["phone"],
                status='approved' if u["role"] == 'landlord' else 'active'
            )
            db.session.add(user)
        db.session.commit()

        # 3. SEED PROPERTIES
        print("🏠 Seeding Properties...")
        properties_data = [
            {"name": "Green Villa", "address": "123 Green St", "city": "Nairobi", "landlord_email": "john.landlord@homehub.com", "status": "approved", "price": 85000, "bedrooms": 4, "bathrooms": 3, "description": "Beautiful villa with a large garden.", "image_url": "https://images.unsplash.com/photo-1580587771525-78b9dba3b91d?w=800"},
            {"name": "Blue Apartment", "address": "45 Blue Ave", "city": "Nairobi", "landlord_email": "john.landlord@homehub.com", "status": "pending", "price": 45000, "bedrooms": 2, "bathrooms": 1, "description": "Cozy apartment near city center.", "image_url": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800"},
            {"name": "Red House", "address": "78 Red Rd", "city": "Mombasa", "landlord_email": "mary.landlord@homehub.com", "status": "approved", "price": 60000, "bedrooms": 3, "bathrooms": 2, "description": "Traditional Swahili style house.", "image_url": "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=800"},
            {"name": "Sunshine Flats", "address": "22 Sunshine Ln", "city": "Kisumu", "landlord_email": "mary.landlord@homehub.com", "status": "pending", "price": 30000, "bedrooms": 2, "bathrooms": 1, "description": "Affordable flats with lake views.", "image_url": "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=800"},
            {"name": "The Westlands Penthouse", "address": "Skyline Tower", "city": "Nairobi", "landlord_email": "john.landlord@homehub.com", "status": "approved", "price": 250000, "bedrooms": 4, "bathrooms": 5, "description": "Exclusive penthouse, private pool.", "image_url": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800"},
            {"name": "Savanna Starter Home", "address": "Milimani Block C", "city": "Nakuru", "landlord_email": "john.landlord@homehub.com", "status": "approved", "price": 18000, "bedrooms": 1, "bathrooms": 1, "description": "Compact bedsitter near university.", "image_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800"},
            {"name": "Karen Forest Cottage", "address": "Dagoretti Road", "city": "Nairobi", "landlord_email": "mary.landlord@homehub.com", "status": "approved", "price": 120000, "bedrooms": 3, "bathrooms": 3, "description": "Serene cottage in the woods.", "image_url": "https://images.unsplash.com/photo-1600596542815-6ad4c728fdbe?w=800"},
            {"name": "Nyali Beach Villa", "address": "Beach Road", "city": "Mombasa", "landlord_email": "mary.landlord@homehub.com", "status": "approved", "price": 180000, "bedrooms": 5, "bathrooms": 4, "description": "Expansive villa with beach access.", "image_url": "https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=800"},
            {"name": "Eldoret Student Hostels", "address": "Kapsoya Estate", "city": "Eldoret", "landlord_email": "john.landlord@homehub.com", "status": "approved", "price": 12000, "bedrooms": 1, "bathrooms": 1, "description": "Secure shared amenities.", "image_url": "https://images.unsplash.com/photo-1554995207-c18c203602cb?w=800"},
            {"name": "Thika Greens Apartment", "address": "Exit 14", "city": "Thika", "landlord_email": "mary.landlord@homehub.com", "status": "approved", "price": 40000, "bedrooms": 2, "bathrooms": 2, "description": "Modern gated community.", "image_url": "https://images.unsplash.com/photo-1493809842364-78817add7ffb?w=800"},
            {"name": "Kilimani Executive Suites", "address": "Argwings Kodhek", "city": "Nairobi", "landlord_email": "john.landlord@homehub.com", "status": "approved", "price": 95000, "bedrooms": 2, "bathrooms": 2, "description": "Fully furnished executive suites.", "image_url": "https://images.unsplash.com/photo-1484154218962-a1c002085d2f?w=800"}
        ]

        for p in properties_data:
            landlord = User.query.filter_by(email=p["landlord_email"]).first()
            if landlord:
                prop = Property(
                    landlord_id=landlord.id, name=p["name"], address=p["address"],
                    city=p["city"], country="Kenya", status=p["status"],
                    price=p["price"], bedrooms=p["bedrooms"], bathrooms=p["bathrooms"],
                    description=p["description"], image_url=p["image_url"]
                )
                db.session.add(prop)
        db.session.commit()

        # 4. SEED UNITS
        print("🏢 Seeding Units...")
        units_data = [
            {"prop": "Green Villa", "no": "101", "floor": "1", "rent": 50000, "stat": "vacant"},
            {"prop": "Green Villa", "no": "102", "floor": "1", "rent": 55000, "stat": "occupied"},
            {"prop": "Blue Apartment", "no": "201", "floor": "2", "rent": 40000, "stat": "vacant"},
            {"prop": "Red House", "no": "301", "floor": "3", "rent": 60000, "stat": "vacant"},
            {"prop": "Sunshine Flats", "no": "401", "floor": "4", "rent": 35000, "stat": "vacant"}
        ]

        # First, add the specific units from your list
        for u in units_data:
            property = Property.query.filter_by(name=u["prop"]).first()
            if property:
                unit = Unit(
                    property_id=property.id, unit_number=u["no"],
                    rent_amount=u["rent"], status=u["stat"]
                )
                db.session.add(unit)

        # Second, ensure EVERY other property has at least one vacant unit for testing
        all_props = Property.query.all()
        for p in all_props:
            existing_unit = Unit.query.filter_by(property_id=p.id).first()
            if not existing_unit:
                unit = Unit(
                    property_id=p.id, unit_number="Unit 1",
                    rent_amount=p.price, status="vacant"
                )
                db.session.add(unit)

        db.session.commit()
        print("✅ Ultimate Seed Complete! Everything is perfectly linked.")

if __name__ == '__main__':
    seed_database()