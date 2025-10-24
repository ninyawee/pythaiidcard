# Desktop Client Implementation Plan
## Cross-Platform Thai ID Card Reader with Web & Chrome Extension Integration

### Executive Summary

This document outlines the architecture and implementation plan for a cross-platform desktop client that enables real-time streaming of Thai ID card data to both web applications and Chrome extensions. The solution uses a Python-based local server with WebSocket support for live updates and easy copy functionality.

---

## Architecture Overview

### Three-Tier Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Desktop Client Layer                      │
│  ┌────────────────┐        ┌──────────────────────────┐    │
│  │  System Tray   │───────▶│   FastAPI Server         │    │
│  │  Application   │        │   (localhost:8765)       │    │
│  │  (PySide6)     │        │   - REST API             │    │
│  └────────────────┘        │   - WebSocket /ws        │    │
│                            │   - CORS enabled         │    │
│                            └──────────┬───────────────┘    │
│                                       │                     │
│                            ┌──────────▼───────────────┐    │
│                            │  Card Reader Service     │    │
│                            │  (pythaiidcard)          │    │
│                            │  - Monitors card events  │    │
│                            │  - Streams data          │    │
│                            └──────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                                       │
                     ┌─────────────────┴─────────────────┐
                     │                                   │
          ┌──────────▼──────────┐           ┌───────────▼──────────┐
          │   Web Application   │           │  Chrome Extension    │
          │   (HTML/JS/CSS)     │           │  (Manifest V3)       │
          │   - WebSocket conn  │           │  - WebSocket conn    │
          │   - Auto-copy       │           │  - Click-to-copy     │
          │   - Live updates    │           │  - Badge notifications│
          └─────────────────────┘           └──────────────────────┘
```

---

## Technology Stack

### Desktop Client Core
- **Framework**: PySide6 (Qt for Python)
  - Cross-platform (Windows, macOS, Linux)
  - System tray support
  - Native look & feel
  - Excellent stability

- **Alternative Options**:
  - **wxPython**: Lighter weight, older API
  - **pystray**: Minimal system tray only (no GUI)
  - **Electron + Python**: Heavier but familiar web stack

### Local API Server
- **FastAPI** (v0.115+)
  - Async/await support for concurrent card reading
  - Native WebSocket support
  - Auto-generated OpenAPI docs
  - Excellent performance with Uvicorn

- **Uvicorn** ASGI server
  - Production-ready
  - WebSocket support
  - Auto-reload in development

### Real-Time Communication
- **WebSocket** protocol
  - Bidirectional communication
  - Low latency for real-time updates
  - Browser and extension support
  - Persistent connections

- **Alternative**: Server-Sent Events (SSE)
  - Simpler, one-way streaming
  - Better for read-only scenarios
  - HTTP-based, easier CORS

### Web Application
- **Vanilla JavaScript** + Modern APIs
  - No build step required
  - WebSocket API native support
  - Clipboard API for easy copy
  - Keep it simple and fast

- **UI Framework** (optional):
  - Tailwind CSS for styling
  - Alpine.js for minimal reactivity

### Chrome Extension
- **Manifest V3**
  - Service worker background script
  - Content scripts (if needed)
  - Native messaging as fallback
  - WebSocket connection from background script

---

## Component Specifications

### 1. Desktop Client (System Tray Application)

#### Purpose
- Run silently in background
- Monitor card reader status
- Control local server lifecycle
- Provide quick settings access

#### Features
```python
# Main Components:
- System tray icon with status indicator
  - Green: Server running, card detected
  - Yellow: Server running, no card
  - Red: Server stopped
  - Gray: No reader detected

- Right-click context menu:
  - "Open Web Interface" → Launch browser to localhost:8765
  - "Settings" → Configure options
  - "View Last Card" → Show cached data
  - "Start/Stop Server"
  - "Exit"

- Settings Dialog:
  - Port configuration (default: 8765)
  - Auto-start with OS
  - Enable/disable notifications
  - Card detection sensitivity
  - Auto-copy preferences
