from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from datetime import datetime, timedelta, time
from models.models import  Empresa,  Servicio, DiasBloqueados,ConfigHorario, Reserva, Empleado,db
from services.appointment_service import  obtener_horas_disponibles, enviar_correo_confirmacion
import pytz


appointment_bp = Blueprint('appointment', __name__)

# --- 1. RUTA PÚBLICA PRINCIPAL (Formulario para Móvil) ---
@appointment_bp.route('/')
def index(): 
    """ Formulario público que ve el cliente al entrar a la IP """
    from sqlalchemy import text # Asegúrate de tener esta importación
    ahora = datetime.now()
    hoy_str = ahora.strftime("%Y-%m-%d")
    fecha_solicitada = request.args.get('date', hoy_str)
    
    emp_id = '01' 
    
    # --- 1. CARGAR DATOS DE LA DB ---
    empresa_data = Empresa.query.filter_by(emp_id=emp_id).first()
    lista_servicios = Servicio.query.all() 
    lista_empleados = Empleado.query.filter_by(emp_id=emp_id, empl_activo=True).all()
    
    # --- 2. MAPA DE HABILIDADES (CONSULTA ROBUSTA) ---
    mapa_habilidades = {}
    for servicio in lista_servicios:
        # Consultamos directamente la tabla intermedia para evitar fallos de relación
        sql = text("SELECT empl_id FROM EMPLEADO_SERVICIOS WHERE ser_id = :sid")
        resultado = db.session.execute(sql, {'sid': servicio.ser_id}).fetchall()
        
        # Guardamos los IDs de los empleados que pueden hacer este servicio
        ids_autorizados = [fila[0] for fila in resultado]
        mapa_habilidades[servicio.ser_nombre] = ids_autorizados

    import json
    # ESTE PRINT ES CLAVE: Debe mostrar IDs dentro de los corchetes
    print(f"--- DEBUG SISTEMA INTELIGENTE ---")
    print(f"Mapa generado: {mapa_habilidades}")
    
    # --- 3. CONFIGURACIÓN DE VISIBILIDAD ---
    empleado_referencia = Empleado.query.filter_by(emp_id=emp_id).first()
    mostrar_staff = empleado_referencia.empl_mostrar_en_reserva if empleado_referencia else False
    
    # Evitar fechas pasadas
    if fecha_solicitada < hoy_str:
        return redirect(url_for('appointment.index', date=hoy_str))

    hora_actual_str = ahora.strftime("%H:%M")

    # Obtener disponibilidad de horas (usa el nombre del servicio enviado por URL si existe)
    todas_las_horas_libres = obtener_horas_disponibles(fecha_solicitada)

    if fecha_solicitada == hoy_str:
        horas_filtradas = [h for h in todas_las_horas_libres if h['valor'] > hora_actual_str]
    else:
        horas_filtradas = todas_las_horas_libres

    form_data = {
        'nombre': request.args.get('nombre', ''),
        'email': request.args.get('email', ''),
        'telefono': request.args.get('telefono', '')
    }

    return render_template(
        'form.html',
        hoy=hoy_str,
        horas_libres=horas_filtradas,
        fecha_seleccionada=fecha_solicitada,
        mostrar_staff=mostrar_staff,
        empleados=lista_empleados,
        form_data=form_data,
        empresa=empresa_data,
        mapa_habilidades=json.dumps(mapa_habilidades), # Enviamos el mapa al JS
        servicios=lista_servicios
    )

# --- 2. RUTAS DE NAVEGACIÓN DEL CLIENTE ---

@appointment_bp.route('/inicio')
def inicio():
    """ 
    Página de bienvenida y formulario de reservas (PÚBLICA).
    """
    empresa_data = Empresa.query.filter_by(emp_id='01').first()
    lista_servicios = Servicio.query.all() # También los cargamos aquí si usas esta ruta
    return render_template('form.html', empresa=empresa_data, servicios=lista_servicios)

