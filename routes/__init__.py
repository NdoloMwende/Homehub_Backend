from .auth import auth_bp
from .users import users_bp
from .properties import properties_bp
from .units import units_bp
from .leases import leases_bp
from .rent_invoices import rent_invoices_bp
from .payments import payments_bp
from .maintenance import maintenance_bp
from .notifications import notifications_bp
from .upload import upload_bp  # 👈 Added this line

__all__ = [
    'auth_bp',
    'users_bp',
    'properties_bp',
    'units_bp',
    'leases_bp',
    'rent_invoices_bp',
    'payments_bp',
    'maintenance_bp',
    'notifications_bp',
    'upload_bp' # 👈 Added this line
]