```

#### Implementation Structure
```
desktop_client/
├── __init__.py
├── main.py                  # Entry point
├── tray_app.py             # System tray GUI
├── settings.py             # Configuration management
├── server_manager.py       # FastAPI lifecycle control
└── resources/
    ├── icon_green.png
    ├── icon_yellow.png
    ├── icon_red.png
    └── icon_gray.png
```

#### Key Code Pattern
```python
# tray_app.py
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PySide6.QtGui import QIcon, QAction
import threading
import uvicorn

class TrayApp(QSystemTrayIcon):
    def __init__(self):
        super().__init__()
        self.server_thread = None
        self.setup_tray()

    def start_server(self):
        """Run FastAPI server in background thread"""
        if not self.server_thread or not self.server_thread.is_alive():
            self.server_thread = threading.Thread(
                target=self._run_server, daemon=True
            )
            self.server_thread.start()

    def _run_server(self):
        uvicorn.run("api_server:app", host="127.0.0.1", port=8765)
```

### 2. Local API Server (FastAPI)

#### Endpoints

##### REST API
```python
GET  /api/status               # Server & reader status
GET  /api/readers              # List available readers
GET  /api/card/current         # Get current card data (cached)
POST /api/card/read            # Trigger manual read
GET  /api/history              # Recent card reads (optional)
POST /api/settings             # Update server settings
```

##### WebSocket
```python
WS   /ws                       # Real-time card data stream
```

#### WebSocket Protocol
```javascript
// Client → Server (commands)
{
  "type": "subscribe",
  "events": ["card_inserted", "card_removed", "card_read", "reader_status"]
}

{
  "type": "read_card",
  "include_photo": true
}

// Server → Client (events)
{
  "type": "card_inserted",
  "timestamp": "2025-10-23T10:30:00Z",
  "reader": "Alcor Link AK9563"
}

{
  "type": "card_read",
  "timestamp": "2025-10-23T10:30:05Z",
  "data": {
    "cid": "1234567890123",
    "name_th": "นาย ทดสอบ ระบบ",
    "name_en": "Mr. Test System",
    "date_of_birth": "1990-01-15",
    "address": "...",
    "photo_base64": "data:image/jpeg;base64,..."
  }
}

{
  "type": "card_removed",
  "timestamp": "2025-10-23T10:35:00Z"
}

{
  "type": "error",
  "error_code": "NO_CARD_DETECTED",
  "message": "No card detected in reader"
}
```

#### Implementation Structure
```
api_server/
├── __init__.py
├── main.py                  # FastAPI app entry
├── routes/
│   ├── __init__.py
│   ├── api.py              # REST endpoints
│   └── websocket.py        # WebSocket handler
├── services/
│   ├── __init__.py
│   ├── card_monitor.py     # Background card monitoring
│   └── connection_manager.py # WebSocket connections
└── models/
    ├── __init__.py
    └── api_models.py       # Pydantic models for API
```

#### Key Implementation Patterns

##### Card Monitoring Service
```python
# services/card_monitor.py
import asyncio
from pythaiidcard import ThaiIDCardReader

class CardMonitorService:
    def __init__(self, connection_manager):
        self.connection_manager = connection_manager
        self.monitoring = False
        self.last_card_data = None
        self.reader = None

    async def start_monitoring(self):
        """Background task to monitor card events"""
        self.monitoring = True
        while self.monitoring:
            try:
                readers = ThaiIDCardReader.list_readers()

                if not readers:
                    await self.broadcast_event({
                        "type": "reader_status",
                        "status": "no_readers"
                    })
                    await asyncio.sleep(2)
                    continue

                # Try to detect card insertion
                if not self.reader:
                    self.reader = ThaiIDCardReader(readers[0])
                    try:
                        self.reader.connect()
                        await self.broadcast_event({
                            "type": "card_inserted",
                            "reader": readers[0]
                        })

                        # Auto-read card
                        await self.read_and_broadcast()

                    except Exception as e:
                        self.reader = None
                        await asyncio.sleep(1)
                        continue

            except Exception as e:
                await self.broadcast_event({
                    "type": "error",
                    "message": str(e)
                })

            await asyncio.sleep(0.5)

    async def read_and_broadcast(self):
        """Read card and broadcast to all connected clients"""
        if self.reader:
            try:
                card_data = self.reader.read_card(include_photo=True)
                self.last_card_data = card_data

                await self.broadcast_event({
                    "type": "card_read",
                    "data": card_data.model_dump()
                })
            except Exception as e:
                await self.broadcast_event({
                    "type": "error",
                    "message": f"Failed to read card: {str(e)}"
                })

    async def broadcast_event(self, event):
        """Send event to all WebSocket connections"""
        await self.connection_manager.broadcast(event)
