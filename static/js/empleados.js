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

function prepararEdicion(id, nombre, cedula, telefono, porcentaje, cargo, serviciosIds) {
    const modal = document.getElementById('modalEmpleado');
    if (!modal) return;

    modal.setAttribute('data-id', id);
    document.getElementById('modalTitulo').innerHTML = 'Editar <span class="text-sky-500">Empleado</span>';
    
    if(document.getElementById('empl_nombre')) document.getElementById('empl_nombre').value = nombre;
    // Limpiamos posibles comillas simples de la cédula que vienen de Jinja2
    if(document.getElementById('empl_cedula')) document.getElementById('empl_cedula').value = String(cedula).replace(/'/g, "");
    if(document.getElementById('empl_telefono')) document.getElementById('empl_telefono').value = telefono;
    if(document.getElementById('empl_porcentaje')) document.getElementById('empl_porcentaje').value = porcentaje;
    if(document.getElementById('empl_cargo')) document.getElementById('empl_cargo').value = cargo;

    const checkboxes = document.querySelectorAll('input[name="servicios_empleado"]');
    
    // Convertimos serviciosIds a un Array si viene como string/JSON
    let listaIds = Array.isArray(serviciosIds) ? serviciosIds : [];

    checkboxes.forEach(cb => {
        cb.checked = false;
        // Comparamos convirtiendo ambos a String para evitar fallos de tipo
        if (listaIds.some(sId => String(sId) === String(cb.value))) {
            cb.checked = true;
        }
    });

    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

function guardarEmpleado() {
    const modal = document.getElementById('modalEmpleado');
    if (!modal) return;

    // 1. Limpieza de ID
    let id = modal.getAttribute('data-id'); 
    if (id === "null" || id === "undefined" || id === "" || !id) {
        id = null;
    }

    // 2. Construcción de la URL
    const url = id ? `/admin/api/empleado/editar/${id}` : '/admin/api/empleado/nuevo';

    // --- CAMBIO CLAVE: Usamos FormData en lugar de un objeto plano ---
    const formData = new FormData();

    // 3. Agregamos los campos de texto
    formData.append('nombre', document.getElementById('empl_nombre')?.value.trim() || '');
    formData.append('cedula', document.getElementById('empl_cedula')?.value.trim() || '');
    formData.append('telefono', document.getElementById('empl_telefono')?.value || '');
    formData.append('porcentaje', document.getElementById('empl_porcentaje')?.value || '40');
    formData.append('cargo', document.getElementById('empl_cargo')?.value || 'Especialista');

    // 4. Agregamos la Foto (Asegúrate que tu input file tenga el id="empl_foto")
    const fotoInput = document.getElementById('empl_foto');
    if (fotoInput && fotoInput.files[0]) {
        formData.append('foto', fotoInput.files[0]);
    }

    // 5. Agregamos los Servicios (como array para Python)
    const checkboxes = document.querySelectorAll('input[name="servicios_empleado"]:checked');
    checkboxes.forEach(cb => {
        formData.append('servicios[]', cb.value); // Nota el uso de [] para que Flask lo reciba como lista
    });

    // 6. Validación previa básica
    const nombre = document.getElementById('empl_nombre')?.value.trim();
    const cedula = document.getElementById('empl_cedula')?.value.trim();

    if (!nombre || !cedula) {
        Swal.fire({ 
            title: 'Atención', 
            text: 'El nombre y la cédula son campos obligatorios', 
            icon: 'warning', 
            background: '#0f172a', 
            color: '#fff' 
        });
        return;
    }

    // 7. Petición al servidor
    // NOTA: Quitamos el 'Content-Type': 'application/json' de los headers.
    // El navegador detectará que es FormData y pondrá el "multipart/form-data" automáticamente.
    fetch(url, {
        method: 'POST',
        headers: { 
            'Accept': 'application/json'
            // No pongas Content-Type aquí
        },
        body: formData 
    })
    .then(res => {
        return res.json().then(data => {
            if (!res.ok) {
                throw new Error(data.message || `Error ${res.status}`);
            }
            return data;
        });
    })
    .then(data => {
        if (data.status === 'success') {
            if (typeof cerrarModal === 'function') cerrarModal();
            
            Swal.fire({
                title: '¡Éxito!',
                text: data.message,
                icon: 'success',
                background: '#0f172a',
                color: '#fff',
                timer: 1500,
                showConfirmButton: false
            });
            
            setTimeout(() => { window.location.reload(); }, 1600);
        } else {
            throw new Error(data.message || 'Ocurrió un error inesperado');
        }
    })
    .catch(error => {
        console.error('Error detallado:', error);
        Swal.fire({ 
            title: 'Atención', 
            text: error.message, 
            icon: 'error', 
            background: '#0f172a', 
            color: '#fff' 
        });
    });
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
    document.getElementById('modalInactivos').classList.remove('hidden');
}

function cerrarModalInactivos() {
    document.getElementById('modalInactivos').classList.add('hidden');
}

function exportarExcel() {
    try {
        const filas = document.querySelectorAll('tbody tr');
        
        // Validamos que la tabla tenga datos (evitamos exportar la fila de "Sin resultados")
        const filasValidas = Array.from(filas).filter(tr => tr.offsetParent !== null && tr.id !== 'sinResultados');

        if (filasValidas.length === 0) {
            Swal.fire({
                icon: 'info',
                title: 'Sin datos',
                text: ' No hay empleados visibles para exportar.'
            });
            return;
        }

        const datosExcel = filasValidas.map(tr => {
            const celdas = tr.getElementsByTagName('td');
            
            // --- EXTRACCIÓN SEGURA DE NOMBRE Y CARGO ---
            // Buscamos el nombre en el elemento con clase font-bold
            const nombreElem = celdas[0].querySelector('.font-bold');
            // Buscamos el cargo en el texto pequeño (ajusta la clase si usas otra para el cargo)
            const cargoElem = celdas[0].querySelector('.text-slate-500') || celdas[0].querySelector('span:last-child');

            const nombre = nombreElem ? nombreElem.innerText.trim() : celdas[0].innerText.split('\n')[0].trim();
            const cargo = cargoElem ? cargoElem.innerText.trim() : "General";

            // --- EXTRACCIÓN DE IDENTIFICACIÓN ---
            // Quitamos comillas o caracteres extraños que puedan venir del front
            const identificacion = celdas[1]?.innerText.trim().replace(/'/g, "") || "N/A";

            return {
                "Nombre": nombre,
                "Cargo": cargo,
                "Identificación": identificacion,
                "Teléfono": celdas[2]?.innerText.trim() || "N/A",
                "Comisión": celdas[3]?.innerText.trim() || "0%",
                "Servicios": tr.getAttribute('data-servicios') || "No asignados"
            };
        });

        // --- GENERACIÓN DEL ARCHIVO ---
        const worksheet = XLSX.utils.json_to_sheet(datosExcel);
        
        // Ajustamos el ancho de las columnas automáticamente para que se vea pro
        const wscols = [
            {wch: 30}, // Nombre
            {wch: 20}, // Cargo
            {wch: 20}, // Identificación
            {wch: 15}, // Teléfono
            {wch: 12}, // Comisión
            {wch: 50}  // Servicios
        ];
        worksheet['!cols'] = wscols;

        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, "Lista_Empleados");
        
        // Descarga el archivo con la fecha de hoy
        const fecha = new Date().toISOString().slice(0, 10);
        XLSX.writeFile(workbook, `Reporte_Empleados_${fecha}.xlsx`);

    } catch (error) {
        console.error("Error al exportar:", error);
        Swal.fire('Error', 'Hubo un fallo al generar el Excel. Revisa la consola.', 'error');
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

// La asignamos a window para que SweetAlert la encuentre siempre
window.descargarPlantillaEmpleados = function() {
    try {
        if (typeof XLSX === 'undefined') {
            throw new Error('Librería XLSX no encontrada');
        }

        // 1. Estructura de la plantilla (IMPORTANTE: Nombres exactos para Python)
        // Usamos los mismos nombres que genera tu función de Exportar
        const data = [
            ["Nombre", "Cargo", "Identificación", "Teléfono", "Comisión", "Servicios"],
            ["Ejemplo Nombre", "Especialista", "1111222333", "3001234567", "40", "Corte, Barba"]
        ];

        // 2. Crear libro
        const ws = XLSX.utils.aoa_to_sheet(data);

        // Ajustar anchos de columna para que se vea bien en móvil/PC
        ws['!cols'] = [
            {wch: 25}, // Nombre
            {wch: 15}, // Cargo
            {wch: 15}, // Identificación
            {wch: 15}, // Teléfono
            {wch: 10}, // Comisión
            {wch: 30}  // Servicios
        ];

        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, "Plantilla");

        // 3. Generar descarga
        XLSX.writeFile(wb, "Plantilla_Empleados.xlsx");

        // Notificación de éxito
        Swal.fire({
            toast: true,
            position: 'top-end',
            icon: 'success',
            title: 'Plantilla descargada',
            showConfirmButton: false,
            timer: 3000,
            background: '#0f172a',
            color: '#fff'
        });
    } catch (error) {
        console.error(error);
        Swal.fire({
            title: 'Error',
            text: 'Asegúrate de tener conexión a internet para cargar los recursos de Excel.',
            icon: 'error',
            background: '#0f172a',
            color: '#fff'
        });
    }
};

function enviarFormularioImportar() {
    const input = document.getElementById('inputImportar');
    if (input.files.length > 0) {
        // Mostrar un aviso de carga (opcional pero pro)
        Swal.fire({
            title: 'Procesando archivo...',
            text: 'Espere un momento mientras cargamos los datos',
            allowOutsideClick: false,
            didOpen: () => {
                Swal.showLoading();
            }
        });
        // Enviar el formulario
        document.getElementById('formImportar').submit();
    }
}

function abrirAyudaEmpleados() {
    Swal.fire({
        title: '<span class="text-emerald-500 font-black">Guía de Personal</span>',
        html: `
            <div class="text-left space-y-4 text-slate-300 text-sm leading-relaxed">
                
                <div class="space-y-2">
                    <p><strong class="text-white">👥 Gestión de Staff:</strong></p>
                    <ul class="space-y-2 ml-2">
                        <li class="flex items-start gap-2">
                            <span class="text-sky-400 font-bold min-w-[85px]">📝 Cargos:</span> 
                            <span>Define roles (Barbero, Manicurista, etc.) para organizar tu agenda.</span>
                        </li>
                        <li class="flex items-start gap-2">
                            <span class="text-emerald-400 font-bold min-w-[85px]">💰 Comisión:</span> 
                            <span>El % configurado se aplicará automáticamente al calcular los pagos.</span>
                        </li>
                    </ul>
                </div>

                <hr class="border-white/5">

                <div class="p-4 bg-sky-500/5 rounded-2xl border border-sky-500/10">
                    <p class="mb-1"><strong class="text-sky-500 italic">📥 Importación Masiva:</strong></p>
                    <p class="text-[11px] mb-3 text-slate-400">El sistema usa la <b>Identificación</b> como llave. Si ya existe, se actualizarán los datos automáticamente.</p>
                    
                    <button type="button" onclick="descargarPlantillaEmpleados()" class="w-full flex items-center justify-center gap-2 bg-sky-500/20 hover:bg-sky-500/30 text-sky-400 py-2.5 rounded-xl transition-all font-bold text-xs border border-sky-500/20">
                        <i class="fa-solid fa-download"></i> Descargar Plantilla Excel
                    </button>
                </div>

                <div class="grid grid-cols-1 gap-3">
                    <p><strong class="text-emerald-500">📊 Reportes:</strong> Genera un Excel con el listado de personal y sus porcentajes de ganancia.</p>
                </div>

            </div>
        `,
        showConfirmButton: true,
        confirmButtonText: '¡Entendido!',
        confirmButtonColor: '#10b981',
        background: '#0f172a',
        color: '#ffffff',
        customClass: {
            popup: 'rounded-[2rem] border border-white/10 shadow-2xl'
        }
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
    const tiposPermitidos = ['image/jpg'];

    if (file) {
        // VALIDACIÓN DE FORMATO
        if (!tiposPermitidos.includes(file.type)) {
            Swal.fire({
                icon: 'error',
                title: 'Archivo no válido',
                text: 'Solo se permiten imágenes JPG.',
                confirmButtonColor: '#0ea5e9'
            });
            input.value = ''; // Limpia el input
            return false;
        }

        // Si es válido, mostrar la miniatura
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('img_preview').src = e.target.result;
            document.getElementById('img_preview').classList.remove('hidden');
            document.getElementById('img_icon').classList.add('hidden');
        }
        reader.readAsDataURL(file);
    }
}