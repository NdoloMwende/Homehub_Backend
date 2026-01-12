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
    
    # 2. Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app)

    # 3. DATABASE RESET & AUTO-CREATE
    # This block runs every time the server starts.
    with app.app_context():
        try:
            # Import routes/models so SQLAlchemy knows what to create
            # (We import one route file to trigger the model loading)
            from routes import auth_bp 
            
            # ⚠️ RESET COMMAND: Deletes old tables to fix the structure
            # Remove 'db.drop_all()' after this deployment works!
            db.drop_all() 
            
            # Create new tables with the correct columns (price, bedrooms, etc.)
            db.create_all()
            print("✅ Database RESET and tables created successfully!")
        except Exception as e:
            print(f"⚠️ Error creating database tables: {e}")

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
                'users': '/api/users'
            }
        }), 200
    
    # 5. Register Blueprints
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
        print(f"⚠️ Warning: Could not import blueprints. {e}")
    except Exception as e:
        print(f"⚠️ Warning: Blueprint registration failed. {e}")
    
    return app