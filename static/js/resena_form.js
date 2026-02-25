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

/**
 * Expande o colapsa la lista de empleados
 */
function toggleEmpleados() {
    const cards = document.querySelectorAll('.emp-card');
    const texto = document.getElementById('texto-boton');
    const icono = document.getElementById('icono-boton');
    
    if (cards.length <= 3) return;

    const estaExpandido = !cards[3].classList.contains('hidden');
    const cantidadRestante = cards.length - 3;

    if (!estaExpandido) {
        cards.forEach((card, index) => {
            if (index >= 3) {
                card.classList.remove('hidden');
                card.classList.add('animate-fade-in');
            }
        });
        texto.innerText = "Ver menos";
        icono.classList.add('rotate-180');
    } else {
        cards.forEach((card, index) => {
            if (index >= 3) {
                card.classList.add('hidden');
                card.classList.remove('animate-fade-in');
            }
        });
        texto.innerText = `Ver ${cantidadRestante} más`;
        icono.classList.remove('rotate-180');
        
        document.getElementById('contenedor-empleados').scrollIntoView({ 
            behavior: 'smooth', 
            block: 'nearest' 
        });
    }
}