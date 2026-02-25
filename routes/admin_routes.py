from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session, send_file, make_response,current_app,send_from_directory
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from services.appointment_service import cancelar_cita_por_id 
from io import BytesIO
from models.models import db, Usuario, Reserva, Cliente, Empleado, Empresa, Servicio, ConfigHorario, DiasBloqueados, Permiso, PlantillaWhatsApp,AvisoPromocional,Resena
from flask_login import login_required, current_user, login_user, logout_user
from datetime import date, datetime, timedelta
import pandas as pd
from io import BytesIO
from werkzeug.security import generate_password_hash
import smtplib
from email.message import EmailMessage
from sqlalchemy import func, text
from werkzeug.utils import secure_filename
import os
from xhtml2pdf import pisa
from PyPDF2 import PdfWriter, PdfReader
import io
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from flask_mail import Message
# También asegúrate de importar el objeto 'mail' que configuraste en tu app





# Definición del Blueprint para Administración
print("✅ El archivo admin_routes.py se ha cargado correctamente")
admin_bp = Blueprint('admin', __name__)

# Configuración

# --- 1. AUTENTICACIÓN --- PARA INGRESAR AL PANEL DE CONTROL
# --- 2. PANEL PRINCIPAL (DASHBOARD) E INICIO
# --- 3. GESTIÓN DE EMPLEADOS 
# --- 4. GESTIÓN DE CLIENTES 
# --- 5. GESTIÓN DE SERVICIOS 
# --- 6. GESTIÓN DE RESERVAS 
# --- 7. GESTION DE HORARIOS
# --- 8. CONFIGURACIÓN DE EMPRESA 
# --- 9. PERMISOS Y GESTIÓN DE USUARIOS
# ----10. GESTION DE COMISIONES 
# ----11. HISTORIAL DE RESERVAS Y REPORTES
#-----12. CÓDIGOS QR
# ----13  configuracion panel de control
#-----14  Gestion de plantillas de correo
#-----15  funciones promoccionales y de fidelización
#-----16  reseñas y testimonios
#




# #"""" 
# ESTA CONFIGURACION EL CLIENTE NO HA ACCEDIDO AL PANEL DE CONTROL SOLO ESTA
#
# EN EL FORMULARIO
#
#
# #"""

#----- citas del cliente lo ve desde el form opcion mis reservas


@admin_bp.route('/mis-citas')
def mis_citas():
    email = request.args.get('email')
    citas = []

    if email:
        cliente = Cliente.query.filter_by(cli_email=email).first()
        if cliente:
            # Primero traemos todas las citas
            citas = Reserva.query.filter_by(cli_id=cliente.cli_id)\
                                 .order_by(Reserva.res_fecha.desc())\
                                 .all()
            
            # --- LÓGICA DE ORDENAMIENTO PERSONALIZADO ---
            # Definimos el peso de cada estado
            prioridad = {
                'pendiente': 1,
                'realizada': 2,
                'confirmada': 2,
                'cancelada': 3
            }
            
            # Ordenamos la lista 'citas' usando el diccionario de prioridad
            # Si un estado no está en el diccionario, le asignamos 4 por defecto
            citas.sort(key=lambda x: prioridad.get(x.res_estado.strip().lower(), 4))
            # --------------------------------------------

    return render_template('cliente_citas.html', 
                           citas_cliente=citas, 
                           email_buscado=email)
    
    
#----- citas del cliente lo ve desde el form opcion mis reservas, cancelar el cliente  la cita
 
@admin_bp.route('/api/cancelar-cita/<int:res_id>', methods=['POST'])
@login_required
def cancelar_cita(res_id):
    try:
                
        resultado = cancelar_cita_por_id(res_id)
        
        if "status" in resultado and resultado["status"] == "success":
            return jsonify(resultado), 200
        else:
            return jsonify({"status": "error", "message": resultado.get("error")}), 400
            
    except Exception as e:
        print(f"❌ ERROR EN RUTA: {str(e)}") # Esto saldrá en tu terminal negra
        return jsonify({"status": "error", "message": f"Error interno: {str(e)}"}), 500
    
    
    
    


#----- citas del cliente lo ve desde el form opcion mis reservas, reagendar el cliente  la cita
@admin_bp.route('/api/reagendar/<int:res_id>', methods=['POST'])
def reagendar_cita(res_id):
    
    from datetime import datetime
    
    data = request.get_json()
    reserva = Reserva.query.get_or_404(res_id)
    
    try:
        # Validamos que lleguen los datos
        if 'date' not in data or 'hora' not in data:
            return jsonify({"status": "error", "message": "Faltan datos de fecha u hora"}), 400

        # Convertimos los strings a objetos de Python
        reserva.res_fecha = datetime.strptime(data['date'], '%Y-%m-%d').date()
        
        # IMPORTANTE: Tu JSON envía "11:00:00", nos aseguramos de capturarlo bien
        reserva.res_hora = datetime.strptime(data['hora'], '%H:%M:%S').time()
        
        db.session.commit()
        return jsonify({"status": "success", "message": "Cita reagendada con éxito"})
        
    except Exception as e:
        db.session.rollback() # Siempre haz rollback si falla
        print(f"Error en reagendar: {str(e)}") # Esto saldrá en tu terminal de Python
        return jsonify({"status": "error", "message": f"Error al guardar: {str(e)}"}), 500  
    
 # HASTA ACA LLEGA EL FORMULARIO PUEDE REAGENDAR Y CANCELAR LAS CITAS DESDE MIS RESERVAS   
    
# --- 1. AUTENTICACIÓN --- PARA INGRESAR AL PANEL DE CONTROL

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Capturamos lo que el usuario escribió (Ej: "ADMIN")
        identificador = request.form.get('usuario') 
        clave = request.form.get('clave')
        
        # CAMBIO CLAVE: Cambiamos usu_nombre por usu_login
        usuario_db = Usuario.query.filter_by(usu_login=identificador).first()

        if usuario_db and usuario_db.check_password(clave):
            login_user(usuario_db, remember=True) 
            session['emp_id'] = usuario_db.emp_id 
            return redirect(url_for('admin.publicidad'))
        
        flash("Usuario o contraseña incorrectos", "danger")
    return render_template('admin/login.html')

@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash("Sesión cerrada correctamente", "success")
    return redirect(url_for('admin.login'))





# --- 2. PANEL PRINCIPAL (DASHBOARD) E INICIO

@admin_bp.route('/inicio')
@login_required
def publicidad():
    """ 
    Página de bienvenida y formulario de reservas (PÚBLICA).
    """
    return render_template('admin/inicio.html')




@admin_bp.route('/dashboard')
@login_required
def dashboard():
    hoy = date.today()
    
    ahora = datetime.now()
    hora_actual = ahora.time()
    emp_id_actual = current_user.emp_id
    siete_dias_atras = hoy - timedelta(days=6)
    
    
    # DICCIONARIO PARA MESES EN ESPAÑOL (AÑADIDO)
    meses_es = {
        1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr', 5: 'May', 6: 'Jun',
        7: 'Jul', 8: 'Ago', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'
    }

    # 1. CONSULTAS BÁSICAS
    empresa_data = Empresa.query.filter_by(emp_id=emp_id_actual).first()
    citas_hoy = Reserva.query.filter_by(res_fecha=hoy, emp_id=emp_id_actual).count()
    total_clientes = Cliente.query.filter_by(cli_activo=True, emp_id=emp_id_actual).count()
    total_usuarios = Usuario.query.filter_by(emp_id=emp_id_actual).count()
    
    # 2. CÁLCULO DE LICENCIA
    limite_usuarios = empresa_data.emp_max_usuarios if empresa_data and empresa_data.emp_max_usuarios else 1
    porcentaje_uso = min(int((total_usuarios / limite_usuarios) * 100), 100)

    # 3. PRÓXIMAS RESERVAS
    proximas_reservas = Reserva.query.filter(Reserva.res_fecha >= hoy, Reserva.emp_id == emp_id_actual)\
        .order_by(Reserva.res_fecha.asc(), Reserva.res_hora.asc())\
        .limit(10).all()

    # 4. CONSULTA DE VENTAS ÚLTIMOS 7 DÍAS (CON SELECT_FROM PARA EVITAR ERROR)
    ventas_data = db.session.query(
        func.date(Reserva.res_fecha).label('fecha'),
        func.sum(Servicio.ser_precio).label('total')
    ).select_from(Reserva).join(
        Servicio, Reserva.res_tipo_servicio == Servicio.ser_nombre
    ).filter(
        Reserva.emp_id == emp_id_actual,
        Reserva.res_fecha >= siete_dias_atras,
        Reserva.res_estado.in_(['Realizada', 'Completada']),
    ).group_by(func.date(Reserva.res_fecha)).all()

    # 5. FORMATEAR DATOS PARA LA GRÁFICA
    labels_ventas = []
    valores_ventas = []
    dict_ventas = {v.fecha.strftime('%Y-%m-%d'): float(v.total) for v in ventas_data}
    
    # Días en español para que se vea 
    dias_es = {'Mon': 'Lun', 'Tue': 'Mar', 'Wed': 'Mié', 'Thu': 'Jue', 'Fri': 'Vie', 'Sat': 'Sáb', 'Sun': 'Dom'}
    
    for i in range(7):
        dia = siete_dias_atras + timedelta(days=i)
        fecha_str = dia.strftime('%Y-%m-%d')
        labels_ventas.append(dias_es.get(dia.strftime('%a'), dia.strftime('%a'))) 
        valores_ventas.append(dict_ventas.get(fecha_str, 0))

    # 6. INGRESOS HOY E INGRESOS TOTALES (FUERA DEL BUCLE)
    ingresos_hoy = dict_ventas.get(hoy.strftime('%Y-%m-%d'), 0)

    total_historico = db.session.query(
        func.sum(Servicio.ser_precio)
    ).select_from(Reserva).join(
        Servicio, Reserva.res_tipo_servicio == Servicio.ser_nombre
    ).filter(
        Reserva.emp_id == emp_id_actual,
        Reserva.res_estado.in_(['Realizada', 'Completada'])
    ).scalar() or 0
    
# CONSULTA PARA GRÁFICO DE DONA (Estados Globales)
    stats_dona = db.session.query(
        Reserva.res_estado, 
        func.count(Reserva.res_id)
    ).filter(
        Reserva.emp_id == emp_id_actual
    ).group_by(Reserva.res_estado).all()

    # Convertimos a diccionario
    dict_dona = {estado: conteo for estado, conteo in stats_dona}

    # Extraemos los 4 estados (usamos .get para que si no hay de uno, ponga 0)
    c_pendiente = dict_dona.get('Pendiente', 0)
    c_confirmada = dict_dona.get('Confirmada', 0)
    c_realizada = dict_dona.get('Realizada', 0)
    c_completadas = dict_dona.get('Completada', 0) # Las ya liquidadas
    c_canceladas = dict_dona.get('Cancelada', 0)
    
    c_logradas_total = c_realizada + c_completadas
    
    
    # Pásalos todos al render_template:
    # return render_template(..., c_pendiente=c_pendiente, c_confirmada=c_confirmada, ...)
    
       
    
    # CONSULTA: Top 5 Servicios más populares
    top_servicios_data = db.session.query(
        Reserva.res_tipo_servicio, 
        func.count(Reserva.res_id).label('total')
    ).filter(
        Reserva.emp_id == emp_id_actual,
        Reserva.res_estado != 'Cancelada'
    ).group_by(Reserva.res_tipo_servicio)\
    .order_by(func.count(Reserva.res_id).desc())\
    .limit(5).all()
    
    
    
# Tendencia de Horarios (Flujo de Citas)
    
# 1. Generar etiquetas de 30 min (08:00 a 20:30)
    labels_flujo = []
    for h in range(8, 21):
        labels_flujo.append(f"{str(h).zfill(2)}:00")
        labels_flujo.append(f"{str(h).zfill(2)}:30")

    valores_flujo = [0] * len(labels_flujo)

    # 2. Consulta MySQL (Histórica: Citas confirmadas o completadas) por hora y minuto
    flujo_data = db.session.query(
        func.hour(Reserva.res_hora).label('hora'),
        func.minute(Reserva.res_hora).label('minuto'),
        func.count(Reserva.res_id).label('total')
    ).filter(
        Reserva.emp_id == emp_id_actual,
        Reserva.res_estado.in_(['Realizada', 'Completada'])
    ).group_by(func.hour(Reserva.res_hora), func.minute(Reserva.res_hora)).all()

    # DEBUG: Para verificar en la terminal de Python
    print(f"--- DEBUG FLUJO ---")
    print(f"Total grupos encontrados en DB: {len(flujo_data)}")

    # 3. Mapeo Robusto a bloques de 30 min
    for f in flujo_data:
        # Validar que la hora no sea None
        if f.hora is not None:
            # Redondeo: 0-29 min -> :00 | 30-59 min -> :30
            min_bloque = "00" if f.minuto < 30 else "30"
            hora_str = f"{str(f.hora).zfill(2)}:{min_bloque}"
            
            if hora_str in labels_flujo:
                idx = labels_flujo.index(hora_str)
                valores_flujo[idx] += f.total
                print(f"Mapeado: {f.hora}:{f.minuto} -> {hora_str} (Total bloque: {valores_flujo[idx]})")
  
            
            
    
    # 3. CITAS INMINENTES (Las próximas 3 que están por suceder)
    ahora = datetime.now()
    citas_proximas = Reserva.query.filter(
        Reserva.emp_id == emp_id_actual,
        Reserva.res_estado == 'Confirmada',
        # Lógica: (Es hoy y la hora es mayor o igual a la actual) O (Es un día después de hoy)
        db.or_(
            db.and_(Reserva.res_fecha == hoy, Reserva.res_hora >= hora_actual),
            Reserva.res_fecha > hoy
        )
    ).order_by(Reserva.res_fecha.asc(), Reserva.res_hora.asc())\
    .limit(4).all()
    ultima_reserva = Reserva.query.filter_by(emp_id=emp_id_actual).order_by(Reserva.res_id.desc()).first()

# Variables para el HTML
    u_id = ultima_reserva.res_id if ultima_reserva else 0
    u_cliente = ultima_reserva.cliente.cli_nombre if (ultima_reserva and ultima_reserva.cliente) else "Sin nombre"
    u_servicio = ultima_reserva.res_tipo_servicio if ultima_reserva else "Sin servicio"
    
# 8. CÁLCULO DEL DÍA PICO Y CONTEO SEMANAL PARA GRÁFICA
    conteo_semanal = [0] * 7
    stats_semana = db.session.query(
        func.weekday(Reserva.res_fecha).label('dia'),
        func.count(Reserva.res_id).label('total')
    ).filter(
        Reserva.emp_id == emp_id_actual,
        Reserva.res_estado.in_(['Realizada', 'Completada'])
    ).group_by('dia').all()

    # Llenamos la lista con los resultados de la DB
    for s in stats_semana:
        if s.dia is not None:
            conteo_semanal[s.dia] = s.total

    # Calculamos cuál es el nombre del día que más citas tiene
    nombres_dias_full = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    
    if max(conteo_semanal) > 0:
        # Buscamos la posición del número más alto en la lista
        dia_pico_idx = conteo_semanal.index(max(conteo_semanal))
        dia_pico_nombre = nombres_dias_full[dia_pico_idx]
    else:
        dia_pico_nombre = "Sin datos"

    # Máximo valor para escalar las barras en el HTML (evita división por cero)
    max_citas = max(conteo_semanal) if max(conteo_semanal) > 0 else 1
    


    # 7. RETURN (Asegúrate que el nombre total_ingresos coincida con tu HTML)
    return render_template('admin/dashboard.html', 
                           empresa=empresa_data,
                           dia_pico=dia_pico_nombre,
                           conteo_semanal=conteo_semanal,
                           c_logradas=c_logradas_total,
                           c_pendiente=c_pendiente,
                           c_confirmada=c_confirmada,
                           c_realizada=c_realizada,
                           c_canceladas=c_canceladas,
                           c_completadas=c_completadas,
                           meses_es=meses_es,
                           max_citas=max_citas,
                           hoy=hoy,
                           citas_hoy=citas_hoy, 
                           total_clientes=total_clientes,
                           total_usuarios=total_usuarios,
                           limite_usuarios=limite_usuarios,
                           labels_flujo=labels_flujo, 
                           valores_flujo=valores_flujo,
                           porcentaje_uso=porcentaje_uso,
                           labels_ventas=labels_ventas,
                           top_servicios=top_servicios_data,
                           valores_ventas=valores_ventas,
                           ingresos_hoy=ingresos_hoy,
                           total_ingresos=total_historico,
                           citas_proximas=citas_proximas,
                            ultimo_id=u_id,
                            ultimo_cliente=u_cliente,
                            ultimo_servicio=u_servicio,
                           reservas=proximas_reservas)
    
    
