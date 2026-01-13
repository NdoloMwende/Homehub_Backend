import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from models import Property, User

app = create_app()

# -------------------------
# EXPANDED PROPERTY LIST (11 Properties)
# -------------------------
properties = [
    # --- ORIGINAL 4 (Kept for consistency) ---
    {
        "name": "Green Villa",
        "address": "123 Green St",
        "city": "Nairobi",
        "country": "Kenya",
        "landlord_email": "john.landlord@homehub.com",
        "status": "approved", # ✅ Visible to Tenants
        "price": 85000,
        "bedrooms": 4,
        "bathrooms": 3,
        "description": "A beautiful green villa in the suburbs with a large garden.",
        "image_url": "https://images.unsplash.com/photo-1580587771525-78b9dba3b91d?auto=format&fit=crop&w=800&q=80"
    },
    {
        "name": "Blue Apartment",
        "address": "45 Blue Ave",
        "city": "Nairobi",
        "country": "Kenya",
        "landlord_email": "john.landlord@homehub.com",
        "status": "pending", # 🔒 HIDDEN (For Admin Demo)
        "price": 45000,
        "bedrooms": 2,
        "bathrooms": 1,
        "description": "Cozy apartment near the city center. Perfect for young professionals.",
        "image_url": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?auto=format&fit=crop&w=800&q=80"
    },
    {
        "name": "Red House",
        "address": "78 Red Rd",
        "city": "Mombasa",
        "country": "Kenya",
        "landlord_email": "mary.landlord@homehub.com",
        "status": "approved", # ✅ Visible
        "price": 60000,
        "bedrooms": 3,
        "bathrooms": 2,
        "description": "Traditional Swahili style house near the beach.",
        "image_url": "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?auto=format&fit=crop&w=800&q=80"
    },
    {
        "name": "Sunshine Flats",
        "address": "22 Sunshine Ln",
        "city": "Kisumu",
        "country": "Kenya",
        "landlord_email": "mary.landlord@homehub.com",
        "status": "pending", # 🔒 HIDDEN
        "price": 30000,
        "bedrooms": 2,
        "bathrooms": 1,
        "description": "Affordable flats with great lake views.",
        "image_url": "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=800&q=80"
    },

    # --- 7 NEW PROPERTIES (Diverse Prices & Locations) ---
    
    # 1. High-End Luxury (Nairobi - Westlands)
    {
        "name": "The Westlands Penthouse",
        "address": "Skyline Tower, Westlands",
        "city": "Nairobi",
        "country": "Kenya",
        "landlord_email": "john.landlord@homehub.com",
        "status": "approved", # ✅ Visible
        "price": 250000,
        "bedrooms": 4,
        "bathrooms": 5,
        "description": "Exclusive penthouse with panoramic city views, private pool, and gym access.",
        "image_url": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=800&q=80"
    },

    # 2. Budget Friendly (Nakuru)
    {
        "name": "Savanna Starter Home",
        "address": "Milimani Block C",
        "city": "Nakuru",
        "country": "Kenya",
        "landlord_email": "john.landlord@homehub.com",
        "status": "approved", # ✅ Visible
        "price": 18000,
        "bedrooms": 1,
        "bathrooms": 1,
        "description": "Compact and secure bedsitter near the university.",
        "image_url": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=800&q=80"
    },

    # 3. Upper Mid-Range (Nairobi - Karen)
    {
        "name": "Karen Forest Cottage",
        "address": "Dagoretti Road",
        "city": "Nairobi",
        "country": "Kenya",
        "landlord_email": "mary.landlord@homehub.com",
        "status": "approved", # ✅ Visible
        "price": 120000,
        "bedrooms": 3,
        "bathrooms": 3,
        "description": "Serene cottage surrounded by lush trees. Ideal for families.",
        "image_url": "https://images.unsplash.com/photo-1600596542815-6ad4c728fdbe?auto=format&fit=crop&w=800&q=80"
    },

    # 4. Coastal Holiday Home (Mombasa - Nyali)
    {
        "name": "Nyali Beach Villa",
        "address": "Beach Road, Nyali",
        "city": "Mombasa",
        "country": "Kenya",
        "landlord_email": "mary.landlord@homehub.com",
        "status": "approved", # ✅ Visible
        "price": 180000,
        "bedrooms": 5,
        "bathrooms": 4,
        "description": "Expansive villa with direct beach access and guest wing.",
        "image_url": "https://images.unsplash.com/photo-1613490493576-7fde63acd811?auto=format&fit=crop&w=800&q=80"
    },

    # 5. Student/Starter (Eldoret)
    {
        "name": "Eldoret Student Hostels",
        "address": "Kapsoya Estate",
        "city": "Eldoret",
        "country": "Kenya",
        "landlord_email": "john.landlord@homehub.com",
        "status": "approved", # ✅ Visible
        "price": 12000,
        "bedrooms": 1,
        "bathrooms": 1,
        "description": "Shared amenities, secure, and walking distance to town.",
        "image_url": "https://images.unsplash.com/photo-1554995207-c18c203602cb?auto=format&fit=crop&w=800&q=80"
    },

    # 6. Mid-Range Apartment (Thika)
    {
        "name": "Thika Greens Apartment",
        "address": "Superhighway Exit 14",
        "city": "Thika",
        "country": "Kenya",
        "landlord_email": "mary.landlord@homehub.com",
        "status": "approved", # ✅ Visible
        "price": 40000,
        "bedrooms": 2,
        "bathrooms": 2,
        "description": "Modern apartment in a gated community with ample parking.",
        "image_url": "https://images.unsplash.com/photo-1493809842364-78817add7ffb?auto=format&fit=crop&w=800&q=80"
    },

    # 7. Executive Suite (Nairobi - Kilimani)
    {
        "name": "Kilimani Executive Suites",
        "address": "Argwings Kodhek Rd",
        "city": "Nairobi",
        "country": "Kenya",
        "landlord_email": "john.landlord@homehub.com",
        "status": "approved", # ✅ Visible
        "price": 95000,
        "bedrooms": 2,
        "bathrooms": 2,
        "description": "Fully furnished executive apartments with gym and elevator.",
        "image_url": "https://images.unsplash.com/photo-1484154218962-a1c002085d2f?auto=format&fit=crop&w=800&q=80"
    }
]

with app.app_context():
    print(f"🌱 Seeding {len(properties)} properties...")
    
    for p in properties:
        landlord = User.query.filter_by(email=p["landlord_email"]).first()
        if not landlord:
            print(f"   ⚠️  Landlord {p['landlord_email']} not found. Skipping {p['name']}.")
            continue

        # Check for duplicates to prevent crashes on re-runs
        existing_prop = Property.query.filter_by(name=p["name"], landlord_id=landlord.id).first()
        if existing_prop:
            print(f"   ℹ️  Skipping {p['name']} (Already exists)")
            continue

        prop = Property(
            landlord_id=landlord.id,
            name=p["name"],
            address=p["address"],
            city=p["city"],
            country=p["country"],
            status=p["status"],
            # Added Fields for Marketplace Display
            price=p.get("price"),
            bedrooms=p.get("bedrooms"),
            bathrooms=p.get("bathrooms"),
            description=p.get("description"),
            image_url=p.get("image_url")
        )
        db.session.add(prop)

    db.session.commit()
    print("✅ Properties seeded successfully!")