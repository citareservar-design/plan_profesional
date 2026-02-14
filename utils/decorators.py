from functools import wraps
from flask import abort
from flask_login import current_user

def requerir_permiso(nombre_permiso):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 1. Si no está logueado, fuera.
            # 2. Si es super_admin (is_admin), pasa siempre.
            # 3. Si tiene el permiso específico, pasa.
            if not current_user.is_authenticated:
                abort(403)
            
            if current_user.is_admin:
                return f(*args, **kwargs)
                
            if not current_user.tiene_permiso(nombre_permiso):
                abort(403)
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator