import os
from flask import Flask, session
from dotenv import load_dotenv
from flask_login import LoginManager
from flask_mail import Mail
from models.models import db, Empresa, Usuario, Servicio

# 1. Cargar configuración
load_dotenv()
app = Flask(__name__)
mail = Mail() # Ahora sí funcionará porque lo importamos arriba


@app.template_filter('fecha_es')
def fecha_es(value):
    if not value:
        return ""
    
    meses = {
        1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr",
        5: "May", 6: "Jun", 7: "Jul", 8: "Ago",
        9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"
    }
    
    dia = value.strftime('%d')
    mes = meses.get(value.month)
    return f"{dia} {mes}"

# CONFIGURACIÓN DE SEGURIDAD Y SESIÓN
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') or 'clave_secreta_por_defecto'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- CONFIGURACIÓN PARA EVITAR CIERRES DE SESIÓN EN MÓVIL ---
app.config['REMEMBER_COOKIE_DURATION'] = 3600  # La sesión dura 1 hora
app.config['SESSION_PROTECTION'] = None        # Evita que el móvil te expulse si cambia la IP/Red
app.config['SESSION_COOKIE_NAME'] = 'agendapp_session' 
# ----------------------------------------------------------

# 2. Inicializar base de datos y Mail
db.init_app(app)
mail.init_app(app) # Lo inicializamos aquí para que esté listo

# 3. CONFIGURACIÓN DE FLASK-LOGIN
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin.login' 
login_manager.login_message = "Por favor, inicia sesión para acceder."
login_manager.login_message_category = "info"

@login_manager.user_loader
def load_user(user_id):
    try:
        if user_id is not None:
            return Usuario.query.get(int(user_id))
    except (ValueError, TypeError):
        return None
    return None

# 4. Importar Blueprints
from routes.admin_routes import admin_bp
from routes.appointment_routes import appointment_bp

# 5. Registrar Blueprints
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(appointment_bp)

# 6. Crear Tablas y verificaciones iniciales
with app.app_context():
    db.create_all()
    # ELIMINÉ: app = Flask(__name__) (No debes volver a crear la app aquí)
    print("--- Base de datos verificada/creada ---")
    print("--- Servidor Listo: Acceso desde 0.0.0.0:5000 ---")
    # ELIMINÉ: return app (Un return solo puede ir dentro de una función 'def')

if __name__ == '__main__':
    # Usar 0.0.0.0 permite que otros dispositivos en tu red (móvil) se conecten
    app.run(host='0.0.0.0', port=5000, debug=True)
    


