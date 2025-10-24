/**
 * Thai ID Card Reader - Web Application
 * Real-time card data display with WebSocket connection
 */

class ThaiIDCardApp {
    constructor() {
        this.ws = null;
        this.reconnectInterval = null;
        this.cardData = null;

        // DOM elements
        this.elements = {
            statusDot: document.getElementById('status-dot'),
            statusText: document.getElementById('status-text'),
            connectionInfo: document.getElementById('connection-info'),
            welcomeMessage: document.getElementById('welcome-message'),
            cardDisplay: document.getElementById('card-display'),
            photo: document.getElementById('photo'),
            photoPlaceholder: document.getElementById('photo-placeholder'),
            logContent: document.getElementById('log-content'),
            toastContainer: document.getElementById('toast-container'),
            btnRead: document.getElementById('btn-read'),
            btnClear: document.getElementById('btn-clear'),
            btnClearLog: document.getElementById('btn-clear-log'),
        };

        // Field mappings (matched to API model fields)
        this.fields = {
            cid: 'cid',
            'name-th': 'thai_fullname',
            'name-en': 'english_fullname',
            dob: 'date_of_birth',
            gender: 'gender_text',
            address: 'address',
            'issue-date': 'issue_date',
            'expire-date': 'expire_date',
        };

        this.init();
    }

    /**
     * Initialize the application
     */
    init() {
        this.log('info', 'Initializing application...');
        this.setupEventListeners();
        this.connectWebSocket();
    }

    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Read card button
        this.elements.btnRead.addEventListener('click', () => {
            this.requestCardRead();
        });

        // Clear data button
        this.elements.btnClear.addEventListener('click', () => {
            this.clearCardData();
        });

        // Clear log button
        this.elements.btnClearLog.addEventListener('click', () => {
            this.clearLog();
        });

