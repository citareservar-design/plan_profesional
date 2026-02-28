console.log('CARGO EL ARCHIVO JS DE CLIENTES')

// --- LÓGICA MODALES ---
function abrirModalEditar(cliente) {
    const modal = document.getElementById('modalEditar');
    if (!modal) return; 

    // --- CAMBIO AQUÍ: Ya no multiplicamos, usamos el valor directo ---
    const descuentoVisible = cliente.descuento || 0; 

    const fieldMap = {
        'edit_cli_id': cliente.id,
        'edit_nombre': cliente.nombre,
        'edit_alias': cliente.alias || '',
        'edit_email': cliente.email || '',
        'edit_telefono': cliente.telefono || '',
        'edit_fecha_nacimiento': cliente.fecha_nacimiento || '',
        'edit_descuento': descuentoVisible, 
        'edit_descuento_cantidad': cliente.descuento_cantidad || 0,
        'edit_notas_personales': cliente.notas_personales || ''
    };

    for (const [id, value] of Object.entries(fieldMap)) {
        const input = document.getElementById(id);
        if (input) input.value = value;
    }

    modal.classList.remove('hidden');
    modal.classList.add('flex'); 
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

    // --- LÓGICA CORREGIDA: ENVIAR EL NÚMERO ENTERO ---
    // Obtenemos el valor del input (ej: 20) directamente sin dividir
    const valorDescuentoInput = document.getElementById('edit_descuento')?.value || 0;
    const descuentoParaBD = parseFloat(valorDescuentoInput); 

    // 2. Recolectar datos del formulario
    const data = {
        nombre: document.getElementById('edit_nombre').value,
        alias: document.getElementById('edit_alias').value,
        email: document.getElementById('edit_email').value,
        telefono: document.getElementById('edit_telefono').value,
        fecha_nacimiento: document.getElementById('edit_fecha_nacimiento').value,
        notas_personales: document.getElementById('edit_notas_personales')?.value || '',
        descuento: descuentoParaBD, // Enviamos el entero (Ej: 20)
        descuento_cantidad: parseInt(document.getElementById('edit_descuento_cantidad')?.value || 0)
    };

    // 3. Definir URL
    const url = `/admin/api/cliente/editar/${cliId}`;
    console.log("📤 Enviando a la BD:", data);

    // 4. Ejecutar la petición
    fetch(url, {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json' 
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Error en el servidor (Código: ${response.status})`);
        }
        return response.json();
    })
    .then(result => {
        if (result.status === 'success') {
            Swal.fire({
                title: '¡Actualizado!',
                text: 'Los datos del cliente se han guardado con éxito.',
                icon: 'success',
                background: '#1e293b',
                color: '#fff',
                timer: 1500,
                showConfirmButton: false
            }).then(() => {
                location.reload(); 
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
        console.error('Error detectado:', error);
        Swal.fire({
            title: 'Error de Conexión',
            text: `No se pudo conectar con el servidor. ${error.message}`,
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
        notas_personales: inputNotas ? inputNotas.value : '',
        descuento: document.getElementById('new_descuento')?.value || 0,
        descuento_cantidad: document.getElementById('new_descuento_cantidad')?.value || 0
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



// Ejecutar al cargar la página para mostrar el total inicial
document.addEventListener('DOMContentLoaded', actualizarContador);


// VARIABLE GLOBAL para saber por qué cliente vamos
let indiceEnvio = 0;

function aplicarFiltroRapido(tipo, elemento) {
    // 1. Cambiar estado visual de los botones
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

    indiceEnvio = 0;

    filas.forEach(fila => {
        const nombre = fila.querySelector('.cli-nombre').innerText.toLowerCase();
        
        // --- CIRUGÍA AQUÍ: Usamos los data-attributes que enviamos desde Flask ---
        const esCumpleHoy = fila.dataset.cumple === 'true';
        const esPreCumple = fila.dataset.precumple === 'true';
        const esRiesgo    = fila.dataset.riesgo === 'true';
        const coincideBusqueda = nombre.includes(busqueda);

        let coincideFiltro = false;

        if (tipo === 'todos') {
            coincideFiltro = true;
        } else if (tipo === 'cumple-hoy') {
            coincideFiltro = esCumpleHoy;
        } else if (tipo === 'pre-cumple') {
            coincideFiltro = esPreCumple;
        } else if (tipo === 'riesgo') {
            coincideFiltro = esRiesgo;
        }

        const visible = (coincideFiltro && coincideBusqueda);
        fila.style.display = visible ? "" : "none";

        if (visible && tipo === 'riesgo') {
            contadorRiesgoVisibles++;
        }
    });

    // 3. Banner de Riesgo
    if (banner) {
        if (tipo === 'riesgo' && contadorRiesgoVisibles > 0) {
            banner.classList.remove('hidden');
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
        fila.classList.add('opacity-50'); // Menos agresivo que 40
        // Mantenemos el color que indica por qué se le contactó
        if (fila.dataset.cumple === 'true') fila.style.borderLeft = "4px solid #ec4899";
        else if (fila.dataset.precumple === 'true') fila.style.borderLeft = "4px solid #0ea5e9";
        else fila.style.borderLeft = "4px solid #10b981";
        
        enlace.classList.remove('btn-brillante', 'animate-pulse');
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

// --- LÓGICA DE WHATSAPP DINÁMICO (SELECTOR DE PLANTILLAS) ---

// Añadimos esPreCumple como quinto parámetro

function abrirSelectorPlantillas(id, nombre, esCumple, telefono, esPreCumple, esRiesgo) {
    const lista = document.getElementById('listaPlantillasDisponibles');
    
    // 1. Mostrar estado de carga
    lista.innerHTML = `
        <div class="text-center py-8 text-slate-500">
            <i class="fa-solid fa-circle-notch animate-spin text-2xl mb-2"></i>
            <p class="text-xs">Cargando plantillas personalizadas...</p>
        </div>`;
    
    document.getElementById('modalSelectorPlantillas').classList.remove('hidden');
    document.getElementById('modalSelectorPlantillas').classList.add('flex');

    // 2. Obtener plantillas desde la API
    fetch('/admin/obtener_plantillas')
        .then(response => response.json())
        .then(data => {
            lista.innerHTML = '';
            const nombreEmpresa = data.empresa;
            const plantillas = data.plantillas;

            // 3. FILTRADO ESTRICTO (Aquí es donde estaba el error)
            const filtradas = plantillas.filter(p => {
                const tipo = p.plan_tipo ? p.plan_tipo.toLowerCase() : '';
                
                if (esCumple) {
                    return tipo === 'cumpleaños';
                } else if (esPreCumple) {
                    return tipo === 'pre-cumple';
                } else if (esRiesgo) {
                    // CAMBIO AQUÍ: Solo mostrar tipo 'ausente' para clientes en riesgo
                    return tipo === 'ausente'; 
                } else {
                    // Para clientes normales, ocultamos todas las especiales
                    return tipo !== 'cumpleaños' && tipo !== 'pre-cumple' && tipo !== 'ausente';
                }
            });

            if (filtradas.length === 0) {
                lista.innerHTML = '<div class="text-center py-8 text-slate-500 text-xs">No hay plantillas configuradas para este estado.</div>';
                return;
            }

            // 4. Renderizado
            filtradas.forEach(plan => {
                let msj = plan.plan_mensaje;
                msj = msj.replace(/{cliente}/gi, nombre);
                msj = msj.replace(/{empresa}/gi, nombreEmpresa);
                msj = msj.replace(/{fecha}/gi, new Date().toLocaleDateString());

                const btn = document.createElement('button');
                
                // Estilos dinámicos
                let colorBorde = "border-l-emerald-500";
                let colorTexto = "text-emerald-500";
                let efectoExtra = ""; 
                let icono = "📱";

                if (esCumple) {
                    colorBorde = "border-l-pink-500";
                    colorTexto = "text-pink-500";
                    icono = "🎂";
                } else if (esPreCumple) {
                    colorBorde = "border-l-sky-500";
                    colorTexto = "text-sky-500";
                    icono = "✨";
                } else if (esRiesgo) {
                    // Estilo naranja para Riesgo/Ausente
                    colorBorde = "border-l-orange-500";
                    colorTexto = "text-orange-500";
                    efectoExtra = "shadow-lg shadow-orange-500/20";
                    icono = "⚠️";
                }

                btn.className = `w-full p-4 rounded-2xl bg-white/5 border border-white/10 text-left hover:bg-white/10 transition-all mb-3 group border-l-4 ${colorBorde} ${efectoExtra}`;
                
                btn.onclick = () => {
                    window.open(`https://wa.me/57${telefono}?text=${encodeURIComponent(msj)}`, '_blank');
                    cerrarSelector();
                    const fila = document.getElementById(`cli-${id}`);
                    if (fila) {
                        const btnOriginal = fila.querySelector('button[onclick*="abrirSelector"]');
                        if (btnOriginal) marcarContactado(btnOriginal);
                    }
                };

                btn.innerHTML = `
                    <div class="${colorTexto} font-black text-[10px] uppercase tracking-wider mb-1 flex items-center gap-2">
                        <span>${icono}</span> ${plan.plan_nombre}
                    </div>
                    <div class="text-slate-300 text-xs leading-relaxed">${msj}</div>
                `;
                lista.appendChild(btn);
            });
        });
}



