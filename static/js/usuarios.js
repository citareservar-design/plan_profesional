console.log('CRAGANDO JS DE USUARIOS')



// Función para Resetear el Modal y ponerlo en modo "NUEVO"
function abrirModalNuevo() {
    document.getElementById('modalTitulo').innerHTML = 'Nuevo <span class="text-sky-500">Usuario</span>';
    
    // CORRECCIÓN: Usar la ruta manual o asegurar que Jinja la renderice una sola vez
    document.getElementById('formUsuario').action = "/admin/usuarios/crear"; 
    
    document.getElementById('formUsuario').reset();
    document.getElementById('usu_password').required = true;
    document.getElementById('btnGuardar').innerText = 'Crear Usuario';
    document.getElementById('modalUsuario').classList.remove('hidden');
}

async function editarUsuario(id) {
    try {
        const response = await fetch(`/admin/usuarios/get/${id}`);
        if (!response.ok) throw new Error("Usuario no encontrado");
        const data = await response.json();

        // 1. Cambiar textos y acción del formulario
        document.getElementById('modalTitulo').innerHTML = 'Editar <span class="text-sky-500">Usuario</span>';
        document.getElementById('btnGuardar').innerText = 'Guardar Cambios';
        document.getElementById('formUsuario').action = `/admin/usuarios/editar/${id}`;
        
        // 2. Llenar inputs de texto
        document.getElementById('usu_login').value = data.usu_login;
        document.getElementById('usu_nombre').value = data.usu_nombre;
        document.getElementById('usu_password').required = false; 
        document.getElementById('usu_password').placeholder = "Dejar en blanco para no cambiar";

        // 3. MARCAR PERMISOS (Aquí estaba el fallo)
        const checkboxes = document.querySelectorAll('.permiso-checkbox');
        checkboxes.forEach(cb => {
            // Comprobamos si el valor del checkbox (ej: 'ver_estadisticas') 
            // está dentro del array que envió el servidor
            cb.checked = data.permisos.includes(cb.value);
            
            // Opcional: Si usas clases de Tailwind para el borde o color cuando está checked
            if(cb.checked) {
                cb.parentElement.classList.add('border-sky-500/50', 'bg-sky-500/5');
            } else {
                cb.parentElement.classList.remove('border-sky-500/50', 'bg-sky-500/5');
            }
        });

        document.getElementById('modalUsuario').classList.remove('hidden');

    } catch (error) {
        alert("Error: No se pudo cargar la información del usuario.");
    }
}

// Cierre inteligente al hacer clic fuera del modal
window.onclick = function(event) {
    const modal = document.getElementById('modalUsuario');
    if (event.target == modal) {
        modal.classList.add('hidden');
    }
}


function confirmarEliminar(id, nombre) {
    Swal.fire({
        title: '<span style="color: #fff">¿Estás seguro?</span>',
        html: `<p style="color: #94a3b8">Vas a eliminar al usuario <b>${nombre}</b>. Esta acción no se puede deshacer.</p>`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#0ea5e9', // Sky 500
        cancelButtonColor: '#1e293b',  // Slate 800
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar',
        background: '#0f172a', // Fondo oscuro (Slate 900)
        iconColor: '#f59e0b',
        customClass: {
            popup: 'rounded-3xl border border-white/10'
        }
    }).then((result) => {
        if (result.isConfirmed) {
            // Si el usuario confirma, lo redirigimos a la ruta de Python
            window.location.href = `/admin/usuarios/eliminar/${id}`;
        }
    })
}
