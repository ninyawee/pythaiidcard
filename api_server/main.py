"""Main FastAPI application for Thai ID Card Reader server."""

import asyncio
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn

from .services.connection_manager import ConnectionManager
from .services.card_monitor import CardMonitorService
from .routes import api
from .models.api_models import WebSocketEvent, WebSocketEventType, WebSocketCommandType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global instances
connection_manager = ConnectionManager()
card_monitor = CardMonitorService(connection_manager)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Starts card monitoring on startup and stops it on shutdown.
    """
    # Startup
    logger.info("Starting Thai ID Card Reader API server")

    # Start card monitoring in background
    monitor_task = asyncio.create_task(card_monitor.start_monitoring())

    yield

    # Shutdown
    logger.info("Shutting down Thai ID Card Reader API server")
    card_monitor.stop_monitoring()

    # Wait for monitor task to complete
    try:
        await asyncio.wait_for(monitor_task, timeout=5.0)
    except asyncio.TimeoutError:
        logger.warning("Card monitor task did not complete in time")


# Create FastAPI application
app = FastAPI(
    title="Thai ID Card Reader API",
    description="Local API server for reading Thai National ID cards with real-time WebSocket streaming",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS for local access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:*",
        "http://127.0.0.1:*",
        "chrome-extension://*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set card monitor in API routes
api.set_card_monitor(card_monitor)

# Include REST API routes
app.include_router(api.router)

# Mount static files for web app
web_app_path = Path(__file__).parent.parent / "web_app"
if web_app_path.exists():
    app.mount("/static", StaticFiles(directory=str(web_app_path)), name="static")
    logger.info(f"Serving web app from {web_app_path}")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the web application."""
    web_app_index = web_app_path / "index.html"
    if web_app_index.exists():
        return web_app_index.read_text()

    # Fallback welcome page if web app not found
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Thai ID Card Reader API</title>
        <style>
            body {
                font-family: system-ui, -apple-system, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: #f5f5f5;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            h1 { color: #333; }
            .status {
                padding: 10px;
                background: #4CAF50;
                color: white;
                border-radius: 4px;
                display: inline-block;
            }
            a {
                color: #2196F3;
                text-decoration: none;
            }
            a:hover { text-decoration: underline; }
            ul { line-height: 1.8; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Thai ID Card Reader API</h1>
            <p class="status">✓ Server Running</p>

            <h2>Available Endpoints</h2>
            <ul>
                <li><a href="/docs">📖 API Documentation (Swagger)</a></li>
                <li><a href="/redoc">📘 API Documentation (ReDoc)</a></li>
                <li><a href="/api/status">🔍 Server Status</a></li>
                <li><a href="/api/readers">🎴 List Card Readers</a></li>
                <li><a href="/api/health">❤️ Health Check</a></li>
                <li><strong>WebSocket:</strong> ws://localhost:8765/ws</li>
            </ul>

            <h2>Quick Start</h2>
            <p>Connect to the WebSocket endpoint to receive real-time card events:</p>
            <pre style="background: #f5f5f5; padding: 15px; border-radius: 4px; overflow-x: auto;">
const ws = new WebSocket('ws://localhost:8765/ws');

ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    console.log('Event:', message);
};

// Read card manually
ws.send(JSON.stringify({type: 'read_card'}));
            </pre>
        </div>
    </body>
    </html>
    """


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time card events.

    Clients connect here to receive card_inserted, card_removed, and card_read events.
    """
    await connection_manager.connect(websocket)

    try:
        # Send welcome message
        await connection_manager.send_event(
            websocket,
            WebSocketEvent(
                type=WebSocketEventType.CONNECTED,
                message="WebSocket connected to Thai ID Card Reader",
            ),
        )

        # Keep connection alive and handle client commands
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            command_type = data.get("type")
            logger.info(f"Received WebSocket command: {command_type}")

            if command_type == WebSocketCommandType.READ_CARD:
                # Trigger manual card read
                include_photo = data.get("include_photo", True)
                await card_monitor.read_and_broadcast(include_photo=include_photo)

            elif command_type == WebSocketCommandType.PING:
                # Respond to ping
                await connection_manager.send_event(
                    websocket,
                    WebSocketEvent(
                        type=WebSocketEventType.PONG,
                        message="pong",
                    ),
                )

            elif command_type == WebSocketCommandType.SUBSCRIBE:
                # Client subscribing to events (no-op, all events sent by default)
                logger.info(f"Client subscribed to events: {data.get('events', [])}")

            else:
                logger.warning(f"Unknown WebSocket command: {command_type}")

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
        connection_manager.disconnect(websocket)

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        connection_manager.disconnect(websocket)


def start_server(host: str = "127.0.0.1", port: int = 8765, reload: bool = False):
    """
    Start the FastAPI server.

    Args:
        host: Host to bind to (default: 127.0.0.1 for security)
        port: Port to bind to (default: 8765)
        reload: Enable auto-reload for development (default: False)
    """
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(
        "api_server.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


if __name__ == "__main__":
    start_server()
