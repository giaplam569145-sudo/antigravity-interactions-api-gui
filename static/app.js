const messagesContainer = document.getElementById('messages');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');

let interactionId = null;

function appendMessage(text, role) {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message', role === 'user' ? 'user-message' : 'agent-message');
    msgDiv.textContent = text;
    messagesContainer.appendChild(msgDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

async function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;

    appendMessage(text, 'user');
    userInput.value = '';

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text, interaction_id: interactionId })
        });

        if (!response.ok) {
            appendMessage("Error communicating with server", 'agent');
            return;
        }

        const data = await response.json();
        interactionId = data.interaction_id;

        if (data.reply) {
            appendMessage(data.reply, 'agent');
        } else {
            appendMessage("(No reply received)", 'agent');
        }
    } catch (e) {
        appendMessage("Network error", 'agent');
    }
}

sendButton.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});
