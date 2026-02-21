from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


db = SQLAlchemy()

class Empresa(db.Model):
    __tablename__ = 'EMPRESAS'
    emp_id = db.Column(db.String(2), primary_key=True)
    emp_razon_social = db.Column(db.String(100), nullable=False)
    emp_nit = db.Column(db.String(20), nullable=False)
    emp_direccion = db.Column(db.String(150))
    emp_email = db.Column(db.String(100))
    emp_ciudad = db.Column(db.String(50))
    emp_telefono = db.Column(db.String(20))
    
    # --- NUEVOS CAMPOS SMTP (AÑADE ESTO) ---
    emp_servidor_smtp = db.Column(db.String(500))
    emp_puerto_smtp = db.Column(db.String(500))
    emp_cuenta_smtp = db.Column(db.String(500))
    emp_clave_cuenta_smtp = db.Column(db.String(500))
    emp_max_usuarios = db.Column(db.Integer, default=1)
    emp_tipo_plan = db.Column(db.String(20))
    emp_ruta_recursos = db.Column(db.String(500), nullable=True)
    # ---------------------------------------

    # Relaciones
    clientes = db.relationship('Cliente', backref='empresa', lazy=True)
    reservas = db.relationship('Reserva', backref='empresa', lazy=True) # Paréntesis cerrado aquí
    
    
    
class EmpleadoServicios(db.Model):
    __tablename__ = 'EMPLEADO_SERVICIOS'
    empl_id = db.Column(db.Integer, db.ForeignKey('EMPLEADOS.empl_id'), primary_key=True)
    ser_id = db.Column(db.Integer, db.ForeignKey('SERVICIOS.ser_id'), primary_key=True)

class Empleado(db.Model):
    __tablename__ = 'EMPLEADOS'

    empl_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    empl_nombre = db.Column(db.String(100), nullable=False)
    empl_cedula = db.Column(db.Numeric(15, 0), unique=True, nullable=False)
    empl_telefono = db.Column(db.String(20))
    empl_cargo = db.Column(db.String(50))
    empl_porcentaje = db.Column(db.Numeric(5, 2), default=40.00)
    empl_activo = db.Column(db.Boolean, default=True, nullable=False)
    empl_mostrar_en_reserva = db.Column(db.Boolean, default=True)
    
    # Relación con Empresa
    emp_id = db.Column(db.String(2), db.ForeignKey('EMPRESAS.emp_id'), nullable=False)

    # --- CORRECCIÓN AQUÍ ---
    # Usamos 'EMPLEADO_SERVICIOS' entre comillas para referirnos al __tablename__ 
    # de la clase de arriba.
    servicios = db.relationship('Servicio', secondary='EMPLEADO_SERVICIOS', backref='empleados')

    def __repr__(self):
        return f'<Empleado {self.empl_nombre}>'
    
    
class Usuario(db.Model, UserMixin):
    __tablename__ = 'USUARIOS'
    __table_args__ = {'extend_existing': True} 
    
    usu_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # Este será el ID de acceso (ej: 'admin24')
    usu_login = db.Column(db.String(50), unique=True, nullable=False) 
    # Este será el nombre de la persona (ej: 'Juan Pérez')
    usu_nombre = db.Column(db.String(100), nullable=False) 
    usu_password = db.Column(db.String(255), nullable=False)
    emp_id = db.Column(db.String(2), db.ForeignKey('EMPRESAS.emp_id'), nullable=False)
    
    usu_is_admin = db.Column(db.Boolean, default=False)
    PERMISOS = db.relationship('Permiso', secondary='USUARIO_PERMISOS', backref='USUARIOS')

    def set_password(self, password):
        self.usu_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.usu_password, password)

    # Método para verificar PERMISOS en el HTML y Decoradores
    def tiene_permiso(self, nombre_permiso):
        if self.usu_is_admin:
            return True
        return any(p.perm_nombre == nombre_permiso for p in self.PERMISOS)
    # Añade esto al final de tu clase USUARIO
    def get_id(self):
        return str(self.usu_id)


