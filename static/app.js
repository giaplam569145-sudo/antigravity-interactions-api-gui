let sessionId = null;
const messagesDiv = document.getElementById('messages');
const inputField = document.getElementById('chat-input');

function appendMessage(role, text) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message ' + role;
    msgDiv.innerText = `${role}: ${text}`;
    messagesDiv.appendChild(msgDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

async function sendMessage() {
    const text = inputField.value;
    if (!text) return;
    inputField.value = '';

    appendMessage('user', text);

    const headers = { 'Content-Type': 'application/json' };
    if (sessionId) {
        headers['X-Session-Id'] = sessionId;
    }

    try {
        const response = await fetch('/v1/chat/completions', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({
                model: 'antigravity-preview-latest',
                messages: [{ role: 'user', content: text }]
            })
        });

        sessionId = response.headers.get('X-Session-Id');

        const data = await response.json();
        const reply = data.choices[0].message.content;
        appendMessage('assistant', reply);
    } catch (e) {
        appendMessage('assistant', 'Error: ' + e.message);
    }
}
