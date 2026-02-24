console.log("Archivo comisiones.js cargado correctamente.");



// 1. Definición global de la función
window.confirmarCerrarCaja = function() {
    const formulario = document.getElementById('formCerrarCaja');
    
    if (typeof Swal === 'undefined') {
        console.warn("SweetAlert no cargado, enviando directo...");
        formulario.submit();
        return;
    }

    Swal.fire({
        title: '¿CERRAR CAJA HOY?',
        text: "Se liquidarán comisiones y se enviarán comprobantes por correo. ¿Deseas continuar?",
        icon: 'warning',
        showCancelButton: true,
        background: '#0f172a',
        color: '#ffffff',
        confirmButtonColor: '#10b981',
        cancelButtonColor: '#334155',
        confirmButtonText: 'SÍ, LIQUIDAR JORNADA',
        cancelButtonText: 'VOLVER',
        borderRadius: '2.5rem',
        customClass: {
            popup: 'rounded-[2.5rem] border border-white/10 shadow-2xl',
            confirmButton: 'rounded-full px-8 py-4 font-black text-sm',
            cancelButton: 'rounded-full px-8 py-4 font-black text-sm'
        }
    }).then((result) => {
        if (result.isConfirmed) {
            // --- BLOQUE DEL LOADER: Se muestra mientras se envían los correos ---
            Swal.fire({
                title: 'ENVIANDO COMPROBANTES',
                html: 'Estamos procesando los pagos y enviando los correos electrónicos. <br><b>Por favor no cierres esta ventana.</b>',
                allowOutsideClick: false,
                allowEscapeKey: false,
                showConfirmButton: false,
                background: '#0f172a',
                color: '#ffffff',
                borderRadius: '2rem',
                didOpen: () => {
                    Swal.showLoading(); // Activa el spinner oficial
                },
                customClass: {
                    popup: 'rounded-[2rem] border border-white/10'
                }
            });

            // Finalmente enviamos el formulario al servidor
            formulario.submit();
        }
    });
};

