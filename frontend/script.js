const chatHistory = document.getElementById('chat-history');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const reflectorLog = document.getElementById('reflector-log');
const systemLog = document.getElementById('system-log');

// WebSocket Connection
const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const wsUrl = `${protocol}//${window.location.host}/ws`;
let ws = new WebSocket(wsUrl);

ws.onopen = () => {
    addSystemLog('WebSocket connected');
};

ws.onclose = () => {
    addSystemLog('WebSocket disconnected. Refresh to reconnect.');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.type === 'agent') {
        // Remove thinking indicator if exists (optional logic)
        addMessage('agent', data.content);
    } else if (data.type === 'thinking') {
        addMessage('thinking', data.content);
    } else if (data.type === 'system') {
        addSystemLog(data.content);
    } else if (data.type === 'reflector') {
        addCritique(data.content);
    }
};

// UI Functions
function addMessage(type, content) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${type}`;

    // Convert newlines to <br> for display
    const formattedContent = content.replace(/\n/g, '<br>');

    msgDiv.innerHTML = `<div class="content">${formattedContent}</div>`;
    chatHistory.appendChild(msgDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

function addCritique(content) {
    const entryDiv = document.createElement('div');
    entryDiv.className = 'critique-entry';

    const timestamp = new Date().toLocaleTimeString();

    entryDiv.innerHTML = `
        <div class="timestamp">[${timestamp}]</div>
        <div class="content">${content}</div>
    `;
    reflectorLog.appendChild(entryDiv);
    reflectorLog.scrollTop = reflectorLog.scrollHeight;
}

function addSystemLog(msg) {
    const div = document.createElement('div');
    div.className = 'log-entry';
    div.textContent = `[SYS] ${msg}`;
    systemLog.appendChild(div);
    systemLog.scrollTop = systemLog.scrollHeight;
}

function sendMessage() {
    const text = messageInput.value.trim();
    if (text && ws.readyState === WebSocket.OPEN) {
        addMessage('user', text);
        ws.send(text);
        messageInput.value = '';
    }
}

// Event Listeners
sendBtn.addEventListener('click', sendMessage);
messageInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});
