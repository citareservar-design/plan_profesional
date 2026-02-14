console.log('CARGO EL JS DE SERVICIOS - VERSION PREMIUM');

/**
 * Convierte minutos a un formato legible
 */
function formatearTiempoHumano(minutos) {
    if (!minutos || minutos < 0) return "0 min";
    const horas = Math.floor(minutos / 60);
    const minsRestantes = minutos % 60;
    if (horas === 0) return `${minsRestantes} min`;
    if (minsRestantes === 0) return `${horas} ${horas === 1 ? 'hr' : 'hrs'}`;
    if (minsRestantes === 30) return `${horas}.5 hrs`;
    return `${horas}h ${minsRestantes}min`;
}

// Función para actualizar el texto de ayuda debajo del input de tiempo
function actualizarAyudaTiempo(minutos) {
    const ayuda = document.getElementById('ayuda_tiempo');
    if (!ayuda) return;
    if (minutos >= 60) {
        const horas = (minutos / 60).toFixed(1);
        ayuda.innerText = `≈ ${horas} horas`;
        ayuda.classList.replace('opacity-0', 'opacity-100');
    } else {
        ayuda.classList.replace('opacity-100', 'opacity-0');
    }
}

function abrirNuevo() {
    document.getElementById('modal-titulo').innerHTML = 'Nuevo <span class="text-sky-500">Servicio</span>';
    const form = document.getElementById('form-servicio');
    form.action = "/admin/servicios/nuevo"; 
    form.reset();
    actualizarAyudaTiempo(0); // Resetear ayuda
    document.getElementById('modal-servicio').classList.remove('hidden');
    document.getElementById('modal-servicio').classList.add('flex');
}

function abrirEditar(id, nombre, precio, tiempo) {
    const modal = document.getElementById('modal-servicio');
    const form = document.getElementById('form-servicio');
    
    document.getElementById('modal-titulo').innerHTML = 'Editar <span class="text-sky-500">Servicio</span>';
    form.action = `/admin/servicios/editar/${id}`;
    
    document.getElementById('input_nombre').value = nombre;
    document.getElementById('input_tiempo').value = tiempo;
    
    // Actualizar la ayuda de horas al abrir
    actualizarAyudaTiempo(parseInt(tiempo));
    
    let precioLimpio = Math.round(parseFloat(precio.toString().replace(/[^0-9.]/g, '')));
    const inputPrecio = document.getElementById('input_precio');
    inputPrecio.value = precioLimpio;
    formatearMiles(inputPrecio);

    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

// --- NUEVA FUNCIÓN PARA INACTIVAR ---
function eliminarServicio(id) {
    let timerInterval;
    
    Swal.fire({
        title: '<span style="color: #f87171;">¿Confirmar Inactivación?</span>',
        html: `
            <div class="text-left text-sm" style="color: #cbd5e1; line-height: 1.5;">
                <p class="mb-3"><strong>Estimado propietario:</strong></p>
                <p>Está a punto de inactivar este servicio. Tenga en cuenta lo siguiente:</p>
                <ul style="margin-top: 10px; list-style-type: disc; margin-left: 20px;">
                    <li>Se <b>eliminará</b> de todos los empleados que lo tienen asignado.</li>
                    <li>Ya no estará disponible para <b>nuevas reservas</b> de clientes.</li>
                </ul>
                <p class="mt-3" style="color: #94a3b8;">El botón de confirmación se habilitará en <b><span id="countdown">5</span></b> segundos...</p>
            </div>
        `,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Confirmar (5)', // Texto inicial
        cancelButtonText: 'Cancelar',
        confirmButtonColor: '#ef4444', // Rojo para advertencia
        cancelButtonColor: '#334155',
        background: '#0f172a',
        color: '#fff',
        allowOutsideClick: false,
        didOpen: () => {
            const confirmBtn = Swal.getConfirmButton();
            confirmBtn.disabled = true; // Deshabilitamos el botón al abrir
            
            let timeLeft = 5;
            const timer = setInterval(() => {
                timeLeft--;
                if (timeLeft > 0) {
                    confirmBtn.innerText = `Confirmar (${timeLeft})`;
                    document.getElementById('countdown').innerText = timeLeft;
                } else {
                    clearInterval(timer);
                    confirmBtn.disabled = false;
                    confirmBtn.innerText = 'Sí, inactivar servicio';
                    document.getElementById('countdown').innerText = '0';
                }
            }, 1000);
        }
    }).then((result) => {
        if (result.isConfirmed) {
            // Tu lógica de fetch que ya funciona
            fetch(`/admin/api/servicio/inactivar/${id}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
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
                    }).then(() => location.reload());
                }
            })
            .catch(err => Swal.fire('Error', 'No se pudo procesar la solicitud', 'error'));
        }
    });
}

function cerrarModal() {
    const modal = document.getElementById('modal-servicio');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
}

function formatearMiles(input) {
    let valor = input.value.replace(/\D/g, ""); 
    if (valor !== "") {
        input.value = new Intl.NumberFormat('de-DE').format(valor);
    }
}

// Listener para el input de tiempo
document.getElementById('input_tiempo')?.addEventListener('input', function(e) {
    const min = parseInt(e.target.value);
    const ayuda = document.getElementById('ayuda_tiempo');
    
    if (!min) {
        ayuda.classList.add('opacity-0');
        return;
    }

    if (min % 30 !== 0) {
        ayuda.innerText = "❌ Debe ser múltiplo de 30 min";
        ayuda.classList.remove('text-sky-500');
        ayuda.classList.add('text-rose-500', 'opacity-100');
    } else {
        const horas = (min / 60).toFixed(1);
        ayuda.innerText = `✅ Equivale a ${horas} horas`;
        ayuda.classList.remove('text-rose-500');
        ayuda.classList.add('text-sky-500', 'opacity-100');
    }
});



function reactivarServicio(id) {
    Swal.fire({
        title: '¿Reactivar servicio?',
        text: "Este servicio volverá a aparecer en tu lista principal y en las reservas.",
        icon: 'question',
        showCancelButton: true,
        background: '#0f172a',
        color: '#fff',
        confirmButtonColor: '#10b981', // Verde esmeralda
        cancelButtonColor: '#334155',
        confirmButtonText: 'Sí, reactivar',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            fetch(`/admin/api/servicio/reactivar/${id}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'success') {
                    Swal.fire({
                        title: '¡Reactivado!',
                        text: data.message,
                        icon: 'success',
                        background: '#0f172a',
                        color: '#fff',
                        timer: 1500,
                        showConfirmButton: false
                    }).then(() => location.reload());
                }
            });
        }
    });
}