# --- 1. FUNCIÓN PARA PROCESAR (La que recibe los datos del Loader) ---
@appointment_bp.route('/reservar', methods=['POST'])
def reservar():
    
    
    empleado_id = request.form.get('empleado_id', 0)

    if empleado_id == "0":
        # Lógica de asignación automática (el que esté libre)
        pass
    else:
    # Lógica de asignación fija al empleado_id seleccionado
        pass
    try:
        # 1. EXTRACCIÓN DE DATOS
        if request.is_json:
            datos = request.get_json()
        else:
            datos = request.form.to_dict()
        
        fecha_valor = datos.get('date') or datos.get('fecha_reserva')
        hora_valor = datos.get('hora')
        servicio_nombre = datos.get('tipo_una')
        emp_id_actual = datos.get('emp_id', '01') # Ajusta según cómo manejes el ID de empresa

        # 2. IMPORTACIONES NECESARIAS
        from models.models import Servicio, Empleado, EmpleadoServicios, Reserva, db
        from services.appointment_service import crear_cita
        from datetime import datetime, timedelta

        # 3. IDENTIFICAR EL SERVICIO Y SU DURACIÓN
        servicio_obj = Servicio.query.filter(
        Servicio.ser_nombre.ilike(servicio_nombre.strip()),
        Servicio.ser_estado == 1  # <--- AGREGAMOS ESTA CONDICIÓN
         ).first()
        
        
        if not servicio_obj:
            return jsonify({"status": "error", "message": "Servicio no encontrado"}), 400

        duracion_nueva = int(servicio_obj.ser_tiempo)

        # 4. BUSCAR EMPLEADOS APTOS PARA ESTE SERVICIO
        empleados_aptos = Empleado.query.join(EmpleadoServicios).filter(
            EmpleadoServicios.ser_id == servicio_obj.ser_id
        ).all()

        if not empleados_aptos:
            return jsonify({"status": "error", "message": "No hay personal para este servicio"}), 400

        # 5. LÓGICA DE ASIGNACIÓN: BUSCAR QUIÉN ESTÁ LIBRE
        empleado_elegido_id = None
        
        # Convertir hora de reserva a objeto datetime para cálculos
        hora_res_dt = datetime.strptime(hora_valor, '%H:%M:%S' if len(hora_valor) > 5 else '%H:%M')
        inicio_nuevo = datetime.combine(datetime.strptime(fecha_valor, '%Y-%m-%d').date(), hora_res_dt.time())
        fin_nuevo = inicio_nuevo + timedelta(minutes=duracion_nueva)

        for emp in empleados_aptos:
            # Revisar si este empleado específico tiene choques de horario
            reservas_emp = Reserva.query.filter_by(
                res_fecha=fecha_valor, 
                empl_id=emp.empl_id
            ).filter(Reserva.res_estado != 'Cancelada').all()

            esta_libre = True
            for r in reservas_emp:
                inicio_existente = datetime.combine(r.res_fecha, r.res_hora)
                # Necesitamos la duración del servicio de la reserva existente
                serv_existente = Servicio.query.filter_by(ser_nombre=r.res_tipo_servicio).first()
                dur_existente = int(serv_existente.ser_tiempo) if serv_existente else 30
                fin_existente = inicio_existente + timedelta(minutes=dur_existente)

                # Validar solapamiento de horarios
                if inicio_nuevo < fin_existente and fin_nuevo > inicio_existente:
                    esta_libre = False
                    break 
            
            if esta_libre:
                empleado_elegido_id = emp.empl_id
                print(f"DEBUG: Empleado asignado -> {emp.empl_nombre} (ID: {emp.empl_id})")
                break

        # 6. VALIDACIÓN FINAL DE DISPONIBILIDAD
        if not empleado_elegido_id:
            return jsonify({"status": "error", "message": "Todos los especialistas están ocupados en este horario"}), 400

        # 7. ASIGNAR EL EMPLEADO LIBRE A LOS DATOS Y CREAR CITA
        datos['empl_id'] = empleado_elegido_id
        resultado = crear_cita(datos, request.host_url)

        if resultado.get('status') == 'success':
            # --- ENVÍO DE CORREO REPARADO ---
            try:
                # 1. Importamos desde el archivo correcto (appointment_service)
                from services.appointment_service import enviar_correo_confirmacion
                from models.models import Empresa

                # 2. Obtenemos el objeto empresa para el SMTP
                empresa_obj = Empresa.query.filter_by(emp_id='01').first()
                
                # 3. Llamamos a la función con los 5 parámetros que pide tu def
                enviar_correo_confirmacion(
                    email_cliente=datos.get('email'),
                    nombre_cliente=datos.get('nombre'),
                    fecha=fecha_valor,
                    hora=hora_valor,
                    empresa=empresa_obj
                )
                
               
                            
                
            except Exception as e:
                # Si el correo falla, imprimimos el error pero la reserva sigue exitosa en web
                print(f"⚠️ Alerta: Reserva OK, pero error en correo: {e}")

            return jsonify({"status": "success", "message": "Reserva confirmada"}), 200
        
        return jsonify({"status": "error", "message": "Error al guardar"}), 400

    except Exception as e:
        import traceback
        print(f"Error: {e}")
        print(traceback.format_exc())
        return jsonify({"status": "error", "message": "Error interno"}), 500
    
    
    
    
    


