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
from tools import TOOL_DEFINITIONS, execute_tool

MODEL_DEPLOYMENT = os.getenv("AZURE_MODEL_DEPLOYMENT", "gpt-5-mini")

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a helpful banking assistant for a digital banking dashboard. You help customers with their accounts, transactions, and financial questions.

Keep responses clear, professional, and concise. Speak naturally like a friendly bank representative.

You have access to visualization tools to display data in the dashboard:
- show_chart: Display charts (line, bar, pie, area) with data points
- show_metrics: Display key metrics/KPIs in the metrics panel

IMPORTANT: When you use a visualization tool, you MUST ALWAYS also provide a brief text response describing what you're showing. For example: "Here's your checking account balance over the last 6 months:" followed by the chart. Never call a tool without also providing explanatory text to the user."""

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
        {"type": "tool_result", "payload": {"tool": "...", "result": {...}}}
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

        logger.info(f"Calling Azure LLM with {len(messages)} messages and {len(TOOL_DEFINITIONS)} tools...")

        # Call LLM with streaming enabled and tools
        response = client.complete(
            model=MODEL_DEPLOYMENT,
            messages=messages,
            stream=True,
            tools=TOOL_DEFINITIONS,
        )

        # Stream response chunks to frontend and collect full response
        # Also accumulate tool call data from streaming chunks
        full_response = ""
        tool_calls: dict[int, dict[str, Any]] = {}  # index -> {id, name, arguments}

        for chunk in response:
            if chunk.choices and len(chunk.choices) > 0:
                choice = chunk.choices[0]

                # Handle text content
                if choice.delta and choice.delta.content:
                    chunk_text = choice.delta.content
                    full_response += chunk_text
                    await websocket.send_text(json.dumps({
                        "type": "chat_chunk",
                        "payload": {"text": chunk_text, "done": False}
                    }))

                # Handle tool calls (streamed incrementally)
                if choice.delta and choice.delta.tool_calls:
                    for tool_call in choice.delta.tool_calls:
                        idx = tool_call.index if hasattr(tool_call, 'index') else 0

                        # Initialize tool call entry if new
                        if idx not in tool_calls:
                            tool_calls[idx] = {
                                "id": "",
                                "name": "",
                                "arguments": ""
                            }

                        # Accumulate tool call data
                        if hasattr(tool_call, 'id') and tool_call.id:
                            tool_calls[idx]["id"] = tool_call.id
                        if hasattr(tool_call, 'function'):
                            if hasattr(tool_call.function, 'name') and tool_call.function.name:
                                tool_calls[idx]["name"] = tool_call.function.name
                            if hasattr(tool_call.function, 'arguments') and tool_call.function.arguments:
                                tool_calls[idx]["arguments"] += tool_call.function.arguments

        # Add assistant response to history
        if full_response:
            add_to_history("assistant", full_response)

        # Process completed tool calls
        for idx in sorted(tool_calls.keys()):
            tool_call = tool_calls[idx]
            tool_name = tool_call["name"]
            arguments_str = tool_call["arguments"]

            if tool_name and arguments_str:
                try:
                    arguments = json.loads(arguments_str)
                    logger.info(f"Executing tool: {tool_name} with args: {arguments}")

                    # Execute the tool
                    result = execute_tool(tool_name, arguments)

                    # Send tool result to frontend
                    await websocket.send_text(json.dumps({
                        "type": "tool_result",
                        "payload": {
                            "tool": tool_name,
                            "result": result
                        }
                    }))

                    logger.info(f"Tool {tool_name} executed successfully")

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse tool arguments: {e}")

        # Signal completion
        await websocket.send_text(json.dumps({
            "type": "chat_chunk",
            "payload": {"text": "", "done": True}
        }))

        logger.info(f"Chat response completed ({len(full_response)} chars, {len(tool_calls)} tool calls)")

    except Exception as e:
        logger.error(f"Error calling LLM: {e}")
        # Send error message to frontend
        await websocket.send_text(json.dumps({
            "type": "chat_error",
            "payload": {"error": str(e)}
        }))
