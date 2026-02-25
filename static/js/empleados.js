let editandoId = null;

// Evita que el usuario escriba más de los caracteres permitidos
function validarLongitud(input, max) {
    if (input.value.length > max) {
        input.value = input.value.slice(0, max);
    }
}

function abrirModalNuevo() {
    const modal = document.getElementById('modalEmpleado');
    modal.setAttribute('data-id', ''); 
    
    const titulo = document.getElementById('modalTitulo');
    if (titulo) titulo.innerHTML = 'Nuevo <span class="text-sky-500">Empleado</span>';

    const campos = ['empl_nombre', 'empl_cedula', 'empl_telefono', 'empl_cargo'];
    campos.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });

    if (document.getElementById('empl_porcentaje')) {
        document.getElementById('empl_porcentaje').value = '40';
    }

    document.querySelectorAll('input[name="servicios_empleado"]').forEach(cb => cb.checked = false);

    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

// CIRUGÍA: Añadimos 'correo' como último parámetro
function prepararEdicion(id, nombre, cedula, telefono, porcentaje, cargo, serviciosIds, correo) {
    const modal = document.getElementById('modalEmpleado');
    if (!modal) return;

    modal.setAttribute('data-id', id);
    document.getElementById('modalTitulo').innerHTML = 'Editar <span class="text-sky-500">Empleado</span>';
    
    // Ahora 'correo' sí existe porque viene en los parámetros
    if(document.getElementById('empl_correo')) {
        document.getElementById('empl_correo').value = correo || '';
    }
    
    if(document.getElementById('empl_nombre')) document.getElementById('empl_nombre').value = nombre;
    if(document.getElementById('empl_cedula')) document.getElementById('empl_cedula').value = String(cedula).replace(/'/g, "");
    if(document.getElementById('empl_telefono')) document.getElementById('empl_telefono').value = telefono;
    if(document.getElementById('empl_porcentaje')) document.getElementById('empl_porcentaje').value = porcentaje;
    if(document.getElementById('empl_cargo')) document.getElementById('empl_cargo').value = cargo;

    const checkboxes = document.querySelectorAll('input[name="servicios_empleado"]');
    let listaIds = Array.isArray(serviciosIds) ? serviciosIds : [];

    checkboxes.forEach(cb => {
        cb.checked = false;
        if (listaIds.some(sId => String(sId) === String(cb.value))) {
            cb.checked = true;
        }
    });

    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

async function guardarEmpleado() {
    const modal = document.getElementById('modalEmpleado');
    if (!modal) return;

    // 1. Elementos de UI para feedback
    const btnGuardar = event?.target || document.querySelector('button[onclick="guardarEmpleado()"]');
    const originalBtnText = btnGuardar ? btnGuardar.innerText : 'Guardar';
    
    // 2. Determinar ID y URL
    let id = modal.getAttribute('data-id');
    const esNuevo = (!id || id === "null" || id === "undefined" || id === "");
    const url = esNuevo ? '/admin/api/empleado/nuevo' : `/admin/api/empleado/editar/${id}`;

    // 3. Validaciones rápidas
    const nombre = document.getElementById('empl_nombre')?.value.trim();
    const cedula = document.getElementById('empl_cedula')?.value.trim();

    if (!nombre || !cedula) {
        Swal.fire({ 
            title: 'Campos Incompletos', 
            text: 'Por favor, ingresa al menos el nombre y la cédula.', 
            icon: 'warning', 
            background: '#0f172a', color: '#fff' 
        });
        return;
    }

    // 4. Preparar FormData
    const formData = new FormData();
    formData.append('nombre', nombre);
    formData.append('cedula', cedula);
    formData.append('telefono', document.getElementById('empl_telefono')?.value || '');
    formData.append('correo', document.getElementById('empl_correo')?.value.trim() || '');
    formData.append('porcentaje', document.getElementById('empl_porcentaje')?.value || '40');
    formData.append('cargo', document.getElementById('empl_cargo')?.value || 'Especialista');

    // Foto
    const fotoInput = document.getElementById('empl_foto');
    if (fotoInput?.files[0]) {
        formData.append('foto', fotoInput.files[0]);
    }

    // Servicios
    document.querySelectorAll('input[name="servicios_empleado"]:checked')
            .forEach(cb => formData.append('servicios[]', cb.value));

    try {
        // Estado de "Cargando"
        if (btnGuardar) {
            btnGuardar.disabled = true;
            btnGuardar.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin mr-2"></i> Procesando...';
        }

        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Accept': 'application/json' },
            body: formData 
        });

        // --- SOLUCIÓN AL ERROR DE JSON ---
        const contentType = response.headers.get("content-type");
        if (!contentType || !contentType.includes("application/json")) {
            const textError = await response.text();
            console.error("Respuesta del servidor no es JSON:", textError);
            throw new Error("El servidor tuvo un problema técnico y no respondió en formato correcto. Revisa la consola de Python.");
        }

        const data = await response.json();

        if (data.status === 'success' || data.success) {
            if (typeof cerrarModal === 'function') cerrarModal();
            
            await Swal.fire({
                title: '¡Perfecto!',
                text: data.message || 'Datos guardados correctamente',
                icon: 'success',
                background: '#0f172a', color: '#fff',
                timer: 1500, showConfirmButton: false
            });
            
            window.location.reload();
        } else {
            throw new Error(data.message || 'Error al guardar');
        }

    } catch (error) {
        console.error("Error en guardarEmpleado:", error);
        Swal.fire({ 
            title: 'Error de Sistema', 
            text: error.message, 
            icon: 'error', 
            background: '#0f172a', color: '#fff' 
        });
    } finally {
        // Restaurar botón
        if (btnGuardar) {
            btnGuardar.disabled = false;
            btnGuardar.innerText = originalBtnText;
        }
    }
}


