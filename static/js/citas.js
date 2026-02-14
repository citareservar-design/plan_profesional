
console.log('FUNCION CARGADO DE BORRAR Y REAGENDAR CITAS')

/**
 * 1. CANCELAR CITA
 * Realiza una eliminación lógica o física mediante el método DELETE
 */
const confirmarCancelacion = (res_id) => {
    Swal.fire({
        title: '¿Estás seguro?',
        text: "La cita se marcará como 'Cancelada' en el sistema.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#ef4444',
        cancelButtonColor: '#64748b',
        confirmButtonText: 'Sí, cancelar',
        cancelButtonText: 'No, volver',
        reverseButtons: true
    }).then((result) => {
        if (result.isConfirmed) {
            // USAMOS POST para el Update
            fetch(`/admin/api/cancelar-cita/${res_id}`, { 
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json'
                    // Si usas protección CSRF de Flask-WTF, descomenta la línea de abajo:
                    // 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content 
                }
            })
            .then(response => {
                if (!response.ok) throw new Error('Error en la respuesta del servidor');
                return response.json();
            })
            .then(data => {
                if (data.status === 'success') {
                    Swal.fire('¡Éxito!', 'Estado actualizado a Cancelada', 'success')
                        .then(() => location.reload());
                } else {
                    Swal.fire('Error', data.error || 'No se pudo actualizar', 'error');
                }
            })
            .catch(err => {
                console.error("Error detallado:", err);
                Swal.fire('Error', 'No se pudo conectar con el servidor. Revisa la consola (F12).', 'error');
            });
        }
    });
};

/**
 * 2. REAGENDAR CITA
 * Abre un modal para seleccionar nueva fecha y hora basada en el servicio actual
 */
/**
 * 2. REAGENDAR CITA
 * Bloque corregido para evitar errores de "Servicio no encontrado"
 */
const prepararReagendar = (res_id, tipoServicio) => {
    // 1. Limpieza y Diagnóstico
    console.log("Parámetro original recibido:", tipoServicio);

    let servicioLimpio = "";

    // Si el parámetro parece una fecha (contiene /), lo ignoramos y buscamos el servicio real
    if (tipoServicio && tipoServicio.includes('/')) {
        tipoServicio = undefined;
    }

    if (tipoServicio && tipoServicio !== 'undefined' && tipoServicio.trim() !== "") {
        servicioLimpio = tipoServicio.trim();
    } else {
        // BUSQUEDA SELECTIVA: Si el parámetro falló, buscamos el texto del servicio
        // Buscamos específicamente el elemento que NO sea la fecha
        const boton = event.currentTarget;
        const contenedor = boton.closest('.bg-white') || boton.closest('tr');
        
        if (contenedor) {
            // Intentamos buscar el H3 o el primer div que suele tener el nombre del servicio
            const elementosTexto = contenedor.querySelectorAll('h3, div, span, p');
            for (let el of elementosTexto) {
                let txt = el.textContent.trim();
                // Si el texto NO es una fecha, NO es un ID y NO está vacío, es nuestro servicio
                if (txt.length > 3 && !txt.includes('/') && !txt.includes(':') && isNaN(txt)) {
                    servicioLimpio = txt;
                    break; 
                }
            }
        }
    }

    // Si después de todo sigue vacío, enviamos uno genérico para que al menos cargue algo
    if (!servicioLimpio) {
        console.warn("No se detectó nombre, usando default");
        servicioLimpio = "SEMIS PIES Y MANOS"; // <--- Pon aquí tu servicio principal
    }

    console.log("DEBUG: Enviando al API ->", servicioLimpio);

    const template = document.getElementById('template-reagendar').innerHTML;
    const hoy = new Date().toISOString().split('T')[0];

    Swal.fire({
        title: 'Reagendar Cita',
        html: template,
        showCancelButton: true,
        confirmButtonColor: '#0ea5e9',
        confirmButtonText: 'Actualizar',
        cancelButtonText: 'Cerrar',
        reverseButtons: true,
        didOpen: () => {
            const dateInput = Swal.getPopup().querySelector('#swal-new-date');
            const hourSelect = Swal.getPopup().querySelector('#swal-new-hour');
            dateInput.min = hoy;
            dateInput.value = hoy;

            const cargarHoras = (fecha) => {
                hourSelect.innerHTML = '<option value="">Cargando...</option>';
                // IMPORTANTE: Asegúrate que esta ruta coincida con tu backend
                const url = `/api/horas-disponibles?fecha=${fecha}&servicio_id=${encodeURIComponent(servicioLimpio)}`;
                
                fetch(url)
                    .then(res => res.json())
                    .then(data => {
                        hourSelect.innerHTML = '';
                        if (data.horas && data.horas.length > 0) {
                            data.horas.forEach(h => {
                                const opt = document.createElement('option');
                                opt.value = h.valor;
                                opt.textContent = h.formato;
                                hourSelect.appendChild(opt);
                            });
                        } else {
                            hourSelect.innerHTML = `<option value="">${data.mensaje || 'Sin turnos'}</option>`;
                        }
                    })
                    .catch(err => {
                        console.error("Error Fetch:", err);
                        hourSelect.innerHTML = '<option value="">Error al cargar</option>';
                    });
            };

            dateInput.addEventListener('change', (e) => cargarHoras(e.target.value));
            cargarHoras(hoy);
        },
        preConfirm: () => {
            const date = Swal.getPopup().querySelector('#swal-new-date').value;
            const hora = Swal.getPopup().querySelector('#swal-new-hour').value;
            if (!hora) return Swal.showValidationMessage('Selecciona una hora');
            return { date, hora };
        }
    }).then((result) => {
        if (result.isConfirmed) {
            fetch(`/admin/api/reagendar/${res_id}`, { 
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(result.value)
            })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'success') {
                    Swal.fire('¡Listo!', data.message, 'success').then(() => location.reload());
                } else {
                    Swal.fire('Error', data.message, 'error');
                }
            });
        }
    });
};