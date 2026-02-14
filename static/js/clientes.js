console.log('CARGO EL ARCHIVO JS DE CLIENTES')

// --- LÓGICA MODALES ---
function abrirModalEditar(cliente) {
    // 1. Llenamos los IDs y campos básicos
    document.getElementById('edit_cli_id').value = cliente.id;
    document.getElementById('edit_nombre').value = cliente.nombre;
    document.getElementById('edit_alias').value = cliente.alias || '';
    document.getElementById('edit_email').value = cliente.email || '';
    document.getElementById('edit_telefono').value = cliente.telefono || '';
    document.getElementById('edit_fecha_nacimiento').value = cliente.fecha_nacimiento || '';
    
    // 2. Llenamos las Notas de Confianza
    const inputNotas = document.getElementById('edit_notas_personales');
    if (inputNotas) {
        inputNotas.value = cliente.notas_personales || '';
    }

    // 3. Mostramos el modal (ajusta el ID si es diferente)
    const modal = document.getElementById('modalEditar');
    if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex'); // Si usas flex para centrar
    }
}

function cerrarModal() { document.getElementById('modalEditar').classList.add('hidden'); }
function abrirModalNuevo() { document.getElementById('modalNuevo').classList.remove('hidden'); }
function cerrarModalNuevo() { document.getElementById('modalNuevo').classList.add('hidden'); }

// --- ACCIONES API ---
function guardarCambiosCliente() {
    // 1. Obtener el ID y verificar que no sea nulo
    const cliIdInput = document.getElementById('edit_cli_id');
    const cliId = cliIdInput ? cliIdInput.value : null;
    
    if (!cliId) {
        console.error("No se encontró el input con ID 'edit_cli_id' o está vacío");
        Swal.fire({
            title: 'Error de Identificación',
            text: 'No se pudo identificar al cliente para editar.',
            icon: 'warning',
            background: '#1e293b',
            color: '#fff'
        });
        return;
    }

    // 2. Recolectar datos del formulario
    const data = {
        nombre: document.getElementById('edit_nombre').value,
        alias: document.getElementById('edit_alias').value,
        email: document.getElementById('edit_email').value,
        telefono: document.getElementById('edit_telefono').value,
        fecha_nacimiento: document.getElementById('edit_fecha_nacimiento').value,
        // Captura las notas o envía vacío si no hay nada
        notas_personales: document.getElementById('edit_notas_personales')?.value || ''
    };


     

    // 3. Definir URL (Asegúrate de que el prefijo coincida con tu Blueprint de Flask)
    const url = `/admin/api/cliente/editar/${cliId}`;
    console.log("Intentando conectar a:", url);
    console.log("Datos enviados:", data);

    // 4. Ejecutar la petición
    fetch(url, {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json' 
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        console.log("Status Code recibido:", response.status); // <--- REVISA ESTO EN F12
        
        if (!response.ok) {
            // Si no es un 200 OK, lanzamos error con el código
            throw new Error(`Error en el servidor (Código: ${response.status})`);
        }
        return response.json();
    })
    .then(result => {
        if (result.status === 'success') {
            Swal.fire({
                title: '¡Actualizado!',
                text: 'Los datos de confianza se han guardado con éxito.',
                icon: 'success',
                background: '#1e293b',
                color: '#fff',
                timer: 1500,
                showConfirmButton: false
            }).then(() => {
                location.reload(); // Recarga para ver cambios
            });
        } else {
            Swal.fire({
                title: 'Error',
                text: result.message || 'No se pudo guardar.',
                icon: 'error',
                background: '#1e293b',
                color: '#fff'
            });
        }
    })
    .catch(error => {
        console.error('Error detallado detectado:', error);
        Swal.fire({
            title: 'Error de Conexión',
            text: `Detalle: ${error.message}. Por favor, verifica la consola (F12).`,
            icon: 'error',
            background: '#1e293b',
            color: '#fff'
        });
    });
}




