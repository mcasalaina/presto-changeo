"""
Chat Handler Module
Handles chat messages and streams LLM responses via WebSocket.
"""
import json
import logging
from typing import Any

from fastapi import WebSocket

from azure.ai.inference.models import SystemMessage, UserMessage

from auth import get_inference_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = "You are a helpful AI assistant for Presto-Change-O, an industry simulation dashboard."


async def handle_chat_message(text: str, websocket: WebSocket) -> None:
    """
    Handle a chat message by calling Azure LLM and streaming the response.

    Args:
        text: The user's chat message text
        websocket: The WebSocket connection to stream response to

    Sends messages in format:
        {"type": "chat_start", "payload": {}}
        {"type": "chat_chunk", "payload": {"text": "...", "done": false}}
        {"type": "chat_chunk", "payload": {"text": "", "done": true}}
    """
    logger.info(f"Handling chat message: {text[:100]}...")

    # Notify frontend that response is starting
    await websocket.send_text(json.dumps({
        "type": "chat_start",
        "payload": {}
    }))

    try:
        # Get the inference client
        client = get_inference_client()

        # Prepare messages for the API
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            UserMessage(content=text),
        ]

        logger.info("Calling Azure LLM with streaming...")

        # Call LLM with streaming enabled
        response = client.complete(
            model="model-router",
            messages=messages,
            stream=True,
        )

        # Stream response chunks to frontend
        for chunk in response:
            if chunk.choices and len(chunk.choices) > 0:
                choice = chunk.choices[0]
                if choice.delta and choice.delta.content:
                    chunk_text = choice.delta.content
                    await websocket.send_text(json.dumps({
                        "type": "chat_chunk",
                        "payload": {"text": chunk_text, "done": False}
                    }))

        # Signal completion
        await websocket.send_text(json.dumps({
            "type": "chat_chunk",
            "payload": {"text": "", "done": True}
        }))

        logger.info("Chat response completed")

    except Exception as e:
        logger.error(f"Error calling LLM: {e}")
        # Send error message to frontend
        await websocket.send_text(json.dumps({
            "type": "chat_error",
            "payload": {"error": str(e)}
        }))