```

##### WebSocket Connection Manager
```python
# services/connection_manager.py
from fastapi import WebSocket
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        # Clean up dead connections
        for conn in disconnected:
            self.disconnect(conn)
```

##### Main FastAPI Application
```python
# main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import asyncio

from .services.card_monitor import CardMonitorService
from .services.connection_manager import ConnectionManager
from .routes import api

app = FastAPI(title="Thai ID Card Reader API", version="1.0.0")

# CORS for local web apps and extensions
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:*",
        "http://127.0.0.1:*",
        "chrome-extension://*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connection manager and card monitor
connection_manager = ConnectionManager()
card_monitor = CardMonitorService(connection_manager)

@app.on_event("startup")
async def startup_event():
    """Start card monitoring on server startup"""
    asyncio.create_task(card_monitor.start_monitoring())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await connection_manager.connect(websocket)
    try:
        # Send current status immediately
        await websocket.send_json({
            "type": "connected",
            "message": "WebSocket connected"
        })

        # Keep connection alive and handle client commands
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "read_card":
                await card_monitor.read_and_broadcast()
            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)

# Include REST API routes
app.include_router(api.router, prefix="/api")

# Serve static web app
app.mount("/", StaticFiles(directory="web_app", html=True), name="web_app")
```

### 3. Web Application

#### Features
- Real-time card data display
- Auto-copy on card read
- Manual copy buttons per field
- Connection status indicator
- Responsive design
- No build step required

#### Implementation Structure
```
web_app/
├── index.html
├── styles.css
├── app.js
└── assets/
    └── icons/
```

#### Key Implementation (app.js)
```javascript
class ThaiIDCardApp {
    constructor() {
        this.ws = null;
        this.reconnectInterval = null;
        this.cardData = null;
        this.autoCopyEnabled = true;

        this.init();
    }

    init() {
        this.connectWebSocket();
        this.setupEventListeners();
        this.loadSettings();
    }

    connectWebSocket() {
        // Connect to local FastAPI server
        this.ws = new WebSocket('ws://localhost:8765/ws');

        this.ws.onopen = () => {
            console.log('Connected to card reader service');
            this.updateStatus('connected');
            this.clearReconnectInterval();
        };

        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
        };