# --- 2. FUNCIÓN PARA MOSTRAR LA PÁGINA (La que soluciona el 404) ---
@appointment_bp.route('/reserva_exitosa') # Esta es la que busca el navegador después
def vista_exito():
    from models.models import Empresa
    empresa_info = Empresa.query.filter_by(emp_id='01').first()
    # Esta función SÍ devuelve el HTML
    return render_template('reserva_exitosa.html', empresa=empresa_info)

# --- 3. API DE DISPONIBILIDAD ---

@appointment_bp.route('/api/horas-disponibles')
def api_horas_disponibles():
    try:
        fecha_str = request.args.get('fecha')
        servicio_id_o_nombre = request.args.get('servicio_id')

        if not fecha_str or not servicio_id_o_nombre:
            return jsonify({"bloqueado": False, "horas": [], "mensaje": "Fecha o servicio no seleccionado"})

        # --- 1. CONFIGURACIÓN DE TIEMPO ---
        zona_horaria = pytz.timezone('America/Bogota')
        ahora_colombia = datetime.now(zona_horaria)
        hoy_colombia = ahora_colombia.date()
        minutos_ahora = (ahora_colombia.hour * 60) + ahora_colombia.minute

        fecha_dt = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        
        
        # --- NUEVA VALIDACIÓN: DÍAS BLOQUEADOS ---
        from models.models import DiasBloqueados
        dia_bloqueado = DiasBloqueados.query.filter_by(fecha=fecha_dt).first()
        
        if dia_bloqueado:
            # Si el día existe en la tabla, bloqueamos todo
            return jsonify({
                "bloqueado": True, 
                "mensaje": f"Este día no habrá servicio: {dia_bloqueado.motivo or 'Día no laboral'}", 
                "horas": []
            })
        
        # --- 2. VALIDAR HORARIO LABORAL ---
        config = ConfigHorario.query.filter_by(dia_semana=fecha_dt.weekday()).first()
        if not config or not config.activo:
            return jsonify({"bloqueado": True, "mensaje": "Local cerrado", "horas": []})

        # --- 3. IDENTIFICAR SERVICIO Y EMPLEADOS APTOS ---
        # Buscamos el servicio por nombre o ID
        servicio = Servicio.query.filter(Servicio.ser_nombre.ilike(servicio_id_o_nombre.strip())).first()
        if not servicio:
            # Imprime esto en tu consola para ver qué está llegando realmente
            print(f"ERROR: No se encontró el servicio '{servicio_id_o_nombre}'")
            return jsonify({"bloqueado": False, "horas": [], "mensaje": f"Servicio '{servicio_id_o_nombre}' no encontrado"})
        
        duracion = int(servicio.ser_tiempo)
        
        # OBTENER EMPLEADOS QUE HACEN ESTE SERVICIO (Usando tu tabla EMPLEADO_SERVICIOS)
        # Importamos los modelos dentro para evitar recursividad si es necesario
        from models.models import Empleado, EmpleadoServicios
        empleados_aptos = Empleado.query.join(EmpleadoServicios).filter(
            EmpleadoServicios.ser_id == servicio.ser_id,
            Empleado.empl_activo == 1
        ).all()
        
        # DEBUG CRÍTICO: Mira esto en tu terminal negra de VSCode
        print(f"--- DEBUG SISTEMA INTELIGENTE ---")
        print(f"Servicio: {servicio.ser_nombre} (ID: {servicio.ser_id}, Tiempo: {servicio.ser_tiempo}min)")
        print(f"Empleados Aptos encontrados: {len(empleados_aptos)}")
        for e in empleados_aptos:
            print(f" - Empleado: {e.empl_nombre} (ID: {e.empl_id})")
        
        if not empleados_aptos:
            return jsonify({"bloqueado": False, "horas": [], "mensaje": "No hay personal disponible para este servicio"})

        # --- 4. RESERVAS DEL DÍA ---
        reservas = Reserva.query.filter(
            Reserva.res_fecha == fecha_dt,
            Reserva.res_estado != 'Cancelada' # <-- Esto hace que para el sistema la cita NO exista
            ).all()
        
        # --- 5. RANGO DEL DÍA ---
        inicio_dt = datetime.combine(fecha_dt, config.hora_inicio)
        fin_dt = datetime.combine(fecha_dt, config.hora_fin)

        # --- 6. GENERAR HORAS DISPONIBLES ---
        horas = []
        actual = inicio_dt
        intervalo_paso = 30 

        while actual + timedelta(minutes=duracion) <= fin_dt:
            # A. VALIDACIÓN DE ALMUERZO
            if config.almuerzo_inicio and config.almuerzo_fin:
                almuerzo_ini = datetime.combine(fecha_dt, config.almuerzo_inicio)
                almuerzo_fin = datetime.combine(fecha_dt, config.almuerzo_fin)
                if actual >= almuerzo_ini and actual < almuerzo_fin:
                    actual = almuerzo_fin
                    continue
                if actual < almuerzo_ini and (actual + timedelta(minutes=duracion)) > almuerzo_ini:
                    actual = almuerzo_fin
                    continue

            # B. FILTRO TIEMPO REAL
            if fecha_dt == hoy_colombia:
                minutos_itera = (actual.hour * 60) + actual.minute
                if minutos_itera <= (minutos_ahora + 5): # Margen de 20 min
                    actual += timedelta(minutes=intervalo_paso)
                    continue

            # C. VALIDAR DISPONIBILIDAD POR EMPLEADO (Lógica Multi-Especialista)
            fin_actual = actual + timedelta(minutes=duracion)
            empleados_libres_en_este_bloque = 0
            
            # Pre-cargamos la duración de los servicios de las reservas para no consultar la DB mil veces
            for emp in empleados_aptos:
                esta_ocupado = False
                
                # Revisamos si ESTE empleado tiene algún choque de horario
                for r in reservas:
                    if r.empl_id == emp.empl_id and r.res_estado != 'Cancelado':
                        inicio_res = datetime.combine(fecha_dt, r.res_hora)
                        
                        # Buscamos cuánto dura el servicio de esta reserva existente
                        # Si no se encuentra, asumimos 60 min por defecto
                        serv_res = Servicio.query.filter_by(ser_nombre=r.res_tipo_servicio).first()
                        dur_res = int(serv_res.ser_tiempo) if serv_res else 60
                        fin_res = inicio_res + timedelta(minutes=dur_res)
                        
                        # Lógica de choque: (A inicia antes de que B termine) Y (B inicia antes de que A termine)
                        if actual < fin_res and fin_actual > inicio_res:
                            esta_ocupado = True
                            break # Este empleado está ocupado, saltamos al siguiente
                
                if not esta_ocupado:
                    empleados_libres_en_este_bloque += 1
            
            # --- LA CLAVE ---
            # Si al menos uno de los 3 especialistas está libre, la hora aparece en el móvil
            if empleados_libres_en_este_bloque > 0:
                horas.append({
                    "valor": actual.strftime("%H:%M:%S"),
                    "formato": actual.strftime("%I:%M %p").lower(),
                    "cupos_libres": empleados_libres_en_este_bloque 
                })

            actual += timedelta(minutes=intervalo_paso)

        return jsonify({
            "bloqueado": False,
            "horas": horas,
            "mensaje": "Selecciona una hora" if horas else "❌ No hay especialistas libres"
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({"bloqueado": False, "horas": [], "error": str(e)}), 500