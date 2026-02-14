// 1. PRIORIDAD MÁXIMA: RENDERIZADO DEL GRÁFICO DE DONA
(function() {
    const initChart = () => {
        try {
            const canvasEl = document.getElementById('canvasEficiencia');
            const dataDiv = document.getElementById('data-eficiencia');
            
            if (!canvasEl || !dataDiv) return;

            // 1. Extraer datos (Sincronizados exactamente con los data-attributes del HTML)
            const pend = parseInt(dataDiv.dataset.pendiente) || 0;
            const conf = parseInt(dataDiv.dataset.confirmada) || 0;
            const real = parseInt(dataDiv.dataset.realizada) || 0;   // Estado: Trabajado, no pagado
            const comp = parseInt(dataDiv.dataset.completada) || 0;  // Estado: Liquidado
            const canc = parseInt(dataDiv.dataset.canceladas) || 0;

            // 2. Lógica de Agrupación para la Estadística
            // Sumamos Realizada + Completada para que el gráfico no cambie al cerrar caja
            const totalLogradas = real + comp; 
            const totalCitas = pend + conf + totalLogradas + canc;
            
            const hasData = totalCitas > 0;
            
            // Si no hay datos, mostramos un aro gris neutro
            const finalData = hasData ? [pend, conf, totalLogradas, canc] : [1];
            const finalColors = hasData 
                ? ['#f59e0b', '#3b82f6', '#10b981', '#f43f5e'] // Amber, Blue, Emerald, Rose
                : ['#334155']; // Slate neutro

            // 3. Crear instancia de Chart.js
            new Chart(canvasEl.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: ['Pendientes', 'Confirmadas', 'Logradas', 'Canceladas'],
                    datasets: [{
                        data: finalData,
                        backgroundColor: finalColors,
                        borderWidth: 0,
                        borderRadius: hasData ? 10 : 0,
                        spacing: hasData ? 5 : 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '80%', 
                    plugins: {
                        legend: { display: false },
                        tooltip: { 
                            enabled: hasData,
                            backgroundColor: '#0f172a',
                            titleFont: { size: 14, weight: 'bold' },
                            callbacks: {
                                label: function(context) {
                                    const value = context.raw || 0;
                                    const percentage = Math.round((value / totalCitas) * 100);
                                    return ` ${context.label}: ${value} (${percentage}%)`;
                                }
                            }
                        }
                    }
                }
            });
            
            console.log("✅ Gráfico de AgendApp sincronizado (Realizadas + Completadas).");
        } catch (error) {
            console.error("❌ Error al crear el gráfico:", error);
        }
    };

    if (document.readyState === 'interactive' || document.readyState === 'complete') {
        initChart();
    } else {
        document.addEventListener('DOMContentLoaded', initChart);
    }
})();

// 2. CONFIGURACIÓN DE ALERTAS DE NUEVAS RESERVAS
const sonidoUrl = 'https://assets.mixkit.co/active_storage/sfx/2358/2358-preview.mp3';

async function verificarNuevasReservas() {
    try {
        const response = await fetch('/admin/check_last_reserva');
        
        if (!response.ok) {
            console.error("Error en la respuesta del servidor");
            return;
        }

        const data = await response.json();
        const idActual = data.id;
        
        const idPrevio = localStorage.getItem('ultimo_id_conocido');
        const alertaCerradaId = localStorage.getItem('alerta_vista_id');

        if (idPrevio === null) {
            localStorage.setItem('ultimo_id_conocido', idActual);
            localStorage.setItem('alerta_vista_id', idActual);
            return;
        }

        // Lógica de Alerta de nueva cita
        if (idActual > parseInt(idPrevio) || (idActual > 0 && alertaCerradaId != idActual)) {
            if (Swal.isVisible()) return;

            localStorage.setItem('ultimo_id_conocido', idActual);

            // Sonido (requiere interacción previa del usuario con la página)
            const audio = new Audio(sonidoUrl);
            audio.play().catch(e => console.log("Audio bloqueado: haz clic en la página."));

            Swal.fire({
                title: '¡NUEVA RESERVA!',
                html: `
                    <div class="text-left mt-4" style="font-family: sans-serif;">
                        <p class="mb-2"><b>👤 Cliente:</b> ${data.cliente}</p>
                        <p class="mb-2"><b>✂️ Servicio:</b> ${data.servicio}</p>
                        <hr class="my-3">
                        <p class="text-xs text-gray-500 italic">La pantalla se actualizará al cerrar este mensaje.</p>
                    </div>
                `,
                icon: 'success',
                confirmButtonText: 'OK!',
                confirmButtonColor: '#4f46e5',
                allowOutsideClick: false
            }).then((result) => {
                if (result.isConfirmed) {
                    localStorage.setItem('alerta_vista_id', idActual);
                    location.reload(); // Recarga controlada por el usuario
                }
            });

            document.title = "🔴 ¡NUEVA CITA!";
        }
    } catch (error) {
        console.error("Fallo al conectar con el servidor:", error);
    }
}

// 3. CONTROL DE CICLOS (SIN PESTAÑEOS)
document.addEventListener('DOMContentLoaded', () => {
    console.log("🚀 Dashboard cargado correctamente.");
    
    // Primera verificación al entrar
    verificarNuevasReservas();
    
    // Ciclo 1: Revisar si hay nuevas reservas cada 60 segundos (SILENCIOSO)
    setInterval(verificarNuevasReservas, 60000);

    // Ciclo 2: Refresco total de seguridad cada 60 segundos
    // PERO solo si el administrador no está viendo una alerta de reserva
    setInterval(() => {
        if (!Swal.isVisible()) {
            console.log("🔄 Actualizando dashboard por tiempo transcurrido...");
            location.reload();
        }
    }, 60000); 
});



document.addEventListener('DOMContentLoaded', function() {
    const ctx = document.getElementById('calorChart').getContext('2d');
    
    // Recibimos los datos reales de Python/Jinja
const labels = labelsFlujoReal; // Ya no uses {{ ... }} aquí
const data = dataFlujoReal;     // Ya no uses {{ ... }} aquí
    
    // Encontrar la hora con más citas para resaltar
    const maxVal = Math.max(...data);
    const peakText = maxVal > 0 
        ? `Hora pico hoy: ${labels[data.indexOf(maxVal)]}` 
        : "Día sin citas registradas aún";
    
    document.getElementById('peak-hour-text').innerText = peakText;

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Citas',
                data: data,
                backgroundColor: (context) => {
                    const val = context.raw;
                    if (val === 0) return 'rgba(255, 255, 255, 0.05)'; // Barra vacía
                    return val === maxVal ? '#f59e0b' : 'rgba(245, 158, 11, 0.3)'; // Resaltar pico en naranja
                },
                borderRadius: 8,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#1e293b',
                    titleColor: '#fff',
                    bodyColor: '#cbd5e1',
                    callbacks: {
                        label: (item) => ` ${item.raw} citas`
                    }
                }
            },
                scales: {
                x: {
                    grid: { display: false },
                    ticks: { 
                        color: '#64748b', 
                        font: { size: 9 },
                        autoSkip: false, // ¡IMPORTANTE! No saltar etiquetas automáticamente
                        maxRotation: 0,
                        callback: function(val, index) {
                            // Mostrar la hora completa (08:00, 08:30) solo si hay espacio
                            // O puedes dejarlo así para que se vean todas:
                            return this.getLabelForValue(val);
                        }
                    }
                },
                y: {
                    beginAtZero: true,
                    display: false 
                }
            }
        }
    });
});


