console.log("resena_form.js cargado correctamente");

/**
 * Valida y procesa el envío del formulario
 */
function prepararEnvio(boton) {
    const puntuacion = document.querySelector('input[name="puntuacion"]:checked');
    const mensajeEstrellas = document.getElementById('mensaje-estrellas');

    // 1. VALIDACIÓN: ¿Seleccionó estrellas?
    if (!puntuacion) {
        // Cambiamos el estilo del mensaje para alertar
        mensajeEstrellas.innerText = "⚠️ Por favor, selecciona una estrella";
        mensajeEstrellas.classList.remove('text-slate-500', 'animate-pulse');
        mensajeEstrellas.classList.add('text-red-500', 'scale-110', 'font-bold');
        
        // Animación de vibración (debes tener el CSS de shake)
        mensajeEstrellas.classList.add('shake-animation');
        setTimeout(() => mensajeEstrellas.classList.remove('shake-animation'), 500);
        
        return false; // Detiene el proceso
    }

    // 2. Si es válido, procedemos con la animación de carga
    const texto = document.getElementById('texto-enviar');
    const icono = document.getElementById('icono-enviar');
    
    // Deshabilitar botón para evitar múltiples clics
    boton.disabled = true;
    texto.innerText = 'Enviando...';
    
    // Cambiar avioncito por spinner girando
    if (icono) {
        icono.className = 'fa-solid fa-circle-notch animate-spin';
    }
    
    // Enviar el formulario
    boton.form.submit();
}

/**
 * Actualiza el texto debajo de las estrellas
 */
function actualizarMensaje(valor) {
    const mensajeElemento = document.getElementById('mensaje-estrellas');
    
    const mensajes = {
        '1': { texto: 'Malísimo 😡', color: 'text-red-500' },
        '2': { texto: 'Mal ☹️', color: 'text-orange-500' },
        '3': { texto: 'Regular 😐', color: 'text-yellow-500' },
        '4': { texto: 'Muy Bien 🙂', color: 'text-sky-400' },
        '5': { texto: '¡Excelente! 🤩', color: 'text-sky-500' }
    };

    const seleccion = mensajes[valor];

    if (seleccion) {
        mensajeElemento.classList.remove('animate-pulse', 'text-slate-500', 'text-red-500', 'text-orange-500', 'text-yellow-500', 'text-sky-400', 'text-sky-500');
        mensajeElemento.innerText = seleccion.texto;
        mensajeElemento.classList.add(seleccion.color, 'font-bold');
    }
}

// Al final de tu archivo resena_form.js añade esto:

document.addEventListener('DOMContentLoaded', function() {
    const radios = document.querySelectorAll('.emp-radio');
    
    radios.forEach(radio => {
        radio.addEventListener('change', function() {
            // 1. Resetear todos los estilos de las tarjetas
            document.querySelectorAll('.emp-card label').forEach(label => {
                label.classList.remove('border-sky-500', 'bg-sky-500/10');
                label.classList.add('border-white/10');
            });
            document.querySelectorAll('.emp-card img').forEach(img => {
                img.classList.remove('border-sky-500');
                img.classList.add('border-transparent');
            });

            // 2. Aplicar estilo solo al seleccionado
            if (this.checked) {
                const container = this.closest('.emp-card');
                const label = container.querySelector('label');
                const img = container.querySelector('img');
                
                label.classList.remove('border-white/10');
                label.classList.add('border-sky-500', 'bg-sky-500/10');
                img.classList.remove('border-transparent');
                img.classList.add('border-sky-500');
            }
        });
    });
});

/**
 * Expande o colapsa la lista de empleados
 * Versión compatible con filtrado por ID de empleado
 */
function toggleEmpleados() {
    const texto = document.getElementById('texto-boton');
    const icono = document.getElementById('icono-boton');
    
    // 1. Verificación de seguridad: si no existe el botón, no hacemos nada
    if (!texto || !icono) return;

    const cards = document.querySelectorAll('.emp-card');
    
    // Si hay 3 o menos tarjetas, no hay nada que colapsar
    if (cards.length <= 3) return;

    // 2. Verificamos el estado actual buscando la primera tarjeta que debería estar oculta
    // Usamos el índice 3 (la cuarta tarjeta) como referencia
    const estaCerrado = cards[3].classList.contains('hidden');

    if (estaCerrado) {
        // ABRIR: Mostrar todos
        cards.forEach(card => {
            card.classList.remove('hidden');
            card.classList.add('animate-fade-in'); // Por si tienes la animación de Tailwind
        });
        texto.innerText = "Ver menos";
        icono.classList.add('rotate-180');
    } else {
        // CERRAR: Ocultar los que sobran, pero NUNCA el que está seleccionado
        cards.forEach((card, index) => {
            if (index >= 3) {
                const radio = card.querySelector('.emp-radio');
                // Solo ocultamos si no es el que el usuario marcó
                if (radio && !radio.checked) {
                    card.classList.add('hidden');
                }
            }
        });
        texto.innerText = "Ver más";
        icono.classList.remove('rotate-180');
        
        // Scroll suave hacia arriba para no perder el contexto
        document.getElementById('contenedor-empleados').scrollIntoView({ 
            behavior: 'smooth', 
            block: 'nearest' 
        });
    }
}