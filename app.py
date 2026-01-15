import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from datetime import timedelta
from dotenv import load_dotenv

# 🟢 IMPORT FROM EXTENSIONS (Matches your models.py setup)
from extensions import db
from models import User, Property, Unit, Lease

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)

    # --- CONFIGURATION ---
    # Database connection for PostgreSQL on Render or local SQLite
    # Handles Render's "postgres://" vs "postgresql://" requirement
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
    # 🟢 FIXED CORS: Maintains your production and local dev access
    # 🟢 UPDATE: Added "PATCH" to methods so Landlords can update status
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

    # 🟢 HEADER HANDLER: Ensures consistency across all responses
    # 🟢 UPDATE: Added "PATCH" here too
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', 'https://homehub-project.onrender.com')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,PATCH,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

    # --- REGISTER BLUEPRINTS (All Original Routes Maintained) ---
    from routes.auth import auth_bp
    from routes.properties import properties_bp
    from routes.leases import leases_bp
    from routes.users import users_bp
    from routes.maintenance import maintenance_bp
    # 🟢 NEW: IMPORT PAYMENTS
    from routes.payments import payments_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(properties_bp, url_prefix='/api/properties')
    app.register_blueprint(leases_bp, url_prefix='/api/leases')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(maintenance_bp, url_prefix='/api/maintenance')
    
    # 🟢 NEW: REGISTER PAYMENTS (Enables Invoicing & M-Pesa)
    app.register_blueprint(payments_bp, url_prefix='/api/payments')

    # --- ROUTES ---
    
    @app.route('/uploads/<path:filename>')
    def serve_uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    @app.route('/')
    def index():
        return "HomeHub Backend is Running! 🚀"

    # --- TEMPORARY SEED ROUTE (Forces Database Sync) ---
    @app.route('/api/admin/force-seed-db-123')
    def force_seed():
        try:
            # 🟢 CRITICAL: This ensures tables are dropped and recreated 
            # with your new columns (KRA PIN, National ID, Lease dates)
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

    # Ensure upload folder exists on startup
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    app.run(debug=True, port=5000)