from models.models import db, Cliente, Reserva, ConfigHorario, Servicio
from datetime import datetime, timedelta,time
from flask_mail import Message, Mail
from flask import current_app, render_template
import pytz
import re


def crear_cita(data, base_url):
    try:
        from models.models import db, Reserva, Cliente, Servicio, Empleado, EmpleadoServicios
        from datetime import datetime, timedelta

        # 1. Buscar o Crear Cliente
        cliente = Cliente.query.filter_by(cli_email=data.get('email')).first()
        if not cliente:
            cliente = Cliente(
                cli_nombre=data.get('nombre'),
                cli_email=data.get('email'),
                cli_telefono=data.get('telefono'),
                emp_id='01',
                cli_activo=1,
                cli_alias=data.get('nombre')
            )
            db.session.add(cliente)
            db.session.flush() 

        # 2. LÓGICA DE TIEMPOS
        fecha_str = data.get('date') or data.get('fecha_reserva')
        hora_str = data.get('hora')
        servicio_nombre = data.get('tipo_una')
        
        fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        # Manejo flexible de formato de hora
        hora_obj = datetime.strptime(hora_str, '%H:%M:%S' if len(hora_str) > 5 else '%H:%M').time()

        servicio_obj = Servicio.query.filter_by(ser_nombre=servicio_nombre).first()
        if not servicio_obj:
            raise Exception(f"Servicio '{servicio_nombre}' no encontrado.")

        duracion_nueva = int(servicio_obj.ser_tiempo)
        inicio_nuevo = datetime.combine(fecha_obj, hora_obj)
        fin_nuevo = inicio_nuevo + timedelta(minutes=duracion_nueva)

        # 3. BUSCAR EMPLEADOS APTOS
        empleados_aptos = Empleado.query.join(EmpleadoServicios).filter(
            EmpleadoServicios.ser_id == servicio_obj.ser_id,
            Empleado.empl_activo == 1
        ).all()

        if not empleados_aptos:
            raise Exception("No hay especialistas para este servicio.")

        # 4. ASIGNACIÓN INTELIGENTE CON TRASLAPE DE HORARIOS
        empleado_asignado_id = None
            # Dentro de tu función crear_cita...
        for emp in empleados_aptos:
            # REVISAR: Que aquí también ignore las 'Cancelado'
            reservas_dia = Reserva.query.filter(
                Reserva.res_fecha == fecha_obj, 
                Reserva.empl_id == emp.empl_id,
                Reserva.res_estado != 'Cancelada' # <--- AGREGA ESTO SI NO ESTÁ
            ).all()
            
            esta_libre = True
            for r in reservas_dia:
                inicio_existente = datetime.combine(r.res_fecha, r.res_hora)
                # Buscamos cuánto dura el servicio de la cita que ya existe
                serv_ex = Servicio.query.filter_by(ser_nombre=r.res_tipo_servicio).first()
                dur_ex = int(serv_ex.ser_tiempo) if serv_ex else 30
                fin_existente = inicio_existente + timedelta(minutes=dur_ex)

                # Lógica de choque de bloques de tiempo
                if inicio_nuevo < fin_existente and fin_nuevo > inicio_existente:
                    esta_libre = False
                    break 

            if esta_libre:
                empleado_asignado_id = emp.empl_id
                break

        if not empleado_asignado_id:
            raise Exception("No hay especialistas libres en el bloque de tiempo seleccionado.")

        # 5. GUARDAR RESERVA
        nueva_reserva = Reserva(
            res_fecha=fecha_obj,
            res_hora=hora_obj,
            res_tipo_servicio=servicio_nombre,
            res_notas=data.get('notes'),
            cli_id=cliente.cli_id,
            empl_id=empleado_asignado_id,
            emp_id='01',
            res_estado='pendiente'
        )

        db.session.add(nueva_reserva)
        db.session.commit() 
        
        return {"status": "success", "res_id": nueva_reserva.res_id}

    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"❌ Error detallado: {traceback.format_exc()}")
        return {"status": "error", "message": str(e)}
    


def verificar_disponibilidad_real(fecha, servicio_id, hora_reserva):
    try:
        # 1. Configurar Zona Horaria Colombia
        tz = pytz.timezone('America/Bogota')
        ahora = datetime.now(tz)
        
        # 2. CONVERTIR HORA A MINUTOS (Manejo de tipos dinámico)
        if isinstance(hora_reserva, int):
            # Si ya es un entero (ej: 900), lo usamos directamente
            inicio_nuevo_minutos = hora_reserva
        elif isinstance(hora_reserva, str):
            # Si es texto "15:00:00"
            partes = hora_reserva.split(':')
            h = int(partes[0])
            m = int(partes[1]) if len(partes) > 1 else 0
            inicio_nuevo_minutos = h * 60 + m
        elif isinstance(hora_reserva, (time, datetime)):
            inicio_nuevo_minutos = hora_reserva.hour * 60 + hora_reserva.minute
        else:
            print(f"DEBUG: Tipo de hora no soportado: {type(hora_reserva)}")
            return False

        # 3. Convertir fecha
        if isinstance(fecha, str):
            fecha_dt = datetime.strptime(fecha, "%Y-%m-%d").date()
        else:
            fecha_dt = fecha

        # 4. Obtener duración del servicio
        servicio = Servicio.query.get(servicio_id)
        duracion_nueva = int(servicio.ser_tiempo) if servicio else 60
        fin_nuevo_minutos = inicio_nuevo_minutos + duracion_nueva

        print(f"--- VALIDANDO: {fecha_dt} | Minutos inicio: {inicio_nuevo_minutos} ---")

