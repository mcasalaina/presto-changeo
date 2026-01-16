"""
Presto-Change-O Backend
FastAPI application with WebSocket endpoint for real-time communication.
"""
import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from chat import handle_chat_message

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    logger.info("Presto-Change-O backend starting...")
    logger.info("Server running on http://localhost:8000")
    logger.info("WebSocket endpoint available at ws://localhost:8000/ws")
    yield
    logger.info("Presto-Change-O backend shutting down...")


app = FastAPI(
    title="Presto-Change-O",
    description="AI-powered multi-industry simulation dashboard backend",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS for frontend development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "presto-changeo"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time communication.

    Routes messages by type:
    - "chat": Routes to LLM chat handler for streaming response
    - Other types: Echo back for debugging

    Message format expected:
    {"type": "chat", "payload": {"text": "user message"}}
    """
    await websocket.accept()
    logger.info("WebSocket connection established")

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            logger.info(f"Received message: {data[:100]}...")

            try:
                # Parse JSON message
                message = json.loads(data)
                message_type = message.get("type")

                if message_type == "chat":
                    # Route to chat handler
                    text = message.get("payload", {}).get("text", "")
                    if text:
                        await handle_chat_message(text, websocket)
                    else:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "payload": {"error": "Chat message text is required"}
                        }))
                else:
                    # Echo for unknown types (debugging)
                    await websocket.send_text(f"Echo: {data}")

            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON received: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "payload": {"error": f"Invalid JSON: {str(e)}"}
                }))

    except WebSocketDisconnect:
        logger.info("WebSocket connection closed")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1011, reason=str(e))
