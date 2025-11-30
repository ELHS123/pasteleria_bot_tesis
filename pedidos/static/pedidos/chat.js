async function enviarMensaje() {
    const input = document.getElementById('user-input');
    const chatBox = document.getElementById('chat-box');
    const typingIndicator = document.getElementById('typing-indicator');
    const mensaje = input.value.trim();

    if (mensaje === "") return;

    // 1. Mostrar mensaje del usuario
    chatBox.innerHTML += `<div class="message user">${mensaje}</div>`;
    input.value = "";
    chatBox.scrollTop = chatBox.scrollHeight;

    // Mostrar indicador
    typingIndicator.style.display = 'block';

    // 2. Enviar al Backend (Django API)
    try {
        const response = await fetch('/api/chat/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mensaje: mensaje })
        });
        const data = await response.json();

        // Ocultar indicador
        typingIndicator.style.display = 'none';

        // 3. Mostrar respuesta del Bot
        chatBox.innerHTML += `<div class="message bot">${data.respuesta}</div>`;
        chatBox.scrollTop = chatBox.scrollHeight;

    } catch (error) {
        typingIndicator.style.display = 'none';
        chatBox.innerHTML += `<div class="message bot" style="color:red">Error de conexión 😓</div>`;
    }
}

function handleEnter(e) {
    if (e.key === 'Enter') enviarMensaje();
}