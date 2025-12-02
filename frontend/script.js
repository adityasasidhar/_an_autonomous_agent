const chatHistory = document.getElementById('chat-history');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const reflectorLog = document.getElementById('reflector-log');
const systemLog = document.getElementById('system-log');

const loginOverlay = document.getElementById('login-overlay');
const mainContainer = document.getElementById('main-container');
const usernameInput = document.getElementById('username-input');
const passwordInput = document.getElementById('password-input');
const loginBtn = document.getElementById('login-btn');
const loginMessage = document.getElementById('login-message');

let userId = localStorage.getItem('userId');
let ws = null;

// Check if user is already logged in (optional: verify token with backend)
// For now, if userId exists, we assume valid and try to connect. 
// If WS fails, we show login.
if (userId) {
    connectWebSocket(userId);
} else {
    showLogin();
}

function showLogin() {
    loginOverlay.style.display = 'flex';
    mainContainer.style.filter = 'blur(5px)';
}

function hideLogin() {
    loginOverlay.style.display = 'none';
    mainContainer.style.filter = 'none';
    mainContainer.style.pointerEvents = 'auto';
}

async function handleLogin() {
    const username = usernameInput.value.trim();
    const password = passwordInput.value.trim();

    if (!username || !password) {
        loginMessage.textContent = 'Please enter username and password';
        loginMessage.className = 'login-message error';
        return;
    }

    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (data.status === 'success' || data.status === 'created') {
            userId = data.token;
            localStorage.setItem('userId', userId);
            loginMessage.textContent = 'Access Granted';
            loginMessage.className = 'login-message success';
            setTimeout(() => {
                hideLogin();
                connectWebSocket(userId);
            }, 1000);
        } else {
            loginMessage.textContent = data.message || 'Authentication failed';
            loginMessage.className = 'login-message error';
        }
    } catch (error) {
        loginMessage.textContent = 'Connection error';
        loginMessage.className = 'login-message error';
    }
}

function connectWebSocket(token) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws?userId=${token}`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        addSystemLog('WebSocket connected');
        addSystemLog(`Identity verified: ${token}`);
    };

    ws.onclose = (event) => {
        addSystemLog('WebSocket disconnected.');
        if (event.code === 1008) { // Policy Violation (Auth failed)
            addSystemLog('Authentication failed or expired.');
            localStorage.removeItem('userId');
            showLogin();
        }
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'agent') {
            addMessage('agent', data.content);
        } else if (data.type === 'thinking') {
            addMessage('thinking', data.content);
        } else if (data.type === 'system') {
            addSystemLog(data.content);
        } else if (data.type === 'reflector') {
            addCritique(data.content);
        }
    };
}

loginBtn.addEventListener('click', handleLogin);
usernameInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') passwordInput.focus(); });
passwordInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') handleLogin(); });

// UI Functions
function addMessage(type, content) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${type}`;
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
    if (text && ws && ws.readyState === WebSocket.OPEN) {
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
