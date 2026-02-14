// static/js/empresa.js
console.log('CARGANDO JS DE EMPRESA');

function probarSMTP() {
    console.log("Iniciando prueba SMTP en URL:", window.URL_TEST_SMTP);

    Swal.fire({
        title: 'Enviando prueba...',
        text: 'Por favor espera',
        didOpen: () => { Swal.showLoading() }
    });

    fetch(window.URL_TEST_SMTP, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        }
    })
    .then(async response => {
        const data = await response.json();
        if (response.ok) {
            Swal.fire('¡Éxito!', data.message, 'success');
        } else {
            Swal.fire('Error', data.message, 'error');
        }
    })
    .catch(error => {
        console.error("Error completo:", error);
        Swal.fire('Error de Red', 'No se pudo conectar con el servidor', 'error');
    });
}

document.getElementById('input_unlock').addEventListener('input', function(e) {
    const claveCorrecta = "agendapp2026*";
    const fMax = document.getElementById('field_max_usuarios');
    const fPlan = document.getElementById('field_plan');
    const badge = document.getElementById('badge-lock');
    const glow = document.getElementById('unlock-glow');
    const icon = document.getElementById('lock-icon');

    if (e.target.value === claveCorrecta) {
        // 1. Notificación de éxito
        Swal.fire({
            icon: 'success',
            title: 'Acceso Concedido',
            text: 'Campos de licencia desbloqueados',
            toast: true,
            position: 'top-end',
            showConfirmButton: false,
            timer: 3000,
            timerProgressBar: true
        });

        // 2. Cambios visuales: Desbloquear
        [fMax, fPlan].forEach(el => {
            el.removeAttribute('readonly');
            el.removeAttribute('disabled');
            el.classList.replace('bg-slate-950', 'bg-slate-900');
            el.classList.replace('text-slate-600', 'text-white');
            el.classList.remove('cursor-not-allowed');
            el.classList.add('border-green-500/50');
        });

        // 3. Estética del contenedor
        badge.innerHTML = '<i class="fa-solid fa-lock-open mr-1"></i> Desbloqueado';
        badge.classList.replace('text-red-400', 'text-green-400');
        badge.classList.replace('bg-red-500/20', 'bg-green-500/20');
        glow.classList.replace('opacity-0', 'opacity-100');
        icon.classList.replace('text-slate-600', 'text-green-500');
        e.target.classList.add('border-green-500');
        e.target.blur(); // Quita el foco del input para cerrar el teclado en móvil
    }
});