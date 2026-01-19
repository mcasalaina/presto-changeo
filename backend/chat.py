"""
Chat Handler Module
Handles chat messages and streams LLM responses via WebSocket.
"""
import json
import logging
import os
from typing import Any

from fastapi import WebSocket

from azure.ai.inference.models import SystemMessage, UserMessage, AssistantMessage

from auth import get_inference_client

MODEL_DEPLOYMENT = os.getenv("AZURE_MODEL_DEPLOYMENT", "gpt-5-mini")

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a helpful banking assistant for a digital banking dashboard. You help customers with their accounts, transactions, and financial questions.

Keep responses clear, professional, and concise. Speak naturally like a friendly bank representative."""

# Conversation history per connection (simple in-memory storage)
# In production, this would be session-based
_conversation_history: list = []


def get_conversation_history() -> list:
    """Get the current conversation history."""
    return _conversation_history


def add_to_history(role: str, content: str) -> None:
    """Add a message to conversation history."""
    _conversation_history.append({"role": role, "content": content})
    # Keep last 20 messages to avoid context overflow
    if len(_conversation_history) > 20:
        _conversation_history.pop(0)


def clear_history() -> None:
    """Clear conversation history."""
    _conversation_history.clear()


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

        # Add user message to history
        add_to_history("user", text)

        # Build messages with conversation history
        messages = [SystemMessage(content=SYSTEM_PROMPT)]
        for msg in get_conversation_history():
            if msg["role"] == "user":
                messages.append(UserMessage(content=msg["content"]))
            else:
                messages.append(AssistantMessage(content=msg["content"]))

        logger.info(f"Calling Azure LLM with {len(messages)} messages...")

        # Call LLM with streaming enabled
        response = client.complete(
            model=MODEL_DEPLOYMENT,
            messages=messages,
            stream=True,
        )

        # Stream response chunks to frontend and collect full response
        full_response = ""
        for chunk in response:
            if chunk.choices and len(chunk.choices) > 0:
                choice = chunk.choices[0]
                if choice.delta and choice.delta.content:
                    chunk_text = choice.delta.content
                    full_response += chunk_text
                    await websocket.send_text(json.dumps({
                        "type": "chat_chunk",
                        "payload": {"text": chunk_text, "done": False}
                    }))

        # Add assistant response to history
        if full_response:
            add_to_history("assistant", full_response)

        # Signal completion
        await websocket.send_text(json.dumps({
            "type": "chat_chunk",
            "payload": {"text": "", "done": True}
        }))

        logger.info(f"Chat response completed ({len(full_response)} chars)")

    except Exception as e:
        logger.error(f"Error calling LLM: {e}")
        # Send error message to frontend
        await websocket.send_text(json.dumps({
            "type": "chat_error",
            "payload": {"error": str(e)}
        }))
