console.log("JS DE AGENDA CARGADO");

window.addEventListener('load', function() {
    // --- LÓGICA DE PANTALLA DE CARGA (INTRO) ---
    const progressBar = document.getElementById('progress-bar');
    const counter = document.getElementById('counter');
    const intro = document.getElementById('intro-screen');
    const main = document.getElementById('main-content');
    
    let currentProgress = 0;
    
    const updateProgress = () => {
        const increment = (100 - currentProgress) * 0.20; 
        currentProgress += increment;

        if (currentProgress > 99.5) {
            currentProgress = 100;
            progressBar.style.width = '100%';
            counter.innerText = '100%';
            finishLoading();
            return;
        }

        progressBar.style.width = currentProgress + '%';
        counter.innerText = Math.floor(currentProgress) + '%';
        requestAnimationFrame(updateProgress);
    };

    const finishLoading = () => {
        setTimeout(() => {
            intro.style.transition = 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
            intro.style.opacity = '0';
            intro.style.transform = 'scale(1.05)'; 

            setTimeout(() => {
                intro.style.display = 'none';
                main.style.display = 'block'; 
                requestAnimationFrame(() => {
                    main.style.transition = 'opacity 0.8s ease, transform 0.8s cubic-bezier(0.16, 1, 0.3, 1)';
                    main.style.opacity = '1';
                    main.style.transform = 'translateY(0)';
                });
            }, 600);
        }, 300);
    };

    requestAnimationFrame(updateProgress);
});

// --- LÓGICA DE HORARIOS Y CITAS ---
const fechaInput = document.getElementById('fecha_reserva');
const servicioSelect = document.getElementById('select_servicio');
const gridHoras = document.getElementById('grid_horas');
const inputOcultoHora = document.getElementById('input_hora_seleccionada');

function bloquearDiasAnteriores() {
    const hoy = new Date();
    const fechaMinima = hoy.toISOString().split('T')[0];
    if (fechaInput) {
        fechaInput.setAttribute('min', fechaMinima);
    }
}

// ESTA FUNCIÓN AHORA CONECTA CON EL GRID DE BOTONES
function actualizarTodo() {
    const fecha = fechaInput.value;
    const servicioId = servicioSelect.value;

    if (fecha && servicioId && servicioId !== "") {
        // Estado de carga visual en el grid
        gridHoras.innerHTML = `
            <div class="col-span-full py-8 text-center animate-pulse">
                <p class="text-sky-500 font-bold text-sm">Buscando turnos...</p>
            </div>`;

        fetch(`/api/horas-disponibles?fecha=${fecha}&servicio_id=${servicioId}`)
            .then(res => res.json())
            .then(data => {
                if (data.bloqueado) {
                    Swal.fire({
                        title: 'Día no disponible',
                        text: data.mensaje,
                        icon: 'warning',
                        confirmButtonColor: '#0ea5e9'
                    });
                    fechaInput.value = ''; 
                    gridHoras.innerHTML = '';
                    return;
                }
                
                // Llamamos a la función que dibuja los botones
                renderizarHoras(data.horas);
            })
            .catch(err => {
                console.error("Error:", err);
                gridHoras.innerHTML = '<p class="col-span-full text-center text-rose-500 text-xs">Error de conexión</p>';
            });
    }
}

function renderizarHoras(horas) {
    gridHoras.innerHTML = ''; 
    inputOcultoHora.value = ''; // Resetear selección previa

    if (!horas || horas.length === 0) {
        gridHoras.innerHTML = `
            <div class="col-span-full text-center p-6 bg-rose-50 rounded-2xl border border-rose-100">
                <i class="fa-solid fa-clock-slash text-rose-300 mb-2 text-xl"></i>
                <p class="text-rose-500 text-xs font-bold">No hay turnos para este servicio</p>
            </div>`;
        return;
    }

    horas.forEach(hora => {
        const boton = document.createElement('button');
        boton.type = 'button';
        boton.className = "py-3.5 px-2 rounded-2xl border-2 border-slate-100 bg-white text-slate-700 font-bold text-sm transition-all hover:border-sky-500 hover:text-sky-600 active:scale-95 shadow-sm";
        boton.innerText = hora.formato;
        
        boton.onclick = () => {
            // Estética de selección
            document.querySelectorAll('#grid_horas button').forEach(b => {
                b.classList.replace('bg-sky-500', 'bg-white');
                b.classList.replace('text-white', 'text-slate-700');
                b.classList.replace('border-sky-500', 'border-slate-100');
            });

            boton.classList.replace('bg-white', 'bg-sky-500');
            boton.classList.replace('text-slate-700', 'text-white');
            boton.classList.replace('border-slate-100', 'border-sky-500');
            boton.classList.add('shadow-lg', 'shadow-sky-200');
            
            // Guardar valor real para el formulario
            inputOcultoHora.value = hora.valor;
        };

        gridHoras.appendChild(boton);
    });
}