function crearCliente() {
    // Capturamos los elementos para validar que existen
    const inputNombre = document.getElementById('new_nombre');
    const inputFecha = document.getElementById('new_fecha_nacimiento');
    const inputNotas = document.getElementById('new_notas_personales');

    const datos = {
        nombre: inputNombre ? inputNombre.value : '',
        alias: document.getElementById('new_alias')?.value || '',
        email: document.getElementById('new_email')?.value || '',
        telefono: document.getElementById('new_telefono')?.value || '',
        // Si el campo no existe o está vacío, enviamos null o vacío
        fecha_nacimiento: inputFecha ? inputFecha.value : '',
        notas_personales: inputNotas ? inputNotas.value : ''
    };

    if(!datos.nombre) {
        Swal.fire({
            title: 'Campo Requerido',
            text: 'Por favor, escribe al menos el nombre del cliente.',
            icon: 'warning',
            background: '#0f172a',
            color: '#fff',
            confirmButtonColor: '#10b981'
        });
        return;
    }

    fetch(`/admin/api/cliente/nuevo`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(datos)
    })
    .then(res => {
        if (!res.ok) throw new Error("Error en la respuesta del servidor (Status: " + res.status + ")");
        return res.json();
    })
    .then(data => {
        if(data.status === 'success') {
            Swal.fire({
                title: '¡Éxito!',
                text: 'Cliente registrado correctamente',
                icon: 'success',
                timer: 1500,
                showConfirmButton: false,
                background: '#0f172a',
                color: '#fff'
            }).then(() => {
                location.reload();
            });
        } else {
            Swal.fire('Error', data.message, 'error');
        }
    })
    .catch(err => {
        console.error(err);
        Swal.fire('Error de Conexión', 'No se pudo registrar el cliente', 'error');
    });
}

function filtrarClientes() {
    const input = document.getElementById('buscador');
    const filtro = input.value.toLowerCase();
    const filas = document.querySelectorAll('tbody tr');

    filas.forEach(fila => {
        const nombre = fila.querySelector('.cli-nombre')?.textContent.toLowerCase() || "";
        const alias = fila.querySelector('.cli-alias')?.textContent.toLowerCase() || "";

        if (nombre.includes(filtro) || alias.includes(filtro)) {
            fila.style.display = "";
            fila.style.opacity = "1";
        } else {
            fila.style.display = "none";
        }
    });

    const sinResultados = Array.from(filas).every(f => f.style.display === "none");
    let mensajeVacio = document.getElementById('mensaje-vacio');
    
    if (sinResultados) {
        if (!mensajeVacio) {
            const tr = document.createElement('tr');
            tr.id = 'mensaje-vacio';
            tr.innerHTML = `<td colspan="10" class="py-20 text-center">
                <i class="fa-solid fa-user-slash text-4xl text-slate-700 mb-4 block"></i>
                <p class="text-slate-500 font-medium">No encontramos clientes con ese nombre...</p>
            </td>`;
            document.querySelector('tbody').appendChild(tr);
        }
    } else if (mensajeVacio) {
        mensajeVacio.remove();
    }
    actualizarContador();
}

function desactivarCliente(id) {
    Swal.fire({
        title: '¿Desactivar cliente?',
        text: "El cliente ya no aparecerá en la lista de activos.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#f59e0b', // Color ámbar
        cancelButtonColor: '#334155', // Color slate
        confirmButtonText: 'Sí, desactivar',
        cancelButtonText: 'Cancelar',
        background: '#0f172a', // Fondo oscuro
        color: '#ffffff',
        reverseButtons: true
    }).then((result) => {
        if (result.isConfirmed) {
            fetch(`/admin/api/cliente/desactivar/${id}`, { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'success') {
                    const fila = document.getElementById(`cli-${id}`);
                    fila.classList.add('opacity-0', '-translate-x-10');
                    setTimeout(() => fila.remove(), 300);
                    
                    Swal.fire({
                        title: '¡Desactivado!',
                        icon: 'success',
                        timer: 1500,
                        showConfirmButton: false,
                        background: '#0f172a',
                        color: '#ffffff'
                    });
                }
                else {
                // ALERTA DE ERROR MODERNA
                Swal.fire({
                    title: 'No se puede eliminar',
                    text: data.message, // Aquí aparecerá el texto de Python
                    icon: 'warning',
                    background: '#0f172a',
                    color: '#ffffff',
                    confirmButtonColor: '#334155'
                });
            }
            });
        }
    });
}


