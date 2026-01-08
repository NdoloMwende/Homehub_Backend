from app import create_app, db
from models import User
from werkzeug.security import generate_password_hash

app = create_app()

users = [
    {"full_name": "System Admin", "email": "admin@homehub.com", "password": "admin123", "role": "admin", "phone": "0700000000"},
    {"full_name": "John Landlord", "email": "john.landlord@homehub.com", "password": "landlord123", "role": "landlord", "phone": "0711111111"},
    {"full_name": "Mary Landlord", "email": "mary.landlord@homehub.com", "password": "landlord123", "role": "landlord", "phone": "0712222222"},
    {"full_name": "Tom Tenant", "email": "tom.tenant@homehub.com", "password": "tenant123", "role": "tenant", "phone": "0721111111"},
    {"full_name": "Jane Tenant", "email": "jane.tenant@homehub.com", "password": "tenant123", "role": "tenant", "phone": "0722222222"},
    {"full_name": "Peter Tenant", "email": "peter.tenant@homehub.com", "password": "tenant123", "role": "tenant", "phone": "0723333333"},
]

with app.app_context():
    for u in users:
        if User.query.filter_by(email=u["email"]).first():
            continue  # skip if already exists
        user = User(
            full_name=u["full_name"],
            email=u["email"],
            password_hash=generate_password_hash(u["password"]),
            role=u["role"],
            phone=u["phone"],
            status='pending' if u["role"] == 'landlord' else 'active',
            is_active=True
        )
        db.session.add(user)
    db.session.commit()
    print("Users seeded successfully!")