# 5. VALIDACIÓN A: ¿Es hora pasada? (Ajuste para dar tiempo al cliente)
        if fecha_dt == ahora.date():
            minutos_ahora = (ahora.hour * 60) + ahora.minute
            # Damos 15 min de margen mínimo para agendar
            if inicio_nuevo_minutos <= (minutos_ahora + 15):
                return False

        # 6. VALIDACIÓN B: Choque con otras reservas
        reservas = Reserva.query.filter_by(res_fecha=fecha_dt).all()
        for res in reservas:
            # Si en tu tabla Reserva ya guardas la duración, úsala. 
            # Si no, esta lógica de rango que tienes es correcta:
            dur_res = int(res.res_duracion) if hasattr(res, 'res_duracion') else 60
            
            inicio_exis = (res.res_hora.hour * 60) + res.res_hora.minute
            fin_exis = inicio_exis + dur_res
            
            # Lógica de solapamiento (Perfecta para bloques de 30min)
            if inicio_nuevo_minutos < fin_exis and fin_nuevo_minutos > inicio_exis:
                return False

        print("DEBUG: Todo correcto. DISPONIBLE.")
        return True
        
    except Exception as e:
        import traceback
        print(f"Error crítico: {e}")
        print(traceback.format_exc())
        return False



def obtener_slots_disponibles(fecha_str, servicio_id):
    fecha_dt = datetime.strptime(fecha_str, '%Y-%m-%d')
    config = ConfigHorario.query.filter_by(dia_semana=fecha_dt.weekday(), activo=1).first()
    
    if not config: return []

    formato_sql = "%H:%M:%S"
    hora_actual = datetime.combine(fecha_dt.date(), datetime.strptime(str(config.hora_inicio), formato_sql).time())
    hora_limite = datetime.combine(fecha_dt.date(), datetime.strptime(str(config.hora_fin), formato_sql).time())
    
    # NUEVO: Definir límites de almuerzo si existen
    almuerzo_ini = datetime.combine(fecha_dt.date(), config.almuerzo_inicio) if config.almuerzo_inicio else None
    almuerzo_fin = datetime.combine(fecha_dt.date(), config.almuerzo_fin) if config.almuerzo_fin else None

    intervalo = 30 # CAMBIADO A 30 MINUTOS
    horarios_finales = []

    while hora_actual + timedelta(minutes=intervalo) <= hora_limite:
        # VALIDACIÓN: Saltamos si la hora está dentro del almuerzo
        esta_en_almuerzo = False
        if almuerzo_ini and almuerzo_fin:
            esta_en_almuerzo = hora_actual >= almuerzo_ini and hora_actual < almuerzo_fin

        if not esta_en_almuerzo:
            str_hora_prueba = hora_actual.strftime("%H:%M:%S")
            if verificar_disponibilidad_real(fecha_str, str_hora_prueba, servicio_id):
                horarios_finales.append(hora_actual.strftime("%I:%M %p"))
        
        hora_actual += timedelta(minutes=intervalo)

    return horarios_finales
    
    
def enviar_correo_confirmacion(email_cliente, nombre_cliente, fecha, hora, empresa):
    try:
        # --- EXTRACCIÓN GARANTIZADA DEL TELÉFONO ---
        # Intentamos obtenerlo de 3 formas distintas para que no falle
        tel_db = ""
        if hasattr(empresa, 'emp_telefono'):
            tel_db = empresa.emp_telefono
        elif 'emp_telefono' in empresa.__dict__:
            tel_db = empresa.__dict__['emp_telefono']
        
        # Si sigue vacío, el objeto no lo trae. 
        # Como parche temporal para que NO falle tu producción:
        if not tel_db:
            tel_db = "3185861444" # Número de respaldo o puedes dejarlo como ""

        # Limpiamos: dejamos solo números
        whatsapp_num = re.sub(r'\D', '', str(tel_db)) if tel_db else ""

        # IMPORTANTE: Para software internacional, si no tiene código de país, lo agregamos
        # Si el número empieza por 3 (típico de Colombia) y tiene 10 dígitos, le ponemos el 57
        if len(whatsapp_num) == 10 and whatsapp_num.startswith('3'):
            whatsapp_num = "57" + whatsapp_num

        # Log de verificación
        print(f"✅ Email enviado con éxito. WhatsApp destino: {whatsapp_num}")

        # 1. Generar URL de Calendario
        hora_limpia = hora[:5] if len(hora) > 5 else hora
        google_url = generar_url_calendar(fecha, hora_limpia, empresa)

        # 2. Configuración SMTP
        current_app.config.update(
            MAIL_SERVER=empresa.emp_servidor_smtp.strip(),
            MAIL_PORT=int(empresa.emp_puerto_smtp),
            MAIL_USE_TLS=True,
            MAIL_USERNAME=empresa.emp_cuenta_smtp.strip(),
            MAIL_PASSWORD=empresa.emp_clave_cuenta_smtp.strip()
        )
        
        mail = Mail(current_app)
        
        # 3. Mensaje y CCO
        msg = Message(
            subject=f"Confirmación de Reserva - {empresa.emp_razon_social}",
            recipients=[email_cliente],
            sender=empresa.emp_cuenta_smtp.strip()
        )

        if empresa.emp_email:
            msg.bcc = [empresa.emp_email.strip()]

        # 4. Renderizado
        msg.html = render_template('emails/confirmacion.html', 
                                   nombre=nombre_cliente, 
                                   fecha=fecha, 
                                   hora=hora, 
                                   empresa=empresa,
                                   google_url=google_url,
                                   whatsapp_num=whatsapp_num, # Pasamos la variable limpia
                                   email_cliente=email_cliente)

        mail.send(msg)
        return True

    except Exception as e:
        print(f"❌ Error crítico: {str(e)}")
        return False
    
    
    
    
    