/**
 * Envía la orden al servidor para procesar el mensaje (reemplazar etiquetas) y abre el link
 */
function enviarWhatsAppConPlantilla(clienteId, plantillaId) {
    // Usamos la API que procesa el mensaje (reemplaza {nombre}, etc)
    fetch(`/api/preparar_mensaje_whatsapp?cliente_id=${clienteId}&plantilla_id=${plantillaId}`)
    .then(res => res.json())
    .then(data => {
        if(data.status === 'success') {
            window.open(data.link, '_blank');
            cerrarSelector();
            
            // Reutilizamos tu función de marcar contactado
            const fila = document.getElementById(`cli-${clienteId}`);
            if (fila) {
                const btnOriginal = fila.querySelector('button[onclick*="abrirSelector"]');
                if (btnOriginal) marcarContactado(btnOriginal);
            }
        } else {
            Swal.fire('Error', 'No se pudo generar el mensaje: ' + data.message, 'error');
        }
    })
    .catch(err => {
        console.error(err);
        Swal.fire('Error', 'Hubo un problema al procesar el envío.', 'error');
    });
}

function cerrarSelector() {
    const modal = document.getElementById('modalSelectorPlantillas');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
}



async function aplicarDescuentoMasivo() {
    let porcentaje = document.getElementById('desc_porcentaje').value;
    const cantidad = document.getElementById('desc_cantidad').value;

    if (!porcentaje || !cantidad) {
        return Swal.fire('Error', 'Ingresa porcentaje y cantidad', 'warning');
    }

    // --- CIRUGÍA DE PORCENTAJE ---
    let valorFinalDesc = parseFloat(porcentaje);
    // Si puso 20, lo convertimos a 0.20. Si puso 0.20, lo dejamos igual.
    if (valorFinalDesc > 1) {
        valorFinalDesc = valorFinalDesc / 100;
    }

    const confirmacion = await Swal.fire({
        title: '¿Lanzar Campaña?',
        text: `Aplicarás ${Math.round(valorFinalDesc * 100)}% de descuento por ${cantidad} citas.`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: '¡Lanzar ahora!',
        confirmButtonColor: '#10b981'
    });

    if (confirmacion.isConfirmed) {
        try {
            // CAMBIO CLAVE AQUÍ: Asegúrate de que la ruta sea /admin/... 
            // porque estás usando admin_bp
            const response = await fetch('/admin/aplicar_descuento_general', { 
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ 
                    porcentaje: valorFinalDesc, 
                    cantidad: parseInt(cantidad) 
                })
            });
            
            // Si la respuesta no es OK (ej: 404), esto atrapará el error antes del JSON
            if (!response.ok) {
                const textError = await response.text();
                console.error("Respuesta del servidor:", textError);
                throw new Error(`Servidor respondió con código ${response.status}`);
            }

            const res = await response.json();
            if (res.status === 'success') {
                Swal.fire('¡Listo!', res.message, 'success').then(() => location.reload());
            }
        } catch (e) {
            console.error("Error detallado:", e);
            Swal.fire('Error de Ruta', 'El servidor no encontró la dirección /admin/aplicar_descuento_general', 'error');
        }
    }
}