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
            
            # --- NUEVA SECCIÓN: VALIDACIÓN DE CLIENTE ACTIVO ---
        from models.models import Cliente, db # Asegúrate de importar Cliente
        
        email_cliente = datos.get('email')
        telefono_cliente = datos.get('telefono')
        
        # Buscamos si existe un cliente con ese email o teléfono
        cliente_check = Cliente.query.filter(
            (Cliente.cli_email == email_cliente) | (Cliente.cli_telefono == telefono_cliente)
        ).first()

        # Si el cliente existe y está inactivo (0), bloqueamos la reserva de inmediato
        if cliente_check and cliente_check.cli_activo == 0:
            return jsonify({
                "status": "error", 
                "message": f"Lo sentimos {cliente_check.cli_nombre}, tu cuenta está inactiva. Por favor contacta con administración."
            }), 403
        
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
            mensaje_descuento = ""
            try:
                print(f"DEBUG: Procesando descuentos para resultado exitoso...")
                
                if cliente_check:
                    # Verificamos si tiene saldo de citas con descuento
                    if cliente_check.cli_descuento_cantidad > 0:
                        # Buscamos la reserva que se acaba de crear
                        reserva_reciente = Reserva.query.filter_by(cli_id=cliente_check.cli_id).order_by(Reserva.res_id.desc()).first()
                        
                        # Capturamos el porcentaje antes de resetearlo
                        porcentaje = int(cliente_check.cli_descuento)
                        
                        if reserva_reciente:
                            reserva_reciente.res_descuento_valor = porcentaje
                        
                        # Restamos saldo y limpiamos si llega a 0
                        cliente_check.cli_descuento_cantidad -= 1
                        if cliente_check.cli_descuento_cantidad <= 0:
                            cliente_check.cli_descuento = 0
                        
                        db.session.commit()
                        
                        # Preparamos el mensaje para el Sweet Alert
                        mensaje_descuento = f"¡Felicidades! Se ha aplicado un {porcentaje}% de descuento a tu cita."
                        
                        print(f"✅ DB Actualizada: {cliente_check.cli_nombre} ahora tiene saldo {cliente_check.cli_descuento_cantidad}")
                    else:
                        print(f"ℹ️ El cliente {cliente_check.cli_nombre} existe pero tiene saldo 0 de descuentos.")
                else:
                    print("⚠️ No se pudo aplicar descuento: cliente_check es None.")

            except Exception as e:
                db.session.rollback()
                import traceback
                print(f"❌ Error CRÍTICO al actualizar descuento: {e}")
                print(traceback.format_exc())

            # 3. ENVÍO DE CORREO (Ahora sí se ejecutará)
            try:
                from services.appointment_service import enviar_correo_confirmacion
                from models.models import Empresa
                empresa_obj = Empresa.query.filter_by(emp_id='01').first()
                enviar_correo_confirmacion(
                    email_cliente=datos.get('email'),
                    nombre_cliente=datos.get('nombre'),
                    fecha=fecha_valor,
                    hora=hora_valor,
                    empresa=empresa_obj
                )
                print("📧 Correo de confirmación enviado.")
            except Exception as e:
                print(f"⚠️ Error correo: {e}")

            # 4. RESPUESTA FINAL AL CLIENTE (JS / SweetAlert)
            print(f"📤 Enviando respuesta al JS. Info descuento: '{mensaje_descuento}'")
            return jsonify({
                "status": "success", 
                "message": "Reserva confirmada con éxito",
                "info_descuento": mensaje_descuento
            }), 200

        # Si el resultado del servicio no fue exitoso
        return jsonify({"status": "error", "message": "Error al guardar la cita"}), 400

    except Exception as e:
        import traceback
        print(f"❌ Error general en la ruta reservar: {e}")
        print(traceback.format_exc())
        return jsonify({"status": "error", "message": "Error interno del servidor"}), 500
    
    
    


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
        # CAPTURAMOS EL EMPLEADO SELECCIONADO
        empleado_seleccionado_id = request.args.get('empleado_id') 

        if not fecha_str or not servicio_id_o_nombre:
            return jsonify({"bloqueado": False, "horas": [], "mensaje": "Fecha o servicio no seleccionado"})

        zona_horaria = pytz.timezone('America/Bogota')
        ahora_colombia = datetime.now(zona_horaria)
        hoy_colombia = ahora_colombia.date()
        minutos_ahora = (ahora_colombia.hour * 60) + ahora_colombia.minute
        fecha_dt = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        
        # --- VALIDACIÓN: DÍAS BLOQUEADOS ---
        from models.models import DiasBloqueados
        dia_bloqueado = DiasBloqueados.query.filter_by(fecha=fecha_dt).first()
        if dia_bloqueado:
            return jsonify({"bloqueado": True, "mensaje": f"Bloqueado: {dia_bloqueado.motivo or 'Día no laboral'}", "horas": []})
        
        # --- VALIDAR HORARIO LABORAL ---
        config = ConfigHorario.query.filter_by(dia_semana=fecha_dt.weekday()).first()
        if not config or not config.activo:
            return jsonify({"bloqueado": True, "mensaje": "Local cerrado", "horas": []})

        # --- IDENTIFICAR SERVICIO ---
        servicio = Servicio.query.filter(Servicio.ser_nombre.ilike(servicio_id_o_nombre.strip())).first()
        if not servicio:
            return jsonify({"bloqueado": False, "horas": [], "mensaje": "Servicio no encontrado"})
        
        duracion = int(servicio.ser_tiempo)
        
        # --- FILTRAR EMPLEADOS ---
        from models.models import Empleado, EmpleadoServicios
        query_emp = Empleado.query.join(EmpleadoServicios).filter(
            EmpleadoServicios.ser_id == servicio.ser_id,
            Empleado.empl_activo == 1
        )

        # SI EL USUARIO ELIGIÓ UNO EN EL GRID, FILTRAMOS SOLO ESE
        if empleado_seleccionado_id and empleado_seleccionado_id != "0":
            empleados_aptos = query_emp.filter(Empleado.empl_id == empleado_seleccionado_id).all()
        else:
            empleados_aptos = query_emp.all()
        
        if not empleados_aptos:
            return jsonify({"bloqueado": False, "horas": [], "mensaje": "No hay personal disponible"})

        # --- RESERVAS DEL DÍA (Solo las que ocupan tiempo) ---
        reservas = Reserva.query.filter(
            Reserva.res_fecha == fecha_dt,
            Reserva.res_estado.notin_(['Cancelada', 'Cancelado'])
        ).all()
        
        inicio_dt = datetime.combine(fecha_dt, config.hora_inicio)
        fin_dt = datetime.combine(fecha_dt, config.hora_fin)

        horas = []
        actual = inicio_dt
        intervalo_paso = 30 

        while actual + timedelta(minutes=duracion) <= fin_dt:
            # --- 1. CÁLCULO DE RANGO POTENCIAL ---
            fin_actual = actual + timedelta(minutes=duracion)
            esta_bloqueado_por_almuerzo = False

            # --- A. VALIDACIÓN DE ALMUERZO ---
            if config.almuerzo_inicio and config.almuerzo_fin:
                almuerzo_ini = datetime.combine(fecha_dt, config.almuerzo_inicio)
                almuerzo_fin = datetime.combine(fecha_dt, config.almuerzo_fin)
                
                # Si el servicio se cruza con el rango del almuerzo
                if fin_actual > almuerzo_ini and actual < almuerzo_fin:
                    esta_bloqueado_por_almuerzo = True

            if esta_bloqueado_por_almuerzo:
                # Si choca, saltamos al final del almuerzo para seguir buscando
                if actual < almuerzo_fin:
                    actual = almuerzo_fin
                else:
                    actual += timedelta(minutes=intervalo_paso)
                continue

            # --- B. FILTRO TIEMPO REAL (Para hoy) ---
            if fecha_dt == hoy_colombia:
                minutos_itera = (actual.hour * 60) + actual.minute
                if minutos_itera <= (minutos_ahora + 10):
                    actual += timedelta(minutes=intervalo_paso)
                    continue

            # --- C. VALIDAR DISPONIBILIDAD DE EMPLEADOS ---
            empleados_libres = 0
            for emp in empleados_aptos:
                esta_ocupado = False
                for r in reservas:
                    if r.empl_id == emp.empl_id:
                        # Asegurar que r.res_hora es un objeto time
                        res_hora_obj = r.res_hora
                        if isinstance(res_hora_obj, timedelta):
                            # Algunos conectores de DB devuelven timedelta para campos TIME
                            total_segundos = int(res_hora_obj.total_seconds())
                            res_hora_obj = time(total_segundos // 3600, (total_segundos % 3600) // 60)
                        
                        inicio_res = datetime.combine(fecha_dt, res_hora_obj)
                        
                        # Obtener duración del servicio de la reserva existente
                        serv_res = Servicio.query.filter_by(ser_nombre=r.res_tipo_servicio).first()
                        dur_res = int(serv_res.ser_tiempo) if serv_res else 60
                        fin_res = inicio_res + timedelta(minutes=dur_res)
                        
                        # Choque de rangos: si el nuevo servicio empieza antes de que termine el otro
                        # Y termina después de que empiece el otro.
                        if actual < fin_res and fin_actual > inicio_res:
                            esta_ocupado = True
                            break 
                
                if not esta_ocupado:
                    empleados_libres += 1
            
            if empleados_libres > 0:
                horas.append({
                    "valor": actual.strftime("%H:%M:%S"),
                    "formato": actual.strftime("%I:%M %p").lower(),
                    "cupos_libres": empleados_libres 
                })

            # Avance normal al siguiente slot
            actual += timedelta(minutes=intervalo_paso)

        return jsonify({
            "bloqueado": False,
            "horas": horas,
            "mensaje": "Selecciona una hora" if horas else "No hay turnos disponibles para este servicio/especialista"
        })

    except Exception as e:
        import traceback
        print(f"❌ Error en API Horas: {e}")
        traceback.print_exc()
        return jsonify({"bloqueado": False, "horas": [], "error": str(e)}), 500