function reactivarCliente(id) {
    Swal.fire({
        title: '¿Reactivar cliente?',
        text: "El cliente volverá a aparecer en tu lista de clientes activos.",
        icon: 'info',
        showCancelButton: true,
        confirmButtonColor: '#10b981', // Color emerald-500
        cancelButtonColor: '#334155', // Color slate-700
        confirmButtonText: 'Sí, reactivar',
        cancelButtonText: 'Cancelar',
        background: '#0f172a', // Fondo oscuro (slate-900)
        color: '#ffffff',
        reverseButtons: true
    }).then((result) => {
        if (result.isConfirmed) {
            // Se mantiene el prefijo /admin para el Blueprint
            fetch(`/admin/api/cliente/activar/${id}`, { 
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(res => {
                if (!res.ok) throw new Error("Error en la ruta del servidor");
                return res.json();
            })
            .then(data => {
                if (data.status === 'success') {
                    // Animación suave para quitarlo de la vista de desactivados
                    const fila = document.getElementById(`cli-${id}`);
                    if (fila) {
                        fila.classList.add('opacity-0', 'translate-x-10');
                        setTimeout(() => fila.remove(), 300);
                    }

                    // Notificación de éxito rápida
                    Swal.fire({
                        title: '¡Activado!',
                        text: 'El cliente ha sido reactivado con éxito.',
                        icon: 'success',
                        timer: 1500,
                        showConfirmButton: false,
                        background: '#0f172a',
                        color: '#ffffff'
                    });
                } else {
                    Swal.fire({
                        title: 'Error',
                        text: data.message,
                        icon: 'error',
                        background: '#0f172a',
                        color: '#ffffff'
                    });
                }
            })
            .catch(err => {
                console.error("Error:", err);
                Swal.fire({
                    title: 'Error de conexión',
                    text: 'No se pudo comunicar con el servidor.',
                    icon: 'error',
                    background: '#0f172a',
                    color: '#ffffff'
                });
            });
        }
    });
}

function eliminarCliente(id) {
    Swal.fire({
        title: '¿ELIMINAR PERMANENTEMENTE?',
        text: "Esta acción no se puede deshacer.",
        icon: 'error',
        showCancelButton: true,
        confirmButtonColor: '#ef4444', // Color rojo
        cancelButtonColor: '#334155',
        confirmButtonText: 'BORRAR AHORA',
        cancelButtonText: 'No, esperar',
        background: '#0f172a',
        color: '#ffffff',
        reverseButtons: true
    }).then((result) => {
        if (result.isConfirmed) {
            fetch(`/admin/api/cliente/eliminar/${id}`, { method: 'DELETE' })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'success') {
                    document.getElementById(`cli-${id}`).remove();
                    Swal.fire({
                        title: 'Eliminado',
                        text: 'El registro ha sido borrado.',
                        icon: 'success',
                        background: '#0f172a',
                        color: '#ffffff'
                    });
                } else {
                    Swal.fire('Error', data.message, 'error');
                }
            });
        }
    });
}



function mostrarCargandoYEnviar() {
    Swal.fire({
        title: 'Procesando archivo...',
        text: 'Estamos validando y cargando tus clientes.',
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading();
        },
        background: '#0f172a',
        color: '#ffffff'
    });
    document.getElementById('importForm').submit();
}


function actualizarContador() {
    // Cuenta solo las filas que no tienen display: none
    const filasVisibles = document.querySelectorAll('tbody tr:not([style*="display: none"])').length;
    const contadorElemento = document.getElementById('contador-clientes');
    
    if (contadorElemento) {
        contadorElemento.textContent = filasVisibles;
    }
}