        this.ws.onclose = () => {
            console.log('Disconnected from card reader service');
            this.updateStatus('disconnected');
            this.scheduleReconnect();
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.updateStatus('error');
        };
    }

    handleMessage(message) {
        switch (message.type) {
            case 'connected':
                this.showNotification('Connected to card reader', 'success');
                break;

            case 'card_inserted':
                this.showNotification('Card detected', 'info');
                break;

            case 'card_read':
                this.displayCardData(message.data);
                if (this.autoCopyEnabled) {
                    this.copyToClipboard(message.data.cid);
                }
                break;

            case 'card_removed':
                this.showNotification('Card removed', 'info');
                this.clearCardData();
                break;

            case 'error':
                this.showNotification(message.message, 'error');
                break;
        }
    }

    displayCardData(data) {
        this.cardData = data;

        // Update UI elements
        document.getElementById('cid').textContent = data.cid;
        document.getElementById('name-th').textContent = data.name_th;
        document.getElementById('name-en').textContent = data.name_en;
        document.getElementById('dob').textContent = data.date_of_birth;
        document.getElementById('address').textContent = data.address;

        // Display photo if available
        if (data.photo_base64) {
            document.getElementById('photo').src = data.photo_base64;
        }

        // Show copy buttons
        document.querySelectorAll('.copy-btn').forEach(btn => {
            btn.style.display = 'inline-block';
        });
    }

    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.showNotification('Copied to clipboard!', 'success');
        } catch (err) {
            console.error('Failed to copy:', err);
            this.showNotification('Failed to copy', 'error');
        }
    }

    copyField(fieldName) {
        if (this.cardData && this.cardData[fieldName]) {
            this.copyToClipboard(this.cardData[fieldName]);
        }
    }

    scheduleReconnect() {
        if (!this.reconnectInterval) {
            this.reconnectInterval = setInterval(() => {
                console.log('Attempting to reconnect...');
                this.connectWebSocket();
            }, 3000);
        }
    }

    clearReconnectInterval() {
        if (this.reconnectInterval) {
            clearInterval(this.reconnectInterval);
            this.reconnectInterval = null;
        }
    }

    updateStatus(status) {
        const indicator = document.getElementById('status-indicator');
        indicator.className = `status-${status}`;
        indicator.textContent = status.charAt(0).toUpperCase() + status.slice(1);
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new ThaiIDCardApp();
});
```

#### UI Design (index.html excerpt)
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Thai ID Card Reader</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>Thai ID Card Reader</h1>
            <div class="status">
                <span id="status-indicator" class="status-disconnected">Disconnected</span>
            </div>
        </header>

        <main>
            <div class="card-display">
                <div class="photo-section">
                    <img id="photo" src="" alt="Card Photo" />
                </div>

                <div class="info-section">
                    <div class="field">
                        <label>Citizen ID:</label>
                        <span id="cid">-</span>
                        <button class="copy-btn" onclick="app.copyField('cid')">📋</button>
                    </div>

                    <div class="field">
                        <label>Name (Thai):</label>
                        <span id="name-th">-</span>
                        <button class="copy-btn" onclick="app.copyField('name_th')">📋</button>
                    </div>

                    <div class="field">
                        <label>Name (English):</label>
                        <span id="name-en">-</span>
                        <button class="copy-btn" onclick="app.copyField('name_en')">📋</button>
                    </div>

                    <div class="field">
                        <label>Date of Birth:</label>
                        <span id="dob">-</span>
                        <button class="copy-btn" onclick="app.copyField('date_of_birth')">📋</button>
                    </div>

                    <div class="field">
                        <label>Address:</label>
                        <span id="address">-</span>
                        <button class="copy-btn" onclick="app.copyField('address')">📋</button>
                    </div>
                </div>
            </div>

            <div class="controls">
                <button onclick="app.ws.send(JSON.stringify({type: 'read_card'}))">
                    🔄 Read Card Manually
                </button>
                <label>
                    <input type="checkbox" id="auto-copy" checked
                           onchange="app.autoCopyEnabled = this.checked">
                    Auto-copy CID
                </label>
            </div>
        </main>
    </div>

    <script src="app.js"></script>
</body>
</html>
```

### 4. Chrome Extension

#### Manifest V3 Structure
```
chrome_extension/
├── manifest.json
├── background.js           # Service worker
├── popup.html             # Extension popup UI
├── popup.js               # Popup logic
├── content.js             # Content script (optional)
└── icons/
    ├── icon16.png
    ├── icon48.png
    └── icon128.png
```

#### manifest.json
```json
{
  "manifest_version": 3,
  "name": "Thai ID Card Reader",
  "version": "1.0.0",
  "description": "Connect to local Thai ID card reader for easy data entry",
  "permissions": [
    "storage",
    "clipboardWrite",
    "notifications"
  ],
  "host_permissions": [
    "http://localhost:*/*",
    "http://127.0.0.1:*/*"
  ],
  "background": {
    "service_worker": "background.js"
  },
  "action": {
    "default_popup": "popup.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png",
      "128": "icons/icon128.png"
    }
  },
  "icons": {
    "16": "icons/icon16.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  }
}
```

