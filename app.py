from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flasgger import Swagger
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
        'postgresql://localhost/homehub_db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app)
    Swagger(app)
    
    # Register blueprints
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
    
    return app