function abrirAyudaClientes() {
    Swal.fire({
        title: '<span class="text-sky-500 font-black text-2xl">Manual de Éxito</span>',
        html: `
            <div class="text-left space-y-5 text-slate-300 text-sm leading-relaxed">
                
                <div class="space-y-2">
                    <p><strong class="text-white border-b border-sky-500/30 pb-1">🏆 Niveles de Fidelidad:</strong></p>
                    <ul class="space-y-2 ml-2 mt-2">
                        <li class="flex items-start gap-2">
                            <span class="text-purple-400 font-bold min-w-[75px]">👑 Fiel:</span> 
                            <span>+5 reservas. Son tus clientes VIP, ¡cuídalos!</span>
                        </li>
                        <li class="flex items-start gap-2">
                            <span class="text-sky-400 font-bold min-w-[75px]">⭐ Frecuente:</span> 
                            <span>2 a 5 reservas. Clientes en crecimiento.</span>
                        </li>
                        <li class="flex items-start gap-2">
                            <span class="text-slate-400 font-bold min-w-[75px]">🆕 Nuevo:</span> 
                            <span>Primera visita al salón.</span>
                        </li>
                    </ul>
                </div>

                <hr class="border-white/5">

                <div class="space-y-3">
                    <p><strong class="text-white border-b border-pink-500/30 pb-1">💡 Herramientas de Fidelización:</strong></p>
                    <div class="grid grid-cols-1 gap-3 mt-2">
                        <div class="flex items-center gap-3 bg-white/5 p-3 rounded-xl border border-white/10">
                            <i class="fa-solid fa-note-sticky text-amber-400 text-lg animate-pulse"></i>
                            <div>
                                <p class="text-amber-400 font-bold text-xs uppercase tracking-wider">Notas de Confianza</p>
                                <p class="text-[11px] text-slate-400">Guarda gustos personales (ej: café sin azúcar) para un trato VIP.</p>
                            </div>
                        </div>
                        <div class="flex items-center gap-3 bg-white/5 p-3 rounded-xl border border-white/10">
                            <i class="fa-solid fa-cake-candles text-pink-400 text-lg"></i>
                            <div>
                                <p class="text-pink-400 font-bold text-xs uppercase tracking-wider">Cumpleaños Hoy</p>
                                <p class="text-[11px] text-slate-400">Brillan en rosa. ¡Es el momento perfecto para un regalo o mensaje!</p>
                            </div>
                        </div>
                        <div class="flex items-center gap-3 bg-white/5 p-3 rounded-xl border border-white/10">
                            <i class="fa-solid fa-triangle-exclamation text-orange-400 text-lg"></i>
                            <div>
                                <p class="text-orange-400 font-bold text-xs uppercase tracking-wider">Clientes en Riesgo</p>
                                <p class="text-[11px] text-slate-400">No han vuelto en +30 días. ¡Contáctalos antes de perderlos!</p>
                            </div>
                        </div>
                    </div>
                </div>

                <hr class="border-white/5">

                <div class="p-4 bg-emerald-500/5 rounded-2xl border border-emerald-500/10">
                    <p class="mb-1"><strong class="text-emerald-500 italic">📥 Importación Inteligente:</strong></p>
                    <p class="text-[11px] mb-3 text-slate-400">Si el email ya existe, actualiza los datos; si no, crea un cliente nuevo.</p>
                    <a href="/admin/clientes/plantilla" class="flex items-center justify-center gap-2 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 py-2 rounded-xl transition-all font-bold text-xs border border-emerald-500/20">
                        <i class="fa-solid fa-download"></i> Obtener Plantilla Excel
                    </a>
                </div>

                <div class="flex flex-wrap gap-4 text-xs pt-2">
                    <p><strong class="text-sky-500 uppercase">📤 Exportar:</strong> Respaldo en Excel.</p>
                    <p><strong class="text-emerald-400 uppercase">💬 WhatsApp:</strong> Chat directo sin agendar.</p>
                </div>

            </div>
        `,
        icon: 'info',
        background: '#0f172a',
        color: '#ffffff',
        confirmButtonText: '¡Entendido, a vender!',
        confirmButtonColor: '#0ea5e9',
        customClass: {
            popup: 'rounded-[2.5rem] border border-white/10 shadow-2xl backdrop-blur-xl',
            title: 'pt-6'
        },
        showClass: {
            popup: 'animate__animated animate__fadeInUp animate__faster'
        },
        hideClass: {
            popup: 'animate__animated animate__fadeOutDown animate__faster'
        }
    });
}

// Ejecutar al cargar la página para mostrar el total inicial
document.addEventListener('DOMContentLoaded', actualizarContador);


// VARIABLE GLOBAL para saber por qué cliente vamos
let indiceEnvio = 0;

