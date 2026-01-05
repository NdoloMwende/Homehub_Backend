from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    from app.routes.users import users_bp
    from app.routes.properties import properties_bp
    from app.routes.units import units_bp

    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(properties_bp, url_prefix="/api/properties")
    app.register_blueprint(units_bp, url_prefix="/api/units")

    return app