// INICIALIZACIÓN
bloquearDiasAnteriores();
fechaInput.addEventListener('change', actualizarTodo);
servicioSelect.addEventListener('change', actualizarTodo);



document.addEventListener('DOMContentLoaded', function() {
    console.log("🚀 Script de Reserva con Auto-guardado Iniciado");

    const formReserva = document.getElementById('form-reserva');
    const loader = document.getElementById('loader-confirmacion');
    const progressBar = document.getElementById('progress-bar-confirm');
    const loaderMsg = document.getElementById('loader-msg');

    // --- 1. LÓGICA DE LOCALSTORAGE (Usando Atributo Name) ---
    const camposConfig = ['nombre', 'email', 'telefono'];

    camposConfig.forEach(nombreCampo => {
        // Buscamos por atributo name ya que no hay ID
        const input = document.querySelector(`[name="${nombreCampo}"]`);
        
        if (input) {
            // A. CARGAR: Si hay algo guardado en el navegador, lo ponemos en el input
            const valorGuardado = localStorage.getItem('cli_' + nombreCampo);
            if (valorGuardado) {
                input.value = valorGuardado;
                console.log(`✅ ${nombreCampo} recuperado del navegador`);
            }

            // B. GUARDAR: Cada vez que el usuario escribe, guardamos al instante
            input.addEventListener('input', () => {
                localStorage.setItem('cli_' + nombreCampo, input.value);
            });
        }
    });

    // --- 2. LÓGICA DE ENVÍO Y LOADER ---
    if (formReserva) {
        formReserva.addEventListener('submit', async function(e) {
            e.preventDefault(); // Detenemos envío tradicional
            console.log("📡 Iniciando proceso de reserva...");

            // Mostrar el loader
            if (loader) {
                loader.classList.remove('hidden');
                loader.classList.add('flex');
            }

            // Animación de barra de progreso
            let progreso = 0;
            const intervalo = setInterval(() => {
                if (progreso < 85) {
                    progreso += 5;
                    if (progressBar) progressBar.style.width = progreso + "%";
                    
                    if (loaderMsg) {
                        if (progreso > 40) loaderMsg.innerText = "Validando disponibilidad...";
                        if (progreso > 70) loaderMsg.innerText = "Casi listo...";
                    }
                }
            }, 100);

            // Preparar datos para el envío
            const formData = new FormData(formReserva);
            const datos = Object.fromEntries(formData.entries());

            try {
                const response = await fetch(formReserva.action, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(datos)
                });

                if (response.ok) {
                    clearInterval(intervalo);
                    if (progressBar) progressBar.style.width = "100%";
                    if (loaderMsg) loaderMsg.innerHTML = "<span class='text-emerald-500 font-bold'>¡Cita Confirmada!</span>";
                    
                    // Redirigir al éxito
                    setTimeout(() => {
                        window.location.href = window.location.origin + "/reserva_exitosa";
                    }, 800);
                } else {
                    const errorData = await response.json();
                    throw new Error(errorData.message || "Error al procesar la reserva");
                }
            } catch (error) {
                clearInterval(intervalo);
                if (loader) {
                    loader.classList.add('hidden');
                    loader.classList.remove('flex');
                }
                
                // @ts-ignore (Si usas SweetAlert)
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: error.message,
                    confirmButtonColor: '#0f172a'
                });
            }
        });
    }
});