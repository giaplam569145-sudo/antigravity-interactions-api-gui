// State Management
const state = {
  currentInteractionId: null,
  activeLanguage: 'python',
  snippets: {
    python: '',
    curl: '',
    javascript: ''
  },
  lastFullPayload: null,
  isSending: false
};

// Preset Templates for Fast Learning
const TEMPLATES = {
  hello: {
    prompt: "Hallo! Wer bist du und worin unterscheidet sich die Interactions API von der normalen Gemini-API?",
    systemInstruction: "",
    resetId: true
  },
  math: {
    prompt: "Ein Zug fährt mit 120 km/h von Station A nach B (Distanz 240 km). Gleichzeitig fährt ein Zug von B nach A mit 80 km/h los. Wann und nach wie vielen Kilometern treffen sie sich? Bitte denke Schritt für Schritt nach.",
    systemInstruction: "",
    resetId: true
  },
  memory: {
    prompt: "Mein Lieblingsbuch ist 'Der Herr der Ringe' und mein Lieblingscharakter ist Samweis Gamdschie. Bitte merke dir das.",
    systemInstruction: "",
    resetId: false
  },
  system: {
    prompt: "Erkläre mir in drei Sätzen, wie Satelliten im Orbit bleiben.",
    systemInstruction: "Antworte ausschließlich im Stil von William Shakespeare auf Frühneuenglisch / altertümlichem Deutsch.",
    resetId: true
  }
};

// DOM Elements
const agentSelect = document.getElementById('agent-select');
const systemInstructionInput = document.getElementById('system-instruction');
const envTypeInput = document.getElementById('env-type');
const prevInteractionIdInput = document.getElementById('prev-interaction-id');
const clearPrevIdBtn = document.getElementById('clear-prev-id');
const streamToggle = document.getElementById('stream-toggle');
const customApiKeyInput = document.getElementById('custom-api-key');

const promptInput = document.getElementById('prompt-input');
const sendBtn = document.getElementById('send-btn');
const messagesContainer = document.getElementById('messages-container');
const rawJsonDisplay = document.getElementById('raw-json-display');
const copyJsonBtn = document.getElementById('copy-json-btn');
const sessionBadge = document.getElementById('session-badge');
const newSessionBtn = document.getElementById('new-session-btn');
const apiStatusBadge = document.getElementById('api-status-badge');
const themeToggle = document.getElementById('theme-toggle');

const codeSnippetDisplay = document.getElementById('code-snippet-display');
const copyCodeBtn = document.getElementById('copy-code-btn');
const langButtons = document.querySelectorAll('.lang-btn');
const tabButtons = document.querySelectorAll('.tab-btn');
const templateChips = document.querySelectorAll('.chip');

// Initialization
document.addEventListener('DOMContentLoaded', () => {
  checkHealth();
  updateCodeSnippets();
  setupEventListeners();
});

// Event Listeners
function setupEventListeners() {
  // Input changes trigger real-time code snippet updates
  promptInput.addEventListener('input', debounce(updateCodeSnippets, 250));
  systemInstructionInput.addEventListener('input', debounce(updateCodeSnippets, 250));
  agentSelect.addEventListener('change', updateCodeSnippets);
  streamToggle.addEventListener('change', updateCodeSnippets);
  prevInteractionIdInput.addEventListener('input', updateCodeSnippets);

  // Send message
  sendBtn.addEventListener('click', handleSendMessage);
  promptInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleSendMessage();
    }
  });

  // Reset Session
  clearPrevIdBtn.addEventListener('click', resetSession);
  newSessionBtn.addEventListener('click', resetSession);

  // Language selectors
  langButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      langButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.activeLanguage = btn.dataset.lang;
      renderActiveCodeSnippet();
    });
  });

  // Copy buttons
  copyCodeBtn.addEventListener('click', () => {
    const code = codeSnippetDisplay.innerText;
    copyToClipboard(code, copyCodeBtn, '📋 Code kopiert!');
  });

  copyJsonBtn.addEventListener('click', () => {
    const jsonText = rawJsonDisplay.innerText;
    copyToClipboard(jsonText, copyJsonBtn, 'Kopiert!');
  });

  // Tabs
  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      tabButtons.forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

      btn.classList.add('active');
      const targetTab = document.getElementById(btn.dataset.tab);
      if (targetTab) targetTab.classList.add('active');
    });
  });

  // Preset Template Chips
  templateChips.forEach(chip => {
    chip.addEventListener('click', () => {
      const templateKey = chip.dataset.template;
      const tpl = TEMPLATES[templateKey];
      if (!tpl) return;

      if (tpl.resetId) {
        resetSession();
      }
      promptInput.value = tpl.prompt;
      if (tpl.systemInstruction !== undefined) {
        systemInstructionInput.value = tpl.systemInstruction;
      }
      promptInput.focus();
      updateCodeSnippets();
    });
  });

  // Theme Toggle
  themeToggle.addEventListener('click', () => {
    const isLight = document.body.getAttribute('data-theme') === 'light';
    if (isLight) {
      document.body.removeAttribute('data-theme');
    } else {
      document.body.setAttribute('data-theme', 'light');
    }
  });
}

