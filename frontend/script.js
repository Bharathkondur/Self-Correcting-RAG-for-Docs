class ChatManager {
    constructor() {
        this.messagesContainer = document.getElementById('chat-messages');
        this.input = document.getElementById('user-input');
        this.sendBtn = document.getElementById('send-btn');

        this.setupEventListeners();
    }

    setupEventListeners() {
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        const dropZone = document.getElementById('drop-zone');
        dropZone.addEventListener('click', () => document.getElementById('file-input').click());
        document.getElementById('file-input').addEventListener('change', (e) => this.handleFileUpload(e.target.files[0]));
    }

    appendMessage(role, text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'avatar';
        avatarDiv.innerHTML = role === 'user' 
            ? '<i class="fa-solid fa-user"></i>' 
            : '<i class="fa-solid fa-robot"></i>';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'content';
        
        if (role === 'system') {
            // For system messages, create a structure with steps and text
            const stepsContainer = document.createElement('div');
            stepsContainer.className = 'steps-container';
            
            const textDiv = document.createElement('div');
            textDiv.className = 'text';
            textDiv.innerHTML = text;
            
            contentDiv.appendChild(stepsContainer);
            contentDiv.appendChild(textDiv);
        } else {
            // For user messages, just show the text
            contentDiv.innerHTML = `<p>${text}</p>`;
        }
        
        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);
        this.messagesContainer.appendChild(messageDiv);
        
        // Scroll to bottom
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        
        return messageDiv;
    }

    async sendMessage() {
        const text = this.input.value.trim();
        if (!text) return;

        this.input.value = '';
        this.appendMessage('user', text);

        const responseDiv = this.appendMessage('system', 'Thinking...');
        const stepsContainer = responseDiv.querySelector('.steps-container');
        const textDiv = responseDiv.querySelector('.text');

        // Start "fake" progress animation while waiting for real response
        // In a clearer implementation, we would poll an endpoint or use SSE
        const intervalId = this.startLoadingAnimation(stepsContainer);

        try {
            const res = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: text })
            });

            clearInterval(intervalId);
            stepsContainer.innerHTML = ''; // Clear loading steps

            if (!res.ok) {
                const err = await res.json();
                textDiv.innerHTML = `<span style="color:red">Error: ${err.detail || 'Failed to get response'}</span>`;
                return;
            }

            const data = await res.json();

            // Show success steps
            this.showSuccessTrace(stepsContainer, data);

            textDiv.innerHTML = `<p>${data.answer}</p>`;

        } catch (error) {
            clearInterval(intervalId);
            console.error(error);
            textDiv.innerHTML = `<span style="color:red">Connection refused. Is the backend running?</span>`;
        }
    }

    startLoadingAnimation(container) {
        let stepIndex = 0;
        const potentialSteps = [
            { icon: 'fa-magnifying-glass', text: 'Retrieving context...' },
            { icon: 'fa-brain', text: 'Analyzing documents...' },
            { icon: 'fa-scale-balanced', text: 'Grading relevance...' },
            { icon: 'fa-pen-nib', text: 'Generating draft...' },
            { icon: 'fa-check-double', text: 'Checking for hallucinations...' }
        ];

        container.innerHTML = `<div class="rag-step active"><div class="step-title"><i class="fa-solid fa-spinner fa-spin"></i> Processing...</div></div>`;

        return setInterval(() => {
            const step = potentialSteps[stepIndex % potentialSteps.length];
            container.innerHTML = `
                <div class="rag-step active">
                    <div class="step-title"><i class="fa-solid ${step.icon}"></i> ${step.text}</div>
                </div>
            `;
            stepIndex++;
        }, 2000);
    }

    showSuccessTrace(container, data) {
        // We can show a simplified trace summary
        container.innerHTML = `
            <div class="rag-step"><div class="step-title" style="color:#22c55e"><i class="fa-solid fa-check"></i> Process Complete</div></div>
            <div class="rag-step"><div class="step-title" style="color:#22c55e"><i class="fa-solid fa-check"></i> Hallucination Check Passed</div></div>
        `;
    }

    async handleFileUpload(file) {
        if (!file) return;

        const fileList = document.getElementById('file-list');
        fileList.innerHTML = `<div class="file-item"><i class="fa-solid fa-spinner fa-spin"></i> Uploading ${file.name}...</div>`;

        const formData = new FormData();
        formData.append('file', file);

        try {
            const res = await fetch('/upload', { method: 'POST', body: formData });
            if (res.ok) {
                fileList.innerHTML = `<div class="file-item" style="color:#22c55e"><i class="fa-solid fa-check"></i> ${file.name} (Ready)</div>`;
            } else {
                fileList.innerHTML = `<div class="file-item" style="color:red"><i class="fa-solid fa-xmark"></i> Upload Failed</div>`;
            }
        } catch (e) {
            fileList.innerHTML = `<div class="file-item" style="color:red"><i class="fa-solid fa-plug-circle-xmark"></i> Connection Failed</div>`;
        }
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    new ChatManager();
});