function cambiarEstadoEmpleado(id, nuevoEstado) {
    const accion = nuevoEstado ? 'activar' : 'inactivar';

    Swal.fire({
        title: `¿Deseas ${accion} al empleado?`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: nuevoEstado ? '#10b981' : '#f59e0b',
        cancelButtonColor: '#64748b',
        confirmButtonText: `Sí, ${accion}`,
        cancelButtonText: 'Cancelar',
        background: '#0f172a',
        color: '#fff'
    }).then((result) => {
        if (result.isConfirmed) {
            // Fíjate que la URL coincida con tu @admin_bp.route
            // Si tu blueprint tiene un prefijo (ej: /admin), la URL debe incluirlo
            fetch(`/admin/api/empleado/estado/${id}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ activo: nuevoEstado })
            })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'success') {
                    Swal.fire({
                        title: '¡Hecho!',
                        text: data.message,
                        icon: 'success',
                        background: '#0f172a',
                        color: '#fff',
                        timer: 1500,
                        showConfirmButton: false
                    });
                    setTimeout(() => window.location.reload(), 1600);
                } else {
                    Swal.fire({ title: 'Error', text: data.message, icon: 'error', background: '#0f172a', color: '#fff' });
                }
            })
            .catch(error => {
                console.error('Error:', error);
                Swal.fire({ title: 'Error de red', text: 'No se pudo contactar con el servidor', icon: 'error', background: '#0f172a', color: '#fff' });
            });
        }
    });
}



function buscarTabla() {
    // 1. Convertimos la búsqueda a Mayúsculas para que no importe si escriben 'juan' o 'JUAN'
    let input = document.getElementById("busquedaEmpleado").value.toUpperCase();
    let table = document.getElementById("tablaEmpleados");
    let tr = table.getElementsByTagName("tr");

    // Recorremos desde i=1 para saltar el encabezado
    for (let i = 1; i < tr.length; i++) {
        // Obtenemos el texto visible de TODA la fila
        let textoVisible = tr[i].textContent || tr[i].innerText;
        
        // Obtenemos los servicios ocultos que pusimos en el data-attribute anteriormente
        let serviciosOcultos = tr[i].getAttribute('data-servicios') || "";
        
        // Unimos todo para buscar en un solo lugar
        let todoElContenido = (textoVisible + " " + serviciosOcultos).toUpperCase();

        // Si el input está en cualquier parte de la fila o de los servicios...
        if (todoElContenido.indexOf(input) > -1) {
            tr[i].style.display = "";
            // Le damos un toque visual a la fila encontrada (opcional)
            tr[i].style.backgroundColor = input !== "" ? "rgba(14, 165, 233, 0.05)" : "";
        } else {
            tr[i].style.display = "none";
        }
    }
}



function cerrarModal() {
    const modal = document.getElementById('modalEmpleado');
    if (modal) {
        modal.classList.remove('flex');
        modal.classList.add('hidden');
        modal.removeAttribute('data-id');
        
        // Limpiar inputs y foto
        document.getElementById('empl_foto').value = '';
        document.getElementById('img_preview').src = '';
        document.getElementById('img_preview').classList.add('hidden');
        document.getElementById('img_icon').classList.remove('hidden');
    }
}

// Función de ayuda para la sección de Equipo
function abrirAyudaEquipo() {
    Swal.fire({
        title: '<span class="text-sky-500 font-black">Guía del Equipo</span>',
        html: `
            <div class="text-left space-y-4 text-slate-300 text-sm leading-relaxed">
                <p><strong class="text-white">🎟️ Límites de Personal:</strong> Tu plan actual tiene un cupo máximo de empleados. La barra superior te indica cuántos espacios libres tienes.</p>
                <div class="p-3 bg-white/5 rounded-2xl border border-white/10">
                    <p class="mb-1"><strong class="text-emerald-500">💰 Porcentaje de Comisión:</strong></p>
                    <p class="text-xs text-slate-400 text-pretty">Define cuánto gana el empleado por cada servicio. El sistema usará este valor para calcular sus pagos automáticamente.</p>
                </div>
                <p><strong class="text-sky-500">🔍 Búsqueda:</strong> Filtra rápidamente por nombre para editar datos o eliminar personal que ya no labore en el negocio.</p>
                <p><strong class="text-amber-500">⚠️ Identificación:</strong> La cédula es única por empleado. No se permite registrar dos personas con el mismo documento.</p>
            </div>
        `,
        icon: 'info',
        background: '#0f172a',
        color: '#ffffff',
        confirmButtonText: '¡Entendido!',
        confirmButtonColor: '#0ea5e9',
        customClass: {
            popup: 'rounded-[2rem] border border-white/10 shadow-2xl'
        }
    });
}


function abrirModalInactivos() {
    const modal = document.getElementById('modalInactivos');
    if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    }
}

function cerrarModalInactivos() {
    const modal = document.getElementById('modalInactivos');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
}


function exportarExcel() {
    try {
        const filas = document.querySelectorAll('#tablaEmpleados tbody tr');
        // Filtramos para no traer filas vacías o de error
        const filasValidas = Array.from(filas).filter(tr => tr.offsetParent !== null && tr.id !== 'sinResultados');

        if (filasValidas.length === 0) {
            Swal.fire('Sin datos', 'No hay empleados para exportar', 'info');
            return;
        }

        const datosExcel = filasValidas.map(tr => {
            // Extraemos los datos usando las clases específicas que pusimos en el HTML
            return {
                "Nombre": tr.querySelector('.empl-nombre')?.innerText.trim() || "N/A",
                "Cargo": tr.querySelector('.empl-cargo')?.innerText.trim() || "General",
                "Correo": tr.querySelector('.empl-correo')?.innerText.trim() || "", // NUEVA COLUMNA
                "Identificación": tr.querySelector('.empl-cedula')?.innerText.trim() || "0",
                "Teléfono": tr.querySelector('.empl-telefono')?.innerText.trim() || "",
                "Comisión": tr.innerText.includes('%') ? tr.querySelector('.text-center span')?.innerText.replace('%', '').trim() : "40",
                "Servicios": tr.getAttribute('data-servicios') || "No asignados"
            };
        });

        // Crear el libro de Excel
        const worksheet = XLSX.utils.json_to_sheet(datosExcel);
        
        // Ajustar anchos de columna para que el correo y nombre se vean bien
        worksheet['!cols'] = [
            { wch: 25 }, // Nombre
            { wch: 15 }, // Cargo
            { wch: 30 }, // Correo
            { wch: 15 }, // Identificación
            { wch: 15 }, // Teléfono
            { wch: 10 }, // Comisión
            { wch: 40 }  // Servicios
        ];

        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, "Empleados");
        
        const fecha = new Date().toISOString().slice(0, 10);
        XLSX.writeFile(workbook, `Reporte_Empleados_${fecha}.xlsx`);

    } catch (error) {
        console.error("Error al exportar:", error);
        Swal.fire('Error', 'No se pudo generar el reporte', 'error');
    }
}




function importarExcel(input) {
    if (input.files && input.files[0]) {
        const archivo = input.files[0];
        const formData = new FormData();
        formData.append('archivo', archivo);

        Swal.fire({
            title: 'Procesando archivo...',
            text: 'Validando límites y datos del Excel',
            allowOutsideClick: false,
            background: '#0f172a',
            color: '#fff',
            didOpen: () => { Swal.showLoading(); }
        });

        fetch('/admin/api/empleado/importar', {
            method: 'POST',
            body: formData
            // Nota: No pongas 'Content-Type', el navegador lo pone solo con FormData
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'success') {
                Swal.fire({
                    title: '¡Importado!',
                    text: data.message,
                    icon: 'success',
                    background: '#0f172a',
                    color: '#fff'
                }).then(() => window.location.reload());
            } else {
                // Aquí mostrará: "Límite de empleados lleno" o el mensaje que envíe Python
                Swal.fire({
                    title: 'No se pudo importar',
                    text: data.message,
                    icon: 'error',
                    background: '#0f172a',
                    color: '#fff'
                });
                // Limpiamos el input por si quiere elegir otro archivo
                input.value = '';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            Swal.fire({
                title: 'Error de conexión',
                text: 'Hubo un problema al subir el archivo.',
                icon: 'error',
                background: '#0f172a',
                color: '#fff'
            });
        });
    }
}



function enviarFormularioImportar() {
    const input = document.getElementById('inputImportar');
    const archivo = input.files[0];

    if (!archivo) return;

    // 1. Mostrar carga (Loading)
    Swal.fire({
        title: 'Procesando Excel...',
        text: 'Estamos cargando tu equipo, por favor espera.',
        allowOutsideClick: false,
        background: '#0f172a',
        color: '#fff',
        didOpen: () => {
            Swal.showLoading();
        }
    });

    // 2. Preparar los datos
    const formData = new FormData();
    formData.append('archivo', archivo);

    // 3. Enviar al servidor
    fetch('/admin/api/empleado/importar', { // Verifica que esta ruta sea la misma de tu @admin_bp
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // MENSAJE DE ÉXITO (Aquí es donde sale lo de "4 creados, 2 actualizados")
            Swal.fire({
                icon: 'success',
                title: '¡Tarea Completada!',
                text: data.message, // Aquí viene el mensaje de Python
                background: '#0f172a',
                color: '#fff',
                confirmButtonColor: '#0ea5e9',
                confirmButtonText: 'Genial'
            }).then(() => {
                window.location.reload(); // Recargamos para ver los nuevos empleados
            });
        } else {
            // MENSAJE DE ERROR DEL SERVIDOR
            Swal.fire({
                icon: 'error',
                title: 'Hubo un problema',
                text: data.message,
                background: '#0f172a',
                color: '#fff',
                confirmButtonColor: '#f43f5e'
            });
        }
    })
    .catch(error => {
        console.error('Error:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error de red',
            text: 'No se pudo conectar con el servidor.',
            background: '#0f172a',
            color: '#fff'
        });
    })
    .finally(() => {
        input.value = ''; // Limpiamos el input
    });
}


// duplicacion de usuario

function prepararDuplicacion(nombre, telefono, porcentaje, cargo, serviciosIds) {
    const modal = document.getElementById('modalEmpleado');
    if (!modal) return;

    // 1. IMPORTANTE: Limpiar el ID para que guarde como NUEVO
    modal.setAttribute('data-id', ''); // O modal.removeAttribute('data-id');
    
    // 2. Cambiar Título y colores para que el usuario sepa que es copia
    document.getElementById('modalTitulo').innerHTML = 'Duplicar <span class="text-violet-500">Empleado</span>';
    
    // 3. Llenar campos
    if(document.getElementById('empl_nombre')) document.getElementById('empl_nombre').value = nombre + " (Copia)";
    if(document.getElementById('empl_cedula')) document.getElementById('empl_cedula').value = ""; // Obligatorio llenar nueva
    if(document.getElementById('empl_telefono')) document.getElementById('empl_telefono').value = telefono;
    if(document.getElementById('empl_porcentaje')) document.getElementById('empl_porcentaje').value = porcentaje;
    if(document.getElementById('empl_cargo')) document.getElementById('empl_cargo').value = cargo;

    // 4. Marcar servicios
    const checkboxes = document.querySelectorAll('input[name="servicios_empleado"]');
    checkboxes.forEach(cb => {
        cb.checked = false;
        if (serviciosIds && serviciosIds.map(String).includes(String(cb.value))) {
            cb.checked = true;
        }
    });

    // 5. Abrir Modal (Asegúrate de usar las clases de tu diseño)
    modal.classList.remove('hidden');
    modal.classList.add('flex'); // Si usas flex para centrarlo
}


// seleccionar todos los checkboxes de servicios_

function toggleTodosServicios() {
    // Usamos la clase que pusiste en el HTML
    const checkboxes = document.querySelectorAll('.checkbox-servicio');
    const todosMarcados = Array.from(checkboxes).every(cb => cb.checked);

    checkboxes.forEach(cb => {
        cb.checked = !todosMarcados;
    });
    
    // Actualizar texto del botón si lo deseas
    const btn = document.getElementById('btnToggleTodos');
    if(btn) btn.innerText = todosMarcados ? "Seleccionar Todos" : "Desmarcar Todos";
}

// --- LÓGICA DE VISIBILIDAD DE EMPLEADOS EN RESERVAS ---

/**
 * Actualiza la preferencia del propietario sobre si mostrar o no
 * la selección de empleados a los clientes.
 */
function actualizarVisibilidadGlobal(mostrar) {
    const textoEstado = document.getElementById('estado_visibilidad');
    const inputSwitch = document.getElementById('toggle_mostrar_empleados');
    
    // 1. Guardar estado anterior por si hay que revertir
    const estadoAnterior = !mostrar;

    // 2. Feedback visual inmediato
    if (textoEstado) {
        textoEstado.innerText = mostrar ? "Activado" : "Desactivado";
        if (mostrar) {
            textoEstado.classList.replace('text-rose-500', 'text-sky-500');
        } else {
            textoEstado.classList.replace('text-sky-500', 'text-rose-500');
        }
    }

    // 3. Enviar al servidor
// Cambia la línea del fetch por esta:
fetch('/admin/api/configuracion/visibilidad-empleados', { 
    method: 'POST',
    headers: { 
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    },
    body: JSON.stringify({ mostrar_empleados: mostrar })
})
    .then(response => {
        // Si el servidor responde 404, 500, etc., lanzamos error
        if (!response.ok) throw new Error('Error en la respuesta del servidor');
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            const Toast = Swal.mixin({
                toast: true,
                position: 'top-end',
                showConfirmButton: false,
                timer: 2000,
                timerProgressBar: true,
                background: '#0f172a',
                color: '#fff'
            });
            
            Toast.fire({
                icon: 'success',
                title: mostrar ? 'Los clientes elegirán personal' : 'Asignación automática desactivada'
            });
        } else {
            throw new Error(data.message || 'Error desconocido');
        }
    })
    .catch(err => {
        console.error("Error al guardar configuración:", err);
        
        // 4. REVERSIÓN: Si falló, regresamos el switch y el texto a como estaban
        if (inputSwitch) inputSwitch.checked = estadoAnterior;
        if (textoEstado) {
            textoEstado.innerText = estadoAnterior ? "Activado" : "Desactivado";
            textoEstado.classList.toggle('text-sky-500', estadoAnterior);
            textoEstado.classList.toggle('text-rose-500', !estadoAnterior);
        }

        Swal.fire({
            title: 'No se pudo guardar',
            text: 'Hubo un problema de conexión o el servidor falló.',
            icon: 'error',
            background: '#0f172a',
            color: '#fff'
        });
    });
}


function previsualizarImagen(input) {
    const file = input.files[0];
    // ÚNICAMENTE permitimos el tipo oficial de JPG
    const tiposPermitidos = ['image/jpeg']; 

    if (file) {
        if (!tiposPermitidos.includes(file.type)) {
            Swal.fire({
                icon: 'error',
                title: 'Formato no permitido',
                text: 'El sistema solo admite imágenes en formato JPG.',
                confirmButtonColor: '#0ea5e9'
            });
            input.value = ''; 
            return false;
        }

        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('img_preview').src = e.target.result;
            document.getElementById('img_preview').classList.remove('hidden');
            document.getElementById('img_icon').classList.add('hidden');
        }
        reader.readAsDataURL(file);
    }
}


function sincronizarDisplay(val) {
    if (val > 100) val = 100;
    if (val < 0) val = 0;
    
    document.getElementById('display_pct').innerText = val + '%';
    document.getElementById('progress_bar').style.width = val + '%';
    // Sincroniza el input oculto o el de número si usas varios
    document.getElementById('empl_porcentaje').value = val;
}

function ajustarComision(cambio) {
    const input = document.getElementById('empl_porcentaje');
    let nuevoValor = parseInt(input.value) + cambio;
    if (nuevoValor >= 0 && nuevoValor <= 100) {
        setComision(nuevoValor);
    }
}

function setComision(val) {
    const input = document.getElementById('empl_porcentaje');
    input.value = val;
    sincronizarDisplay(val);
}

function sincronizarInput(val) {
    document.getElementById('empl_porcentaje').value = val;
    sincronizarDisplay(val);
}