#### background.js (Service Worker)
```javascript
// Persistent WebSocket connection in service worker
let ws = null;
let lastCardData = null;
let reconnectInterval = null;

// Connect to local FastAPI server
function connectWebSocket() {
    ws = new WebSocket('ws://localhost:8765/ws');

    ws.onopen = () => {
        console.log('Extension connected to card reader');
        updateBadge('✓', '#4CAF50');
        clearReconnectInterval();
    };

    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleMessage(message);
    };

    ws.onclose = () => {
        console.log('Extension disconnected from card reader');
        updateBadge('✗', '#f44336');
        scheduleReconnect();
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        updateBadge('!', '#ff9800');
    };
}

function handleMessage(message) {
    switch (message.type) {
        case 'card_read':
            lastCardData = message.data;

            // Store in chrome.storage for popup access
            chrome.storage.local.set({ lastCardData: message.data });

            // Show notification
            chrome.notifications.create({
                type: 'basic',
                iconUrl: 'icons/icon48.png',
                title: 'Card Read',
                message: `CID: ${message.data.cid}`,
                priority: 2
            });

            // Update badge
            updateBadge('NEW', '#2196F3');

            break;

        case 'card_removed':
            chrome.notifications.create({
                type: 'basic',
                iconUrl: 'icons/icon48.png',
                title: 'Card Removed',
                message: 'Thai ID card has been removed',
                priority: 1
            });
            break;
    }
}

function updateBadge(text, color) {
    chrome.action.setBadgeText({ text });
    chrome.action.setBadgeBackgroundColor({ color });
}

function scheduleReconnect() {
    if (!reconnectInterval) {
        reconnectInterval = setInterval(() => {
            connectWebSocket();
        }, 3000);
    }
}

function clearReconnectInterval() {
    if (reconnectInterval) {
        clearInterval(reconnectInterval);
        reconnectInterval = null;
    }
}

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'getLastCardData') {
        sendResponse({ data: lastCardData });
    } else if (request.action === 'requestRead') {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'read_card' }));
            sendResponse({ success: true });
        } else {
            sendResponse({ success: false, error: 'Not connected' });
        }
    }
    return true; // Keep channel open for async response
});

// Initialize on install/startup
chrome.runtime.onInstalled.addListener(() => {
    connectWebSocket();
});

chrome.runtime.onStartup.addListener(() => {
    connectWebSocket();
});

// Initialize immediately
connectWebSocket();
```

