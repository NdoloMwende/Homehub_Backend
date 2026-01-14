from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from dotenv import load_dotenv
import os

# 1. Load environment variables immediately
load_dotenv()

# Initialize extensions globally
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app(config_name='development'):
    app = Flask(__name__)
    
    # 2. Get the Database URL
    db_url = os.getenv('DATABASE_URL')

    # 🔴 THE MISSING FIX FOR RENDER:
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    # 3. Print it to the terminal (so you can prove it's the Cloud DB)
    print(f"👀 Flask connecting to: {db_url or 'Local Default'}")

    # 4. Configure App
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url or 'postgresql://localhost/homehub_db2'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
    
    # Configure Upload Folder
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
        
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app)

    # Standard Routes
    @app.route('/')
    def health_check():
        return jsonify({
            'message': 'HomeHub Backend is running', 
            'status': 'healthy', 
            'version': '1.0.0'
        }), 200

    @app.route('/api')
    def api_info():
        return jsonify({
            'name': 'HomeHub Backend API',
            'version': '1.0.0',
            'endpoints': {
                'auth': '/api/auth',
                'properties': '/api/properties',
                'users': '/api/users',
                'uploads': '/uploads'
            }
        }), 200
    
    # Register Blueprints
    try:
        from routes import auth_bp, users_bp, properties_bp, units_bp, leases_bp, \
            rent_invoices_bp, payments_bp, maintenance_bp, notifications_bp, upload_bp
    
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        app.register_blueprint(users_bp, url_prefix='/api/users')
        app.register_blueprint(properties_bp, url_prefix='/api/properties')
        app.register_blueprint(units_bp, url_prefix='/api/units')
        app.register_blueprint(leases_bp, url_prefix='/api/leases')
        app.register_blueprint(rent_invoices_bp, url_prefix='/api/rent-invoices')
        app.register_blueprint(payments_bp, url_prefix='/api/payments')
        app.register_blueprint(maintenance_bp, url_prefix='/api/maintenance')
        app.register_blueprint(notifications_bp, url_prefix='/api/notifications')
        app.register_blueprint(upload_bp, url_prefix='/uploads')
        
    except ImportError as e:
        print(f" Warning: Could not import blueprints. {e}")
    except Exception as e:
        print(f" Warning: Blueprint registration failed. {e}")
    
    return app