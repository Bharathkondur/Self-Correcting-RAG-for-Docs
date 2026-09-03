class ChatManager {
    constructor() {
        this.messagesContainer = document.getElementById('chat-messages');
        this.input = document.getElementById('user-input');
        this.sendBtn = document.getElementById('send-btn');
        this.fileInput = document.getElementById('file-input');
        this.fileList = document.getElementById('file-list');
        this.temperature = document.getElementById('temperature');
        this.temperatureValue = document.getElementById('temperature-value');
        this.sessionId = null;
        this.isBusy = false;
        this.conversation = [];
        this.setupEventListeners();
        this.checkHealth();
    }

    setupEventListeners() {
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.input.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                this.sendMessage();
            }
        });
        this.input.addEventListener('input', () => {
            this.input.style.height = 'auto';
            this.input.style.height = `${Math.min(this.input.scrollHeight, 150)}px`;
        });

        const dropZone = document.getElementById('drop-zone');
        dropZone.addEventListener('click', () => this.fileInput.click());
        dropZone.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                this.fileInput.click();
            }
        });
        dropZone.addEventListener('dragover', (event) => {
            event.preventDefault();
            dropZone.classList.add('dragging');
        });
        dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragging'));
        dropZone.addEventListener('drop', (event) => {
            event.preventDefault();
            dropZone.classList.remove('dragging');
            this.handleFileUpload(event.dataTransfer.files[0]);
        });
        this.fileInput.addEventListener('change', (event) => {
            this.handleFileUpload(event.target.files[0]);
        });
        this.temperature.addEventListener('input', () => {
            this.temperatureValue.textContent = Number(this.temperature.value).toFixed(1);
        });
        document.getElementById('clear-btn').addEventListener('click', () => this.clearChat());
        document.getElementById('export-btn').addEventListener('click', () => this.exportChat());
    }

    async checkHealth() {
        const label = document.getElementById('system-status');
        const dot = document.querySelector('.status-dot');
        try {
            const response = await fetch('/api/health');
            if (!response.ok) throw new Error('Unavailable');
            const data = await response.json();
            label.textContent = `Ready · ${data.provider}`;
            dot.classList.add('online');
        } catch (_error) {
            label.textContent = 'Backend unavailable';
            dot.classList.remove('online');
        }
    }

    createMessage(role) {
        const message = document.createElement('div');
        message.className = `message ${role}`;

        const avatar = document.createElement('div');
        avatar.className = 'avatar';
        const icon = document.createElement('i');
        icon.className = role === 'user' ? 'fa-solid fa-user' : 'fa-solid fa-robot';
        avatar.appendChild(icon);

        const content = document.createElement('div');
        content.className = 'content';
        message.append(avatar, content);
        this.messagesContainer.appendChild(message);
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        return content;
    }

    appendTextMessage(role, text) {
        const content = this.createMessage(role);
        const paragraph = document.createElement('p');
        paragraph.textContent = text;
        content.appendChild(paragraph);
        return content;
    }

    setBusy(busy) {
        this.isBusy = busy;
        this.sendBtn.disabled = busy;
        this.fileInput.disabled = busy;
        this.input.disabled = busy;
    }

    async sendMessage() {
        const question = this.input.value.trim();
        if (!question || this.isBusy) return;
        if (!this.sessionId) {
            this.appendTextMessage('system', 'Upload a PDF before asking a question.');
            return;
        }

        this.input.value = '';
        this.input.style.height = 'auto';
        this.appendTextMessage('user', question);
        this.conversation.push({ role: 'user', text: question });

        const responseContent = this.createMessage('system');
        const progress = document.createElement('div');
        progress.className = 'processing';
        progress.textContent = 'Running corrective retrieval…';
        responseContent.appendChild(progress);
        this.setBusy(true);

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    question,
                    temperature: Number(this.temperature.value),
                }),
            });
            const data = await response.json();
            responseContent.replaceChildren();
            if (!response.ok) {
                this.renderError(responseContent, data.detail || 'Unable to generate an answer.');
                return;
            }
            this.renderTrace(responseContent, data.trace, data.status, data.attempts);
            const answer = document.createElement('p');
            answer.className = 'answer';
            answer.textContent = data.answer;
            responseContent.appendChild(answer);
            this.renderSources(responseContent, data.sources);
            this.conversation.push({ role: 'assistant', text: data.answer, sources: data.sources });
        } catch (_error) {
            responseContent.replaceChildren();
            this.renderError(responseContent, 'Connection failed. Confirm that the backend is running.');
        } finally {
            this.setBusy(false);
            this.input.focus();
        }
    }

    renderTrace(container, trace, finalStatus, attempts) {
        const details = document.createElement('details');
        details.className = `trace trace-${finalStatus}`;
        const summary = document.createElement('summary');
        const label = finalStatus === 'passed'
            ? 'Verified answer'
            : finalStatus === 'no_context'
                ? 'No supported answer found'
                : 'Best-effort answer';
        summary.textContent = `${label} · ${attempts} attempt${attempts === 1 ? '' : 's'}`;
        details.appendChild(summary);

        trace.forEach((event) => {
            const item = document.createElement('div');
            item.className = `rag-step step-${event.status}`;
            const title = document.createElement('strong');
            title.textContent = event.step.replaceAll('_', ' ');
            const description = document.createElement('span');
            description.textContent = event.detail;
            item.append(title, description);
            details.appendChild(item);
        });
        container.appendChild(details);
    }

    renderSources(container, sources) {
        if (!sources.length) return;
        const details = document.createElement('details');
        details.className = 'sources';
        const summary = document.createElement('summary');
        summary.textContent = `${sources.length} supporting source${sources.length === 1 ? '' : 's'}`;
        details.appendChild(summary);
        sources.forEach((source) => {
            const item = document.createElement('div');
            item.className = 'source-item';
            const heading = document.createElement('strong');
            heading.textContent = `[Source ${source.id}] ${source.filename}${source.page ? ` · page ${source.page}` : ''}`;
            const snippet = document.createElement('p');
            snippet.textContent = source.snippet;
            item.append(heading, snippet);
            details.appendChild(item);
        });
        container.appendChild(details);
    }

    renderError(container, message) {
        const error = document.createElement('p');
        error.className = 'error-message';
        error.textContent = message;
        container.appendChild(error);
    }

    async handleFileUpload(file) {
        if (!file || this.isBusy) return;
        this.fileList.replaceChildren();
        const status = document.createElement('div');
        status.className = 'file-item processing';
        status.textContent = `Indexing ${file.name}…`;
        this.fileList.appendChild(status);
        this.setBusy(true);

        const formData = new FormData();
        formData.append('file', file);
        try {
            const response = await fetch('/api/documents', { method: 'POST', body: formData });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'Upload failed.');
            const previousSessionId = this.sessionId;
            this.sessionId = data.session_id;
            if (previousSessionId) {
                fetch(`/api/documents/${previousSessionId}`, { method: 'DELETE' }).catch(() => {});
            }
            status.className = 'file-item success';
            status.textContent = `${data.filename} · ${data.chunk_count} chunks ready`;
            this.appendTextMessage('system', `${data.filename} is indexed. Ask a question about it.`);
        } catch (error) {
            this.sessionId = null;
            status.className = 'file-item error-message';
            status.textContent = error.message;
        } finally {
            this.fileInput.value = '';
            this.setBusy(false);
        }
    }

    clearChat() {
        this.messagesContainer.querySelectorAll('.message:not(.system-welcome)').forEach((node) => node.remove());
        this.conversation = [];
    }

    exportChat() {
        if (!this.conversation.length) return;
        const content = this.conversation.map((entry) => {
            const sources = (entry.sources || [])
                .map((source) => `  - ${source.filename}${source.page ? `, page ${source.page}` : ''}`)
                .join('\n');
            return `${entry.role.toUpperCase()}\n${entry.text}${sources ? `\nSources:\n${sources}` : ''}`;
        }).join('\n\n');
        const blob = new Blob([content], { type: 'text/plain' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = 'rag-conversation.txt';
        link.click();
        URL.revokeObjectURL(link.href);
    }
}

document.addEventListener('DOMContentLoaded', () => new ChatManager());