#### popup.html
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {
            width: 350px;
            padding: 16px;
            font-family: system-ui, -apple-system, sans-serif;
            margin: 0;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }

        .status {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }

        .status.connected { background: #4CAF50; color: white; }
        .status.disconnected { background: #f44336; color: white; }

        .field {
            margin-bottom: 12px;
            padding: 8px;
            background: #f5f5f5;
            border-radius: 4px;
        }

        .field label {
            display: block;
            font-size: 11px;
            color: #666;
            margin-bottom: 4px;
        }

        .field .value {
            font-size: 14px;
            color: #333;
            word-break: break-word;
        }

        .copy-btn {
            margin-top: 4px;
            padding: 4px 12px;
            background: #2196F3;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        }

        .copy-btn:hover {
            background: #1976D2;
        }

        .photo {
            max-width: 100%;
            border-radius: 4px;
            margin-bottom: 12px;
        }

        .actions {
            margin-top: 16px;
            display: flex;
            gap: 8px;
        }

        .btn {
            flex: 1;
            padding: 8px;
            background: #673AB7;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 13px;
        }

        .btn:hover {
            background: #5E35B1;
        }

        .no-data {
            text-align: center;
            padding: 32px;
            color: #999;
        }
    </style>
</head>
<body>
    <div class="header">
        <h2 style="margin: 0; font-size: 16px;">Thai ID Card Reader</h2>
        <span id="status" class="status disconnected">Disconnected</span>
    </div>

    <div id="card-data" style="display: none;">
        <img id="photo" class="photo" alt="Card Photo" />

        <div class="field">
            <label>Citizen ID</label>
            <div class="value" id="cid"></div>
            <button class="copy-btn" data-field="cid">Copy</button>
        </div>

        <div class="field">
            <label>Name (Thai)</label>
            <div class="value" id="name-th"></div>
            <button class="copy-btn" data-field="name_th">Copy</button>
        </div>

        <div class="field">
            <label>Name (English)</label>
            <div class="value" id="name-en"></div>
            <button class="copy-btn" data-field="name_en">Copy</button>
        </div>

        <div class="field">
            <label>Date of Birth</label>
            <div class="value" id="dob"></div>
            <button class="copy-btn" data-field="date_of_birth">Copy</button>
        </div>
    </div>

    <div id="no-data" class="no-data">
        No card data available.<br>
        Insert a card to read.
    </div>

    <div class="actions">
        <button class="btn" id="read-btn">🔄 Read Card</button>
        <button class="btn" id="open-web-btn">🌐 Open Web App</button>
    </div>

    <script src="popup.js"></script>
</body>
</html>
```

#### popup.js
```javascript
let cardData = null;

// Load card data from storage
chrome.storage.local.get(['lastCardData'], (result) => {
    if (result.lastCardData) {
        displayCardData(result.lastCardData);
    }
});

// Check connection status from background
chrome.runtime.sendMessage({ action: 'getLastCardData' }, (response) => {
    if (response.data) {
        displayCardData(response.data);
    }
});

function displayCardData(data) {
    cardData = data;

    document.getElementById('no-data').style.display = 'none';
    document.getElementById('card-data').style.display = 'block';

    document.getElementById('cid').textContent = data.cid;
    document.getElementById('name-th').textContent = data.name_th;
    document.getElementById('name-en').textContent = data.name_en;
    document.getElementById('dob').textContent = data.date_of_birth;

    if (data.photo_base64) {
        document.getElementById('photo').src = data.photo_base64;
        document.getElementById('photo').style.display = 'block';
    }

    // Update status
    document.getElementById('status').className = 'status connected';
    document.getElementById('status').textContent = 'Connected';
}

// Copy button handlers
document.querySelectorAll('.copy-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        const field = e.target.dataset.field;
        if (cardData && cardData[field]) {
            navigator.clipboard.writeText(cardData[field]).then(() => {
                e.target.textContent = '✓ Copied!';
                setTimeout(() => {
                    e.target.textContent = 'Copy';
                }, 2000);
            });
        }
    });
});

// Read button handler
document.getElementById('read-btn').addEventListener('click', () => {
    chrome.runtime.sendMessage({ action: 'requestRead' }, (response) => {
        if (response.success) {
            document.getElementById('read-btn').textContent = '⏳ Reading...';
        } else {
            alert('Not connected to card reader service');
        }
    });
});

// Open web app button
document.getElementById('open-web-btn').addEventListener('click', () => {
    chrome.tabs.create({ url: 'http://localhost:8765' });
});

