console.log('CARGANDO JS RESERVAS')



function abrirReagendar(id, fecha, hora, nombre) {
    const modal = document.getElementById('modal-reagendar');
    document.getElementById('reagendar-cliente').innerText = "Cliente: " + nombre;
    document.getElementById('input_fecha').value = fecha;
    document.getElementById('input_hora').value = hora;
    document.getElementById('form-reagendar').action = `/admin/reservas/reagendar/${id}`;
    modal.classList.remove('hidden');
    modal.classList.add('flex');
}
function cerrarReagendar() {
    document.getElementById('modal-reagendar').classList.add('hidden');
    document.getElementById('modal-reagendar').classList.remove('flex');
}



/**
 * Cambia el estado en la base de datos (SIN enviar WhatsApp automáticamente)
 */
async function confirmarAccionMasiva(nuevoEstado, ids) {
    // 1. FILTRADO: Solo permitimos procesar citas que NO estén realizadas o completadas
    const idsValidos = ids.filter(id => {
        const tarjeta = document.querySelector(`[data-id="${id}"]`);
        const estado = tarjeta ? tarjeta.getAttribute('data-estado').toLowerCase() : '';
        return estado !== 'completada' && estado !== 'realizada';
    });

    // 2. VALIDACIÓN: Si después de filtrar no queda ninguna o si no seleccionó nada
    if (idsValidos.length === 0) {
        Swal.fire({
            title: ids.length > 0 ? 'Acción no permitida' : '¡Ups!',
            text: ids.length > 0 
                ? 'Las reservas ya finalizadas o pagadas no se pueden modificar masivamente.' 
                : 'Primero selecciona las tarjetas que deseas modificar.',
            icon: 'info',
            background: '#0f172a',
            color: '#fff',
            confirmButtonColor: '#3b82f6'
        });
        return;
    }

    // Configuración de colores y textos según el estado
    const config = {
        'Realizada': { titulo: '¿Finalizar servicios?', color: '#10b981', btn: 'SÍ, FINALIZAR' },
        'confirmada': { titulo: '¿Confirmar citas?', color: '#f59e0b', btn: 'SÍ, CONFIRMAR' },
        'Cancelada':  { titulo: '¿Anular reservas?', color: '#ef4444', btn: 'SÍ, CANCELAR' },
        'Pendiente':  { titulo: '¿Revertir a pendiente?', color: '#0ea5e9', btn: 'SÍ, REVERTIR' }
    };

    const sel = config[nuevoEstado] || { titulo: '¿Cambiar estado?', color: '#3b82f6', btn: 'SÍ, CAMBIAR' };

    if (navigator.vibrate) navigator.vibrate(50);

    // 3. CONFIRMACIÓN: Mostramos la cantidad de IDs VÁLIDOS (idsValidos.length)
    const resultConfirm = await Swal.fire({
        title: sel.titulo,
        html: `Vas a marcar <b>${idsValidos.length}</b> reserva(s) como <span style="color:${sel.color}">${nuevoEstado}</span>.`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: sel.color,
        cancelButtonColor: '#334155',
        confirmButtonText: sel.btn,
        cancelButtonText: 'VOLVER',
        background: '#0f172a',
        color: '#fff',
        backdrop: `rgba(15, 23, 42, 0.8)`
    });

    if (resultConfirm.isConfirmed) {
        Swal.showLoading();
        
        try {
            // 4. ENVÍO: Mandamos los idsValidos al servidor
            const response = await fetch('/admin/acciones-masivas-reservas', { 
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    ids: idsValidos, 
                    accion: nuevoEstado.toLowerCase() 
                }) 
            });
            
            const data = await response.json();

            if (data.success) {
                await Swal.fire({
                    title: '¡Actualizado!',
                    text: data.message,
                    icon: 'success',
                    timer: 1500,
                    showConfirmButton: false,
                    background: '#0f172a',
                    color: '#fff'
                });
                
                window.location.reload();
            } else {
                Swal.fire('Error', data.message, 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            Swal.fire('Error', 'No se pudo conectar con el servidor', 'error');
        }
    }
}

