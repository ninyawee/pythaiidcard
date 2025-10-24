# Phase 1 Implementation - Desktop Client Core Infrastructure

## Overview

Phase 1 delivers the core infrastructure for the Thai ID Card Reader desktop client system:

- ✅ **FastAPI Server** with REST API and WebSocket support
- ✅ **Card Monitoring Service** for automatic card detection
- ✅ **System Tray Application** for server management
- ✅ **Web Application** for real-time card data display

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Desktop Client                            │
│  ┌────────────────┐        ┌──────────────────────────┐    │
│  │  System Tray   │───────▶│   FastAPI Server         │    │
│  │  (PySide6)     │        │   localhost:8765         │    │
│  │                │        │   - REST API /api/*      │    │
│  │  - Start/Stop  │        │   - WebSocket /ws        │    │
│  │  - Settings    │        │   - Web App /            │    │
│  └────────────────┘        └──────────┬───────────────┘    │
│                                       │                     │
│                            ┌──────────▼───────────────┐    │
│                            │  Card Monitor Service    │    │
│                            │  - Auto-detect cards     │    │
│                            │  - Read card data        │    │
│                            │  - Broadcast events      │    │
│                            └──────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                                       │
                                       │ WebSocket
                                       │
                          ┌────────────▼─────────────┐
                          │   Web Application        │
                          │   (Browser)              │
                          │   - Real-time updates    │
                          │   - Auto-copy CID        │
                          │   - Manual copy buttons  │
                          └──────────────────────────┘
```

## Project Structure

```
pythaiidcard/
├── api_server/                 # FastAPI server package
│   ├── __init__.py
│   ├── main.py                # Main FastAPI app with WebSocket
│   ├── models/
│   │   ├── __init__.py
│   │   └── api_models.py      # Pydantic models for API
│   ├── routes/
│   │   ├── __init__.py
│   │   └── api.py             # REST API endpoints
│   └── services/
│       ├── __init__.py
│       ├── connection_manager.py  # WebSocket connections
│       └── card_monitor.py        # Card monitoring service
│
├── desktop_client/             # Desktop tray application
│   ├── __init__.py
│   ├── main.py                # Entry point
│   ├── tray_app.py            # PySide6 system tray app
│   ├── server_manager.py      # Server lifecycle control
│   └── settings.py            # Configuration management
│
└── web_app/                    # Web application
    ├── index.html             # Main UI
    ├── styles.css             # Styling
    └── app.js                 # WebSocket client logic
```

## Installation

### 1. Install Dependencies

First, install the desktop dependencies:

```bash
# Install desktop dependencies (includes FastAPI, Uvicorn, PySide6)
uv sync --group desktop
```

### 2. System Dependencies (Linux)

If you're on Linux, ensure PC/SC daemon is installed:

```bash
sudo apt-get update
sudo apt-get install pcscd libpcsclite-dev
sudo systemctl start pcscd
```

## Usage

### Option 1: Desktop Client (Recommended)

The desktop client runs a system tray application that manages the server:

```bash
# Run the desktop client
uv run pythaiidcard-desktop
```

**Features:**
- System tray icon
- Right-click menu with options:
  - Start/Stop Server
  - Restart Server
  - Open Web Interface
  - Open API Docs
  - About
  - Exit
- Double-click tray icon to open web interface
- Auto-start option (configurable)

### Option 2: Server Only

Run just the API server without the tray application:

```bash
# Run server directly
uv run pythaiidcard-server

# Or with Python
uv run python -m api_server.main
```

The server will start on `http://localhost:8765`

## Testing Phase 1

### 1. Start the Desktop Client

```bash
uv run pythaiidcard-desktop
```

You should see:
- A system tray icon appear
- Log output showing initialization
- Server status in the tray menu

### 2. Start the Server

Right-click the tray icon and select **"Start Server"**

You should see:
- A notification "Server Started"
- Status changes to "Server: Running (:8765)"
- Log shows "Server started on 127.0.0.1:8765"

### 3. Open the Web Application

**Method 1:** Double-click the tray icon

**Method 2:** Right-click → "Open Web Interface"

**Method 3:** Open browser manually to `http://localhost:8765`

### 4. Test Card Reading

**Without a physical card reader:**
The application will show "No card readers detected" in the logs.

**With a card reader:**
1. Connect your PC/SC card reader
2. Insert a Thai National ID card
3. The application will:
   - Detect the card automatically
   - Read the card data
   - Display it in the web interface
   - Auto-copy the CID (if enabled)

### 5. Test WebSocket Connection

Open the browser console (F12) and observe:
- WebSocket connection messages
- Real-time event updates
- Card read events

### 6. Test API Endpoints

Open these URLs in your browser:

- **API Documentation:** `http://localhost:8765/docs`
- **Server Status:** `http://localhost:8765/api/status`
- **List Readers:** `http://localhost:8765/api/readers`
- **Health Check:** `http://localhost:8765/api/health`

## API Reference

### REST Endpoints

#### GET /api/status
Get server and reader status.

**Response:**
```json
{
  "status": "running",
  "version": "1.0.0",
  "readers_available": 1,
  "card_detected": true,
  "reader_name": "Alcor Link AK9563",
  "timestamp": "2025-10-24T10:30:00Z"
}
```

#### GET /api/readers
List all available card readers.

**Response:**
```json
{
  "readers": ["Alcor Link AK9563"],
  "count": 1,
  "timestamp": "2025-10-24T10:30:00Z"
}
```

#### GET /api/card/current
Get the last read card data (cached, without photo).

**Response:**
```json
{
  "success": true,
  "data": {
    "cid": "1234567890123",
    "name_th": "นาย ทดสอบ ระบบ",
    "name_en": "Mr. Test System",
    "date_of_birth": "1990-01-15",
    "address": "123 ถนนทดสอบ...",
    ...
  },
  "timestamp": "2025-10-24T10:30:05Z"
}
```

#### POST /api/card/read
Trigger a manual card read.

**Query Parameters:**
- `include_photo` (boolean, default: true) - Whether to include photo

**Response:**
```json
{
  "success": true,
  "data": { ... },
  "timestamp": "2025-10-24T10:30:05Z"
}
```

### WebSocket Protocol

**Endpoint:** `ws://localhost:8765/ws`

#### Client → Server (Commands)

**Read Card:**
```json
{
  "type": "read_card",
  "include_photo": true
}
```

**Ping:**
```json
{
  "type": "ping"
}
```

#### Server → Client (Events)

**Connected:**
```json
{
  "type": "connected",
  "message": "WebSocket connected to Thai ID Card Reader",
  "timestamp": "2025-10-24T10:30:00Z"
}
```

**Card Inserted:**
```json
{
  "type": "card_inserted",
  "message": "Card detected",
  "reader": "Alcor Link AK9563",
  "timestamp": "2025-10-24T10:30:02Z"
}
```

**Card Read:**
```json
{
  "type": "card_read",
  "message": "Card data read successfully",
  "reader": "Alcor Link AK9563",
  "data": {
    "cid": "1234567890123",
    "name_th": "นาย ทดสอบ ระบบ",
    "name_en": "Mr. Test System",
    "photo_base64": "data:image/jpeg;base64,/9j/4AAQ...",
    ...
  },
  "timestamp": "2025-10-24T10:30:05Z"
}
```

**Card Removed:**
```json
{
  "type": "card_removed",
  "message": "Card removed",
  "reader": "Alcor Link AK9563",
  "timestamp": "2025-10-24T10:35:00Z"
}
```

**Error:**
```json
{
  "type": "error",
  "message": "Failed to read card: No card detected",
  "error_code": "CARD_READ_ERROR",
  "timestamp": "2025-10-24T10:30:00Z"
}
```

## Web Application Features

### Real-Time Updates
- WebSocket connection with auto-reconnect
- Live card insertion/removal detection
- Automatic card reading on insertion
- Event log with timestamps

### Card Data Display
- Photo display (JPEG from card)
- All card fields in Thai and English
- Formatted date fields
- Gender display

### Copy Functionality
- **Auto-copy CID:** Automatically copies Citizen ID on card read (toggleable)
- **Manual copy:** Click 📋 button next to any field
- **Visual feedback:** Button changes to ✓ when copied
- **Toast notifications:** Confirmation messages

### Connection Status
- Real-time connection indicator (green/red dot)
- Connection info display
- Auto-reconnect on disconnect

### Event Log
- All events logged with timestamps
- Color-coded by type (info/success/warning/error)
- Auto-scroll to latest
- Clear log button

## Configuration

Settings are stored in `~/.pythaiidcard/settings.json`

**Default Settings:**
```json
{
  "port": 8765,
  "host": "127.0.0.1",
  "auto_start": false,
  "notifications_enabled": true,
  "auto_copy_enabled": true
}
```

**Configuration Options:**
- `port`: Server port (default: 8765)
- `host`: Server host (default: 127.0.0.1 for security)
- `auto_start`: Auto-start server when app launches
- `notifications_enabled`: Show system tray notifications
- `auto_copy_enabled`: Auto-copy CID on card read

## Troubleshooting

### Server won't start

**Check port availability:**
```bash
# Linux/macOS
lsof -i :8765

# Windows
netstat -ano | findstr :8765
```

**Solution:** Change port in settings or stop conflicting process

### No card readers detected

**Linux - Check PC/SC daemon:**
```bash
sudo systemctl status pcscd
sudo systemctl start pcscd
```

**Verify reader:**
```bash
pcsc_scan
```

### WebSocket connection fails

**Check:**
1. Server is running (check tray icon status)
2. No firewall blocking localhost
3. Browser console for error messages
4. Try `ws://127.0.0.1:8765/ws` instead of `localhost`

### Card read fails

**Common issues:**
1. Card not fully inserted
2. Dirty card contacts
3. Reader not compatible
4. PC/SC daemon not running

**Check logs:**
- Desktop client: `pythaiidcard-desktop.log`
- Server: Console output

## Logs

### Desktop Client Logs
Location: `./pythaiidcard-desktop.log`

### Server Logs
Printed to console (stdout)

### Log Levels
- `INFO`: Normal operations
- `WARNING`: Non-critical issues
- `ERROR`: Failed operations
- `DEBUG`: Detailed debugging (not enabled by default)

## Next Steps

Phase 1 is complete! Next phases:

**Phase 2:** Enhanced web application
- Improved UI/UX
- Settings panel
- Card history
- Export functionality

**Phase 3:** Chrome Extension
- Popup interface
- Background service worker
- Notifications
- Quick access

**Phase 4:** Production deployment
- Installers for Windows/macOS/Linux
- Auto-update mechanism
- Enhanced security
- Documentation

## Known Limitations

1. **Single reader support:** Only uses first detected reader
2. **No history:** Card data not persisted
3. **Basic UI:** Web app is functional but minimal
4. **No settings UI:** Settings must be edited manually
5. **No auto-start:** Must start desktop client manually

These will be addressed in future phases.

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review logs for error messages
3. Check GitHub issues: https://github.com/ninyawee/pythaiidcard/issues
4. Refer to main project documentation

## License

ISC License - See LICENSE file for details