function aplicarFiltroRapido(tipo, elemento) {
    // 1. Cambiar estado visual de los botones (Tu lógica original)
    document.querySelectorAll('.btn-filtro').forEach(btn => {
        btn.classList.remove('active', 'bg-sky-500', 'text-white', 'shadow-lg', 'shadow-sky-500/20');
        btn.classList.add('bg-white/5', 'text-slate-400', 'border-white/10');
    });
    elemento.classList.add('active', 'bg-sky-500', 'text-white', 'shadow-lg', 'shadow-sky-500/20');
    elemento.classList.remove('bg-white/5', 'text-slate-400', 'border-white/10');

    // 2. Filtrar las filas
    const filas = document.querySelectorAll('.cliente-row');
    const busqueda = document.getElementById("buscador").value.toLowerCase();
    const banner = document.getElementById('banner-riesgo');
    let contadorRiesgoVisibles = 0;

    // Resetear el índice cuando cambias de filtro para empezar de cero
    indiceEnvio = 0;

    filas.forEach(fila => {
        const textoFila = fila.innerText.toUpperCase();
        const nombre = fila.querySelector('.cli-nombre').innerText.toLowerCase();
        
        let cumple = textoFila.includes('CUMPLEAÑOS');
        let riesgo = textoFila.includes('RIESGO');
        let nuevo = textoFila.includes('NUEVO');
        let coincideBusqueda = nombre.includes(busqueda);

        let coincideFiltro = false;
        if (tipo === 'todos') coincideFiltro = true;
        if (tipo === 'cumple' && cumple) coincideFiltro = true;
        if (tipo === 'riesgo' && riesgo) coincideFiltro = true;
        if (tipo === 'nuevo' && nuevo) coincideFiltro = true;

        const visible = (coincideFiltro && coincideBusqueda);
        fila.style.display = visible ? "" : "none";

        if (visible && tipo === 'riesgo') {
            contadorRiesgoVisibles++;
        }
    });

    // 3. ACTUALIZACIÓN: Mostrar contador en el banner
    if (banner) {
        if (tipo === 'riesgo' && contadorRiesgoVisibles > 0) {
            banner.classList.remove('hidden');
            // Buscamos un elemento para poner el texto (puedes añadir un id="total-riesgo" en tu HTML)
            const p = banner.querySelector('p');
            p.innerHTML = `Tienes <b class="text-white">${contadorRiesgoVisibles}</b> clientes inactivos para recuperar.`;
        } else {
            banner.classList.add('hidden');
        }
    }
}

function enviarRecordatorioMasivo() {
    const filasVisibles = Array.from(document.querySelectorAll('.cliente-row'))
                               .filter(f => f.style.display !== 'none');

    if (indiceEnvio < filasVisibles.length) {
        const filaActual = filasVisibles[indiceEnvio];
        const btnWhatsApp = filaActual.querySelector('a[href*="wa.me"]');

        if (btnWhatsApp) {
            window.open(btnWhatsApp.href, '_blank');
            marcarContactado(btnWhatsApp);
            
            indiceEnvio++;
            
            if (indiceEnvio < filasVisibles.length) {
                const proximaFila = filasVisibles[indiceEnvio];
                const proximoBtn = proximaFila.querySelector('a[href*="wa.me"]');
                
                document.querySelectorAll('.btn-brillante').forEach(b => b.classList.remove('btn-brillante'));
                
                if (proximoBtn) {
                    proximoBtn.classList.add('btn-brillante');
                    proximaFila.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            } else {
                // --- MENSAJE PERSISTENTE (ESPERA EL OK) ---
                Swal.fire({
                    title: '¡HECHO!',
                    text: 'Has terminado de contactar a todos los clientes de la lista seleccionada.',
                    icon: 'success',
                    background: '#1e293b',
                    color: '#f8fafc',
                    confirmButtonText: 'OK',
                    confirmButtonColor: '#10b981', // Color verde esmeralda
                    allowOutsideClick: false // No se cierra si tocan fuera
                });
                
                indiceEnvio = 0; // Reiniciamos el contador para la próxima vez
            }
        }
    }
}

function marcarContactado(enlace) {
    const fila = enlace.closest('.cliente-row');
    if (fila) {
        fila.classList.add('opacity-40', 'grayscale-[0.5]'); // Se vuelve grisáceo y tenue
        fila.style.borderLeft = "4px solid #10b981";
        enlace.classList.remove('btn-brillante');
    }
}

function filtrarClientes() {
    const activeBtn = document.querySelector('.btn-filtro.active');
    if (!activeBtn) return;
    const textoBoton = activeBtn.innerText.toLowerCase();
    const tipo = textoBoton.includes('cumple') ? 'cumple' : 
                 textoBoton.includes('riesgo') ? 'riesgo' :
                 textoBoton.includes('nuevo') ? 'nuevo' : 'todos';
    aplicarFiltroRapido(tipo, activeBtn);
}