/**
 * Función de envío de WhatsApp con FORMATO 12 HORAS y DIRECCIÓN
 */
async function enviarMensajeConfirmacion(ids) {
    if (!ids || ids.length === 0) {
        Swal.fire({ title: 'Atención', text: 'No hay tarjetas seleccionadas', icon: 'warning', background: '#0f172a', color: '#fff' });
        return;
    }

    const colaDeEnvio = [...ids];

    for (let i = 0; i < colaDeEnvio.length; i++) {
        const id = colaDeEnvio[i];
        const tarjeta = document.querySelector(`[data-id="${id}"]`);
        
        if (tarjeta) {
            const telefono = tarjeta.getAttribute('data-tel');
            const nombre = tarjeta.getAttribute('data-nombre');
            const empresa = tarjeta.getAttribute('data-empresa');
            const direccion = tarjeta.getAttribute('data-direccion') || "";
            const fechaAttr = tarjeta.getAttribute('data-fecha');
            
            // --- CONVERSIÓN A FORMATO 12 HORAS ---
            const horaRaw = tarjeta.getAttribute('data-hora') || "00:00";
            let [hh, mm] = horaRaw.split(':');
            hh = parseInt(hh);
            const ampm = hh >= 12 ? 'PM' : 'AM';
            hh = hh % 12 || 12; // Convierte 0 a 12 (medianoche) y 13 a 1
            const hora12 = `${hh}:${mm} ${ampm}`;

            let fraseFecha = calcularFraseFecha(fechaAttr); 

            // --- MENSAJE ---
            let texto = `*¡Hola, ${nombre}!* 👋\n\nTe escribimos de *${empresa}*\n\nTe recordamos tu cita de *${fraseFecha}* a las *${hora12}*.\n`;
            if (direccion) texto += `📍 *Ubicación:* ${direccion}\n`;
            texto += `\n*📌 ACCIÓN REQUERIDA:* Por favor responde con la palabra *CONFIRMAR* o *CANCELAR*.\n\n⚠️ Si no respondes en las próximas horas, el turno se cancelará.`;

            const url = `https://api.whatsapp.com/send?phone=${telefono}&text=${encodeURIComponent(texto)}`;
            window.open(url, '_blank');

            if (colaDeEnvio.length > 1 && i < colaDeEnvio.length - 1) {
                const result = await Swal.fire({
                    title: `Enviado a ${nombre}`,
                    text: `¿Deseas enviar el siguiente mensaje? (${i + 2} de ${colaDeEnvio.length})`,
                    icon: 'info',
                    showCancelButton: true,
                    confirmButtonText: 'SÍ, SIGUIENTE',
                    cancelButtonText: 'DETENER',
                    background: '#0f172a',
                    color: '#fff',
                    confirmButtonColor: '#10b981'
                });

                if (!result.isConfirmed) break;
            }
        }
    }
}

function calcularFraseFecha(fechaStr) {
    if(!fechaStr) return "tu cita";
    const hoy = new Date().toLocaleDateString('en-CA');
    const mañana = new Date();
    mañana.setDate(mañana.getDate() + 1);
    const mañanaStr = mañana.toLocaleDateString('en-CA');

    if (fechaStr === hoy) return "hoy";
    if (fechaStr === mañanaStr) return "mañana";
    
    const opciones = { weekday: 'long', day: 'numeric', month: 'long' };
    return "el " + new Date(fechaStr + "T12:00:00").toLocaleDateString('es-ES', opciones);
}


// Función para mostrar/ocultar el cargando
const toggleLoading = (show) => {
    const overlay = document.getElementById('loading-overlay');
    if (show) overlay.classList.remove('hidden');
    else overlay.classList.add('hidden');
};




