from flask import Blueprint

# Import all route blueprints
from routes.auth import auth_bp
from routes.users import users_bp
from routes.properties import properties_bp
from routes.units import units_bp
from routes.leases import leases_bp
from routes.rent_invoices import rent_invoices_bp
from routes.payments import payments_bp
from routes.maintenance import maintenance_bp
from routes.notifications import notifications_bp

__all__ = [
    'auth_bp',
    'users_bp',
    'properties_bp',
    'units_bp',
    'leases_bp',
    'rent_invoices_bp',
    'payments_bp',
    'maintenance_bp',
    'notifications_bp'
]
