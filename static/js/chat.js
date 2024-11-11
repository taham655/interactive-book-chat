document.getElementById('messageForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    if (!message) return;
    
    const chatMessages = document.getElementById('chatMessages');
    const characterId = window.location.pathname.split('/').pop();
    
    try {
        const response = await fetch(`/chat/${characterId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `message=${encodeURIComponent(message)}`
        });
        
        const data = await response.json();
        
        // Add user message
        const userMessageDiv = document.createElement('div');
        userMessageDiv.className = 'message user-message text-end mb-2';
        userMessageDiv.innerHTML = `
            <div class="message-bubble p-2 rounded bg-primary">
                <small class="text-muted">${new Date().toLocaleTimeString()}</small>
                <div>${message}</div>
            </div>
        `;
        chatMessages.appendChild(userMessageDiv);
        
        // Add character response
        const characterMessageDiv = document.createElement('div');
        characterMessageDiv.className = 'message character-message mb-2';
        characterMessageDiv.innerHTML = `
            <div class="message-bubble p-2 rounded bg-secondary">
                <small class="text-muted">${new Date().toLocaleTimeString()}</small>
                <div>${data.message}</div>
            </div>
        `;
        chatMessages.appendChild(characterMessageDiv);
        
        // Clear input and scroll to bottom
        messageInput.value = '';
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
    } catch (error) {
        alert('Failed to send message: ' + error.message);
    }
});

// Scroll to bottom on load
document.getElementById('chatMessages').scrollTop = document.getElementById('chatMessages').scrollHeight;