        // Copy buttons
        document.querySelectorAll('.copy-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const field = e.target.dataset.field;
                this.copyField(field, e.target);
            });
        });
    }

    /**
     * Connect to WebSocket server
     */
    connectWebSocket() {
        this.log('info', 'Connecting to WebSocket...');

        try {
            this.ws = new WebSocket('ws://localhost:8765/ws');

            this.ws.onopen = () => this.onWebSocketOpen();
            this.ws.onmessage = (event) => this.onWebSocketMessage(event);
            this.ws.onclose = () => this.onWebSocketClose();
            this.ws.onerror = (error) => this.onWebSocketError(error);

        } catch (error) {
            this.log('error', `Connection error: ${error.message}`);
            this.updateConnectionStatus('disconnected');
        }
    }

    /**
     * WebSocket opened handler
     */
    onWebSocketOpen() {
        this.log('success', 'Connected to card reader service');
        this.updateConnectionStatus('connected');
        this.clearReconnectInterval();
        this.showToast('success', 'Connected to server');
    }

    /**
     * WebSocket message handler
     */
    onWebSocketMessage(event) {
        try {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
        } catch (error) {
            this.log('error', `Failed to parse message: ${error.message}`);
        }
    }

    /**
     * WebSocket closed handler
     */
    onWebSocketClose() {
        this.log('warning', 'Disconnected from card reader service');
        this.updateConnectionStatus('disconnected');
        this.scheduleReconnect();
        this.showToast('warning', 'Disconnected from server');
    }

    /**
     * WebSocket error handler
     */
    onWebSocketError(error) {
        this.log('error', `WebSocket error: ${error.message || 'Unknown error'}`);
        this.updateConnectionStatus('error');
    }

    /**
     * Handle incoming WebSocket message
     */
    handleMessage(message) {
        const { type, data, reader, message: msg } = message;

        switch (type) {
            case 'connected':
                this.log('info', msg || 'WebSocket connection established');
                break;

            case 'card_inserted':
                this.log('success', `Card detected in ${reader || 'reader'}`);
                // Check message to determine if auto-read is happening
                if (msg && msg.includes('reading automatically')) {
                    this.showToast('info', 'Card detected - reading automatically...');
                } else {
                    this.showToast('info', 'Card detected - click "Read Card" button');
                }
                break;

            case 'card_read':
                // Check if data is from cache
                const isCached = data.cached === true;
                const readAt = data.read_at;

                if (isCached) {
                    this.log('info', 'Card data from cache (remove card for fresh read)');
                    this.displayCardData(data, { cached: true, readAt });
                    this.showToast('info', 'Data from cache - remove card for fresh read');
                } else {
                    this.log('success', 'Card data read from hardware');
                    this.displayCardData(data, { cached: false, readAt });
                    this.showToast('success', 'Card read successfully!');
                }
                break;

            case 'card_removed':
                this.log('warning', 'Card removed');
                this.showToast('info', 'Card removed');
                // Auto-clear card data when card is removed
                this.clearCardData();
                break;

            case 'reader_status':
                this.log('info', msg || 'Reader status update');
                break;

            case 'error':
                this.log('error', msg || 'Error occurred');
                this.showToast('error', msg || 'An error occurred');
                break;

            default:
                this.log('info', `Unknown event: ${type}`);
        }
    }

    /**
     * Display card data
     */
    displayCardData(data, metadata = {}) {
        if (!data) return;

        this.cardData = data;

        // Hide welcome, show card display
        this.elements.welcomeMessage.style.display = 'none';
        this.elements.cardDisplay.style.display = 'block';

        // Update cache indicator
        this.updateCacheIndicator(metadata.cached, metadata.readAt);

        // Update all fields
        for (const [elementId, fieldName] of Object.entries(this.fields)) {
            const element = document.getElementById(elementId);
            if (element && data[fieldName]) {
                element.textContent = data[fieldName];
            }
        }

        // Handle photo
        if (data.photo_base64) {
            this.elements.photo.src = data.photo_base64;
            this.elements.photo.style.display = 'block';
            this.elements.photoPlaceholder.style.display = 'none';
        } else {
            this.elements.photo.style.display = 'none';
            this.elements.photoPlaceholder.style.display = 'flex';
        }
    }

    /**
     * Update cache indicator badge
     */
    updateCacheIndicator(isCached, readAt) {
        let indicator = document.getElementById('cache-indicator');

        // Create indicator if it doesn't exist
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'cache-indicator';
            indicator.className = 'cache-indicator';

            // Insert at the top of card display
            const cardDisplay = this.elements.cardDisplay;
            cardDisplay.insertBefore(indicator, cardDisplay.firstChild);
        }

        if (isCached) {
            const timestamp = readAt ? new Date(readAt).toLocaleString() : 'Unknown';
            indicator.innerHTML = `
                <span class="cache-badge cached">📋 Cached Data</span>
                <span class="cache-timestamp">Read at: ${timestamp}</span>
                <span class="cache-hint">Remove card for fresh read</span>
            `;
            indicator.className = 'cache-indicator cached';
            indicator.style.display = 'block';
        } else if (readAt) {
            const timestamp = new Date(readAt).toLocaleString();
            indicator.innerHTML = `
                <span class="cache-badge fresh">✓ Fresh Read</span>
                <span class="cache-timestamp">Read at: ${timestamp}</span>
            `;
            indicator.className = 'cache-indicator fresh';
            indicator.style.display = 'block';
        } else {
            indicator.style.display = 'none';
        }
    }

    /**
     * Clear card data display
     */
    clearCardData() {
        this.cardData = null;
        this.elements.cardDisplay.style.display = 'none';
        this.elements.welcomeMessage.style.display = 'block';
        this.log('info', 'Card data cleared');
    }

    /**
     * Request manual card read
     */
    requestCardRead() {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            this.showToast('error', 'Not connected to server');
            return;
        }

        this.log('info', 'Requesting card read...');
        this.ws.send(JSON.stringify({
            type: 'read_card',
            include_photo: true,
        }));

        // Update button state
        this.elements.btnRead.textContent = '⏳ Reading...';
        this.elements.btnRead.disabled = true;

        setTimeout(() => {
            this.elements.btnRead.textContent = '🔄 Read Card Manually';
            this.elements.btnRead.disabled = false;
        }, 3000);
    }

    /**
     * Copy field to clipboard
     */
    async copyField(fieldName, buttonElement = null) {
        if (!this.cardData || !this.cardData[fieldName]) {
            this.showToast('warning', 'No data to copy');
            return;
        }

        await this.copyToClipboard(this.cardData[fieldName], true, buttonElement);
    }

    /**
     * Copy text to clipboard
     */
    async copyToClipboard(text, showToast = true, buttonElement = null) {
        try {
            await navigator.clipboard.writeText(text);

            if (showToast) {
                this.showToast('success', 'Copied to clipboard!');
            }

            // Update button appearance
            if (buttonElement) {
                const originalText = buttonElement.textContent;
                buttonElement.classList.add('copied');
                buttonElement.textContent = '✓';

                setTimeout(() => {
                    buttonElement.classList.remove('copied');
                    buttonElement.textContent = originalText;
                }, 2000);
            }

        } catch (error) {
            this.log('error', `Failed to copy: ${error.message}`);
            this.showToast('error', 'Failed to copy to clipboard');
        }
    }

    /**
     * Update connection status display
     */
    updateConnectionStatus(status) {
        const statusMap = {
            connected: {
                text: 'Connected',
                dotClass: 'connected',
                info: 'WebSocket connected to localhost:8765',
            },
            disconnected: {
                text: 'Disconnected',
                dotClass: '',
                info: 'Attempting to reconnect...',
            },
            error: {
                text: 'Error',
                dotClass: '',
                info: 'Connection error',
            },
        };

        const config = statusMap[status] || statusMap.disconnected;

        this.elements.statusText.textContent = config.text;
        this.elements.statusDot.className = `status-dot ${config.dotClass}`;
        this.elements.connectionInfo.textContent = config.info;
    }

    /**
     * Schedule reconnection attempt
     */
    scheduleReconnect() {
        if (this.reconnectInterval) return;

        this.reconnectInterval = setInterval(() => {
            this.log('info', 'Attempting to reconnect...');
            this.connectWebSocket();
        }, 3000);
    }

    /**
     * Clear reconnect interval
     */
    clearReconnectInterval() {
        if (this.reconnectInterval) {
            clearInterval(this.reconnectInterval);
            this.reconnectInterval = null;
        }
    }

    /**
     * Add log entry
     */
    log(type, message) {
        const time = new Date().toLocaleTimeString();
        const entry = document.createElement('div');
        entry.className = `log-entry log-${type}`;
        entry.innerHTML = `
            <span class="log-time">${time}</span>
            <span class="log-message">${message}</span>
        `;

        this.elements.logContent.appendChild(entry);

        // Auto-scroll to bottom
        this.elements.logContent.scrollTop = this.elements.logContent.scrollHeight;

        // Limit log entries (keep last 50)
        const entries = this.elements.logContent.querySelectorAll('.log-entry');
        if (entries.length > 50) {
            entries[0].remove();
        }
    }

    /**
     * Clear log
     */
    clearLog() {
        this.elements.logContent.innerHTML = '';
        this.log('info', 'Log cleared');
    }

    /**
     * Show toast notification
     */
    showToast(type, message, duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;

        const icons = {
            success: '✓',
            error: '✗',
            info: 'ℹ',
            warning: '⚠',
        };

        toast.innerHTML = `
            <span class="toast-icon">${icons[type] || 'ℹ'}</span>
            <span class="toast-message">${message}</span>
        `;

        this.elements.toastContainer.appendChild(toast);

        // Auto-remove after duration
        setTimeout(() => {
            toast.style.animation = 'slideIn 0.3s ease-out reverse';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new ThaiIDCardApp();
});