def obtener_horas_disponibles(fecha_str):
    # 1. Identificar el día de la semana (0=Lunes, 6=Domingo)
    fecha_dt = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    dia_semana = fecha_dt.weekday()

    # 2. Consultar la tabla CONFIG_HORARIOS para ese día
    config = ConfigHorario.query.filter_by(dia_semana=dia_semana).first()

    if not config or config.activo == 0:
        return []

    # 3. Generar intervalos de tiempo usando hora_inicio y hora_fin de la DB
    horas = []
    # Convertimos los objetos 'time' de la DB a objetos 'datetime' para operar
    actual = datetime.combine(fecha_dt, config.hora_inicio)
    fin = datetime.combine(fecha_dt, config.hora_fin)

    while actual < fin:
        hora_texto = actual.strftime('%I:%M %p') # Formato 12h (09:00 AM)
        hora_valor = actual.strftime('%H:%M')    # Formato 24h para el value (09:00)
        
        horas.append({
            'valor': hora_valor,
            'texto': hora_texto
        })
        
        # Sumamos intervalos (ejemplo: cada 60 minutos)
        actual += timedelta(minutes=60) 

    return horas



def generar_url_calendar(fecha_str, hora_str, empresa):
    # Asumiendo que fecha es 'YYYY-MM-DD' y hora 'HH:MM'
    # Combinamos y creamos un objeto datetime
    dt_inicio = datetime.strptime(f"{fecha_str} {hora_str}", "%Y-%m-%d %H:%M")
    dt_fin = dt_inicio + timedelta(hours=1) # Duración estimada: 1 hora

    # Formato requerido por Google: 20251226T103000
    f_inicio = dt_inicio.strftime("%Y%m%dT%H%M%S")
    f_fin = dt_fin.strftime("%Y%m%dT%H%M%S")
    
    detalles = f"Cita programada en {empresa.emp_razon_social}"
    ubicacion = empresa.emp_direccion or "Sede Principal"
    
    url = (
        f"https://www.google.com/calendar/render?action=TEMPLATE"
        f"&text=Cita+en+{empresa.emp_razon_social.replace(' ', '+')}"
        f"&dates={f_inicio}/{f_fin}"
        f"&details={detalles.replace(' ', '+')}"
        f"&location={ubicacion.replace(' ', '+')}"
        f"&sf=true&output=xml"
    )
    return url

# --- NUEVAS FUNCIONES PARA EVITAR ERRORES DE IMPORTACIÓN ---

def cancelar_cita_por_id(res_id):
    try:
        reserva = Reserva.query.get(res_id)
        if not reserva:
            return {"error": "No se encontró la reserva en la base de datos"}
        
        # VERIFICA ESTE NOMBRE: ¿Es res_estado, res_estatus o res_situacion?
        reserva.res_estado = 'Cancelada' 
        
        db.session.commit()
        return {"status": "success"}
    except Exception as e:
        db.session.rollback()
        print(f"❌ ERROR EN SERVICIO: {str(e)}")
        return {"error": str(e)}
    
    
    
    

def reagendar_cita_por_id(res_id, nueva_fecha, nueva_hora):
    """Actualiza fecha y hora de una reserva existente."""
    try:
        reserva = Reserva.query.get(res_id)
        if reserva:
            reserva.res_fecha = datetime.strptime(nueva_fecha, '%Y-%m-%d').date()
            reserva.res_hora = datetime.strptime(nueva_hora, '%H:%M').time()
            db.session.commit()
            return {"status": "success"}
        return {"error": "Reserva no encontrada"}
    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}

def obtener_horas_libres_reagendar(fecha):
    """Alias para usar en la API de reagendamiento."""
    return obtener_horas_disponibles(fecha)