@admin_bp.route('/check_last_reserva')
@login_required
def check_last_reserva():
    print(f"Buscando última reserva para empresa: {current_user.emp_id}") # Esto saldrá en tu consola
    ultima = Reserva.query.filter_by(emp_id=current_user.emp_id).order_by(Reserva.res_id.desc()).first()
    
    if ultima:
        return jsonify({
            'id': ultima.res_id,
            'cliente': ultima.cliente.cli_nombre if ultima.cliente else "Cliente Nuevo",
            'servicio': ultima.res_tipo_servicio
        })
    return jsonify({'id': 0})


# --- 3. GESTIÓN DE EMPLEADOS ---


@admin_bp.route('/foto_empleado/<cedula>/<filename>')
def serve_emp_photo(cedula, filename):
    try:
        from models.models import Empresa # Asegúrate de importar tu modelo
        # Obtenemos la empresa (asumiendo que es la primera o la del usuario actual)
        empresa = Empresa.query.first() 
        
        # Ruta base: C:\Apps\cocoanails
        ruta_base = (empresa.emp_ruta_recursos).strip()
        
        # Construimos: C:\Apps\cocoanails\empleados\10888304344
        directorio_final = os.path.join(ruta_base, 'empleados', str(cedula))
        
        print(f"--- Buscando archivo: {filename} en {directorio_final} ---")
        
        return send_from_directory(directorio_final, filename)
    except Exception as e:
        print(f"❌ Error en serve_emp_photo: {str(e)}")
        return "No encontrada", 404
    
    
    
@admin_bp.route('/empleados')
@login_required
def gestion_empleados():
    empresa = Empresa.query.filter_by(emp_id=current_user.emp_id).first() # Usa current_user.emp_id
    LIMITE_EMPLEADOS = empresa.emp_max_usuarios if empresa else 1
        
    activos = Empleado.query.filter_by(emp_id=current_user.emp_id, empl_activo=True).all()
    inactivos = Empleado.query.filter_by(emp_id=current_user.emp_id, empl_activo=False).all()
    
    # --- CORRECCIÓN AQUÍ: Solo servicios activos (ser_estado=1) ---
    lista_servicios = Servicio.query.filter_by(
        emp_id=current_user.emp_id, 
        ser_estado=1
    ).all()
    
    return render_template('admin/empleados.html', 
                           empleados=activos, 
                           empleados_inactivos=inactivos,
                           conteo=len(activos), 
                           limite=LIMITE_EMPLEADOS,
                           servicios=lista_servicios) # Enviar servicios al HTML
    
    
    

def nuevo_empleados():
    from models.models import Empleado, Servicio, Empresa, db
    
    # 1. Recibimos los datos (Usamos request.form porque ahora enviamos archivos)
    nombre = request.form.get('nombre', '').strip()
    cedula = str(request.form.get('cedula', '')).strip()
    correo = request.form.get('correo', '').strip()
    servicios_ids = request.form.getlist('servicios[]') 
    foto_archivo = request.files.get('foto') 

    if not nombre or not cedula:
        return jsonify({'status': 'error', 'message': 'Nombre y Cédula son obligatorios'}), 400

    # 2. Obtenemos la empresa del usuario actual
    empresa = Empresa.query.get(current_user.emp_id)
    
    if not empresa or not empresa.emp_ruta_recursos:
        return jsonify({'status': 'error', 'message': 'La empresa no tiene una ruta de recursos configurada'}), 400

    # 3. LÓGICA DINÁMICA DE CARPETAS
    # Usamos la ruta de la DB como punto de partida inicial
    ruta_raiz_empresa = empresa.emp_ruta_recursos.strip()
    nombre_foto_db = None

    if foto_archivo:
        try:
            # Construimos: [ruta_de_la_db]/empleados/[cedula]/
            carpeta_empleado = os.path.join(ruta_raiz_empresa, 'empleados', cedula)
            
            # El código crea lo que falta (empleados y la carpeta de la cedula)
            if not os.path.exists(carpeta_empleado):
                os.makedirs(carpeta_empleado, exist_ok=True)
            
            # Limpiamos el nombre de la foto (ej: mi foto.jpg -> mi_foto.jpg)
            filename = secure_filename(foto_archivo.filename)
            ruta_fisica_final = os.path.join(carpeta_empleado, filename)
            
            # Guardamos físicamente
            foto_archivo.save(ruta_fisica_final)
            
            # Guardamos en DB la ruta relativa: 'empleados/10888/foto.jpg'
            nombre_foto_db = f"empleados/{cedula}/{filename}"
            
        except Exception as e:
            print(f"❌ Error al crear carpetas o guardar: {str(e)}")
            return jsonify({'status': 'error', 'message': f'Error al gestionar archivos: {str(e)}'}), 500

    # 4. Guardado en la base de datos del Empleado
    try:
        nuevo_emp = Empleado(
            empl_nombre=nombre,
            empl_cedula=cedula,
            empl_correo=correo,
            empl_telefono=request.form.get('telefono'),
            empl_porcentaje=request.form.get('porcentaje', 40),
            empl_cargo=request.form.get('cargo', 'Especialista'),
            empl_foto=nombre_foto_db, # Aquí queda la ruta relativa
            emp_id=current_user.emp_id,
            empl_activo=True
        )
        
        db.session.add(nuevo_emp)
        db.session.flush()

        # Relación de servicios
        if servicios_ids:
            for s_id in servicios_ids:
                servicio = Servicio.query.filter_by(ser_id=s_id, emp_id=current_user.emp_id).first()
                if servicio:
                    nuevo_emp.servicios.append(servicio)

        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Empleado y carpeta creados correctamente'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'Error en DB: {str(e)}'}), 500
    


@admin_bp.route('/api/empleado/editar/<int:id>', methods=['POST'])
@login_required
def editar_empleado(id):
    from models.models import Empleado, Servicio, Empresa, db
    import os
    from werkzeug.utils import secure_filename

    # Configuración de extensiones permitidas
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    # 1. Buscar empleado y empresa
    emp = Empleado.query.filter_by(empl_id=id, emp_id=current_user.emp_id).first()
    if not emp:
        return jsonify({'status': 'error', 'message': 'Empleado no encontrado'}), 404

    empresa = Empresa.query.get(current_user.emp_id)
    ruta_raiz = empresa.emp_ruta_recursos.strip()

    # 2. Recibir datos
    nombre = request.form.get('nombre', '').strip()
    cedula_nueva = str(request.form.get('cedula', '')).strip()
    correo = request.form.get('correo', '').strip()
    cedula_anterior = str(emp.empl_cedula)
    foto_nueva = request.files.get('foto')

    if not nombre or not cedula_nueva:
        return jsonify({'status': 'error', 'message': 'Nombre y Cédula son obligatorios'}), 400

    try:
        # --- LÓGICA DE CARPETAS (Si cambia la cédula) ---
        ruta_vieja = os.path.join(ruta_raiz, 'empleados', cedula_anterior)
        ruta_nueva = os.path.join(ruta_raiz, 'empleados', cedula_nueva)

        if cedula_nueva != cedula_anterior:
            if os.path.exists(ruta_vieja):
                # Si la carpeta nueva ya existe por error, la borramos o manejamos
                os.rename(ruta_vieja, ruta_nueva)
            
        # Asegurar que la carpeta (nueva o vieja) existe
        if not os.path.exists(ruta_nueva):
            os.makedirs(ruta_nueva, exist_ok=True)

        # --- LÓGICA DE LA FOTO (Renombrar a la cédula) ---
        if foto_nueva and foto_nueva.filename != '':
            # Validar extensión
            if not allowed_file(foto_nueva.filename):
                return jsonify({'status': 'error', 'message': 'Solo se permiten imágenes (JPG, PNG, WEBP)'}), 400

            # Extraer extensión original
            extension = foto_nueva.filename.rsplit('.', 1)[1].lower()
            
            # Nombre final: "10888304344.png" (por ejemplo)
            nombre_foto = f"{cedula_nueva}.{extension}"
            ruta_destino = os.path.join(ruta_nueva, nombre_foto)

            # Si ya existía una foto con otro nombre o extensión, podrías borrarla aquí
            # Pero lo más limpio es guardar la nueva:
            foto_nueva.save(ruta_destino)
            
            # Guardamos solo el nombre del archivo en la DB
            emp.empl_foto = nombre_foto

        # 3. Actualizar datos básicos
        emp.empl_nombre = nombre
        emp.empl_cedula = cedula_nueva
        emp.empl_correo = correo
        emp.empl_telefono = request.form.get('telefono')
        emp.empl_porcentaje = request.form.get('porcentaje', 40)
        emp.empl_cargo = request.form.get('cargo', 'Especialista')

        # 4. Actualizar Servicios
        servicios_ids = request.form.getlist('servicios[]')
        emp.servicios = [] 
        if servicios_ids:
            servicios_validos = Servicio.query.filter(
                Servicio.ser_id.in_(servicios_ids), 
                Servicio.emp_id == current_user.emp_id
            ).all()
            emp.servicios = servicios_validos

        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Empleado actualizado correctamente'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'Error técnico: {str(e)}'}), 500
    
    
    
    
@admin_bp.route('/api/empleado/estado/<int:id>', methods=['POST'])
@login_required
def cambiar_estado_empleado(id):
    # Importamos Empresa para validar el límite
    from models.models import Empleado, Empresa, db
    
    emp = Empleado.query.filter_by(empl_id=id, emp_id=current_user.emp_id).first()
    
    if not emp:
        return jsonify({'status': 'error', 'message': 'Empleado no encontrado'}), 404
        
    data = request.get_json()
    nuevo_estado = data.get('activo', True)

    # --- VALIDACIÓN DE LÍMITE AL ACTIVAR ---
    # Solo validamos si el usuario intenta pasar de Inactivo a Activo
    if nuevo_estado is True and emp.empl_activo is False:
        empresa = Empresa.query.get(current_user.emp_id)
        limite_max = empresa.emp_max_usuarios if empresa.emp_max_usuarios else 1
        
        # Contamos cuántos empleados ya están activos
        total_activos = Empleado.query.filter_by(
            emp_id=current_user.emp_id, 
            empl_activo=True
        ).count()

        if total_activos >= limite_max:
            return jsonify({
                'status': 'error', 
                'message': f'Cupo lleno. Tu plan permite máximo {limite_max} empleados activos. Inactiva a otro para poder activar este.'
            }), 400
    # ---------------------------------------

    emp.empl_activo = nuevo_estado
    
    try:
        db.session.commit()
        msg = "Empleado activado" if emp.empl_activo else "Empleado inactivado"
        return jsonify({'status': 'success', 'message': msg})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    


@admin_bp.route('/empleados/importar', methods=['POST'])
@login_required
def importar_empleados():
    from models.models import Empleado, Empresa, db
    import pandas as pd

    if 'archivo' not in request.files:
        flash('No se seleccionó ningún archivo', 'error')
        return redirect(url_for('admin.gestion_empleados'))

    file = request.files['archivo']
    
    try:
        # 1. Leer el Excel
        df = pd.read_excel(file)
        df.columns = df.columns.str.strip()

        # 2. Obtener límites de la empresa
        empresa = Empresa.query.get(current_user.emp_id)
        limite_max = empresa.emp_max_usuarios if empresa.emp_max_usuarios else 1
        
        # --- CAMBIO CLAVE AQUÍ ---
        # Contamos solo los empleados que están ACTIVOS actualmente
        total_activos_ahora = Empleado.query.filter_by(
            emp_id=current_user.emp_id, 
            empl_activo=True
        ).count()

        # 3. Analizar el Excel antes de guardar
        filas_nuevas_a_crear = 0
        df_valido = []

        for _, row in df.iterrows():
            nombre = str(row.get('Nombre', '')).strip()
            cedula = str(row.get('Identificación', '')).strip().replace(".0", "").replace("'", "")
            
            if nombre and nombre != 'nan' and cedula and cedula != 'nan':
                # Buscamos si el empleado ya existe (sea activo o inactivo)
                empleado_existente = Empleado.query.filter_by(
                    empl_cedula=cedula, 
                    emp_id=current_user.emp_id
                ).first()
                
                # Si NO existe, sumará como un nuevo activo
                if not empleado_existente:
                    filas_nuevas_a_crear += 1
                
                # Si EXISTE pero está INACTIVO y el Excel lo va a reactivar (opcional)
                # o si simplemente lo vamos a procesar:
                df_valido.append(row)

        # 4. VALIDACIÓN DE LÍMITE (Basado solo en activos)
        if (total_activos_ahora + filas_nuevas_a_crear) > limite_max:
            flash(f'Cupos agotados: Tu plan permite {limite_max} empleados activos. '
                  f'Tienes {total_activos_ahora} activos y el archivo intenta crear {filas_nuevas_a_crear} nuevos.', 'error')
            return redirect(url_for('admin.gestion_empleados'))

        # 5. Procesar la importación
        nuevos = 0
        actualizados = 0

        for row in df_valido:
            nombre = str(row.get('Nombre', '')).strip()
            cargo = str(row.get('Cargo', 'General')).strip()
            cedula = str(row.get('Identificación', '')).strip().replace(".0", "").replace("'", "")
            telefono = str(row.get('Teléfono', '')).strip()
            
            comision_raw = str(row.get('Comisión', '40')).replace('%', '').strip()
            try:
                porcentaje = float(comision_raw)
            except ValueError:
                porcentaje = 40.0

            empleado = Empleado.query.filter_by(empl_cedula=cedula, emp_id=current_user.emp_id).first()

            if empleado:
                # Si ya existe, actualizamos sus datos
                empleado.empl_nombre = nombre
                empleado.empl_cargo = cargo
                empleado.empl_telefono = telefono
                empleado.empl_porcentaje = porcentaje
                # Nota: Aquí decides si al importar quieres que los inactivos se vuelvan activos
                # empleado.empl_activo = True 
                actualizados += 1
            else:
                # Si es nuevo, se crea como ACTIVO por defecto
                nuevo_emp = Empleado(
                    empl_nombre=nombre,
                    empl_cedula=cedula,
                    empl_telefono=telefono,
                    empl_cargo=cargo,
                    empl_porcentaje=porcentaje,
                    empl_activo=True,
                    emp_id=current_user.emp_id
                )
                db.session.add(nuevo_emp)
                nuevos += 1

        db.session.commit()
        flash(f'Importación exitosa: {nuevos} nuevos activos creados y {actualizados} actualizados.', 'success')

    except Exception as e:
        db.session.rollback()
        print(f"Error detallado: {str(e)}")
        flash(f'Error al procesar el archivo Excel.', 'error')

    return redirect(url_for('admin.gestion_empleados'))




