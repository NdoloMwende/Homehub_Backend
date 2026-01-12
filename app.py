from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app(config_name='development'):
    app = Flask(__name__)
    
    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        'postgresql://localhost/homehub_db2'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
    
    # Initialize extensions
    db.init_app(app)
    
    # --- NEW: Auto-Create Tables on Startup ---
    # This block forces the database to create tables if they don't exist.
    # It runs every time the server restarts.
    with app.app_context():
        try:
            db.create_all()
            print(" Database tables created successfully!")
        except Exception as e:
            print(f" Error creating database tables: {e}")
    # ------------------------------------------

    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app)

    @app.route('/')
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'message': 'HomeHub Backend is running',
            'status': 'healthy',
            'version': '1.0.0'
        }), 200

    @app.route('/api')
    def api_info():
        """API information endpoint"""
        return jsonify({
            'name': 'HomeHub Backend API',
            'version': '1.0.0',
            'description': 'Property rental management system',
            'endpoints': {
                'auth': '/api/auth',
                'users': '/api/users',
                'properties': '/api/properties',
                'units': '/api/units',
                'leases': '/api/leases',
                'rent_invoices': '/api/rent-invoices',
                'payments': '/api/payments',
                'maintenance': '/api/maintenance',
                'notifications': '/api/notifications'
            }
        }), 200
    
    # Register blueprints
    # Note: Ensure these imports work. If 'routes' is a folder, you might need 'from routes import ...'
    # If this fails, make sure your folder structure allows these imports.
    try:
        from routes import auth_bp, users_bp, properties_bp, units_bp, leases_bp, \
            rent_invoices_bp, payments_bp, maintenance_bp, notifications_bp
    
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        app.register_blueprint(users_bp, url_prefix='/api/users')
        app.register_blueprint(properties_bp, url_prefix='/api/properties')
        app.register_blueprint(units_bp, url_prefix='/api/units')
        app.register_blueprint(leases_bp, url_prefix='/api/leases')
        app.register_blueprint(rent_invoices_bp, url_prefix='/api/rent-invoices')
        app.register_blueprint(payments_bp, url_prefix='/api/payments')
        app.register_blueprint(maintenance_bp, url_prefix='/api/maintenance')
        app.register_blueprint(notifications_bp, url_prefix='/api/notifications')
    except ImportError as e:
        print(f" Warning: Could not import blueprints. {e}")
    
    return app