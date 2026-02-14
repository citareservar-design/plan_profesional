console.log("historial.js cargado correctamente");

function aplicarFiltros() {
    const busqueda = document.getElementById('busquedaGeneral').value.toLowerCase();
    const estado = document.getElementById('filtroEstado').value.toLowerCase();
    const fecha = document.getElementById('filtroFecha').value;
    
    const filas = document.querySelectorAll('#tablaHistorial tr');

    filas.forEach(fila => {
        const textoFila = fila.innerText.toLowerCase();
        const estadoFila = fila.getAttribute('data-estado').toLowerCase();
        const fechaFila = fila.getAttribute('data-fecha');

        // Lógica de coincidencia
        const coincideTexto = textoFila.includes(busqueda);
        const coincideEstado = estado === "" || estadoFila === estado;
        const coincideFecha = fecha === "" || fechaFila === fecha;

        if (coincideTexto && coincideEstado && coincideFecha) {
            fila.style.display = "";
            fila.classList.add('animate-fade-in');
        } else {
            fila.style.display = "none";
        }
    });
}

// Ejemplo de cómo insertar una fila con Badges Dinámicos
function agregarFilaEjemplo(datos) {
    const tbody = document.getElementById('tablaHistorial');
    const badgeColor = {
        'completada': 'bg-emerald-500/10 text-emerald-400',
        'cancelada': 'bg-rose-500/10 text-rose-400',
        'confirmada': 'bg-sky-500/10 text-sky-400',
        'pendiente': 'bg-amber-500/10 text-amber-400'
    };

    const html = `
        <tr data-estado="${datos.estado}" data-fecha="${datos.fecha}" class="hover:bg-white/[0.02] transition-colors group">
            <td class="px-8 py-6">
                <p class="text-white font-bold">${datos.cliente}</p>
                <p class="text-[10px] text-slate-500 font-medium tracking-wide">ID: #RE-${datos.id}</p>
            </td>
            <td class="px-8 py-6 font-bold text-slate-300">${datos.servicio}</td>
            <td class="px-8 py-6">
                <p class="text-white font-bold">${datos.fecha}</p>
                <p class="text-xs text-slate-500">${datos.hora}</p>
            </td>
            <td class="px-8 py-6 font-black text-sky-500">$${datos.precio}</td>
            <td class="px-8 py-6">
                <span class="px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-wider ${badgeColor[datos.estado]}">
                    ${datos.estado}
                </span>
            </td>
        </tr>
    `;
    tbody.innerHTML += html;
}