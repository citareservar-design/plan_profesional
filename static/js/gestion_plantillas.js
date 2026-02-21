console.log("✅ Gestión de plantillas de WhatsApp cargada");


/**
 * Cierra el modal de plantillas
 */
function cerrarModal() {
    document.getElementById('modalPlantilla').classList.add('hidden');
    document.getElementById('modalPlantilla').classList.remove('flex');
}

/**
 * Carga los datos de una plantilla desde la DB y abre el modal para editar
 */
function editarPlantilla(id) {
    console.log("Editando plantilla ID:", id);
    
    fetch(`/admin/obtener_plantilla/${id}`)
    .then(response => {
        if (!response.ok) throw new Error("Error al obtener datos");
        return response.json();
    })
    .then(data => {
        // Rellenamos los campos con los datos que vienen del servidor (to_dict)
        document.getElementById('plan_id').value = data.id;
        document.getElementById('plan_nombre').value = data.nombre;
        document.getElementById('plan_mensaje').value = data.mensaje;
        document.getElementById('plan_tipo').value = data.tipo;
        
        document.getElementById('modalTitulo').innerHTML = 'Editar <span class="text-sky-500">Plantilla</span>';
        
        document.getElementById('modalPlantilla').classList.remove('hidden');
        document.getElementById('modalPlantilla').classList.add('flex');
    })
    .catch(error => {
        console.error("Error:", error);
        Swal.fire("Error", "No se pudo cargar la información de la plantilla", "error");
    });
}

/**
 * Guarda o Actualiza la plantilla en la base de datos
 */
function guardarPlantilla() {
    const data = {
        id: document.getElementById('plan_id').value,
        nombre: document.getElementById('plan_nombre').value,
        mensaje: document.getElementById('plan_mensaje').value,
        tipo: document.getElementById('plan_tipo').value
    };

    if (!data.nombre || !data.mensaje) {
        Swal.fire({
            icon: 'warning',
            title: 'Campos incompletos',
            text: 'Debes ingresar un nombre y un mensaje.',
            background: '#0f172a',
            color: '#fff'
        });
        return;
    }

    fetch('/admin/guardar_plantilla', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(res => {
        if (res.status === 'success') {
            Swal.fire({
                icon: 'success',
                title: '¡Logrado!',
                text: res.message,
                background: '#0f172a',
                color: '#fff'
            }).then(() => location.reload());
        } else {
            Swal.fire('Error', res.message, 'error');
        }
    })
    .catch(error => {
        console.error("Error:", error);
        Swal.fire("Error", "Ocurrió un problema al guardar", "error");
    });
}



/**
 * Inserta una variable en la posición actual del cursor dentro del mensaje
 * @param {string} variable - Ejemplo: '{cliente}'
 */
function insertarVariable(variable) {
    const textarea = document.getElementById('plan_mensaje');
    
    // Forzamos el foco para asegurar que la posición del cursor sea válida
    textarea.focus();

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const textoActual = textarea.value;

    // Insertar el texto
    textarea.value = textoActual.substring(0, start) + variable + textoActual.substring(end);

    // Mover el cursor justo después de la variable insertada
    const nuevaPosicion = start + variable.length;
    textarea.setSelectionRange(nuevaPosicion, nuevaPosicion);
}