// Usar window. asegura que Alpine pueda ver la función desde el HTML
window.initSortableCol = function(el) {
    if (!el) return;

    new Sortable(el, {
        group: 'reservas',
        draggable: '.tarjeta-reserva',
        filter: 'select, button, input, .no-drag',
        preventOnFilter: false, 
        animation: 150,
        ghostClass: 'opacity-50',
        forceFallback: true, 
        
    onStart: function(evt) {
            const estado = evt.item.getAttribute('data-estado');
            if (estado === 'Completada') {
                evt.preventDefault(); // Detiene el arrastre de inmediato
                return false;
            }
        },

        onEnd: async function (evt) {
            console.log("✅ TARJETA SOLTADA");
            document.body.classList.remove('dragging');
            
            const tarjeta = evt.item;
            const estado = tarjeta.getAttribute('data-estado');

            if (estado === 'Completada') {
                Swal.fire('Cita Finalizada', 'Esta reserva ya está completada y no puede moverse.', 'info');
                window.location.reload();
                return;
            }

            const empresa = tarjeta.getAttribute('data-empresa') || "Nuestro Establecimiento";
            const direccion = tarjeta.getAttribute('data-direccion') || "nuestra ubicación";
            const res_id = tarjeta.getAttribute('data-id');
            const nuevaFecha = evt.to.getAttribute('data-fecha');
            
            const nombre = tarjeta.getAttribute('data-nombre');
            const telefono = tarjeta.getAttribute('data-tel');
            const horaRaw = tarjeta.getAttribute('data-hora') || "00:00";

            // --- CONVERSIÓN A FORMATO 12 HORAS (19:00 -> 7:00 PM) ---
            const [h, m] = horaRaw.split(':');
            const horaAmigable = new Date(0, 0, 0, h, m).toLocaleTimeString('en-US', { 
                hour: 'numeric', 
                minute: '2-digit', 
                hour12: true 
            });

            const selectEmp = tarjeta.querySelector('select[name="empleado_id"]');
            const emplId = selectEmp ? selectEmp.value : tarjeta.getAttribute('data-empl-id');

            if (!res_id || !nuevaFecha || nuevaFecha === 'futuro') {
                if(nuevaFecha === 'futuro') {
                    Swal.fire({ title: 'Nota', text: 'Para fechas lejanas usa el botón editar', icon: 'info' });
                }
                window.location.reload();
                return;
            }

            if (typeof toggleLoading === 'function') toggleLoading(true);

            try {
                const response = await fetch('/admin/mover_reserva', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id: res_id, fecha: nuevaFecha, empl_id: emplId })
                });
                
                const data = await response.json();

                if (data.status === 'success') {
                    if (navigator.vibrate) navigator.vibrate(50);
                    if (typeof toggleLoading === 'function') toggleLoading(false);

                    await Swal.fire({
                        title: '¡Cita Movida!',
                        html: `¿Quieres avisar a <b>${nombre}</b> del cambio?`,
                        icon: 'success',
                        showCancelButton: true,
                        confirmButtonColor: '#25D366',
                        confirmButtonText: 'SÍ, ENVIAR WHATSAPP',
                        cancelButtonText: 'NO, SOLO CERRAR',
                        background: '#0f172a',
                        color: '#fff'
                    }).then((result) => {
                        if (result.isConfirmed) {
                            let fraseFecha = calcularFraseFecha(nuevaFecha);
                            
                            // MENSAJE CON FORMATO 12H Y DATOS DINÁMICOS
                            const msg = `*¡Hola, ${nombre}!* 👋\n\nTe informamos que tu cita en *${empresa}* ha sido modificada para *${fraseFecha}* a las *${horaAmigable}*.\n\n📍 *Dirección:* ${direccion}\n\n⚠️ *Nota:* Por favor presentarse *15 minutos antes* de su cita. Si no puede asistir, infórmenos por aquí.`;
                            
                            window.open(`https://api.whatsapp.com/send?phone=${telefono}&text=${encodeURIComponent(msg)}`, '_blank');
                        }
                    });

                    window.location.reload();
                } else {
                    throw new Error(data.message);
                }
            } catch (error) {
                if (typeof toggleLoading === 'function') toggleLoading(false);
                Swal.fire('Error', error.message, 'error').then(() => window.location.reload());
            }
        }
    });
};