// Check Backend and API Key
async function checkHealth() {
  try {
    const res = await fetch('/api/health');
    const data = await res.json();
    if (data.has_api_key_configured) {
      apiStatusBadge.className = 'status-badge connected';
      apiStatusBadge.innerText = '● API Key aktiv (Umgebung)';
    } else {
      apiStatusBadge.className = 'status-badge missing-key';
      apiStatusBadge.innerText = '⚠️ Kein API Key im Backend!';
    }
  } catch (err) {
    apiStatusBadge.className = 'status-badge missing-key';
    apiStatusBadge.innerText = '⚠️ Server offline';
  }
}

// Reset Session / Chain
function resetSession() {
  state.currentInteractionId = null;
  prevInteractionIdInput.value = '';
  sessionBadge.innerText = 'Session: Neu';
  sessionBadge.style.color = '';
  updateCodeSnippets();
}

// Fetch and render code snippets
async function updateCodeSnippets() {
  const payload = {
    agent: agentSelect.value,
    input_text: promptInput.value || "Hallo Welt!",
    system_instruction: systemInstructionInput.value || null,
    previous_interaction_id: prevInteractionIdInput.value || null,
    environment_type: envTypeInput.value || "remote",
    stream: streamToggle.checked
  };

  try {
    const res = await fetch('/api/code-snippet', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      state.snippets = await res.json();
      renderActiveCodeSnippet();
    }
  } catch (err) {
    console.error('Failed to generate snippets:', err);
  }
}

function renderActiveCodeSnippet() {
  const code = state.snippets[state.activeLanguage] || '';
  codeSnippetDisplay.innerText = code;
}

// Send Message Flow
async function handleSendMessage() {
  const text = promptInput.value.trim();
  if (!text || state.isSending) return;

  const agent = agentSelect.value;
  const systemInstruction = systemInstructionInput.value.trim() || null;
  const previousId = prevInteractionIdInput.value.trim() || null;
  const environmentType = envTypeInput.value.trim() || 'remote';
  const isStream = streamToggle.checked;
  const customKey = customApiKeyInput.value.trim() || null;

  // Append user message to UI
  appendUserMessage(text);
  promptInput.value = '';
  updateCodeSnippets();

  state.isSending = true;
  sendBtn.disabled = true;

  // Create bot message container with streaming elements
  const { bubble, thoughtAccordion, thoughtBody, tokenStats, updateThought, appendDelta, finishMessage } = createAssistantMessage();

  const requestBody = {
    agent: agent,
    input_text: text,
    system_instruction: systemInstruction,
    previous_interaction_id: previousId,
    environment_type: environmentType,
    stream: isStream,
    api_key: customKey
  };

  try {
    if (isStream) {
      const response = await fetch('/api/interact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Fehler beim Abruf.');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // keep remainder

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const jsonStr = line.slice(6).trim();
            if (!jsonStr) continue;
            try {
              const eventPayload = JSON.parse(jsonStr);
              handleStreamEvent(eventPayload, {
                appendDelta,
                updateThought,
                tokenStats,
                finishMessage
              });
            } catch (e) {
              console.error('Error parsing SSE line:', jsonStr, e);
            }
          }
        }
      }
    } else {
      // Non-streaming request
      const response = await fetch('/api/interact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Fehler bei der Interaktion.');
      }

      state.lastFullPayload = data.interaction;
      rawJsonDisplay.innerText = JSON.stringify(data.interaction, null, 2);

      const inter = data.interaction;
      if (inter.id) {
        setNewInteractionId(inter.id);
      }

      // Check steps for thoughts
      if (inter.steps && Array.isArray(inter.steps)) {
        for (const step of inter.steps) {
          if (step.type === 'thought' && step.summary) {
            const thoughtText = Array.isArray(step.summary)
              ? step.summary.map(s => s.text || '').join('\n')
              : String(step.summary);
            updateThought(thoughtText);
          }
        }
      }

      appendDelta(inter.output_text || '(Keine Textantwort)');
      if (inter.usage) {
        renderTokenUsage(tokenStats, inter.usage);
      }
    }
  } catch (err) {
    appendDelta(`\n[Fehler: ${err.message}]`);
    bubble.style.borderColor = 'var(--error)';
  } finally {
    finishMessage();
    state.isSending = false;
    sendBtn.disabled = false;
  }
}

// SSE Event Dispatcher
function handleStreamEvent(eventPayload, handlers) {
  const { type, data } = eventPayload;

  if (type === 'error') {
    handlers.appendDelta(`\n[Fehler: ${eventPayload.error}]`);
    return;
  }

  if (type === 'InteractionCreatedEvent') {
    if (data.interaction && data.interaction.id) {
      setNewInteractionId(data.interaction.id);
    }
  } else if (type === 'StepDelta') {
    if (data.delta && data.delta.text) {
      handlers.appendDelta(data.delta.text);
    }
  } else if (type === 'StepStop') {
    if (data.usage) {
      renderTokenUsage(handlers.tokenStats, data.usage);
    }
  } else if (type === 'InteractionCompletedEvent') {
    state.lastFullPayload = data.interaction;
    rawJsonDisplay.innerText = JSON.stringify(data.interaction, null, 2);

    if (data.interaction) {
      if (data.interaction.id) {
        setNewInteractionId(data.interaction.id);
      }
      if (data.interaction.steps) {
        for (const step of data.interaction.steps) {
          if (step.type === 'thought' && step.summary) {
            const thoughtText = Array.isArray(step.summary)
              ? step.summary.map(s => s.text || '').join('\n')
              : String(step.summary);
            handlers.updateThought(thoughtText);
          }
        }
      }
      if (data.interaction.usage) {
        renderTokenUsage(handlers.tokenStats, data.interaction.usage);
      }
    }
  }
}

