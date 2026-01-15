import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from datetime import timedelta
from dotenv import load_dotenv
# 🟢 Import text to run raw SQL
from sqlalchemy import text

# 🟢 IMPORT FROM EXTENSIONS
from extensions import db
# 🟢 Ensure all models are imported so create_all() works
from models import User, Property, Unit, Lease, Invoice, Payment

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)

    # --- CONFIGURATION ---
    uri = os.getenv('DATABASE_URL', 'sqlite:///homehub.db')
    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Security Keys
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'super-secret-key-change-this')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

    # File Uploads
    app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')

    # --- INITIALIZE EXTENSIONS ---
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

    db.init_app(app)
    migrate = Migrate(app, db)
    jwt = JWTManager(app)

    # 🟢 HEADER HANDLER
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', 'https://homehub-project.onrender.com')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,PATCH,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

    # --- REGISTER BLUEPRINTS ---
    from routes.auth import auth_bp
    from routes.properties import properties_bp
    from routes.leases import leases_bp
    from routes.users import users_bp
    from routes.maintenance import maintenance_bp
    from routes.payments import payments_bp
    # 🟢 NEW: Import Admin Blueprint
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(properties_bp, url_prefix='/api/properties')
    app.register_blueprint(leases_bp, url_prefix='/api/leases')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(maintenance_bp, url_prefix='/api/maintenance')
    app.register_blueprint(payments_bp, url_prefix='/api/payments')
    # 🟢 NEW: Register Admin Blueprint
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    # --- ROUTES ---
    @app.route('/uploads/<path:filename>')
    def serve_uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    @app.route('/')
    def index():
        return "HomeHub Backend is Running! 🚀"

    # --- TEMPORARY SEED ROUTE (With Fix) ---
    @app.route('/api/admin/force-seed-db-123')
    def force_seed():
        try:
            # 🟢 CRITICAL FIX: Manually drop the "ghost" tables first
            # We use CASCADE to force them to let go of the 'leases' table
            with app.app_context():
                with db.session.begin():
                    db.session.execute(text("DROP TABLE IF EXISTS rent_invoices CASCADE;"))
                    db.session.execute(text("DROP TABLE IF EXISTS payments CASCADE;"))
                    db.session.execute(text("DROP TABLE IF EXISTS invoices CASCADE;"))

            # Now standard drop_all will work without conflicts
            db.drop_all()
            db.create_all()
            
            from seed import seed_database
            seed_database()
            return "✅ Database Wiped, Recreated, and Seeded Successfully!", 200
        except Exception as e:
            return f"❌ Seed Failed: {str(e)}", 500

    return app

# Entry point
if __name__ == '__main__':
    app = create_app()

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    app.run(debug=True, port=5000)