# --- NUEVAS TABLAS PARA LA FLEXIBILIDAD ---

class Permiso(db.Model):
    __tablename__ = 'PERMISOS'
    perm_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    perm_nombre = db.Column(db.String(50), unique=True, nullable=False) # Ej: 'ver_clientes'
    perm_descripcion = db.Column(db.String(100))

# Tabla intermedia para la relación Muchos a Muchos
USUARIO_PERMISOS = db.Table('USUARIO_PERMISOS',
    db.Column('usu_id', db.Integer, db.ForeignKey('USUARIOS.usu_id'), primary_key=True),
    db.Column('perm_id', db.Integer, db.ForeignKey('PERMISOS.perm_id'), primary_key=True),
    extend_existing=True
)
    

class Cliente(db.Model):
    __tablename__ = 'CLIENTES'
    cli_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cli_nombre = db.Column(db.String(100), nullable=False)
    cli_email = db.Column(db.String(100), unique=True, nullable=False)
    cli_telefono = db.Column(db.String(20), nullable=False)
    emp_id = db.Column(db.String(2), db.ForeignKey('EMPRESAS.emp_id'), nullable=False)
    # Relación: Un cliente tiene muchas reservas
    reservas = db.relationship('Reserva', backref='cliente', lazy=True)
    cli_notas_personales = db.Column(db.Text, nullable=True)
    cli_fecha_nacimiento = db.Column(db.Date, nullable=True)
    cli_alias = db.Column(db.String(50))
    cli_activo = db.Column(db.Boolean, default=True)
    
    

class Reserva(db.Model):
    __tablename__ = 'RESERVAS'
    res_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    res_fecha = db.Column(db.Date, nullable=False)
    res_hora = db.Column(db.Time, nullable=False)
    res_notas = db.Column(db.Text)
    res_tipo_servicio = db.Column(db.String(100))
    res_estado = db.Column(db.String(20), default='pendiente')
    
    empl = db.relationship('Empleado', backref='reservas')
    
    # Llaves foráneas
    cli_id = db.Column(db.Integer, db.ForeignKey('CLIENTES.cli_id'), nullable=False)
    emp_id = db.Column(db.String(2), db.ForeignKey('EMPRESAS.emp_id'), nullable=False) # <--- EMPRESA
    
    # NUEVA COLUMNA PARA EL PROFESIONAL (Añade esta línea)
    empl_id = db.Column(db.Integer, db.ForeignKey('EMPLEADOS.empl_id'), nullable=True)
    
class Servicio(db.Model):
    __tablename__ = 'SERVICIOS'

    ser_id = db.Column(db.Integer, primary_key=True)
    ser_nombre = db.Column(db.String(100), nullable=False)
    ser_precio = db.Column(db.Numeric(10,2), nullable=False)
    ser_estado = db.Column(db.Integer, default=1)
    emp_id = db.Column(db.String(2))
    ser_tiempo = db.Column(db.Integer, default=60)
    mostrar_precio = db.Column(db.Boolean, default=True)
    mostrar_tiempo = db.Column(db.Boolean, default=True)

    
    
class ConfigHorario(db.Model):
    __tablename__ = 'CONFIG_HORARIOS'
    id = db.Column(db.Integer, primary_key=True)
    dia_semana = db.Column(db.Integer, unique=True) # 0 a 6
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fin = db.Column(db.Time, nullable=False)
    activo = db.Column(db.Boolean, default=True)  # Si es False, no trabaja ese día
    almuerzo_inicio = db.Column(db.Time, nullable=True)
    almuerzo_fin = db.Column(db.Time, nullable=True)

# models/models.py

class DiasBloqueados(db.Model):
    __tablename__ = 'DIAS_BLOQUEADOS'
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False, unique=True)
    motivo = db.Column(db.String(100))
    
    