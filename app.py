import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from datetime import timedelta
from dotenv import load_dotenv
from sqlalchemy import text

# IMPORT FROM EXTENSIONS
from extensions import db
from models import User, Property, Unit, Lease, Invoice, Payment

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)

    # --- CONFIGURATION ---
    uri = os.getenv('DATABASE_URL', 'sqlite:///homehub.db')
    if uri and uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Security Keys
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'super-secret-key-change-this')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

    # File Uploads
    app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')

    # --- INITIALIZE EXTENSIONS ---
    db.init_app(app)
    migrate = Migrate(app, db)
    jwt = JWTManager(app)

    # 🟢 THE FIX IS HERE:
    # We use ONLY this CORS block. 
    # We have DELETED the manual "@app.after_request" block that was causing the conflict.
    CORS(app, resources={r"/api/*": {
        "origins": [
            "https://homehub-project.onrender.com", 
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }})

    # --- REGISTER BLUEPRINTS ---
    from routes.auth import auth_bp
    from routes.properties import properties_bp
    from routes.leases import leases_bp
    from routes.users import users_bp
    from routes.maintenance import maintenance_bp
    from routes.payments import payments_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(properties_bp, url_prefix='/api/properties')
    app.register_blueprint(leases_bp, url_prefix='/api/leases')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(maintenance_bp, url_prefix='/api/maintenance')
    app.register_blueprint(payments_bp, url_prefix='/api/payments')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    # --- ROUTES ---
    @app.route('/uploads/<path:filename>')
    def serve_uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    @app.route('/')
    def index():
        return "HomeHub Backend is Running! 🚀"

    # --- TEMPORARY SEED ROUTE ---
    @app.route('/api/admin/force-seed-db-123')
    def force_seed():
        try:
            with app.app_context():
                with db.session.begin():
                    # Clear all tables cleanly
                    db.session.execute(text("DROP TABLE IF EXISTS payments CASCADE;"))
                    db.session.execute(text("DROP TABLE IF EXISTS invoices CASCADE;"))
                    db.session.execute(text("DROP TABLE IF EXISTS rent_invoices CASCADE;"))
                    db.session.execute(text("DROP TABLE IF EXISTS maintenance_requests CASCADE;"))
                    db.session.execute(text("DROP TABLE IF EXISTS notifications CASCADE;"))
                    db.session.execute(text("DROP TABLE IF EXISTS leases CASCADE;"))
                    db.session.execute(text("DROP TABLE IF EXISTS units CASCADE;"))
                    db.session.execute(text("DROP TABLE IF EXISTS property_images CASCADE;"))
                    db.session.execute(text("DROP TABLE IF EXISTS properties CASCADE;"))
                    db.session.execute(text("DROP TABLE IF EXISTS users CASCADE;"))
                    db.session.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE;"))

            db.drop_all()
            db.create_all()
            
            from seed import seed_database
            seed_database()
            return "✅ Database Wiped, Recreated, and Seeded Successfully!", 200
        except Exception as e:
            return f"❌ Seed Failed: {str(e)}", 500

    return app

if __name__ == '__main__':
    app = create_app()
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True, port=5000)