function setNewInteractionId(id) {
  state.currentInteractionId = id;
  prevInteractionIdInput.value = id;
  sessionBadge.innerText = `Chained: ${id.slice(0, 14)}...`;
  sessionBadge.style.color = 'var(--accent-color)';
  updateCodeSnippets();
}

// UI Message Builders
function appendUserMessage(text) {
  const welcome = document.querySelector('.welcome-banner');
  if (welcome) welcome.remove();

  const msgDiv = document.createElement('div');
  msgDiv.className = 'message user';
  msgDiv.innerHTML = `
    <div class="message-header">Du (Prompt)</div>
    <div class="message-bubble">${escapeHtml(text)}</div>
  `;
  messagesContainer.appendChild(msgDiv);
  scrollToBottom();
}

function createAssistantMessage() {
  const welcome = document.querySelector('.welcome-banner');
  if (welcome) welcome.remove();

  const msgDiv = document.createElement('div');
  msgDiv.className = 'message assistant';

  const header = document.createElement('div');
  header.className = 'message-header';
  header.innerText = `${agentSelect.value} (Interactions API)`;

  const thoughtAccordion = document.createElement('div');
  thoughtAccordion.className = 'thought-accordion';
  thoughtAccordion.style.display = 'none';

  const thoughtHeader = document.createElement('div');
  thoughtHeader.className = 'thought-header';
  thoughtHeader.innerHTML = `<span>🧠 Überlegung / Denkprozess</span><span>▼</span>`;

  const thoughtBody = document.createElement('div');
  thoughtBody.className = 'thought-body';

  let isThoughtCollapsed = false;
  thoughtHeader.addEventListener('click', () => {
    isThoughtCollapsed = !isThoughtCollapsed;
    thoughtBody.style.display = isThoughtCollapsed ? 'none' : 'block';
    thoughtHeader.querySelector('span:last-child').innerText = isThoughtCollapsed ? '▶' : '▼';
  });

  thoughtAccordion.appendChild(thoughtHeader);
  thoughtAccordion.appendChild(thoughtBody);

  const bubble = document.createElement('div');
  bubble.className = 'message-bubble';
  bubble.innerText = 'Antwort wird generiert...';

  const tokenStats = document.createElement('div');
  tokenStats.className = 'token-stats';

  msgDiv.appendChild(header);
  msgDiv.appendChild(thoughtAccordion);
  msgDiv.appendChild(bubble);
  msgDiv.appendChild(tokenStats);
  messagesContainer.appendChild(msgDiv);
  scrollToBottom();

  let hasStartedText = false;

  return {
    bubble,
    thoughtAccordion,
    thoughtBody,
    tokenStats,
    updateThought: (thoughtText) => {
      thoughtAccordion.style.display = 'block';
      thoughtBody.innerText = thoughtText;
    },
    appendDelta: (deltaText) => {
      if (!hasStartedText) {
        bubble.innerText = '';
        hasStartedText = true;
      }
      bubble.innerText += deltaText;
      scrollToBottom();
    },
    finishMessage: () => {
      if (!hasStartedText && bubble.innerText === 'Antwort wird generiert...') {
        bubble.innerText = '(Keine Textantwort erhalten)';
      }
    }
  };
}

function renderTokenUsage(container, usage) {
  if (!usage) return;
  const inTokens = usage.total_input_tokens ?? usage.input_tokens ?? '-';
  const outTokens = usage.total_output_tokens ?? usage.output_tokens ?? '-';
  const thoughtTokens = usage.total_thought_tokens ?? '-';
  const total = usage.total_tokens ?? '-';

  container.innerHTML = `
    <span>📥 Input: <strong>${inTokens}</strong></span>
    <span>🧠 Thought: <strong>${thoughtTokens}</strong></span>
    <span>📤 Output: <strong>${outTokens}</strong></span>
    <span>Total: <strong>${total}</strong></span>
  `;
}

function scrollToBottom() {
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function copyToClipboard(text, buttonElement, successMsg = 'Kopiert!') {
  navigator.clipboard.writeText(text).then(() => {
    const originalText = buttonElement.innerText;
    buttonElement.innerText = successMsg;
    setTimeout(() => {
      buttonElement.innerText = originalText;
    }, 2000);
  }).catch(err => {
    console.error('Clipboard copy failed:', err);
  });
}

function escapeHtml(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function debounce(func, delay) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), delay);
  };
}