// Listen for updates from background
chrome.storage.onChanged.addListener((changes, namespace) => {
    if (namespace === 'local' && changes.lastCardData) {
        displayCardData(changes.lastCardData.newValue);

        // Reset read button text
        document.getElementById('read-btn').textContent = '🔄 Read Card';
    }
});
```

---

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1)
1. Set up project structure with separate packages
2. Implement FastAPI server with basic REST endpoints
3. Add WebSocket support and connection manager
4. Implement card monitoring service
5. Create basic system tray application
6. Test card reading integration

**Deliverables:**
- Working local server on localhost:8765
- System tray app that starts/stops server
- Basic card reading via API

### Phase 2: Web Application (Week 2)
1. Create web application UI
2. Implement WebSocket client
3. Add card data display
4. Implement copy functionality
5. Add auto-copy on card read
6. Polish UI/UX

**Deliverables:**
- Functional web app at http://localhost:8765
- Real-time card updates
- One-click copy for all fields

### Phase 3: Chrome Extension (Week 3)
1. Create extension manifest and structure
2. Implement service worker with WebSocket
3. Create popup UI
4. Add notification system
5. Implement copy functionality
6. Add badge indicators

**Deliverables:**
- Installable Chrome extension
- Real-time notifications
- Quick access popup

### Phase 4: Polish & Packaging (Week 4)
1. Add error handling and recovery
2. Implement settings/configuration
3. Add auto-start capability
4. Create installers for Windows/macOS/Linux
5. Write documentation
6. Perform security audit

**Deliverables:**
- Production-ready installers
- Complete documentation
- Security review completed

---

## Installation & Deployment

### Desktop Client Distribution

#### Windows
```bash
# Using PyInstaller
pyinstaller --windowed --onefile \
    --icon=resources/icon.ico \
    --name="Thai ID Card Reader" \
    desktop_client/main.py

# Or use cx_Freeze for better results
python setup.py bdist_msi
```

#### macOS
```bash
# Create .app bundle
pyinstaller --windowed --onefile \
    --icon=resources/icon.icns \
    --name="Thai ID Card Reader" \
    --osx-bundle-identifier="com.pythaiidcard.reader" \
    desktop_client/main.py

# Create DMG
hdiutil create -volname "Thai ID Card Reader" \
    -srcfolder dist/Thai\ ID\ Card\ Reader.app \
    -ov -format UDZO ThaiIDCardReader.dmg
```

#### Linux
```bash
# Create AppImage or .deb package
# Using fpm (Effing Package Management)
fpm -s dir -t deb \
    --name thai-id-card-reader \
    --version 1.0.0 \
    --architecture amd64 \
    --depends python3.13 \
    --depends pcscd \
    usr/local/bin/pythaiidcard-desktop
```

### Chrome Extension Distribution

#### For Development
1. Open `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select the `chrome_extension` directory

#### For Production
1. Create ZIP of extension directory
2. Upload to Chrome Web Store
3. Submit for review
4. Publish to users

---

## Security Considerations

### Local Server Security
1. **Localhost Only**: Bind to 127.0.0.1 only, never 0.0.0.0
2. **No Authentication**: Not needed for localhost
3. **CORS**: Restrict to localhost origins
4. **Data Privacy**: Never log sensitive card data
5. **HTTPS**: Not required for localhost, but consider for production

### Chrome Extension Security
1. **Manifest V3**: Use latest security standards
2. **Minimal Permissions**: Only request necessary permissions
3. **CSP**: Implement Content Security Policy
4. **No External Calls**: All data stays local
5. **Data Storage**: Use chrome.storage.local (encrypted)

### Desktop Client Security
1. **Auto-update**: Implement secure update mechanism
2. **Code Signing**: Sign executables (Windows/macOS)
3. **Permissions**: Request minimal system permissions
4. **No Telemetry**: Keep all data local unless opted-in

---

## Testing Strategy

### Unit Tests
- Card reader service logic
- API endpoint functionality
- WebSocket message handling
- Data validation (Pydantic models)

### Integration Tests
- Full card read workflow
- WebSocket connection lifecycle
- API + WebSocket interaction
- Cross-component communication

### End-to-End Tests
- Desktop app → Server → Web app flow
- Desktop app → Server → Extension flow
- Card insertion/removal detection
- Multiple simultaneous connections

### Manual Testing Checklist
- [ ] System tray icon updates correctly
- [ ] Server starts/stops cleanly
- [ ] Web app connects and displays data
- [ ] Extension receives notifications
- [ ] Copy functionality works in all contexts
- [ ] Reconnection works after disconnect
- [ ] Multiple clients can connect simultaneously
- [ ] Photo display works correctly
- [ ] Buddhist Era dates convert properly
- [ ] Card removal is detected

---

## Performance Optimization

### Server Performance
- Use async/await throughout
- Implement connection pooling for card reader
- Cache last read card data
- Debounce rapid card reads
- Limit photo resolution if needed