@admin_bp.route('/api/configuracion/visibilidad-empleados', methods=['POST'])
def cambiar_visibilidad_staff():
    try:
        data = request.get_json()
        nuevo_estado = data.get('mostrar_empleados')
        
        # Obtenemos el ID de la empresa/negocio de la sesión
        emp_id_actual = session.get('emp_id') 

        if not emp_id_actual:
            return jsonify({'status': 'error', 'message': 'Sesión expirada'}), 401

        # Filtramos por empresa y actualizamos
        empleados = Empleado.query.filter_by(emp_id=emp_id_actual).all()
        
        if not empleados:
             return jsonify({'status': 'success', 'message': 'No hay empleados para actualizar'})

        for emp in empleados:
            emp.empl_mostrar_en_reserva = nuevo_estado
        
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Visibilidad actualizada'})
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error en DB: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Error interno del servidor'}), 500



    
# --- 4. GESTIÓN DE CLIENTES ---


@admin_bp.route('/aplicar_descuento_general', methods=['POST'])
def aplicar_descuento_general():
    try:
        from models.models import Cliente, db
        datos = request.get_json()
        
        nuevo_porcentaje = float(datos.get('porcentaje', 0))
        nueva_cantidad = int(datos.get('cantidad', 0))

        # --- NORMALIZACIÓN ---
        # Si el admin pone 0.20, lo convertimos en 20
        if 0 < nuevo_porcentaje < 1:
            nuevo_porcentaje = nuevo_porcentaje * 100

        # Actualización masiva
        Cliente.query.filter(Cliente.cli_activo == 1).update({
            Cliente.cli_descuento: nuevo_porcentaje,
            Cliente.cli_descuento_cantidad: nueva_cantidad
        }, synchronize_session=False)
        
        db.session.commit()
        return jsonify({"status": "success", "message": f"Campaña activada al {int(nuevo_porcentaje)}%"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@admin_bp.route('/obtener_plantillas')
@login_required
def obtener_plantillas():
    try:
        # 1. Consultar el nombre de la empresa (tomamos la primera fila)
        sql_empresa = text("SELECT emp_razon_social FROM EMPRESAS LIMIT 1")
        res_empresa = db.session.execute(sql_empresa).fetchone()
        nombre_empresa = res_empresa.emp_razon_social if res_empresa else "Nuestra Empresa"

        # 2. Consultar las plantillas
        sql_plantillas = text("SELECT plan_nombre, plan_mensaje, plan_tipo FROM PLANTILLAS_WHATSAPP WHERE plan_activo = 1")
        res_plantillas = db.session.execute(sql_plantillas)
        
        plantillas = []
        for fila in res_plantillas:
            plantillas.append({
                "plan_nombre": fila.plan_nombre,
                "plan_mensaje": fila.plan_mensaje,
                "plan_tipo": fila.plan_tipo
            })
        
        # Enviamos un objeto que contiene AMBAS cosas
        return jsonify({
            "empresa": nombre_empresa,
            "plantillas": plantillas
        })

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Error al cargar datos"}), 500
    

@admin_bp.route('/api/preparar_mensaje_whatsapp')
@login_required
def preparar_mensaje_whatsapp():
    cliente_id = request.args.get('cliente_id')
    plantilla_id = request.args.get('plantilla_id')
    
    cliente = Cliente.query.get_or_404(cliente_id)
    plantilla = PlantillaWhatsApp.query.get_or_404(plantilla_id)
    
    # Obtenemos el nombre del negocio (usando tu lógica existente)
    sql = "SELECT emp_razon_social FROM EMPRESAS WHERE emp_id = :id"
    resultado = db.session.execute(db.text(sql), {'id': str(current_user.emp_id)}).fetchone()
    negocio_nombre = resultado[0] if resultado else "Nuestro Negocio"

    mensaje = plantilla.plan_mensaje
    
    # --- PROCESO DE REEMPLAZO (The Magic) ---
    # Reemplazamos las variables que definimos antes
    mensaje = mensaje.replace('{cliente}', cliente.cli_nombre)
    mensaje = mensaje.replace('{empresa}', negocio_nombre)
    
    # Como estamos en el módulo clientes, fecha/hora/servicio pueden ser genéricos 
    # o puedes buscar la última cita si quisieras ser más específico
    mensaje = mensaje.replace('{fecha}', 'próximamente') 
    
    # Limpiar el número de teléfono (quitar espacios, +, etc)
    telefono = "".join(filter(str.isdigit, cliente.cli_telefono))
    
    # Si el teléfono no tiene código de país, podrías añadir el de tu país por defecto (ej: 57 para Colombia)
    if len(telefono) == 10: # Ejemplo para números de 10 dígitos
        telefono = "57" + telefono

    # Retornamos el link de WhatsApp Web / App
    # El mensaje debe estar codificado para URL
    import urllib.parse
    mensaje_codificado = urllib.parse.quote(mensaje)
    link = f"https://wa.me/{telefono}?text={mensaje_codificado}"
    
    return jsonify({
        "status": "success",
        "link": link,
        "mensaje_previa": mensaje
    })


@admin_bp.route('/clientes')
@login_required
def gestion_clientes():
    estado = request.args.get('estado', 'activos')
    query = Cliente.query.filter_by(emp_id=current_user.emp_id)
    
    if estado == 'desactivados':
        lista_clientes = query.filter_by(cli_activo=False).all()
    else:
        lista_clientes = query.filter_by(cli_activo=True).all()
    
    from app import db 
    from datetime import datetime, date
    
    # 1. Obtener nombre del negocio (Optimizado)
    try:
        sql = text("SELECT emp_razon_social FROM EMPRESAS WHERE emp_id = :id")
        resultado = db.session.execute(sql, {'id': str(current_user.emp_id)}).fetchone()
        negocio_nombre = resultado[0] if resultado else "Nuestro Negocio"
    except Exception as e:
        print(f"Error BD Empresa: {e}")
        negocio_nombre = "Nuestro Negocio"
    
    hoy = date.today() # Usamos .today() para comparar solo fechas
    
    for cliente in lista_clientes:
        # --- A. CONTEO DE RESERVAS ---
        cliente.num_reservas = Reserva.query.filter_by(cli_id=cliente.cli_id).count()
        
        # --- B. LÓGICA DE CUMPLEAÑOS (Hoy y 2 días antes) ---
        cliente.es_cumpleanos = False
        cliente.es_pre_cumple = False
        
        if cliente.cli_fecha_nacimiento:
            # Creamos la fecha del cumple en el año actual para comparar
            try:
                # El replace(year=hoy.year) puede fallar el 29 de feb, por eso el try
                cumple_actual = cliente.cli_fecha_nacimiento.replace(year=hoy.year)
            except ValueError:
                cumple_actual = cliente.cli_fecha_nacimiento.replace(year=hoy.year, day=28)

            diferencia = (cumple_actual - hoy).days
            
            if diferencia == 0:
                cliente.es_cumpleanos = True
            elif 1 <= diferencia <= 2:
                cliente.es_pre_cumple = True

        # --- C. LÓGICA DE CLIENTE EN RIESGO ---
        ultima_reserva = Reserva.query.filter_by(cli_id=cliente.cli_id)\
            .order_by(Reserva.res_fecha.desc()).first()
        
        cliente.en_riesgo = False
        cliente.dias_ausente = 0
        
        if ultima_reserva:
            diferencia_riesgo = hoy - ultima_reserva.res_fecha
            cliente.dias_ausente = diferencia_riesgo.days
            
            if cliente.dias_ausente > 30:
                cliente.en_riesgo = True
    
    # Ordenamos: Cumpleaños Hoy > Pre-Cumple > En Riesgo > Más Reservas
    lista_clientes.sort(
        key=lambda x: (x.es_cumpleanos, x.es_pre_cumple, x.en_riesgo, x.num_reservas), 
        reverse=True
    )
    
    return render_template('admin/clientes.html',
                           clientes=lista_clientes,
                           nombre_negocio=negocio_nombre)
    
    
    
    
@admin_bp.context_processor
def inject_cumpleanos():
    from models.models import Cliente
    from datetime import date
    import sqlalchemy # Por si usas text()
    
    hay_hoy = False
    hay_pre = False
    
    if current_user.is_authenticated:
        hoy = date.today()
        # Traemos solo los activos de la empresa actual
        clientes = Cliente.query.filter_by(emp_id=current_user.emp_id, cli_activo=True).all()
        
        for c in clientes:
            if c.cli_fecha_nacimiento:
                # Ajustar al año actual
                try:
                    cumple_este_ano = c.cli_fecha_nacimiento.replace(year=hoy.year)
                except ValueError: # Caso 29 de febrero
                    cumple_este_ano = c.cli_fecha_nacimiento.replace(year=hoy.year, day=28)
                
                diff = (cumple_este_ano - hoy).days
                
                if diff == 0:
                    hay_hoy = True
                elif 1 <= diff <= 2:
                    hay_pre = True
                    
                # Si ya encontramos ambos, podemos dejar de buscar para ahorrar energía
                if hay_hoy and hay_pre:
                    break

    # ESTO ES VITAL: Los nombres aquí deben coincidir con tu HTML
    return {
        'hay_cumpleanos_global': hay_hoy,
        'hay_precumpleanos_global': hay_pre
    }


@admin_bp.route('/api/cliente/nuevo', methods=['POST'])
@login_required
def nuevo_cliente():
    data = request.get_json()
    try:
        from models.models import Cliente, db
        from datetime import datetime

        # 1. Procesamiento de la fecha
        fecha_nac = data.get('fecha_nacimiento')
        fecha_obj = datetime.strptime(fecha_nac, '%Y-%m-%d').date() if fecha_nac else None

        # 2. Captura y Normalización del Descuento
        # Si el usuario manda 0.20, lo convertimos a 20.00
        desc_bruto = float(data.get('descuento', 0))
        if 0 < desc_bruto < 1:
            desc_final = desc_bruto * 100
        else:
            desc_final = desc_bruto

        # 3. Creación del objeto Cliente
        nuevo = Cliente(
            cli_nombre=data.get('nombre'),
            cli_email=data.get('email'),
            cli_alias=data.get('alias'),
            cli_telefono=data.get('telefono'),
            cli_fecha_nacimiento=fecha_obj,
            cli_notas_personales=data.get('notas_personales'), 
            
            # Guardamos el valor normalizado (Ej: 20.00)
            cli_descuento=desc_final,
            cli_descuento_cantidad=int(data.get('descuento_cantidad', 0)),
            
            emp_id=current_user.emp_id,
            cli_activo=True
        )

        # 4. Guardado en Base de Datos
        db.session.add(nuevo)
        db.session.commit()

        print(f"✅ Cliente creado: {nuevo.cli_nombre} con {desc_final}% de descuento.")
        return jsonify({"status": "success", "message": "Cliente creado correctamente"})

    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"❌ Error al crear cliente: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"status": "error", "message": f"No se pudo crear el cliente: {str(e)}"})
    
    

@admin_bp.route('/api/cliente/editar/<int:cli_id>', methods=['POST'])
@login_required
def editar_cliente(cli_id):
    data = request.get_json()
    cliente = Cliente.query.filter_by(cli_id=cli_id, emp_id=current_user.emp_id).first_or_404()
    
    try:
        cliente.cli_nombre = data.get('nombre')
        cliente.cli_alias = data.get('alias')
        cliente.cli_email = data.get('email')
        cliente.cli_telefono = data.get('telefono')
        cliente.cli_notas_personales = data.get('notas_personales') 
        
        # --- NUEVOS CAMPOS ---
        cliente.cli_descuento = float(data.get('descuento', 0))
        cliente.cli_descuento_cantidad = int(data.get('descuento_cantidad', 0))
        # ---------------------
        
        fecha_nac = data.get('fecha_nacimiento')
        if fecha_nac:
            cliente.cli_fecha_nacimiento = datetime.strptime(fecha_nac, '%Y-%m-%d').date()
        else:
            cliente.cli_fecha_nacimiento = None # Por si quieren borrar la fecha
        
        db.session.commit()
        return jsonify({"status": "success", "message": "Cliente actualizado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500



@admin_bp.route('/api/cliente/desactivar/<int:id>', methods=['POST'])
@login_required
def api_desactivar_cliente(id):
    try:
        sql = text("UPDATE CLIENTES SET cli_activo = 0 WHERE cli_id = :id")
        db.session.execute(sql, {"id": id})
        db.session.commit()
        return jsonify({"status": "success", "message": "Cliente desactivado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    

@admin_bp.route('/api/cliente/activar/<int:id>', methods=['POST'])
@login_required
def api_activar_cliente(id):
    try:
        sql = text("UPDATE CLIENTES SET cli_activo = 1 WHERE cli_id = :id")
        db.session.execute(sql, {"id": id})
        db.session.commit()
        return jsonify({"status": "success", "message": "Cliente activado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    



@admin_bp.route('/api/cliente/eliminar/<int:cli_id>', methods=['DELETE'])
@login_required
def eliminar_cliente(cli_id):
    
    
    cliente = Cliente.query.filter_by(cli_id=cli_id, emp_id=current_user.emp_id).first_or_404()
    
    # VERIFICACIÓN MANUAL: ¿Tiene reservas?
    tiene_reservas = Reserva.query.filter_by(cli_id=cli_id).first()
    
    if tiene_reservas:
        return jsonify({
            "status": "error", 
            "message": "No se puede eliminar el cliente porque tiene reservas realizadas. Intenta desactivarlo en su lugar."
        }), 400

    try:
        db.session.delete(cliente)
        db.session.commit()
        return jsonify({"status": "success", "message": "Cliente eliminado"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": "Error interno del servidor"}), 500
    
    
    
# EXPORTAR A EXCEL
@admin_bp.route('/clientes/exportar')
@login_required
def exportar_clientes():
    from models.models import Cliente
    clientes = Cliente.query.filter_by(emp_id=current_user.emp_id).all()
    
    # Crear lista de datos
    data = [{
        'Nombre': c.cli_nombre,
        'Alias': c.cli_alias,
        'Email': c.cli_email,
        'Telefono': c.cli_telefono,
        'Estado': 'Activo' if c.cli_activo else 'Inactivo'
    } for c in clientes]
    
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Clientes')
    
    output.seek(0)
    return send_file(output, 
                     download_name="Mis_Clientes.xlsx", 
                     as_attachment=True,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# IMPORTAR DESDE EXCEL
@admin_bp.route('/clientes/importar', methods=['POST'])
@login_required
def importar_clientes():
    from models.models import db, Cliente
    file = request.files.get('file')
    
    if not file:
        return redirect(url_for('admin.gestion_clientes'))

    registros_nuevos = 0
    registros_actualizados = 0

    try:
        # Leemos el archivo
        df = pd.read_excel(file)
        
        for index, row in df.iterrows():
            nombre = str(row.get('Nombre', '')).strip()
            email = str(row.get('Email', '')).strip().lower()
            
            if not nombre or nombre == 'nan':
                continue

            # 1. Buscamos si el cliente ya existe en esta empresa
            cliente_existente = Cliente.query.filter_by(cli_email=email, emp_id=current_user.emp_id).first()
            
            if cliente_existente:
                # ACTUALIZAR: Si existe, actualizamos sus otros datos
                cliente_existente.cli_nombre = nombre
                cliente_existente.cli_alias = str(row.get('Alias', '')) if str(row.get('Alias')) != 'nan' else cliente_existente.cli_alias
                cliente_existente.cli_telefono = str(row.get('Telefono', '')).split('.')[0] if str(row.get('Telefono')) != 'nan' else cliente_existente.cli_telefono
                registros_actualizados += 1
            else:
                # INSERTAR: Si no existe, creamos uno nuevo
                nuevo = Cliente(
                    cli_nombre=nombre,
                    cli_alias=str(row.get('Alias', '')) if str(row.get('Alias')) != 'nan' else '',
                    cli_email=email if email != 'nan' else None,
                    cli_telefono=str(row.get('Telefono', '')).split('.')[0],
                    emp_id=current_user.emp_id,
                    cli_activo=True
                )
                db.session.add(nuevo)
                registros_nuevos += 1
            
        db.session.commit()
        
        # Reporte final para el usuario
        flash(f"Proceso completado: {registros_nuevos} clientes nuevos creados y {registros_actualizados} actualizados.", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error al procesar el archivo: {str(e)}", "error")
            
    return redirect(url_for('admin.gestion_clientes'))



@admin_bp.route('/clientes/plantilla')
@login_required
def descargar_plantilla():
    import pandas as pd
    from io import BytesIO
    
    # Definimos las columnas exactas que espera el sistema
    df = pd.DataFrame(columns=['Nombre', 'Alias', 'Email', 'Telefono'])
    
    # Agregamos una fila de ejemplo (opcional)
    df.loc[0] = ['Ejemplo Nombre', 'Ejemplo Alias', 'ejemplo@correo.com', '3001234567']
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Plantilla')
    
    output.seek(0)
    return send_file(output, 
                     download_name="Plantilla_Clientes.xlsx", 
                     as_attachment=True)

# --- 5. GESTIÓN DE SERVICIOS 

@admin_bp.route('/servicios')
@login_required
def gestion_servicios():
    # 1. Servicios que se muestran en la tabla principal y en las reservas
    servicios_activos = Servicio.query.filter_by(
        emp_id=current_user.emp_id, 
        ser_estado=1
    ).all()

    # 2. Servicios que Diego ha "borrado" (inactivado)
    servicios_inactivos = Servicio.query.filter_by(
        emp_id=current_user.emp_id, 
        ser_estado=0
    ).all()

    # Pasamos AMBAS listas al HTML
    return render_template(
        'admin/servicios.html', 
        servicios=servicios_activos, 
        inactivos=servicios_inactivos
    )

@admin_bp.route('/servicios/nuevo', methods=['POST'])
@login_required
def servicio_nuevo():
    try:
        nombre = request.form.get('nombre').strip()
        precio_raw = request.form.get('precio').replace('.', '').replace(' ', '')
        tiempo = int(request.form.get('tiempo', 0))

        # VALIDACIÓN DE BLOQUES DE 30 MIN
        if tiempo < 30 or tiempo % 30 != 0:
            flash("El tiempo debe ser en bloques de 30 minutos (ej: 30, 60, 90, 120)", "error")
            return redirect(url_for('admin.gestion_servicios'))
        
        nuevo_servicio = Servicio(
            ser_nombre=nombre, 
            ser_precio=int(precio_raw),
            ser_tiempo=tiempo,
            emp_id=current_user.emp_id,
            ser_estado=1
        )
        db.session.add(nuevo_servicio)
        db.session.commit()
        flash("Servicio añadido correctamente", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al guardar: {str(e)}", "error")
        
    return redirect(url_for('admin.gestion_servicios'))

@admin_bp.route('/servicios/editar/<int:servicio_id>', methods=['POST'])
@login_required
def editar_servicio(servicio_id):
    servicio = Servicio.query.get_or_404(servicio_id)
    try:
        precio_raw = request.form.get('precio', '0').replace('.', '').replace(' ', '')
        tiempo = int(request.form.get('tiempo', 0))

        # VALIDACIÓN DE BLOQUES DE 30 MIN
        if tiempo < 30 or tiempo % 30 != 0:
            flash("El tiempo debe ser en bloques de 30 minutos (ej: 30, 60, 90, 120)", "error")
            return redirect(url_for('admin.gestion_servicios'))

        servicio.ser_nombre = request.form.get('nombre')
        servicio.ser_precio = int(precio_raw)
        servicio.ser_tiempo = tiempo 
        
        db.session.commit()
        flash('Servicio actualizado correctamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar: {str(e)}', 'error')

    return redirect(url_for('admin.gestion_servicios'))

@admin_bp.route('/api/servicio/inactivar/<int:servicio_id>', methods=['POST'])
@login_required
def inactivar_servicio(servicio_id):
    from models.models import Servicio, db
    
    # Buscamos el servicio
    servicio = Servicio.query.get_or_404(servicio_id)
    
    # Verificamos seguridad
    if servicio.emp_id != current_user.emp_id:
        return jsonify({"status": "error", "message": "No tienes permiso para modificar este servicio"}), 403

    try:
        # --- PASO 1: LIMPIEZA DE RELACIONES ---
        # Al vaciar la lista 'empleados', SQLAlchemy elimina automáticamente 
        # las filas correspondientes en la tabla EMPLEADO_SERVICIOS
        if hasattr(servicio, 'empleados'):
            servicio.empleados = [] 
        
        # --- PASO 2: INACTIVAR EL SERVICIO ---
        servicio.ser_estado = 0 
        
        db.session.commit()
        
        return jsonify({
            "status": "success", 
            "message": f"El servicio '{servicio.ser_nombre}' ha sido inactivado y removido de todos los empleados."
        })

    except Exception as e:
        db.session.rollback()
        print(f"Error al inactivar: {str(e)}")
        return jsonify({"status": "error", "message": f"Error técnico: {str(e)}"}), 500
    
    
    
@admin_bp.route('/api/servicio/reactivar/<int:servicio_id>', methods=['POST'])
@login_required
def reactivar_servicio(servicio_id):
    servicio = Servicio.query.get_or_404(servicio_id)
    
    if servicio.emp_id != current_user.emp_id:
        return jsonify({"status": "error", "message": "No autorizado"}), 403

    try:
        servicio.ser_estado = 1 # Volver a Activo
        db.session.commit()
        return jsonify({"status": "success", "message": "Servicio reactivado correctamente."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    
    
    
@admin_bp.route('/actualizar-servicios-masivo', methods=['POST'])
@login_required
def actualizar_servicios_masivo():
    # Detectamos si los switches están en el request
    nuevo_estado_precio = 1 if 'switch_precio' in request.form else 0
    nuevo_estado_tiempo = 1 if 'switch_tiempo' in request.form else 0

    try:
        # CORRECCIÓN: Usamos 'Servicio' que es como lo tienes importado
        db.session.query(Servicio).update({
            Servicio.mostrar_precio: nuevo_estado_precio,
            Servicio.mostrar_tiempo: nuevo_estado_tiempo
        })
        db.session.commit()
        # Opcional: print("¡Actualización masiva exitosa!") 
    except Exception as e:
        db.session.rollback()
        print(f"Error en update masivo: {e}")

    return redirect(url_for('admin.gestion_servicios'))
    
    

# --- 6. GESTIÓN DE RESERVAS 


def enviar_recibo_por_correo(reserva, cliente, empresa, precio_base, precio_final, descuento_porc):
    if not cliente.cli_email or not empresa.emp_cuenta_smtp: 
        print("Falta email del cliente o cuenta SMTP de la empresa")
        return False
        
    try:
        # 1. Generar el PDF en memoria (Sigue igual)
        html_pdf = render_template('admin/pdf_recibo.html', 
                                   r=reserva, 
                                   c=cliente, 
                                   empresa=empresa,
                                   p_original=precio_base,
                                   p_final=precio_final,
                                   p_desc=descuento_porc)
        
        output = io.BytesIO()
        pisa.CreatePDF(io.BytesIO(html_pdf.encode("UTF-8")), dest=output, encoding='UTF-8')
        pdf_binario = output.getvalue()
        nombre_archivo = f"Recibo_{reserva.res_id}.pdf"

        # --- NUEVO: 2. GENERAR EL LINK Y EL CUERPO HTML DEL CORREO ---
        # Creamos el link que irá en el botón del correo
        link_resena = url_for('admin.dejar_resena', 
                             emp_id=empresa.emp_id, 
                             res_id=reserva.res_id, 
                             empl_id=reserva.empl_id, 
                             _external=True)

        # Renderizamos el nuevo template que creaste
        cuerpo_html = render_template('emails/email_cuerpo.html', 
                                     cliente=cliente, 
                                     empresa=empresa, 
                                     reserva=reserva,
                                     link_resena=link_resena)

        # 3. Configurar el Mensaje MIME
        msg = MIMEMultipart()
        msg['From'] = empresa.emp_cuenta_smtp
        msg['To'] = cliente.cli_email
        msg['Subject'] = f"Tu Recibo de Servicio - {empresa.emp_razon_social}"
        
        # CAMBIO AQUÍ: Usamos 'html' en lugar de 'plain'
        msg.attach(MIMEText(cuerpo_html, 'html'))

        # 4. Adjuntar el PDF (Sigue igual)
        part = MIMEApplication(pdf_binario, Name=nombre_archivo)
        part['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
        msg.attach(part)

        # 5. Conexión SMTP manual
        servidor = smtplib.SMTP(empresa.emp_servidor_smtp, int(empresa.emp_puerto_smtp))
        servidor.starttls()
        servidor.login(empresa.emp_cuenta_smtp, empresa.emp_clave_cuenta_smtp)
        servidor.send_message(msg)
        servidor.quit()
        
        print(f"✅ Recibo HTML enviado con éxito a {cliente.cli_email}")
        return True
        
    except Exception as e:
        print(f"❌ Error enviando recibo a cliente: {e}")
        return False


@admin_bp.app_context_processor
def inject_pendientes():
    from models.models import Reserva
    # Contamos las reservas con estado 'pendiente'
    count = Reserva.query.filter_by(res_estado='pendiente').count()
    return dict(pendientes_count=count)



@admin_bp.route('/reserva/recibo/<int:res_id>')
@login_required
def generar_recibo_cliente(res_id):
    import io
    from flask import render_template, make_response
    from xhtml2pdf import pisa
    from models.models import Reserva, Cliente, Empresa, Servicio

    reserva = Reserva.query.get_or_404(res_id)
    cliente = Cliente.query.get(reserva.cli_id)
    empresa = Empresa.query.get(current_user.emp_id)
    
    # --- LÓGICA DE EMERGENCIA PARA SER_ID NULL ---
    servicio = None
    
    # 1. Intentamos por ID (si existe)
    if reserva.ser_id:
        servicio = Servicio.query.get(reserva.ser_id)
    
    # 2. Si no hay ID, buscamos por el NOMBRE escrito en res_tipo_servicio
    if not servicio and reserva.res_tipo_servicio:
        servicio = Servicio.query.filter_by(
            ser_nombre=reserva.res_tipo_servicio, 
            emp_id=reserva.emp_id
        ).first()

    # 3. Asignamos precios
    precio_base = float(servicio.ser_precio) if servicio else 0.0
    descuento_porc = float(reserva.res_descuento_valor or 0)
    
    # 4. Calculamos montos
    monto_ahorro = precio_base * (descuento_porc / 100)
    precio_final = precio_base - monto_ahorro

    # DEBUG para que veas en la terminal qué encontró
    print(f"--- REPORTE RECIBO {res_id} ---")
    print(f"Buscando: {reserva.res_tipo_servicio}")
    print(f"Encontrado: {servicio.ser_nombre if servicio else 'NADA'}")
    print(f"Precio: {precio_base} | Descuento: {descuento_porc}% | Total: {precio_final}")

    html = render_template('admin/pdf_recibo.html', 
                           r=reserva, 
                           c=cliente, 
                           empresa=empresa,
                           p_original=precio_base,
                           p_final=precio_final,
                           p_desc=descuento_porc)

    output = io.BytesIO()
    pisa.CreatePDF(io.BytesIO(html.encode("UTF-8")), dest=output, encoding='UTF-8')
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=Recibo_{reserva.res_id}.pdf'
    
    return response


@admin_bp.route('/reservas')
@login_required
def reservas():
    ahora = datetime.now()
    hoy = ahora.date()
    ayer = hoy - timedelta(days=1)
    manana = hoy + timedelta(days=1)
    
    # 1. Datos básicos
    datos_empresa = Empresa.query.get(current_user.emp_id)
    lista_empleados = Empleado.query.filter_by(emp_id=current_user.emp_id, empl_activo=1).all()
    
    # 2. Carga de reservas
    todas_las_reservas = Reserva.query.filter_by(emp_id=current_user.emp_id)\
                        .order_by(Reserva.res_fecha.asc(), Reserva.res_hora.asc()).all()
    
    reservas_data = []
    
    for r in todas_las_reservas:
        r.estado_normalizado = r.res_estado.lower().strip() if r.res_estado else ""
        # --- 3. LÓGICA DE PRECIO Y DESCUENTO REAL (COLUMNA PROPIA) ---
        servicio_obj = Servicio.query.filter_by(
            ser_nombre=r.res_tipo_servicio, 
            emp_id=current_user.emp_id
        ).first()
        
        # Convertimos Decimal a float para evitar errores de cálculo
        if servicio_obj and servicio_obj.ser_precio:
            precio_base = float(servicio_obj.ser_precio)
        else:
            precio_base = 0.0
            
        r.precio_estimado = precio_base 
        
        # PRIORIDAD: Usamos la nueva columna res_descuento_valor que "congelamos" al reservar
        # Si es None o 0, el float lo manejará correctamente.
        porcentaje_desc = float(r.res_descuento_valor or 0.0)
        
        # Si por alguna razón la reserva no tiene descuento guardado (reservas viejas),
        # revisamos si el cliente tiene uno activo ahora mismo.
        if porcentaje_desc == 0 and r.cliente and r.cliente.cli_descuento:
            porcentaje_desc = float(r.res_descuento_valor or 0.0) # Ahora vendrá un 20.0

        # Cálculo de precio final
        if porcentaje_desc > 0:
            r.precio_final = precio_base * (1 - (porcentaje_desc / 100))
            r.tiene_descuento = True
            r.monto_descuento = int(porcentaje_desc)
        else:
            r.precio_final = precio_base
            r.tiene_descuento = False

        # --- 4. ASIGNACIÓN DE EMPLEADOS APTOS ---
        empleados_aptos = [] 
        if servicio_obj:
            from sqlalchemy import text
            sql = text("""
                SELECT e.* FROM EMPLEADOS e
                JOIN EMPLEADO_SERVICIOS es ON e.empl_id = es.empl_id
                WHERE es.ser_id = :s_id AND e.empl_activo = 1
            """)
            try:
                # Usamos la conexión de base de datos para ejecutar el SQL crudo
                empleados_aptos = db.session.query(Empleado).from_statement(sql).params(s_id=servicio_obj.ser_id).all()
            except Exception as e:
                print(f"Error SQL empleados: {e}")
                empleados_aptos = lista_empleados
        
        if not empleados_aptos:
            empleados_aptos = lista_empleados

        # --- 5. EMPAQUETADO FINAL ---
        reservas_data.append((r, r.cliente, empleados_aptos))

    return render_template('admin/reservas.html', 
                           reservas_data=reservas_data, 
                           lista_empleados=lista_empleados,
                           hoy=hoy, ayer=ayer, manana=manana,
                           empresa=datos_empresa)
    
    
    

@admin_bp.route('/reserva_estado/<int:id>', methods=['POST'])
@login_required
def reserva_estado(id):
    reserva = Reserva.query.get_or_404(id)
    estado_actual = reserva.res_estado.lower().strip() if reserva.res_estado else ""
    
    if estado_actual in ['realizada', 'completada']:
        flash("Esta cita ya ha sido finalizada.", "error")
        return redirect(url_for('admin.reservas'))

    nuevo_estado = request.form.get('estado')
    if not nuevo_estado:
        return redirect(url_for('admin.reservas'))

    nuevo_estado_clean = nuevo_estado.lower().strip()

    # ... (Tu lógica de validación de conflictos se mantiene igual) ...

    # ACTUALIZACIÓN DE ESTADO
    reserva.res_estado = nuevo_estado
    db.session.commit()

    # --- NUEVA LÓGICA DE ENVÍO AUTOMÁTICO ---
    if nuevo_estado_clean == 'realizada':
        # Buscamos datos para el recibo (reutilizando tu lógica del def generar_recibo_cliente)
        cliente = Cliente.query.get(reserva.cli_id)
        empresa = Empresa.query.get(current_user.emp_id)
        servicio = Servicio.query.get(reserva.ser_id) if reserva.ser_id else \
                   Servicio.query.filter_by(ser_nombre=reserva.res_tipo_servicio, emp_id=reserva.emp_id).first()

        precio_base = float(servicio.ser_precio) if servicio else 0.0
        descuento_porc = float(reserva.res_descuento_valor or 0)
        precio_final = precio_base * (1 - (descuento_porc / 100))

        if cliente and cliente.cli_email:
            enviar_recibo_por_correo(reserva, cliente, empresa, precio_base, precio_final, descuento_porc)
            flash(f"Reserva finalizada y recibo enviado a {cliente.cli_email}", "success")
        else:
            flash("Reserva finalizada, pero el cliente no tiene correo registrado.", "warning")

    return redirect(url_for('admin.reservas'))



@admin_bp.route('/reserva/asignar_empleado/<int:id>', methods=['POST'])
@login_required
def asignar_empleado(id):
    reserva = Reserva.query.get_or_404(id)
    empleado_seleccionado = request.form.get('empleado_id')
    
    if empleado_seleccionado:
        # CORRECCIÓN: Usamos empl_id (empleado), no emp_id (empresa)
        reserva.empl_id = int(empleado_seleccionado) 
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return f"Error al guardar: {str(e)}"
            
    return redirect(url_for('admin.reservas'))


@admin_bp.route('/acciones-masivas-reservas', methods=['POST'])
@login_required
def acciones_masivas_reservas():
    data = request.get_json()
    ids = data.get('ids', [])
    accion = data.get('accion') 
    
    if not ids:
        return jsonify({'success': False, 'message': 'No hay selecciones'}), 400

    try:
        # Obtenemos las reservas y la empresa (una sola vez para ahorrar recursos)
        reservas = Reserva.query.filter(Reserva.res_id.in_(ids)).all()
        empresa = Empresa.query.get(current_user.emp_id)
        
        contador_correos = 0

        for res in reservas:
            if accion == 'realizada':
                # Evitamos procesar si ya estaba realizada
                if res.res_estado.lower().strip() != 'realizada':
                    res.res_estado = 'Realizada'
                    
                    # --- LÓGICA DE ENVÍO DE CORREO ---
                    cliente = Cliente.query.get(res.cli_id)
                    if cliente and cliente.cli_email:
                        # Buscamos el servicio para el precio
                        servicio = Servicio.query.get(res.ser_id) if res.ser_id else \
                                   Servicio.query.filter_by(ser_nombre=res.res_tipo_servicio, emp_id=res.emp_id).first()
                        
                        precio_base = float(servicio.ser_precio) if servicio else 0.0
                        descuento_porc = float(res.res_descuento_valor or 0)
                        precio_final = precio_base * (1 - (descuento_porc / 100))
                        
                        # Llamamos a la función de utilidad (definida previamente)
                        enviar_recibo_por_correo(res, cliente, empresa, precio_base, precio_final, descuento_porc)
                        contador_correos += 1

            elif accion == 'confirmada':
                res.res_estado = 'Confirmada'
            elif accion == 'pendiente':
                res.res_estado = 'Pendiente'
            elif accion == 'cancelada':
                res.res_estado = 'Cancelada'
            elif accion == 'eliminar':
                db.session.delete(res)

        db.session.commit()
        
        msg_extra = f" y se enviaron {contador_correos} recibos" if contador_correos > 0 else ""
        return jsonify({
            'success': True, 
            'message': f'{len(ids)} reservas procesadas (Acción: {accion}){msg_extra}.'
        })

    except Exception as e:
        db.session.rollback()
        print(f"Error en acciones masivas: {str(e)}")
        return jsonify({'success': False, 'message': f"Error en el servidor: {str(e)}"}), 500
    
    

@admin_bp.route('/cliente/update-nota/<int:id>', methods=['POST'])
@login_required
def update_nota_cliente(id):
    data = request.get_json()
    cliente = Cliente.query.get_or_404(id)
    cliente.cli_notas_personales = data.get('nota')
    db.session.commit()
    return jsonify({'status': 'ok'})
    
    

@admin_bp.route('/mover_reserva', methods=['POST'])
@login_required
def mover_reserva():
    try:
        data = request.get_json()
        res_id = data.get('id')
        empl_id = data.get('empl_id')
        nueva_fecha_str = data.get('fecha')

        # 1. USAMOS EL NOMBRE CORRECTO: ConfigHorario (singular)
        reserva = Reserva.query.get(res_id)
        emp = Empresa.query.get(current_user.emp_id)
        nombre_empresa = emp.emp_razon_social if emp else "el establecimiento"

        fecha_nueva = datetime.strptime(nueva_fecha_str, '%Y-%m-%d').date()
        dia_semana_index = fecha_nueva.weekday() 
        
        # BUSQUEDA CON EL NOMBRE CORRECTO
        config = ConfigHorario.query.filter_by(dia_semana=dia_semana_index).first()

        if not config or not config.activo:
            return jsonify({
                "status": "error", 
                "message": f"Estás intentando reagendar en un día que no está disponible para {nombre_empresa}."
            }), 400

        hora_cita = reserva.res_hora

        # Validar Apertura y Cierre
        if hora_cita < config.hora_inicio or hora_cita >= config.hora_fin:
            return jsonify({
                "status": "error", 
                "message": f"Horario fuera de servicio para {nombre_empresa} a esta hora."
            }), 400

        # Validar Almuerzo
        if config.almuerzo_inicio and config.almuerzo_fin:
            if config.almuerzo_inicio <= hora_cita < config.almuerzo_fin:
                return jsonify({
                    "status": "error", 
                    "message": f"El horario coincide con el tiempo de descanso de {nombre_empresa}."
                }), 400
                
                
                
                
                # ... obtener data y reserva ...
        reserva = Reserva.query.get(res_id)

        if reserva.res_estado == 'Completada':
            return jsonify({
                "status": "error", 
                "message": "La reserva ya ha sido completada y no permite más cambios."
            }), 403

        # Validación de Choque (Empleado ocupado)
        choque = Reserva.query.filter(
            Reserva.res_fecha == fecha_nueva,
            Reserva.res_hora == hora_cita,
            Reserva.empl_id == empl_id,
            Reserva.res_id != res_id,
            Reserva.res_estado.in_(['Confirmada', 'Pendiente', 'Realizada'])
        ).first()

        if choque:
            return jsonify({
                "status": "error", 
                "message": "El profesional seleccionado ya tiene una cita reservada a esta hora."
            }), 400

        # Si todo está OK, actualizamos
        reserva.res_fecha = fecha_nueva
        reserva.empl_id = empl_id
        db.session.commit()
        
        return jsonify({"status": "success", "message": "Reserva movida exitosamente"}), 200

    except Exception as e:
        db.session.rollback()
        print(f"ERROR: {str(e)}")
        return jsonify({"status": "error", "message": f"Error al procesar el cambio: {str(e)}"}), 500
    
    
@admin_bp.route('/reagendar_hora', methods=['POST'])
@login_required
def reagendar_hora():
    data = request.get_json()
    res_id = data.get('id')
    nueva_hora_str = data.get('hora')
    nueva_fecha_str = data.get('fecha') # Recibimos la fecha también

    reserva = Reserva.query.get(res_id)
    if not reserva:
        return jsonify({"status": "error", "message": "Reserva no encontrada"}), 404

    try:
        # 1. Actualizar Hora
        # Si la hora viene de tu API como "10:30:00"
        reserva.res_hora = datetime.strptime(nueva_hora_str, "%H:%M:%S").time()
        
        # 2. Actualizar Fecha (Si se envió)
        if nueva_fecha_str:
            reserva.res_fecha = datetime.strptime(nueva_fecha_str, "%Y-%m-%d").date()
            
        db.session.commit()
        return jsonify({"status": "success", "message": "Reserva actualizada correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": f"Error al procesar datos: {str(e)}"}), 500

# --- 7. GESTION DE HORARIOS ---

@admin_bp.route('/configurar-horarios')
@login_required
def configurar_horarios():
    horarios = ConfigHorario.query.order_by(ConfigHorario.dia_semana).all()
    # CAMBIO AQUÍ: DiasBloqueados en lugar de DiaBloqueado
    bloqueos = DiasBloqueados.query.order_by(DiasBloqueados.fecha).all() 
    return render_template('admin/horarios.html', horarios=horarios, bloqueos=bloqueos)



@admin_bp.route('/admin/horarios/guardar', methods=['POST'])
@login_required
def guardar_horarios():
    try:
        # 1. ACTUALIZAR HORARIOS SEMANALES (Lunes a Domingo)
        for i in range(7):
            # Captura de datos desde el formulario
            activo = request.form.get(f'activo_{i}') == 'on'
            apertura = request.form.get(f'apertura_{i}')
            cierre = request.form.get(f'cierre_{i}')
            almuerzo_ini = request.form.get(f'almuerzo_inicio_{i}')
            almuerzo_fin = request.form.get(f'almuerzo_fin_{i}')

            # Buscar configuración existente o crear una nueva
            config = ConfigHorario.query.filter_by(dia_semana=i).first()
            if not config:
                config = ConfigHorario(dia_semana=i)
                db.session.add(config)

            # Actualizar Jornada Laboral
            config.activo = activo
            if apertura:
                config.hora_inicio = datetime.strptime(apertura, '%H:%M').time()
            if cierre:
                config.hora_fin = datetime.strptime(cierre, '%H:%M').time()

            # Actualizar Receso de Almuerzo (Manejo de vacíos)
            if almuerzo_ini and almuerzo_fin and almuerzo_ini.strip() and almuerzo_fin.strip():
                config.almuerzo_inicio = datetime.strptime(almuerzo_ini, '%H:%M').time()
                config.almuerzo_fin = datetime.strptime(almuerzo_fin, '%H:%M').time()
            else:
                config.almuerzo_inicio = None
                config.almuerzo_fin = None

        # 2. BLOQUEAR FECHA ESPECÍFICA (Festivos / Vacaciones)
        fecha_bloqueo_str = request.form.get('fecha_bloqueo')
        motivo_bloqueo = request.form.get('motivo_bloqueo')

        if fecha_bloqueo_str and fecha_bloqueo_str.strip():
            fecha_dt = datetime.strptime(fecha_bloqueo_str, '%Y-%m-%d').date()
            
            # Verificar si la fecha ya estaba bloqueada para evitar duplicados
            existe_bloqueo = DiasBloqueados.query.filter_by(fecha=fecha_dt).first()
            
            if not existe_bloqueo:
                nuevo_bloqueo = DiasBloqueados(
                    fecha=fecha_dt,
                    motivo=motivo_bloqueo if motivo_bloqueo else "Día no laborable"
                )
                db.session.add(nuevo_bloqueo)

        # 3. GUARDAR TODO EN LA BASE DE DATOS
        db.session.flush() # Sincroniza los cambios en la sesión
        db.session.commit() # Guarda permanentemente
        flash("✅ Configuración general actualizada correctamente", "success")

    except Exception as e:
        db.session.rollback() # Cancela cambios si hay error
        import traceback
        print(f"ERROR EN GUARDAR_HORARIOS: {traceback.format_exc()}")
        flash(f"❌ Error al guardar: {str(e)}", "error")

    # Redirección a tu función de vista (confirmamos que se llama configurar_horarios)
    return redirect(url_for('admin.configurar_horarios'))


@admin_bp.route('/eliminar-bloqueo/<int:id>')
@login_required
def eliminar_bloqueo(id):
    # CAMBIO AQUÍ: DiasBloqueados
    bloqueo = DiasBloqueados.query.get_or_404(id)
    try:
        db.session.delete(bloqueo)
        db.session.commit()
        flash("Fecha desbloqueada correctamente.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar el bloqueo: {str(e)}", "danger")
    
    return redirect(url_for('admin.configurar_horarios'))

# --- 8. CONFIGURACIÓN DE EMPRESA ---

@admin_bp.route('/empresa', methods=['GET', 'POST'])
@login_required
def configurar_empresa():
    empresa = Empresa.query.get_or_404(current_user.emp_id)

    if request.method == 'POST':
        try:
            # Estos nombres deben coincidir exactamente con el 'name' en el HTML
            empresa.emp_razon_social = request.form.get('nombre')
            empresa.emp_nit = request.form.get('nit')
            empresa.emp_direccion = request.form.get('direccion')
            empresa.emp_email = request.form.get('email')
            
            # --- NUEVA LÍNEA PARA EL TELÉFONO ---
            # Guardamos el teléfono que viene del input name="telefono"
            empresa.emp_telefono = request.form.get('telefono')
            # ------------------------------------

            # SMTP (Aseguramos que no tengan espacios accidentales con .strip())
            empresa.emp_servidor_smtp = request.form.get('smtp_servidor').strip() if request.form.get('smtp_servidor') else None
            empresa.emp_puerto_smtp = request.form.get('smtp_puerto').strip() if request.form.get('smtp_puerto') else None
            empresa.emp_cuenta_smtp = request.form.get('smtp_cuenta').strip() if request.form.get('smtp_cuenta') else None

            # Licencia (Con la validación de clave que querías)
            clave = request.form.get('clave_autorizacion')
            if clave == "agendapp2026*":
                empresa.emp_max_usuarios = request.form.get('max_usuarios')
                empresa.emp_tipo_plan = request.form.get('plan')

            db.session.commit()
            flash("Datos actualizados correctamente", "success")
        except Exception as e:
            db.session.rollback()
            print(f"ERROR AL GUARDAR EN BD: {e}") 
            flash(f"Error al guardar: {str(e)}", "danger")
            
        return redirect(url_for('admin.configurar_empresa'))

    return render_template('admin/empresa.html', empresa=empresa)


@admin_bp.route('/test-smtp', methods=['POST'])
@login_required
def test_smtp():
    empresa = Empresa.query.get_or_404(current_user.emp_id)
    
    try:
        msg = EmailMessage()
        msg['Subject'] = "Prueba de Conexión AgendApp"
        msg['From'] = empresa.emp_cuenta_smtp
        msg['To'] = empresa.emp_email if empresa.emp_email else empresa.emp_cuenta_smtp
        msg.set_content(f"Prueba exitosa para {empresa.emp_razon_social}")

        # --- CAMBIO AQUÍ: Usamos puerto 587 y starttls() ---
        servidor = 'smtp.gmail.com'
        puerto = 587 

        # Nota: Usamos smtplib.SMTP (sin _SSL)
        server = smtplib.SMTP(servidor, puerto)
        server.starttls() # Esto activa el cifrado de forma correcta
        server.login(empresa.emp_cuenta_smtp, empresa.emp_clave_cuenta_smtp)
        server.send_message(msg)
        server.quit()
            
        return {"success": True, "message": "¡Correo enviado con éxito!"}
    
    except Exception as e:
        print(f"Error SMTP Detallado: {str(e)}") 
        return {"success": False, "message": f"Error de conexión: {str(e)}"}, 500

# --- 9. PERMISOS Y GESTIÓN DE USUARIOS

@admin_bp.route('/usuarios')
@login_required
def gestion_usuarios():
    # Permitir si es admin O si tiene el permiso habilitado
    if not (current_user.usu_is_admin or current_user.tiene_permiso('ver_usuarios')):
        flash("Acceso denegado: Se requieren permisos para gestionar usuarios.", "danger")
        return redirect(url_for('admin.dashboard'))
    
    usuarios = Usuario.query.all()
    permisos = Permiso.query.all()
    return render_template('admin/usuarios.html', usuarios=usuarios, permisos=permisos)

@admin_bp.route('/usuarios/crear', methods=['POST'])
@login_required
def crear_usuario():
    # Seguridad: Admin o personal autorizado
    if not (current_user.usu_is_admin or current_user.tiene_permiso('ver_usuarios')):
        flash("Acceso denegado.", "danger")
        return redirect(url_for('admin.dashboard'))

    login = request.form.get('usu_login')
    nombre = request.form.get('usu_nombre')
    password = request.form.get('usu_password')
    permisos_seleccionados = request.form.getlist('permisos')

    existe = Usuario.query.filter_by(usu_login=login).first()
    if existe:
        flash(f"El usuario '{login}' ya existe.", "warning")
        return redirect(url_for('admin.gestion_usuarios'))

    try:
        nuevo_usuario = Usuario(
            usu_login=login,
            usu_nombre=nombre,
            usu_password=generate_password_hash(password),
            emp_id=current_user.emp_id,
            usu_is_admin=False
        )
        
        db.session.add(nuevo_usuario)
        db.session.flush() 

        for p_nom in permisos_seleccionados:
            # Buscamos por perm_nombre (coincide con tu tabla PERMISOS)
            permiso = Permiso.query.filter_by(perm_nombre=p_nom).first()
            
            if not permiso:
                permiso = Permiso(perm_nombre=p_nom, perm_descripcion=f"Acceso a {p_nom}")
                db.session.add(permiso)
                db.session.flush()
            
            # Usamos la relación en mayúsculas PERMISOS
            nuevo_usuario.PERMISOS.append(permiso)

        db.session.commit()
        flash(f"✅ Usuario {login} creado correctamente.", "success")
        
    except Exception as e:
        db.session.rollback()
        print(f"DEBUG ERROR: {str(e)}") 
        flash(f"❌ Error al crear: {str(e)}", "danger")

    return redirect(url_for('admin.gestion_usuarios'))

@admin_bp.route('/usuarios/get/<int:id>')
@login_required
def get_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    # Importante: El nombre de la clave debe ser 'permisos' para el JS
    return jsonify({
        'usu_login': usuario.usu_login,
        'usu_nombre': usuario.usu_nombre,
        'permisos': [p.perm_nombre for p in usuario.PERMISOS] # Aquí usamos la relación PERMISOS
    })

@admin_bp.route('/usuarios/editar/<int:id>', methods=['POST'])
@login_required
def editar_usuario_save(id):
    # 1. Seguridad: Permitir si es admin O si tiene el permiso asignado
    if not (current_user.usu_is_admin or current_user.tiene_permiso('ver_usuarios')):
        flash("Acceso denegado: No tienes permisos para editar usuarios.", "danger")
        return redirect(url_for('admin.dashboard'))

    usuario = Usuario.query.get_or_404(id)
    
    # 2. Protección Extra: Un no-admin no puede editar a un Super Admin
    if usuario.usu_is_admin and not current_user.usu_is_admin:
        flash("❌ No tienes nivel de autoridad para editar a un Administrador.", "warning")
        return redirect(url_for('admin.gestion_usuarios'))

    # --- 2.5 PROTECCIÓN PARA EL USUARIO RAÍZ 'agendapp' ---
    if usuario.usu_login == 'agendapp' and current_user.usu_login != 'agendapp':
        flash("❌ El usuario maestro 'agendapp' está protegido. Solo él puede editar su información.", "danger")
        return redirect(url_for('admin.gestion_usuarios'))
    # -----------------------------------------------------

    try:
        # 3. Actualizar datos básicos
        # Solo permitimos cambiar el login si NO es agendapp para evitar que pierda su identidad de sistema
        if usuario.usu_login != 'agendapp':
            usuario.usu_login = request.form.get('usu_login')
            
        usuario.usu_nombre = request.form.get('usu_nombre')
        
        # 4. Manejo de contraseña (solo si se ingresó una nueva)
        nueva_clave = request.form.get('usu_password')
        if nueva_clave and nueva_clave.strip() != "":
            usuario.usu_password = generate_password_hash(nueva_clave)

        # 5. Actualizar Permisos
        permisos_seleccionados = request.form.getlist('permisos')
        
        # Limpiamos los permisos actuales usando la relación correcta (Mayúsculas)
        usuario.PERMISOS = []
        
        for p_nom in permisos_seleccionados:
            permiso = Permiso.query.filter_by(perm_nombre=p_nom).first()
            if not permiso:
                permiso = Permiso(perm_nombre=p_nom, perm_descripcion=f"Acceso a {p_nom}")
                db.session.add(permiso)
                db.session.flush() 
            
            usuario.PERMISOS.append(permiso)

        db.session.commit()
        flash(f"✅ Usuario {usuario.usu_login} actualizado correctamente.", "success")

    except Exception as e:
        db.session.rollback()
        print(f"DEBUG: Error al editar usuario {id}: {str(e)}")
        flash(f"❌ Error al actualizar: {str(e)}", "danger")

    return redirect(url_for('admin.gestion_usuarios'))

@admin_bp.route('/usuarios/eliminar/<int:id>')
@login_required
def eliminar_usuario(id):
    # 1. Seguridad: Permitir si es admin O si tiene el permiso específico
    if not (current_user.usu_is_admin or current_user.tiene_permiso('ver_usuarios')):
        flash("Acceso denegado: No tienes permiso para eliminar usuarios.", "danger")
        return redirect(url_for('admin.dashboard'))

    # 2. Evitar suicidio de cuenta (No eliminarse a sí mismo)
    if id == current_user.usu_id:
        flash("❌ No puedes eliminar tu propia cuenta.", "warning")
        return redirect(url_for('admin.gestion_usuarios'))

    usuario = Usuario.query.get_or_404(id)

    # 3. Protección de Jerarquía: Un no-admin NO puede eliminar a un Admin
    if usuario.usu_is_admin and not current_user.usu_is_admin:
        flash("❌ No tienes autoridad para eliminar a un Administrador.", "danger")
        return redirect(url_for('admin.gestion_usuarios'))

    # 4. Protección para el ID 1 (Root)
    if id == 1:
        flash("❌ El usuario raíz del sistema es intocable.", "danger")
        return redirect(url_for('admin.gestion_usuarios'))

    try:
        db.session.delete(usuario)
        db.session.commit()
        flash(f"✅ Usuario '{usuario.usu_login}' eliminado correctamente.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"❌ Error al eliminar: {str(e)}", "danger")

    return redirect(url_for('admin.gestion_usuarios'))



# ----10. GESTION DE COMISIONES 


@admin_bp.route('/descargar-reporte-cierre')
@login_required
def descargar_reporte_cierre():
    lista_empleados = Empleado.query.filter_by(emp_id=current_user.emp_id, empl_activo=1).all()
    
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = 750

    # --- ENCABEZADO PRINCIPAL ---
    p.setFont("Helvetica-Bold", 18)
    p.drawString(50, y, "REPORTE DETALLADO DE CIERRE DE CAJA")
    y -= 20
    p.setFont("Helvetica", 10)
    p.drawString(50, y, f"Fecha de Generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    y -= 30

    total_bruto_general = 0
    total_pagos_empleados = 0

    for emp in lista_empleados:
        reservas = Reserva.query.filter_by(empl_id=emp.empl_id, res_estado='Realizada').all()
        
        if not reservas:
            continue

        # Espacio mínimo para un nuevo bloque de empleado
        if y < 150:
            p.showPage()
            y = 750

        # --- BLOQUE DE COLABORADOR ---
        p.setFillColorRGB(0.95, 0.95, 0.95)
        p.rect(50, y-15, 512, 20, fill=1)
        p.setFillColorRGB(0, 0, 0)
        p.setFont("Helvetica-Bold", 11)
        p.drawString(60, y-10, f"COLABORADOR: {emp.empl_nombre.upper()}")
        y -= 35

        # Encabezados de tabla
        p.setFont("Helvetica-Bold", 8)
        columnas = [
            (55, "FECHA/HORA"), (140, "SERVICIO"), (250, "BASE"), 
            (300, "DESC %"), (350, "FINAL"), (400, "COMISIÓN"), (470, "AL LOCAL")
        ]
        for pos, texto in columnas:
            p.drawString(pos, y, texto)
        
        y -= 5
        p.line(50, y, 562, y)
        y -= 12

        subtotal_bruto_emp = 0
        subtotal_pago_emp = 0
        porcentaje_comision = float(emp.empl_porcentaje or 40)

        p.setFont("Helvetica", 8)
        for res in reservas:
            ser = Servicio.query.filter_by(ser_nombre=res.res_tipo_servicio, emp_id=current_user.emp_id).first()
            if ser:
                # Lógica de porcentaje corregida
                precio_base = float(ser.ser_precio)
                porc_desc = float(res.res_descuento_valor or 0)
                valor_desc = precio_base * (porc_desc / 100)
                precio_final = precio_base - valor_desc
                
                comision_servicio = precio_final * (porcentaje_comision / 100)
                local_servicio = precio_final - comision_servicio

                # Dibujar Fila
                p.drawString(55, y, f"{res.res_fecha.strftime('%d/%m')} {res.res_hora.strftime('%H:%M')}")
                p.drawString(140, y, res.res_tipo_servicio[:20])
                p.drawString(250, y, f"${precio_base:,.0f}")
                p.drawString(300, y, f"{int(porc_desc)}%")
                p.drawString(350, y, f"${precio_final:,.0f}")
                p.drawString(400, y, f"${comision_servicio:,.0f}")
                p.drawString(470, y, f"${local_servicio:,.0f}")

                subtotal_bruto_emp += precio_final
                subtotal_pago_emp += comision_servicio
                y -= 12

                if y < 60:
                    p.showPage()
                    y = 750
                    p.setFont("Helvetica", 8)

        # Totales por empleado
        y -= 5
        p.line(340, y+10, 562, y+10)
        p.setFont("Helvetica-Bold", 9)
        p.drawString(240, y, "TOTALES:")
        p.drawString(350, y, f"${subtotal_bruto_emp:,.0f}")
        p.drawString(400, y, f"${subtotal_pago_emp:,.0f}")
        p.drawString(470, y, f"${(subtotal_bruto_emp - subtotal_pago_emp):,.0f}")
        
        total_bruto_general += subtotal_bruto_emp
        total_pagos_empleados += subtotal_pago_emp
        y -= 35

    # --- RESUMEN FINAL ---
    if y < 160:
        p.showPage()
        y = 750

    y -= 10
    p.setStrokeColorRGB(0.5, 0.5, 0.5)
    p.roundRect(50, y-70, 512, 85, 10, fill=0)
    
    y -= 15
    p.setFont("Helvetica-Bold", 12)
    p.drawString(70, y, f"PRODUCCIÓN TOTAL BRUTA GENERAL:   ${total_bruto_general:,.0f}")
    y -= 20
    p.setFillColorRGB(0.7, 0, 0)
    p.drawString(70, y, f"TOTAL EGRESOS (PAGOS EMPLEADOS):  -${total_pagos_empleados:,.0f}")
    y -= 25
    p.setFillColorRGB(0, 0.4, 0.2)
    p.setFont("Helvetica-Bold", 15)
    p.drawString(70, y, f"UTILIDAD NETA TOTAL LOCAL:        ${(total_bruto_general - total_pagos_empleados):,.0f}")

    # --- PIE DE PÁGINA (BRANDING) ---
    p.setStrokeColorRGB(0.8, 0.8, 0.8)
    p.line(50, 50, 562, 50) # Línea decorativa final
    p.setFont("Helvetica-Oblique", 9)
    p.setFillColorRGB(0.4, 0.4, 0.4)
    p.drawCentredString(width/2, 35, "Impreso por AgendApp - Reserva fácil e inteligente")

    p.showPage()
    p.save()
    buffer.seek(0)
    
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=Reporte_Cierre_General.pdf'
    return response



# --- FUNCIÓN 1: GENERAR EL PDF BINARIO PARA EL DUEÑO ---
def generar_reporte_general_binario(lista_empleados, current_user):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = 750

    # --- ENCABEZADO PRINCIPAL ---
    p.setFont("Helvetica-Bold", 18)
    p.drawString(50, y, "REPORTE DETALLADO DE CIERRE DE CAJA")
    y -= 20
    p.setFont("Helvetica", 10)
    p.drawString(50, y, f"Fecha de Cierre: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    y -= 30

    total_bruto_general = 0
    total_pagos_empleados = 0

    for emp in lista_empleados:
        reservas = Reserva.query.filter_by(empl_id=emp.empl_id, res_estado='Realizada').all()
        if not reservas:
            continue

        if y < 150:
            p.showPage()
            y = 750

        # --- BLOQUE DE COLABORADOR ---
        p.setFillColorRGB(0.95, 0.95, 0.95)
        p.rect(50, y-15, 512, 20, fill=1)
        p.setFillColorRGB(0, 0, 0)
        p.setFont("Helvetica-Bold", 11)
        p.drawString(60, y-10, f"COLABORADOR: {emp.empl_nombre.upper()}")
        y -= 35

        # Encabezados de tabla
        p.setFont("Helvetica-Bold", 8)
        columnas = [
            (55, "FECHA/HORA"), (140, "SERVICIO"), (250, "BASE"), 
            (300, "DESC %"), (350, "FINAL"), (400, "COMISIÓN"), (470, "AL LOCAL")
        ]
        for pos, texto in columnas:
            p.drawString(pos, y, texto)
        
        y -= 5
        p.line(50, y, 562, y)
        y -= 12

        subtotal_bruto_emp = 0
        subtotal_pago_emp = 0
        porcentaje_comision = float(emp.empl_porcentaje or 40)

        p.setFont("Helvetica", 8)
        for res in reservas:
            ser = Servicio.query.filter_by(ser_nombre=res.res_tipo_servicio, emp_id=current_user.emp_id).first()
            if ser:
                precio_base = float(ser.ser_precio)
                porc_desc = float(res.res_descuento_valor or 0)
                precio_final = precio_base - (precio_base * (porc_desc / 100))
                comision_servicio = precio_final * (porcentaje_comision / 100)
                local_servicio = precio_final - comision_servicio

                p.drawString(55, y, f"{res.res_fecha.strftime('%d/%m')} {res.res_hora.strftime('%H:%M')}")
                p.drawString(140, y, res.res_tipo_servicio[:20])
                p.drawString(250, y, f"${precio_base:,.0f}")
                p.drawString(300, y, f"{int(porc_desc)}%")
                p.drawString(350, y, f"${precio_final:,.0f}")
                p.drawString(400, y, f"${comision_servicio:,.0f}")
                p.drawString(470, y, f"${local_servicio:,.0f}")

                subtotal_bruto_emp += precio_final
                subtotal_pago_emp += comision_servicio
                y -= 12

                if y < 60:
                    p.showPage()
                    y = 750
                    p.setFont("Helvetica", 8)

        # Totales por colaborador
        y -= 5
        p.line(340, y+10, 562, y+10)
        p.setFont("Helvetica-Bold", 9)
        p.drawString(240, y, "TOTALES:")
        p.drawString(350, y, f"${subtotal_bruto_emp:,.0f}")
        p.drawString(400, y, f"${subtotal_pago_emp:,.0f}")
        p.drawString(470, y, f"${(subtotal_bruto_emp - subtotal_pago_emp):,.0f}")
        
        total_bruto_general += subtotal_bruto_emp
        total_pagos_empleados += subtotal_pago_emp
        y -= 35

    # --- RESUMEN FINAL ---
    if y < 160: p.showPage(); y = 750
    y -= 10
    p.setStrokeColorRGB(0.5, 0.5, 0.5)
    p.roundRect(50, y-70, 512, 85, 10, fill=0)
    y -= 15
    p.setFont("Helvetica-Bold", 12)
    p.drawString(70, y, f"PRODUCCIÓN TOTAL BRUTA GENERAL:   ${total_bruto_general:,.0f}")
    y -= 20
    p.setFillColorRGB(0.7, 0, 0)
    p.drawString(70, y, f"TOTAL EGRESOS (PAGOS EMPLEADOS):  -${total_pagos_empleados:,.0f}")
    y -= 25
    p.setFillColorRGB(0, 0.4, 0.2)
    p.setFont("Helvetica-Bold", 15)
    p.drawString(70, y, f"UTILIDAD NETA TOTAL LOCAL:        ${(total_bruto_general - total_pagos_empleados):,.0f}")

    # Pie de página
    p.setStrokeColorRGB(0.8, 0.8, 0.8)
    p.line(50, 50, 562, 50)
    p.setFont("Helvetica-Oblique", 9)
    p.setFillColorRGB(0.4, 0.4, 0.4)
    p.drawCentredString(width/2, 35, "Impreso por AgendApp - Reserva fácil e inteligente")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# --- FUNCIÓN 2: ENVIAR CORREO AL DUEÑO ---
def enviar_correo_reporte_general(empresa, pdf_binario, nombre_archivo):
    if not empresa.emp_email or not empresa.emp_cuenta_smtp: return False
    try:
        msg = MIMEMultipart()
        msg['From'] = empresa.emp_cuenta_smtp
        msg['To'] = empresa.emp_email
        msg['Subject'] = f"CIERRE DE CAJA - {empresa.emp_razon_social}"
        msg.attach(MIMEText("Se adjunta el reporte detallado de utilidades del cierre actual.", 'plain'))
        part = MIMEApplication(pdf_binario, Name=nombre_archivo)
        part['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
        msg.attach(part)
        servidor = smtplib.SMTP(empresa.emp_servidor_smtp, int(empresa.emp_puerto_smtp))
        servidor.starttls()
        servidor.login(empresa.emp_cuenta_smtp, empresa.emp_clave_cuenta_smtp)
        servidor.send_message(msg)
        servidor.quit()
        return True
    except Exception as e:
        print(f"Error correo dueño: {e}"); return False

# --- FUNCIÓN 3: ENVIAR CORREO AL EMPLEADO ---
def enviar_correo_comision_empleado(empresa, empleado, pdf_binario, nombre_archivo):
    if not empleado.empl_correo or not empresa.emp_cuenta_smtp: return False
    try:
        msg = MIMEMultipart()
        msg['From'] = empresa.emp_cuenta_smtp
        msg['To'] = empleado.empl_correo
        msg['Subject'] = f"Tu Recibo de Pago - {empresa.emp_razon_social}"
        msg.attach(MIMEText(f"Hola {empleado.empl_nombre}, adjuntamos tu recibo de comisiones.", 'plain'))
        part = MIMEApplication(pdf_binario, Name=nombre_archivo)
        part['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
        msg.attach(part)
        servidor = smtplib.SMTP(empresa.emp_servidor_smtp, int(empresa.emp_puerto_smtp))
        servidor.starttls()
        servidor.login(empresa.emp_cuenta_smtp, empresa.emp_clave_cuenta_smtp)
        servidor.send_message(msg)
        servidor.quit()
        return True
    except Exception as e:
        print(f"Error correo empleado: {e}"); return False
    




@admin_bp.route('/reporte-comisiones')
@login_required
def reporte_comisiones():
    lista_empleados = Empleado.query.filter_by(emp_id=current_user.emp_id, empl_activo=1).all()
    reporte = []
    total_negocio_neto = 0
    fecha_actual = datetime.now()

    for emp in lista_empleados:
        porcentaje_comision = float(emp.empl_porcentaje if emp.empl_porcentaje else 40)
        reservas_por_pagar = Reserva.query.filter(
            Reserva.empl_id == emp.empl_id,
            Reserva.res_estado.ilike('Realizada') 
        ).all()

        total_generado_empleado = 0
        lista_detallada_servicios = []
        servicios_resumen_wpp = "" 
        
        for res in reservas_por_pagar:
            servicio = Servicio.query.filter(
                Servicio.ser_nombre.ilike(res.res_tipo_servicio),
                Servicio.emp_id == current_user.emp_id
            ).first()
            
            if servicio:
                # --- NUEVA LÓGICA DE DESCUENTO POR PORCENTAJE ---
                precio_base = float(servicio.ser_precio)
                porcentaje_desc = float(res.res_descuento_valor or 0)
                
                # Calculamos cuánto dinero representa ese porcentaje
                valor_descuento_dinero = precio_base * (porcentaje_desc / 100)
                # El precio final es el base menos el dinero calculado
                precio_final = precio_base - valor_descuento_dinero
                
                total_generado_empleado += precio_final
                servicios_resumen_wpp += f"• {res.res_tipo_servicio} (${precio_final:,.0f})\n"
                lista_detallada_servicios.append({
                    'fecha': res.res_fecha.strftime('%d/%m'),
                    'nombre': res.res_tipo_servicio,
                    'precio': precio_final
                })

        pago_profesional = total_generado_empleado * (porcentaje_comision / 100)
        ganancia_local = total_generado_empleado - pago_profesional
        total_negocio_neto += ganancia_local

        reporte.append({
            'id': emp.empl_id,
            'nombre': emp.empl_nombre,
            'telefono': emp.empl_telefono,
            'cargo': emp.empl_cargo,
            'porcentaje': porcentaje_comision,
            'cantidad_citas': len(reservas_por_pagar),
            'bruto': total_generado_empleado,
            'pago_empleado': pago_profesional,
            'servicios_detalle': lista_detallada_servicios,
            'servicios_wpp': servicios_resumen_wpp
        })

    return render_template('admin/comisiones.html', reporte=reporte, hoy=fecha_actual, total_negocio=total_negocio_neto)
    
    

def generar_pdf_binario(emp, reservas, current_user):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # --- CONFIGURACIÓN DE PÁGINA Y CABECERA ---
    y = 750
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, y, f"COMPROBANTE DE PAGO - {emp.empl_nombre.upper()}")
    
    y -= 20
    p.setFont("Helvetica", 10)
    p.setFillColorRGB(0.3, 0.3, 0.3)
    p.drawString(50, y, f"Colaborador: {emp.empl_nombre} | Cédula: {emp.empl_cedula}")
    y -= 15
    p.drawString(50, y, f"Fecha de reporte: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    y -= 20
    p.setStrokeColorRGB(0.8, 0.8, 0.8)
    p.line(50, y, 560, y)

    # --- CABECERA DE TABLA (Igual al reporte de descarga) ---
    y -= 25
    p.setFillColorRGB(0, 0, 0)
    p.setFont("Helvetica-Bold", 9)
    
    # Definición de columnas
    col_fecha = 50
    col_ser = 110
    col_valor = 280
    col_desc = 360
    col_v_desc = 430
    col_total = 500

    p.drawString(col_fecha, y, "FECHA")
    p.drawString(col_ser, y, "SERVICIO")
    p.drawString(col_valor, y, "VALOR")
    p.drawString(col_desc, y, "DESC %")
    p.drawString(col_v_desc, y, "V. DESC")
    p.drawString(col_total, y, "TOTAL")
    
    y -= 8
    p.line(50, y, 560, y)
    y -= 15

    # --- PROCESAMIENTO DE DATOS ---
    total_bruto = 0
    p.setFont("Courier", 9)
    
    for res in reservas:
        ser = Servicio.query.filter_by(
            ser_nombre=res.res_tipo_servicio, 
            emp_id=current_user.emp_id
        ).first()
        
        if ser:
            precio_base = float(ser.ser_precio)
            porcentaje_desc = float(res.res_descuento_valor or 0)
            valor_descuento_dinero = precio_base * (porcentaje_desc / 100)
            precio_final = precio_base - valor_descuento_dinero
            total_bruto += precio_final

            # Control de salto de página
            if y < 80:
                p.showPage()
                y = 750
                p.setFont("Courier", 9)

            # Dibujar Fila
            p.drawString(col_fecha, y, res.res_fecha.strftime('%d/%m'))
            p.drawString(col_ser, y, res.res_tipo_servicio[:22])
            p.drawString(col_valor, y, f"{precio_base:,.0f}")
            p.drawString(col_desc, y, f"{int(porcentaje_desc)}%")
            p.drawString(col_v_desc, y, f"{valor_descuento_dinero:,.0f}")
            p.drawString(col_total, y, f"{precio_final:,.0f}")
            
            y -= 15

    # --- TOTALES FINALES ---
    if y < 150:
        p.showPage()
        y = 750

    y -= 20
    p.setStrokeColorRGB(0.5, 0.5, 0.5)
    p.line(350, y+10, 560, y+10)
    
    porcentaje = float(emp.empl_porcentaje if emp.empl_porcentaje else 40)
    pago_empleado = total_bruto * (porcentaje / 100)

    p.setFont("Helvetica-Bold", 11)
    p.drawString(350, y, "SUBTOTAL:")
    p.drawRightString(555, y, f"${total_bruto:,.0f}")
    
    y -= 20
    p.setFont("Helvetica-Bold", 13)
    p.setFillColorRGB(0, 0.4, 0.2) 
    p.drawString(350, y, f"TOTAL PAGO ({int(porcentaje)}%):")
    p.drawRightString(555, y, f"${pago_empleado:,.0f}")

    # --- PIE DE PÁGINA ---
    p.setFont("Helvetica-Oblique", 8)
    p.setFillColorRGB(0.5, 0.5, 0.5)
    p.drawCentredString(width/2, 40, "AgendApp - Comprobante oficial de servicios")

    p.showPage()
    p.save()
    
    buffer.seek(0)
    return buffer




@admin_bp.route('/cerrar-caja-comisiones', methods=['POST'])
@login_required
def cerrar_caja_comisiones():
    empresa = Empresa.query.get(current_user.emp_id)
    empleados = Empleado.query.filter_by(emp_id=empresa.emp_id, empl_activo=1).all()
    ahora = datetime.now()
    fecha_hoy = ahora.strftime('%Y-%m-%d')
    dia_hora_archivo = ahora.strftime('%Y%m%d_%H%M%S') 
    
    ruta_recursos = str(empresa.emp_ruta_recursos) if empresa.emp_ruta_recursos else 'recursos'
    ruta_base_comisiones = os.path.join(ruta_recursos, 'comisiones', fecha_hoy)
    ruta_base_cierres = os.path.join(ruta_recursos, 'cierrecaja', fecha_hoy)

    try:
        servicios_liquidados = 0
        # Validar si hay algo que cerrar
        hay_datos = any(Reserva.query.filter_by(empl_id=e.empl_id, res_estado='Realizada').first() for e in empleados)
        
        if not hay_datos:
            flash('ℹ️ No hay servicios para liquidar.', 'info')
            return redirect(url_for('admin.reporte_comisiones'))

        # --- 1. GENERAR REPORTE DETALLADO DEL NEGOCIO ---
        buffer_general = generar_reporte_general_binario(empleados, current_user)
        
        # CIFRAR CON CLAVE "123"
        pdf_gen_cifrado = BytesIO()
        reader_gen = PdfReader(buffer_general)
        writer_gen = PdfWriter()
        for page in reader_gen.pages: writer_gen.add_page(page)
        writer_gen.encrypt("123")
        writer_gen.write(pdf_gen_cifrado)
        contenido_general = pdf_gen_cifrado.getvalue()

        # GUARDAR FÍSICAMENTE EN RECURSOS/cierrecaja
        os.makedirs(ruta_base_cierres, exist_ok=True)
        nombre_cierre = f"cierrecaja_{dia_hora_archivo}.pdf"
        with open(os.path.join(ruta_base_cierres, nombre_cierre), "wb") as f:
            f.write(contenido_general)

        # ENVIAR AL DUEÑO
        enviar_correo_reporte_general(empresa, contenido_general, nombre_cierre)

        # --- 2. PROCESAR CADA EMPLEADO ---
        for emp in empleados:
            reservas = Reserva.query.filter_by(empl_id=emp.empl_id, res_estado='Realizada').all()
            if not reservas: continue
            
            # PDF Individual
            buf_emp = generar_pdf_binario(emp, reservas, current_user)
            pdf_emp_cifrado = BytesIO()
            reader_e = PdfReader(buf_emp)
            writer_e = PdfWriter()
            for page in reader_e.pages: writer_e.add_page(page)
            writer_e.encrypt(str(emp.empl_cedula))
            writer_e.write(pdf_emp_cifrado)
            cont_emp = pdf_emp_cifrado.getvalue()
            
            # Guardar PDF Empleado
            ruta_emp_folder = os.path.join(ruta_base_comisiones, str(emp.empl_cedula))
            os.makedirs(ruta_emp_folder, exist_ok=True)
            n_archivo_emp = f"Recibo_{emp.empl_nombre.replace(' ', '_')}_{dia_hora_archivo}.pdf"
            with open(os.path.join(ruta_emp_folder, n_archivo_emp), "wb") as f:
                f.write(cont_emp)

            # Correo Empleado
            if emp.empl_correo:
                enviar_correo_comision_empleado(empresa, emp, cont_emp, n_archivo_emp)

            # Cambiar estados
            for res in reservas:
                res.res_estado = 'Completada'
                servicios_liquidados += 1

        db.session.commit()
        flash(f'✅ Cierre exitoso. Reporte detallado guardado y enviado. Clave: 123', 'success')

    except Exception as e:
        db.session.rollback()
        print(f"🔥 Error: {e}")
        flash(f'Error: {str(e)}', 'danger')

    return redirect(url_for('admin.reporte_comisiones'))


@admin_bp.route('/descargar-recibo/<int:emp_id>')
@login_required
def descargar_recibo(emp_id):
    emp = Empleado.query.get_or_404(emp_id)
    reservas = Reserva.query.filter(
            Reserva.empl_id == emp_id, 
            Reserva.res_estado == 'Realizada'
        ).all()
    
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = 750

    # --- ENCABEZADO ---
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, y, f"COMPROBANTE DE PAGO - {emp.empl_nombre.upper()}")
    y -= 20
    p.setFont("Helvetica", 10)
    p.setFillColorRGB(0.3, 0.3, 0.3)
    p.drawString(50, y, f"Colaborador: {emp.empl_nombre} | Cédula: {emp.empl_cedula}")
    y -= 15
    p.drawString(50, y, f"Fecha de reporte: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    y -= 20
    p.setStrokeColorRGB(0.8, 0.8, 0.8)
    p.line(50, y, 560, y)

    # --- CABECERA DE TABLA ---
    y -= 25
    p.setFillColorRGB(0, 0, 0)
    p.setFont("Helvetica-Bold", 9)
    # Definimos posiciones X para las columnas
    col_fecha = 50
    col_ser = 110
    col_valor = 280
    col_desc = 360
    col_v_desc = 430
    col_total = 500

    p.drawString(col_fecha, y, "FECHA")
    p.drawString(col_ser, y, "SERVICIO")
    p.drawString(col_valor, y, "VALOR")
    p.drawString(col_desc, y, "DESC %")
    p.drawString(col_v_desc, y, "V. DESC")
    p.drawString(col_total, y, "TOTAL")
    
    y -= 8
    p.line(50, y, 560, y)
    y -= 15

    # --- LISTADO DE SERVICIOS ---
    total_bruto = 0
    p.setFont("Courier", 9)
    
    for res in reservas:
        ser = Servicio.query.filter_by(ser_nombre=res.res_tipo_servicio, emp_id=current_user.emp_id).first()
        
        if ser:
            precio_base = float(ser.ser_precio)
            porcentaje_desc = float(res.res_descuento_valor or 0)
            valor_descuento_dinero = precio_base * (porcentaje_desc / 100)
            precio_final = precio_base - valor_descuento_dinero
            total_bruto += precio_final

            if y < 80:
                p.showPage()
                y = 750
                p.setFont("Courier", 9)

            # Escribir fila
            p.drawString(col_fecha, y, res.res_fecha.strftime('%d/%m'))
            p.drawString(col_ser, y, res.res_tipo_servicio[:22]) # Truncar nombre largo
            p.drawString(col_valor, y, f"{precio_base:,.0f}")
            p.drawString(col_desc, y, f"{int(porcentaje_desc)}%")
            p.drawString(col_v_desc, y, f"{valor_descuento_dinero:,.0f}")
            p.drawString(col_total, y, f"{precio_final:,.0f}")
            
            y -= 15

    # --- SECCIÓN DE TOTALES ---
    if y < 150:
        p.showPage()
        y = 750

    y -= 20
    p.setStrokeColorRGB(0.5, 0.5, 0.5)
    p.line(350, y+10, 560, y+10) # Línea decorativa para el total
    
    porcentaje = float(emp.empl_porcentaje if emp.empl_porcentaje else 40)
    pago_empleado = total_bruto * (porcentaje / 100)

    p.setFont("Helvetica-Bold", 11)
    p.setFillColorRGB(0, 0, 0)
    p.drawString(350, y, f"SUBTOTAL:")
    p.drawRightString(555, y, f"${total_bruto:,.0f}")
    
    y -= 20
    p.setFont("Helvetica-Bold", 13)
    p.setFillColorRGB(0, 0.4, 0.2) 
    p.drawString(350, y, f"TOTAL PAGO ({int(porcentaje)}%):")
    p.drawRightString(555, y, f"${pago_empleado:,.0f}")

    # --- PIE DE PÁGINA ---
    p.setFont("Helvetica-Oblique", 8)
    p.setFillColorRGB(0.5, 0.5, 0.5)
    p.drawCentredString(width/2, 40, "AgendApp - Comprobante oficial de servicios")

    p.showPage()
    p.save()
    
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=Recibo_{emp.empl_nombre}.pdf'
    
    return response




## ---11. HISTORIAL DE RESERVAS Y REPORTES

@admin_bp.route('/historial')
@login_required
def gestion_historial():
    try:
        from sqlalchemy import text
        import json
        from flask import request

        # 1. Obtener el parámetro de búsqueda
        busqueda = request.args.get('busqueda', '').strip()
        
        # 2. Consulta Base
        query_base = """
            SELECT 
                r.res_id as id,
                c.cli_nombre as cliente,
                s.ser_nombre as servicio_nombre,
                r.res_tipo_servicio as servicio_manual,
                e.empl_nombre as empleado,
                r.res_fecha as fecha,
                r.res_hora as hora,
                r.res_estado as estado
            FROM RESERVAS r
            LEFT JOIN CLIENTES c ON r.cli_id = c.cli_id
            LEFT JOIN SERVICIOS s ON r.ser_id = s.ser_id
            LEFT JOIN EMPLEADOS e ON r.empl_id = e.empl_id
            WHERE 1=1
        """
        
        params = {}
        if busqueda:
            query_base += " AND (c.cli_nombre LIKE :val OR s.ser_nombre LIKE :val OR r.res_tipo_servicio LIKE :val)"
            params['val'] = f"%{busqueda}%"

        query_base += " ORDER BY r.res_fecha DESC, r.res_hora DESC LIMIT 100"
        
        # 3. Ejecutar
        resultado_db = db.session.execute(text(query_base), params)
        
        resultados = []
        for fila in resultado_db:
            servicio_final = fila.servicio_manual if fila.servicio_manual else (fila.servicio_nombre or "Servicio General")
            
            # --- LÓGICA DE HORA 12H ---
            hora_12 = ""
            if fila.hora:
                # Forzamos la conversión a formato 12 horas con AM/PM
                # %I = Hora 01-12 | %M = Minutos | %p = AM/PM
                try:
                    # Si es un objeto de hora, lo formateamos directamente
                    hora_12 = fila.hora.strftime('%I:%M %p')
                except AttributeError:
                    # Si llega como un string "14:30:00", lo convertimos primero
                    from datetime import datetime
                    t = datetime.strptime(str(fila.hora), '%H:%M:%S')
                    hora_12 = t.strftime('%I:%M %p')

            resultados.append({
                'id': fila.id,
                'cliente': fila.cliente or "Sin Nombre",
                'servicio': servicio_final,
                'empleado': fila.empleado or "No asignado",
                # FECHA PARA FILTRAR (Formato: 2026-01-24)
                'fecha_iso': fila.fecha.strftime('%Y-%m-%d') if fila.fecha else "", 
                # FECHA PARA MOSTRAR EN TABLA (Formato: 24/01/2026)
                'fecha_display': fila.fecha.strftime('%d/%m/%Y') if fila.fecha else "",
                'hora': hora_12,
                'estado': fila.estado
            })
            
            
        reservas_json = json.dumps(resultados, ensure_ascii=False)
        return render_template('admin/historial.html', reservas_json=reservas_json, busqueda_actual=busqueda)

    except Exception as e:
        print(f"Error en historial: {str(e)}")
        # Importante: devolver algo para que no explote la página
        return render_template('admin/historial.html', reservas_json="[]", busqueda_actual="")
    
    

#---12. CÓDIGOS QR
    
# Suponiendo que arriba dice 'from extensiones import db' o similar
@admin_bp.route('/mi-qr')
@login_required
def mi_qr():
    from sqlalchemy import text
    from app import db 
    
    try:
        # 1. Asegúrate de usar el nombre exacto de la tabla: EMPRESAS
        sql = text("SELECT * FROM EMPRESAS WHERE emp_id = :id")
        resultado = db.session.execute(sql, {'id': current_user.emp_id}).fetchone()
        
        # 2. IMPORTANTE: SQLAlchemy fetchone() devuelve una fila que se accede por nombre
        # Si 'resultado' es None, 'empresa' será None
        empresa = resultado
        
    except Exception as e:
        print(f"Error al obtener empresa: {e}")
        empresa = None

    # 3. CORRECCIÓN: Aquí decía 'empres', debe ser 'empresa'
    return render_template('admin/miqr.html', empresa=empresa)


# ---13  configuracion panel de control

@admin_bp.route('/configuracion')
@login_required
def panel_configuracion():
    # Solo permitimos entrar si tiene permiso de ver configuración
    if not current_user.tiene_permiso('ver_configuracion'):
        abort(403)
    return render_template('admin/panel_configuracion.html')




#-----14  Gestion de plantillas de correo

@admin_bp.route('/obtener_plantilla/<int:id>')
@login_required
def obtener_plantilla(id):
    try:
        # Buscamos la plantilla por ID
        plantilla = PlantillaWhatsApp.query.get_or_404(id)
        
        # Retornamos los datos en formato JSON
        # Asegúrate de que los nombres coincidan con los que usa tu JS
        return jsonify({
            "id": plantilla.plan_id,
            "nombre": plantilla.plan_nombre,
            "mensaje": plantilla.plan_mensaje,
            "tipo": plantilla.plan_tipo,
            "activo": plantilla.plan_activo
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500



@admin_bp.route('/gestion-plantillas')
@login_required
def gestion_plantillas():
    # Consultamos todas las plantillas guardadas en la base de datos
    plantillas = PlantillaWhatsApp.query.order_by(PlantillaWhatsApp.plan_fecha_creacion.desc()).all()
    # Las pasamos al HTML
    return render_template('admin/gestion_plantillas.html', plantillas=plantillas)


@admin_bp.route('/guardar_plantilla', methods=['POST'])
@login_required
def guardar_plantilla():
    data = request.get_json()
    plan_id = data.get('id')
    
    try:
        if plan_id and plan_id != "":
            # EDITAR: Buscamos la existente
            plantilla = PlantillaWhatsApp.query.get(plan_id)
            if not plantilla:
                return jsonify({"status": "error", "message": "Plantilla no encontrada"}), 404
            
            plantilla.plan_nombre = data['nombre']
            plantilla.plan_mensaje = data['mensaje']
            plantilla.plan_tipo = data['tipo']
            mensaje_exito = "Plantilla actualizada correctamente"
        else:
            # CREAR: Nueva instancia
            nueva = PlantillaWhatsApp(
                plan_nombre=data['nombre'],
                plan_mensaje=data['mensaje'],
                plan_tipo=data['tipo']
            )
            db.session.add(nueva)
            mensaje_exito = "Plantilla creada con éxito"
            
        db.session.commit()
        return jsonify({"status": "success", "message": mensaje_exito})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500



#-----15  funciones promoccionales y de fidelización


@admin_bp.route('/fidelizacion-promociones')
def fidelizacion_promociones():
    aviso = AvisoPromocional.query.first()
    empresa = Empresa.query.first() # Para obtener la ruta base en el HTML si es necesario
    
    if not aviso:
        aviso = AvisoPromocional(
            titulo="¡Nueva Promoción!",
            mensaje="Bienvenidos a nuestra plataforma.",
            activo=False,
            texto_boton="¡Entendido!"
        )
        db.session.add(aviso)
        db.session.commit()
        
    return render_template('admin/fidelizacion.html', aviso=aviso, empresa=empresa)




@admin_bp.route('/ver-recurso-promo/<filename>')
def servir_promo(filename):
    empresa = Empresa.query.first()
    # C:\Apps\cocoanails
    ruta_base = empresa.emp_ruta_recursos.strip()
    
    # Unimos: C:\Apps\cocoanails + promociones
    directorio_final = os.path.join(ruta_base, 'promociones')
    directorio_final = os.path.normpath(directorio_final)

    # filename aquí será '2222222222.jpg'
    return send_from_directory(directorio_final, filename)



@admin_bp.route('/guardar-aviso', methods=['POST'])
def guardar_aviso():
    try:
        aviso = AvisoPromocional.query.first()
        # Obtenemos los datos de la empresa (asumiendo que hay una sola o usas la del usuario)
        empresa = Empresa.query.first() 
        
        if not empresa:
            flash('No se encontró la configuración de la empresa.', 'error')
            return redirect(url_for('admin.fidelizacion_promociones'))

        # 1. Actualizamos datos de texto
        aviso.titulo = request.form.get('titulo')
        aviso.mensaje = request.form.get('mensaje')
        aviso.texto_boton = request.form.get('texto_boton', '¡Entendido!')
        aviso.enlace_boton = request.form.get('enlace_boton')
        aviso.activo = True if request.form.get('activo') else False
        aviso.solo_una_vez = True if request.form.get('solo_una_vez') else False
        
        # 2. Manejo de la imagen
        file = request.files.get('imagen')
        if file and file.filename != '':
            # Validar que sea JPG
            if not file.filename.lower().endswith('.jpg'):
                flash('Solo se permiten imágenes en formato .jpg', 'error')
                return redirect(url_for('admin.fidelizacion_promociones'))

            # Definir la ruta: ruta_recursos/promociones/
            # Nota: empresa.emp_ruta_recursos debería ser algo como 'static/recursos'
            ruta_base = empresa.emp_ruta_recursos.replace('\\', '/').strip('/')
            carpeta_promo = os.path.abspath(os.path.join(current_app.root_path, ruta_base, 'promociones'))
            
            # Crear la carpeta 'promociones' si no existe
            if not os.path.exists(carpeta_promo):
                os.makedirs(carpeta_promo, exist_ok=True)

            nombre_archivo = f"{empresa.emp_nit}.jpg"
            ruta_final = os.path.join(carpeta_promo, nombre_archivo)

            file.save(ruta_final)
            # Guardamos solo el nombre para que sea más fácil de manejar
            aviso.imagen_url = nombre_archivo

        db.session.commit()
        flash('¡Campaña de fidelización actualizada con éxito!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al procesar: {str(e)}', 'error')
    
    return redirect(url_for('admin.fidelizacion_promociones'))


@admin_bp.route('/api/aviso-activo')
def aviso_activo():
    aviso = AvisoPromocional.query.first()
    if aviso and aviso.activo:
        # Extraemos solo el nombre del archivo (ej: de 'promociones/2222222222.jpg' a '2222222222.jpg')
        nombre_limpio = aviso.imagen_url.split('/')[-1] if aviso.imagen_url else None
        
        return {
            "id": aviso.id,
            "titulo": aviso.titulo,
            "mensaje": aviso.mensaje,
            "imagen_url": nombre_limpio, # <--- ENVIAMOS SOLO EL NOMBRE
            "activo": aviso.activo,
            "solo_una_vez": aviso.solo_una_vez,
            "texto_boton": aviso.texto_boton,
            "enlace_boton": aviso.enlace_boton
        }
    return {"activo": False}


#-----16  reseñas y testimonios

@admin_bp.route('/foto_perfil/<emp_id>/<cedula>')
def obtener_foto_empleado(emp_id, cedula):
    empresa = Empresa.query.get_or_404(emp_id)
    # os.path.join detecta automáticamente si usar / o \
    ruta_carpeta = os.path.join(empresa.emp_ruta_recursos, 'empleados', str(cedula))
    return send_from_directory(ruta_carpeta, f"{cedula}.jpg")



@admin_bp.route('/valorar/<emp_id>', methods=['GET', 'POST'])
def dejar_resena(emp_id):
    empresa = Empresa.query.filter_by(emp_id=emp_id).first_or_404()
    ruta_limpia = empresa.emp_ruta_recursos.replace('\\', '/') if empresa.emp_ruta_recursos else ''

    if request.method == 'POST':
        # --- LÍNEA DE PRUEBA: Mira tu terminal cuando des click ---
        print(f"DEBUG: Recibido POST para empresa {emp_id}")
        print(f"DEBUG: Datos del Formulario: {request.form}")

        try:
            puntuacion = request.form.get('puntuacion')
            
            # Si no hay puntuación, redirigimos con aviso
            if not puntuacion:
                print("DEBUG: Error - No se recibió puntuación")
                flash('Por favor, selecciona una puntuación antes de enviar.', 'warning')
                return redirect(url_for('admin.dejar_resena', emp_id=emp_id))

            empl_id_raw = request.form.get('empl_id')
            # Validamos que el ID sea numérico para evitar errores de base de datos
            empl_id_final = int(empl_id_raw) if empl_id_raw and str(empl_id_raw).isdigit() else None

            nueva_resena = Resena(
                emp_id=emp_id,
                empl_id=empl_id_final,
                res_cliente_nombre=request.form.get('nombre', 'Anónimo').strip() or 'Anónimo',
                res_puntuacion=int(puntuacion),
                res_comentario=request.form.get('comentario', '').strip(),
                res_fecha=datetime.now(),
                res_visible=1
            )
            
            db.session.add(nueva_resena)
            db.session.commit()
            print("DEBUG: Reseña guardada exitosamente")
            
            # Asegúrate de que el archivo 'admin/gracias.html' exista
            return render_template('admin/gracias.html', empresa=empresa)

        except Exception as e:
            db.session.rollback()
            print(f"DEBUG: ERROR CRÍTICO: {e}")
            flash('Error interno al guardar. Inténtalo de nuevo.', 'danger')
            return redirect(url_for('admin.dejar_resena', emp_id=emp_id))

    # GET: Cargar empleados
    empleados = Empleado.query.filter_by(
        emp_id=emp_id, 
        empl_activo=1, 
        empl_mostrar_en_reserva=1
    ).all()

    return render_template('admin/resena_form.html', 
                           empresa=empresa, 
                           empleados=empleados, 
                           ruta_recursos=ruta_limpia)

@admin_bp.route('/panel-resenas')
@login_required
def ver_resenas():
    # Usamos join para traer los nombres de los empleados en una sola consulta (más rápido)
    resenas = Resena.query.filter_by(emp_id=current_user.emp_id)\
                          .order_by(Resena.res_fecha.desc()).all()
    return render_template('admin/resenas_listado.html', resenas=resenas)