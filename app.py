from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()

# Initialize extensions globally
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app(config_name='development'):
    app = Flask(__name__)
    
    # 1. Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        'postgresql://localhost/homehub_db2'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
    
    # 📂 CONFIGURE UPLOAD FOLDER (New)
    # This creates a folder named 'uploads' in your backend directory
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
        
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit max size to 16MB
    
    # 2. Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app)

    # 3. AUTO-CREATE TABLES (Safe Mode)
    with app.app_context():
        try:
            from routes import auth_bp 
            db.create_all()
            print(" Database connected and tables verified!")
        except Exception as e:
            print(f" Database connection warning: {e}")

    # 4. Standard Routes
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
    
    # 5. Register Blueprints
    try:
        # Added upload_bp to imports
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
        
        # Register Uploads (Note: Prefix is /uploads, not /api/uploads for easier image serving)
        app.register_blueprint(upload_bp, url_prefix='/uploads')
        
    except ImportError as e:
        print(f" Warning: Could not import blueprints. {e}")
    except Exception as e:
        print(f" Warning: Blueprint registration failed. {e}")
    
    return app