window.reagendarHora = async function(reservaId, nuevaHora, nuevaFecha) {
    if (typeof toggleLoading === 'function') toggleLoading(true);

    try {
        const response = await fetch(`/admin/api/reagendar/${reservaId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                date: nuevaFecha, // La fecha seleccionada en el input
                hora: nuevaHora   // La hora seleccionada en la lista
            })
        });

        const data = await response.json();

        if (data.status === 'success') {
            window.location.reload();
        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        if (typeof toggleLoading === 'function') toggleLoading(false);
        alert("Error: " + error.message);
    }
};



// mensaje por wpp al modificar hora

window.reagendarHora = function(reservaId, nuevaHora, nuevaFecha) {
    if (typeof toggleLoading === 'function') toggleLoading(true);

    fetch('/admin/reagendar_hora', { 
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            id: reservaId,
            hora: nuevaHora,
            fecha: nuevaFecha
        })
    })
    .then(response => {
        if (!response.ok) throw new Error('Ruta no encontrada o error de servidor');
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            if (typeof toggleLoading === 'function') toggleLoading(false);

            // 1. Buscamos la tarjeta para sacar los datos dinámicos
            const tarjeta = document.querySelector(`[data-id="${reservaId}"]`);
            const telefono = tarjeta.getAttribute('data-tel');
            const nombre = tarjeta.getAttribute('data-nombre');
            const empresa = tarjeta.getAttribute('data-empresa') || "Nuestro Negocio";
            const direccion = tarjeta.getAttribute('data-direccion') || "";
            
            // 2. Formateamos la hora para que el cliente la entienda (AM/PM)
            const [h, m] = nuevaHora.split(':');
            const horaAmigable = new Date(0,0,0, h, m).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit', hour12: true });

            // 3. Usamos tu función para poner la fecha bonita (hoy, mañana, etc.)
            const fraseFecha = typeof calcularFraseFecha === 'function' ? calcularFraseFecha(nuevaFecha) : nuevaFecha;

            Swal.fire({
                title: '¡Cita Reagendada!',
                text: "¿Deseas notificar al cliente por WhatsApp?",
                icon: 'success',
                showCancelButton: true,
                confirmButtonColor: '#25D366',
                confirmButtonText: '<i class="fa-brands fa-whatsapp"></i> Enviar WhatsApp',
                cancelButtonText: 'No, solo cerrar',
                background: '#1e293b',
                color: '#fff'
            }).then((result) => {
                if (result.isConfirmed) {
                    // MENSAJE CON TODOS LOS CAMPOS DINÁMICOS
                    const msg = `*¡Hola, ${nombre}!* 👋\n\nTe informamos que tu cita en *${empresa}* ha sido modificada para *${fraseFecha}* a las *${horaAmigable}*.\n\n📍 *Dirección:* ${direccion}\n\n⚠️ *Nota:* Por favor presentarse *15 minutos antes* de su cita. Si no puede asistir, infórmenos por aquí.`;
                    
                    window.open(`https://api.whatsapp.com/send?phone=${telefono}&text=${encodeURIComponent(msg)}`, '_blank');
                }
                window.location.reload();
            });
        }
    })
    .catch(error => {
        if (typeof toggleLoading === 'function') toggleLoading(false);
        console.error('Error Detallado:', error);
        Swal.fire('Error', 'No se pudo actualizar la reserva.', 'error');
    });
};