### Web App Performance
- Lazy load photo data
- Debounce copy operations
- Minimize DOM updates
- Use requestAnimationFrame for animations
- Implement service worker for offline capability

### Extension Performance
- Keep service worker lightweight
- Use chrome.storage for persistence
- Debounce notifications
- Lazy load popup UI

---

## Alternative Architectures Considered

### 1. Native Messaging (Rejected)
**Pros:**
- Official Chrome extension method
- No server required

**Cons:**
- Complex setup (manifest host registry)
- No web app support
- Per-extension instance
- Harder to debug

### 2. Electron + Python Backend (Rejected)
**Pros:**
- Single package for everything
- Modern web UI
- Great developer experience

**Cons:**
- Large bundle size (150MB+)
- Higher resource usage
- Overkill for this use case

### 3. Pure WebSocket Server (Current Choice)
**Pros:**
- Simple architecture
- Cross-platform clients
- Low resource usage
- Easy to extend
- Standard protocols

**Cons:**
- Requires local server
- Multiple components to distribute

---

## Dependencies & Requirements

### Python Package Dependencies
```toml
[project]
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "pyscard>=2.3.0",
    "pydantic>=2.0",
    "pillow>=11.3.0",
    "python-dateutil>=2.8.2",
]

[dependency-groups]
desktop = [
    "PySide6>=6.8.0",
    "pyinstaller>=6.0.0",
]
dev = [
    "ruff>=0.8.4",
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
]
```

### System Dependencies
- **Linux**: pcscd, libpcsclite-dev, swig, python3-dev
- **Windows**: PC/SC drivers (usually included)
- **macOS**: PC/SC framework (included in OS)

---

## Documentation Deliverables

### User Documentation
1. Installation Guide (per platform)
2. Quick Start Guide
3. Troubleshooting Guide
4. FAQ

### Developer Documentation
1. API Reference (auto-generated from FastAPI)
2. Architecture Overview (this document)
3. Contributing Guide
4. Testing Guide

### End-User Guides
1. Desktop Client User Manual
2. Web App User Guide
3. Chrome Extension User Guide
4. Video Tutorials (optional)

---

## Success Metrics

### Technical Metrics
- WebSocket connection latency < 100ms
- Card read time < 2 seconds (including photo)
- Memory usage < 100MB (desktop client)
- CPU usage < 5% when idle
- Zero data loss during reconnection

### User Experience Metrics
- Installation time < 5 minutes
- First card read < 30 seconds after install
- Copy operation < 1 second
- UI response time < 100ms
- Reconnection time < 3 seconds

---

## Future Enhancements

### Phase 5+ (Future)
1. **Multi-card Support**: Handle multiple readers simultaneously
2. **History/Logging**: Optional encrypted log of card reads
3. **Cloud Sync**: Optional cloud backup (with encryption)
4. **Batch Reading**: Queue multiple card reads
5. **Custom Fields**: User-defined field extraction
6. **Webhooks**: POST card data to custom endpoints
7. **Mobile App**: iOS/Android companion app
8. **OCR Fallback**: Camera-based card reading
9. **QR Code Export**: Generate QR from card data
10. **Print Templates**: Customizable print formats

---

## Conclusion

This architecture provides a solid foundation for cross-platform Thai ID card reading with real-time streaming to both web applications and Chrome extensions. The use of standard protocols (WebSocket, REST API) and modern frameworks (FastAPI, PySide6) ensures maintainability and extensibility.

### Key Advantages
- **Cross-platform**: Windows, macOS, Linux support
- **Multiple clients**: Web app + Chrome extension
- **Real-time**: WebSocket streaming for instant updates
- **Easy to use**: One-click copy, auto-copy options
- **Maintainable**: Clean architecture, standard protocols
- **Extensible**: Easy to add new clients or features

### Next Steps
1. Review and approve this plan
2. Set up development environment
3. Begin Phase 1 implementation
4. Iterate based on testing feedback
