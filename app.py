import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from datetime import timedelta
from dotenv import load_dotenv

# 🟢 FIX 1: Import db strictly from extensions to avoid circular imports
from extensions import db
# Import models to ensure they are registered with SQLAlchemy
from models import User, Property, Unit, Lease

load_dotenv()

def create_app():
    app = Flask(__name__)

    # --- CONFIGURATION ---
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///homehub.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'super-secret-key-change-this')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')

    # --- INITIALIZE EXTENSIONS ---
    # 🟢 FIX 2: Enhanced CORS to handle Preflight (OPTIONS) requests
    CORS(app, resources={r"/api/*": {
        "origins": [
            "https://homehub-project.onrender.com", 
            "http://localhost:5173"
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }})

    db.init_app(app)
    migrate = Migrate(app, db)
    jwt = JWTManager(app)

    # 🟢 FIX 3: Global Header Handler
    # This ensures that even if a blueprint fails, the CORS headers are sent back
    @app.after_request
    def after_request(response):
        origin = app.config.get('FRONTEND_URL', 'https://homehub-project.onrender.com')
        response.headers.add('Access-Control-Allow-Origin', origin)
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

    # --- REGISTER BLUEPRINTS ---
    from routes.auth import auth_bp
    from routes.properties import properties_bp
    from routes.leases import leases_bp
    from routes.users import users_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(properties_bp, url_prefix='/api/properties')
    app.register_blueprint(leases_bp, url_prefix='/api/leases')
    app.register_blueprint(users_bp, url_prefix='/api/users')

    # --- SERVE UPLOADED FILES ---
    @app.route('/uploads/<path:filename>')
    def serve_uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    @app.route('/')
    def index():
        return "HomeHub Backend is Running! 🚀"

    # --- SEED ROUTE ---
    @app.route('/api/admin/force-seed-db-123')
    def force_seed():
        try:
            from seed import seed_database
            seed_database()
            return "✅ Database Seeded Successfully!", 200
        except Exception as e:
            return f"❌ Seed Failed: {str(e)}", 500

    return app

if __name__ == '__main__':
    app = create_app()
    
    # Ensure upload folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    app.run(debug=True, port=5000)