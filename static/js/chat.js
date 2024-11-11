document.getElementById('messageForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    if (!message) return;
    
    const chatMessages = document.getElementById('chatMessages');
    const characterId = window.location.pathname.split('/').pop();
    
    // Disable input while sending
    messageInput.disabled = true;
    
    try {
        // Add user message immediately with pending status
        const userMessageDiv = document.createElement('div');
        userMessageDiv.className = 'message user-message';
        userMessageDiv.innerHTML = `
            <div class="message-bubble">
                <div class="mb-1">${message}</div>
                <div class="message-info">
                    <small class="text-muted">
                        <i class="bi bi-clock me-1"></i>
                        ${new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
                        <i class="bi bi-check ms-1"></i>
                    </small>
                </div>
            </div>
        `;
        chatMessages.appendChild(userMessageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Send message to server
        const response = await fetch(`/chat/${characterId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `message=${encodeURIComponent(message)}`
        });
        
        const data = await response.json();
        
        // Update user message to show delivered status
        const statusIcon = userMessageDiv.querySelector('.bi-check');
        statusIcon.className = 'bi bi-check2-all text-primary';
        
        // Add character response
        const characterMessageDiv = document.createElement('div');
        characterMessageDiv.className = 'message character-message';
        characterMessageDiv.innerHTML = `
            <div class="message-bubble">
                <div class="mb-1">${data.message}</div>
                <div class="message-info">
                    <small class="text-muted">
                        <i class="bi bi-clock me-1"></i>
                        ${new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
                    </small>
                </div>
            </div>
        `;
        chatMessages.appendChild(characterMessageDiv);
        
        // Clear input and scroll to bottom
        messageInput.value = '';
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
    } catch (error) {
        alert('Failed to send message: ' + error.message);
    } finally {
        messageInput.disabled = false;
        messageInput.focus();
    }
});

// Scroll to bottom on load
document.getElementById('chatMessages').scrollTop = document.getElementById('chatMessages').scrollHeight;

// Auto-resize chat messages container based on viewport height
function adjustChatMessagesHeight() {
    const chatMessages = document.getElementById('chatMessages');
    const viewport = window.innerHeight;
    const headerHeight = document.querySelector('.card-header').offsetHeight;
    const formHeight = document.getElementById('messageForm').offsetHeight;
    const padding = 32; // 2rem top and bottom padding
    
    chatMessages.style.height = `${viewport - headerHeight - formHeight - padding}px`;
}

window.addEventListener('resize', adjustChatMessagesHeight);
document.addEventListener('DOMContentLoaded', adjustChatMessagesHeight);
