// FIEK Chatbot Frontend JavaScript

const API_URL = 'http://localhost:5001/api';

// DOM Elements
const chatMessages = document.getElementById('chatMessages');
const userInput = document.getElementById('userInput');
const sendButton = document.getElementById('sendButton');
const loadingIndicator = document.getElementById('loadingIndicator');
const suggestions = document.getElementById('suggestions');

// State
let currentLanguage = 'en';

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkAPIHealth();
    setupEventListeners();
    setupLanguageToggle();
});

// Check if API is available
async function checkAPIHealth() {
    try {
        const response = await fetch(`${API_URL}/health`);
        const data = await response.json();
        
        if (!data.chatbot_initialized) {
            addSystemMessage('Chatbot is initializing. Please wait a moment...');
            // Try to initialize
            try {
                await fetch(`${API_URL}/initialize`, { method: 'POST' });
                setTimeout(() => {
                    addSystemMessage('Chatbot ready! You can start asking questions.');
                }, 2000);
            } catch (initError) {
                addSystemMessage('Initialization failed. Please check the backend logs.');
            }
        } else {
            addSystemMessage('Chatbot is ready! Ask me anything about FIEK.');
        }
    } catch (error) {
        addSystemMessage('⚠️ Unable to connect to the chatbot server. Please make sure the backend is running on http://localhost:5001');
        console.error('API health check failed:', error);
    }
}

// Setup event listeners
function setupEventListeners() {
    sendButton.addEventListener('click', handleSendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });

    // Suggestion chips
    document.querySelectorAll('.suggestion-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            const query = chip.getAttribute('data-query');
            userInput.value = query;
            handleSendMessage();
        });
    });
}

// Setup language toggle
function setupLanguageToggle() {
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const lang = btn.getAttribute('data-lang');
            currentLanguage = lang;
            
            document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Update placeholder based on language
            if (lang === 'sq') {
                userInput.placeholder = 'Më pyetni çdo gjë për FIEK...';
            } else {
                userInput.placeholder = 'Ask me anything about FIEK...';
            }
        });
    });
}

// Handle send message
async function handleSendMessage() {
    const message = userInput.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addMessage(message, 'user');
    
    // Clear input
    userInput.value = '';
    
    // Disable input while processing
    setInputEnabled(false);
    showLoading(true);
    
    try {
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            addMessage(`⚠️ ${data.error}`, 'bot');
        } else {
            addMessage(data.response, 'bot', data.sources);
        }
    } catch (error) {
        console.error('Error sending message:', error);
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            addMessage('❌ Cannot connect to the server. Please make sure the backend is running on http://localhost:5001', 'bot');
        } else {
            addMessage(`❌ Sorry, I encountered an error: ${error.message}. Please try again.`, 'bot');
        }
    } finally {
        showLoading(false);
        setInputEnabled(true);
        userInput.focus();
    }
}

// Add message to chat
function addMessage(text, sender, sources = []) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // Format text (preserve line breaks and lists)
    const formattedText = formatMessage(text);
    contentDiv.innerHTML = formattedText;
    
    // Add sources if available
    if (sources && sources.length > 0) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'sources';
        sourcesDiv.textContent = `Sources: ${sources.join(', ')}`;
        contentDiv.appendChild(sourcesDiv);
    }
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Format message text
function formatMessage(text) {
    // Convert line breaks to <br>
    let formatted = text.replace(/\n/g, '<br>');
    
    // Convert markdown-style lists to HTML lists
    formatted = formatted.replace(/(<br>)?\* (.+?)(<br>|$)/g, '<li>$2</li>');
    
    // Wrap consecutive list items in <ul>
    formatted = formatted.replace(/(<li>.*?<\/li>(?:<br>)?)+/g, (match) => {
        return '<ul>' + match.replace(/<br>/g, '') + '</ul>';
    });
    
    // Wrap in paragraph tags
    const paragraphs = formatted.split('<br><br>');
    formatted = paragraphs.map(p => {
        if (p.trim() && !p.includes('<ul>') && !p.includes('<li>')) {
            return '<p>' + p.replace(/<br>/g, '') + '</p>';
        }
        return p;
    }).join('');
    
    return formatted;
}

// Add system message
function addSystemMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message';
    messageDiv.style.opacity = '0.7';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = text;
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Show/hide loading indicator
function showLoading(show) {
    loadingIndicator.style.display = show ? 'flex' : 'none';
}

// Enable/disable input
function setInputEnabled(enabled) {
    userInput.disabled = !enabled;
    sendButton.disabled = !enabled;
}

