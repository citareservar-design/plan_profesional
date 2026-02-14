/**
 * Generador de QR para AgendApp - Versión Final sin Logo
 */

const generarQR = () => {
    if (typeof QRCode === "undefined") {
        setTimeout(generarQR, 100);
        return;
    }

    const qrContainer = document.getElementById('qr-data-container');
    if (!qrContainer) return;

    const slug = qrContainer.getAttribute('data-slug') || 'negocio';
    const host = window.location.host;
    let finalUrl = "";

    if (host.includes('192.168') || host.includes('localhost')) {
        finalUrl = window.location.protocol + "//" + host + "/";
    } else {
        const cleanHost = host.replace('www.', '');
        finalUrl = `https://${cleanHost}/`;
    }

    document.getElementById('url-text').innerText = finalUrl;

    const qrDiv = document.getElementById("qrcode");
    qrDiv.innerHTML = "";
    
    new QRCode(qrDiv, {
        text: finalUrl,
        width: 250,
        height: 250,
        colorDark: "#0f172a",
        colorLight: "#ffffff",
        correctLevel: QRCode.CorrectLevel.H
    });
};

// --- FUNCIONES DE BOTONES ---

window.downloadQR = function() {
    const img = document.querySelector("#qrcode img");
    const canvas = document.querySelector("#qrcode canvas");
    if (!img && !canvas) return;

    const link = document.createElement("a");
    link.download = "Mi_Acceso_QR.png";
    link.href = canvas ? canvas.toDataURL("image/png") : img.src;
    link.click();
};

window.copyLink = function() {
    const url = document.getElementById('url-text').innerText;
    navigator.clipboard.writeText(url).then(() => {
        if (window.Swal) {
            Swal.fire({ 
                toast: true, position: 'top-end', icon: 'success', title: '¡Copiado!', 
                showConfirmButton: false, timer: 1500, background: '#1e293b', color: '#fff' 
            });
        }
    });
};

async function shareLink() {
    const url = document.getElementById('url-text').innerText;
    const qrContainer = document.getElementById('qr-data-container');
    
    // Captura el nombre real de la base de datos
    const nombreBD = qrContainer.getAttribute('data-nombre') || 'nuestro establecimiento';
    
    // MENSAJE MEJORADO: Más profesional y con estructura clara
    const mensajeCompleto = 
        `*¡Hola! Te escribimos de ${nombreBD}* \n\n` +
        `Queremos facilitarte el proceso de tus próximas citas. \n\n` +
        `A través del siguiente enlace, podrás ver nuestra disponibilidad y realizar tu reserva en segundos:\n\n` +
        `*Reserva aquí:* ${url}\n\n` +
        `¡Te esperamos pronto! `;

    if (navigator.share && window.isSecureContext) {
        try {
            await navigator.share({
                title: 'Reserva en ' + nombreBD,
                text: mensajeCompleto,
                // Nota: Algunos navegadores en móviles pegan el url al final del texto automáticamente
            });
        } catch (err) {
            if (err.name !== 'AbortError') abrirWhatsAppFallback(mensajeCompleto);
        }
    } else {
        abrirWhatsAppFallback(mensajeCompleto);
    }
}

// Función auxiliar para abrir WhatsApp con el mensaje formateado
function abrirWhatsAppFallback(mensaje) {
    const urlWa = `https://wa.me/?text=${encodeURIComponent(mensaje)}`;
    window.open(urlWa, '_blank');
}

window.downloadQR = function() {
    const img = document.querySelector("#qrcode img");
    const canvas = document.querySelector("#qrcode canvas");
    if (!img && !canvas) return;
    const link = document.createElement("a");
    link.download = "QR_Reserva.png";
    link.href = canvas ? canvas.toDataURL("image/png") : img.src;
    link.click();
};

function copyLink() {
    const url = document.getElementById('url-text').innerText;
    navigator.clipboard.writeText(url).then(() => {
        if (window.Swal) {
            Swal.fire({ toast: true, position: 'top-end', icon: 'success', title: '¡Copiado!', showConfirmButton: false, timer: 1500 });
        }
    });
}

window.onload = generarQR;