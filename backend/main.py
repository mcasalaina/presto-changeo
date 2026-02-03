"""
Presto-Change-O Backend
FastAPI application with WebSocket endpoint for real-time communication.
"""
import json
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from azure.ai.inference.models import SystemMessage, UserMessage

from auth import get_inference_client
from chat import handle_chat_message, clear_history, ensure_persona, get_session_seed
from voice import handle_voice_session
from modes import get_current_mode

MODEL_DEPLOYMENT = os.getenv("AZURE_MODEL_DEPLOYMENT", "gpt-5-mini")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def verify_llm_connection() -> None:
    """
    Verify LLM connection at startup by running a test prompt.

    This forces authentication and validates the model is responding.
    Raises an exception if connection fails, preventing server startup.
    """
    logger.info("Verifying LLM connection...")
    logger.info("(Browser login may be required)")

    client = get_inference_client()

    # Send a minimal test prompt
    response = client.complete(
        model=MODEL_DEPLOYMENT,
        messages=[
            SystemMessage(content="You are a test assistant."),
            UserMessage(content="Say hello"),
        ],
    )

    # Log full response for debugging
    logger.info(f"LLM response object: {response}")

    # If we got here without exception, connection works
    if response.choices:
        content = response.choices[0].message.content if response.choices[0].message else ""
        logger.info(f"LLM connection verified. Response: {content[:50] if content else '(empty)'}")
    else:
        logger.info("LLM connection verified (no choices in response, but no error)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    logger.info("Presto-Change-O backend starting...")

    # Verify LLM connection before accepting requests
    verify_llm_connection()

    logger.info("Server running on http://localhost:8000")
    logger.info("WebSocket endpoint available at ws://localhost:8000/ws")
    logger.info("Voice WebSocket endpoint available at ws://localhost:8000/voice")
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


@app.get("/api/state")
async def get_state():
    """
    Get the current application state (mode + persona).
    Called by frontend on startup to restore previous session.
    """
    current_mode = get_current_mode()
    persona = ensure_persona(current_mode.id)

    return {
        "mode": {
            "id": current_mode.id,
            "name": current_mode.name,
            "company_name": current_mode.company_name,
            "tagline": current_mode.tagline,
            "theme": current_mode.theme.model_dump(),
            "tabs": [tab.model_dump() for tab in current_mode.tabs],
            "defaultMetrics": [m.model_dump() for m in current_mode.default_metrics]
        },
        "persona": persona
    }


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
                elif message_type == "clear_chat":
                    # Clear conversation history
                    clear_history()
                    logger.info("Conversation history cleared")
                    await websocket.send_text(json.dumps({
                        "type": "chat_cleared",
                        "payload": {}
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


@app.websocket("/voice")
async def voice_endpoint(websocket: WebSocket):
    """WebSocket endpoint for voice interactions with gpt-realtime."""
    await websocket.accept()
    logger.info("Voice WebSocket connection established")
    try:
        await handle_voice_session(websocket)
    except WebSocketDisconnect:
        logger.info("Voice WebSocket connection closed")
    except Exception as e:
        logger.error(f"Voice WebSocket error: {e}")
