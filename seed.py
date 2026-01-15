import os
from app import create_app
from extensions import db
# 🟢 UPDATED: Added PropertyImage to imports
from models import User, Property, Unit, Lease, Notification, MaintenanceRequest, RentInvoice, Payment, PropertyImage
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import uuid

app = create_app()

def seed_database():
    with app.app_context():
        print("🚀 Starting PostgreSQL-Compatible Seed...")
        
        # 1. THE POSTGRESQL CASCADE FIX
        print("🧹 Dropping tables with CASCADE...")
        db.session.execute(db.text('''
            DROP TABLE IF EXISTS payments CASCADE;
            DROP TABLE IF EXISTS rent_invoices CASCADE;
            DROP TABLE IF EXISTS maintenance_requests CASCADE;
            DROP TABLE IF EXISTS notifications CASCADE;
            DROP TABLE IF EXISTS leases CASCADE;
            DROP TABLE IF EXISTS units CASCADE;
            DROP TABLE IF EXISTS property_images CASCADE;
            DROP TABLE IF EXISTS properties CASCADE;
            DROP TABLE IF EXISTS users CASCADE;
        '''))
        db.session.commit()

        print("🏗️ Rebuilding database schema...")
        db.create_all()

        # 2. SEED USERS
        print("👤 Seeding users...")
        users_data = [
            {"full_name": "System Admin", "email": "admin@homehub.com", "password": "admin123", "role": "admin", "phone": "0700000000"},
            {"full_name": "John Landlord", "email": "john.landlord@homehub.com", "password": "landlord123", "role": "landlord", "phone": "0711111111"},
            {"full_name": "Mary Landlord", "email": "mary.landlord@homehub.com", "password": "landlord123", "role": "landlord", "phone": "0712222222"},
            {"full_name": "Tom Tenant", "email": "tom.tenant@homehub.com", "password": "tenant123", "role": "tenant", "phone": "0721111111"},
            {"full_name": "Jane Tenant", "email": "jane.tenant@homehub.com", "password": "tenant123", "role": "tenant", "phone": "0722222222"},
        ]

        for u in users_data:
            user = User(
                id=str(uuid.uuid4()), # 🟢 Explicit UUID for users
                full_name=u["full_name"],
                email=u["email"],
                password_hash=generate_password_hash(u["password"]),
                role=u["role"],
                phone_number=u["phone"],
                status='approved' if u["role"] == 'landlord' else 'active'
            )
            db.session.add(user)
        db.session.commit()

        # 3. SEED PROPERTIES (With Extra Images)
        print("🏠 Seeding expanded property list with gallery images...")
        
        properties_list = [
            {
                "name": "Green Villa", "address": "123 Green St", "city": "Nairobi", "landlord_email": "john.landlord@homehub.com", 
                "status": "approved", "price": 85000, "bedrooms": 4, "bathrooms": 3, 
                "description": "Beautiful villa with a large garden and modern finishes.", 
                "image_url": "https://images.unsplash.com/photo-1580587771525-78b9dba3b91d?w=800",
                # 🟢 NEW: Extra Images (Kitchen, Bedroom, Bath)
                "extra_images": [
                    "https://images.unsplash.com/photo-1556911220-e15b29be8c8f?w=800", # Kitchen
                    "https://images.unsplash.com/photo-1616594039964-40891a909d99?w=800", # Bedroom
                    "https://images.unsplash.com/photo-1584622650111-993a426fbf0a?w=800", # Bathroom
                    "https://images.unsplash.com/photo-1572331165267-854da2b8f98c?w=800"  # Living Room
                ]
            },
            {
                "name": "Blue Apartment", "address": "45 Blue Ave", "city": "Nairobi", "landlord_email": "john.landlord@homehub.com", 
                "status": "pending", "price": 45000, "bedrooms": 2, "bathrooms": 1, 
                "description": "Cozy apartment near city center.", 
                "image_url": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800",
                "extra_images": [
                    "https://images.unsplash.com/photo-1484154218962-a1c002085d2f?w=800", # Kitchen
                    "https://images.unsplash.com/photo-1595526114035-0d45ed16cfbf?w=800", # Bedroom
                    "https://images.unsplash.com/photo-1507089947368-19c1da9775ae?w=800"  # Interior
                ]
            },
            {
                "name": "Red House", "address": "78 Red Rd", "city": "Mombasa", "landlord_email": "mary.landlord@homehub.com", 
                "status": "approved", "price": 60000, "bedrooms": 3, "bathrooms": 2, 
                "description": "Traditional Swahili style house.", 
                "image_url": "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=800",
                "extra_images": [
                    "https://images.unsplash.com/photo-1598928506311-c55ded91a20c?w=800", # Interior
                    "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800"  # Pool/View
                ]
            },
            {
                "name": "Sunshine Flats", "address": "22 Sunshine Ln", "city": "Kisumu", "landlord_email": "mary.landlord@homehub.com", 
                "status": "pending", "price": 30000, "bedrooms": 2, "bathrooms": 1, 
                "description": "Affordable flats with lake views.", 
                "image_url": "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=800",
                "extra_images": [
                    "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800", # Room
                    "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=800"  # Living
                ]
            },
            {
                "name": "The Westlands Penthouse", "address": "Skyline Tower", "city": "Nairobi", "landlord_email": "john.landlord@homehub.com", 
                "status": "approved", "price": 250000, "bedrooms": 4, "bathrooms": 5, 
                "description": "Exclusive penthouse with a private pool.", 
                "image_url": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800",
                "extra_images": [
                    "https://images.unsplash.com/photo-1576013551627-0cc20b96c2a7?w=800", # Pool
                    "https://images.unsplash.com/photo-1565538810643-b5bdb714032a?w=800", # Kitchen
                    "https://images.unsplash.com/photo-1631679706909-1844bbd07221?w=800"  # Living
                ]
            },
            {
                "name": "Savanna Starter Home", "address": "Milimani Block C", "city": "Nakuru", "landlord_email": "john.landlord@homehub.com", 
                "status": "approved", "price": 18000, "bedrooms": 1, "bathrooms": 1, 
                "description": "Compact bedsitter near the university.", 
                "image_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800",
                "extra_images": [
                     "https://images.unsplash.com/photo-1554995207-c18c203602cb?w=800"
                ]
            },
            {
                "name": "Karen Forest Cottage", "address": "Dagoretti Road", "city": "Nairobi", "landlord_email": "mary.landlord@homehub.com", 
                "status": "approved", "price": 120000, "bedrooms": 3, "bathrooms": 3, 
                "description": "Serene cottage in the woods.", 
                "image_url": "https://images.unsplash.com/photo-1600596542815-6ad4c728fdbe?w=800",
                "extra_images": [
                    "https://images.unsplash.com/photo-1510798831971-661eb04b3739?w=800", # Forest View
                    "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?w=800"  # Kitchen
                ]
            },
            {
                "name": "Nyali Beach Villa", "address": "Beach Road", "city": "Mombasa", "landlord_email": "mary.landlord@homehub.com", 
                "status": "approved", "price": 180000, "bedrooms": 5, "bathrooms": 4, 
                "description": "Expansive villa with beach access.", 
                "image_url": "https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=800",
                "extra_images": [
                    "https://images.unsplash.com/photo-1540555700478-4be289fbecef?w=800", # Beach
                    "https://images.unsplash.com/photo-1493809842364-78817add7ffb?w=800"  # Living
                ]
            },
            {
                "name": "Eldoret Student Hostels", "address": "Kapsoya Estate", "city": "Eldoret", "landlord_email": "john.landlord@homehub.com", 
                "status": "approved", "price": 12000, "bedrooms": 1, "bathrooms": 1, 
                "description": "Secure shared student amenities.", 
                "image_url": "https://images.unsplash.com/photo-1554995207-c18c203602cb?w=800",
                "extra_images": []
            },
            {
                "name": "Thika Greens Apartment", "address": "Exit 14", "city": "Thika", "landlord_email": "mary.landlord@homehub.com", 
                "status": "approved", "price": 40000, "bedrooms": 2, "bathrooms": 2, 
                "description": "Modern apartment in a gated community.", 
                "image_url": "https://images.unsplash.com/photo-1493809842364-78817add7ffb?w=800",
                "extra_images": [
                    "https://images.unsplash.com/photo-1588880331179-bc9b93a8cb5e?w=800" # Garden
                ]
            },
            {
                "name": "Kilimani Executive Suites", "address": "Argwings Kodhek", "city": "Nairobi", "landlord_email": "john.landlord@homehub.com", 
                "status": "approved", "price": 95000, "bedrooms": 2, "bathrooms": 2, 
                "description": "Fully furnished executive apartments.", 
                "image_url": "https://images.unsplash.com/photo-1484154218962-a1c002085d2f?w=800",
                "extra_images": [
                    "https://images.unsplash.com/photo-1524758631624-e2822e304c36?w=800", # Office/Desk
                    "https://images.unsplash.com/photo-1556910103-1c02745a30bf?w=800"  # Dining
                ]
            }
        ]

        for p_data in properties_list:
            landlord = User.query.filter_by(email=p_data["landlord_email"]).first()
            if not landlord: continue

            prop = Property(
                id=str(uuid.uuid4()), # 🟢 Explicit ID
                landlord_id=landlord.id,
                name=p_data["name"],
                address=p_data["address"],
                city=p_data["city"],
                country="Kenya",
                status=p_data["status"],
                price=p_data["price"],
                bedrooms=p_data["bedrooms"],
                bathrooms=p_data["bathrooms"],
                description=p_data["description"],
                image_url=p_data["image_url"]
            )
            db.session.add(prop)
            
            # 🟢 SEED EXTRA IMAGES
            for extra_img_url in p_data.get("extra_images", []):
                extra_img = PropertyImage(
                    property_id=prop.id,
                    image_url=extra_img_url
                )
                db.session.add(extra_img)
        
        db.session.commit()

        # 4. SEED UNITS (Required for 'Lease Now' functionality)
        print("🏢 Seeding units and floors...")
        
        # We need to fetch properties back from DB to get their IDs
        units_data = [
            {"prop": "Green Villa", "no": "A-101", "rent": 85000, "stat": "vacant"},
            {"prop": "Green Villa", "no": "A-102", "rent": 85000, "stat": "vacant"},
            {"prop": "Blue Apartment", "no": "B-201", "rent": 45000, "stat": "vacant"},
            {"prop": "Red House", "no": "C-301", "rent": 60000, "stat": "vacant"},
            {"prop": "Sunshine Flats", "no": "D-401", "rent": 30000, "stat": "vacant"}
        ]

        for u in units_data:
            property = Property.query.filter_by(name=u["prop"]).first()
            if property:
                unit = Unit(
                    id=str(uuid.uuid4()),
                    property_id=property.id,
                    unit_number=u["no"],
                    rent_amount=u["rent"],
                    status=u["stat"]
                )
                db.session.add(unit)

        # Fallback: Ensure every other property has a generic vacant unit
        all_props = Property.query.all()
        for p in all_props:
            existing_unit = Unit.query.filter_by(property_id=p.id).first()
            if not existing_unit:
                db.session.add(Unit(
                    id=str(uuid.uuid4()),
                    property_id=p.id,
                    unit_number="Unit 1",
                    rent_amount=p.price,
                    status="vacant"
                ))
        db.session.commit()

        # 5. CREATE ACTIVE LEASE FOR TOM (For Maintenance Testing)
        print("📝 Creating Lease for Tom Tenant...")
        tom = User.query.filter_by(email="tom.tenant@homehub.com").first()
        green_villa = Property.query.filter_by(name="Green Villa").first()
        
        # Find Unit A-101 in Green Villa
        unit_101 = Unit.query.filter_by(property_id=green_villa.id, unit_number="A-101").first()
        
        if tom and unit_101:
            lease = Lease(
                id=str(uuid.uuid4()),
                unit_id=unit_101.id, # 🟢 Linked Correctly
                tenant_id=tom.id,
                rent_amount=85000,
                status='active',
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=365)
            )
            unit_101.status = 'occupied' # Mark unit as taken
            db.session.add(lease)
            db.session.commit()
            print(f"   - Created Active Lease for Tom at Green Villa (Unit A-101)")

        print("✅ Perfect Seed Complete! Database is ready.")

if __name__ == '__main__':
    seed_database()