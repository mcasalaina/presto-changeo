"""
Chat Handler Module
Handles chat messages and streams LLM responses via WebSocket.
"""
import hashlib
import json
import logging
import os
import re
from typing import Any

from fastapi import WebSocket

from azure.ai.inference.models import SystemMessage, UserMessage, AssistantMessage

from auth import get_inference_client
from tools import TOOL_DEFINITIONS, execute_tool
from modes import Mode, get_mode, get_current_mode, set_current_mode
from persona import generate_persona

MODEL_DEPLOYMENT = os.getenv("AZURE_MODEL_DEPLOYMENT", "gpt-5-mini")

logger = logging.getLogger(__name__)

# NOTE: System prompt is now dynamic, sourced from get_current_mode().system_prompt
# Old hardcoded prompt removed in favor of mode-specific prompts in modes.py

# Conversation history per connection (simple in-memory storage)
# In production, this would be session-based
_conversation_history: list = []

# Current persona state (module-level, similar to conversation history)
_current_persona: dict = {}


def get_session_seed() -> int:
    """
    Get deterministic seed for persona generation.
    For now, use a fixed seed per session.
    In multi-connection setup, derive from WebSocket connection ID.
    """
    # Simple implementation: use hash of a session marker
    # TODO: In production, derive from actual session/connection ID
    return int(hashlib.md5(b"demo-session").hexdigest()[:8], 16)


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


def build_system_prompt(mode: Mode, persona: dict) -> str:
    """
    Build system prompt with persona context for AI responses.

    Args:
        mode: The current Mode configuration
        persona: The generated persona dictionary

    Returns:
        System prompt string with persona details appended
    """
    base = mode.system_prompt
    if not persona:
        return base

    # Build persona context based on mode type
    if mode.id == "banking":
        persona_context = f"""
Current Customer Profile:
- Name: {persona.get('name')}
- Member Since: {persona.get('member_since')}
- Checking Balance: ${persona.get('checking_balance', 0):,.2f}
- Savings Balance: ${persona.get('savings_balance', 0):,.2f}
- Credit Score: {persona.get('credit_score')}

Reference this customer's information naturally in your responses."""
    elif mode.id == "insurance":
        persona_context = f"""
Current Customer Profile:
- Name: {persona.get('name')}
- Member Since: {persona.get('member_since')}
- Active Policies: {len(persona.get('active_policies', []))}
- Total Coverage: ${persona.get('total_coverage', 0):,.2f}
- Monthly Premium: ${persona.get('monthly_premium', 0):,.2f}

Reference this customer's information naturally in your responses."""
    elif mode.id == "healthcare":
        persona_context = f"""
Current Patient Profile:
- Name: {persona.get('name')}
- Member ID: {persona.get('member_id')}
- Primary Care Provider: {persona.get('primary_care_provider')}
- Deductible Progress: ${persona.get('deductible_met', 0):,.2f} of ${persona.get('deductible', 0):,.2f}
- Active Prescriptions: {len(persona.get('active_prescriptions', []))}

Reference this patient's information naturally in your responses."""
    else:
        persona_context = ""

    return f"{base}\n\n{persona_context}" if persona_context else base


def detect_mode_switch(text: str) -> str | None:
    """
    Detect if the user is requesting a mode switch.
    Returns the mode ID if detected, None otherwise.

    Patterns matched:
    - "Presto-Change-O, you're a bank"
    - "presto change o youre a healthcare provider"
    - "Presto-Change-O, you're an insurance company"
    """
    # Normalize: lowercase, remove punctuation except spaces
    normalized = re.sub(r"[^\w\s]", "", text.lower())

    # Check for the trigger phrase (handles "presto-change-o", "presto change o", "prestochangeo")
    if "presto change o" not in normalized and "prestochangeo" not in normalized:
        return None

    # Look for industry keywords
    if any(word in normalized for word in ["bank", "banking", "financial"]):
        return "banking"
    if any(word in normalized for word in ["insurance", "insurer", "policy"]):
        return "insurance"
    if any(word in normalized for word in ["health", "healthcare", "medical", "hospital", "doctor"]):
        return "healthcare"

    return None


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

    # Check for mode switch command
    global _current_persona
    new_mode_id = detect_mode_switch(text)
    if new_mode_id:
        new_mode = set_current_mode(new_mode_id)
        if new_mode:
            logger.info(f"Mode switched to: {new_mode.name}")

            # Clear conversation history on mode switch
            clear_history()

            # Generate persona for the new mode
            _current_persona = generate_persona(new_mode_id, get_session_seed())
            logger.info(f"Generated persona: {_current_persona.get('name', 'Unknown')}")

            # Send mode_switch message to frontend with persona
            await websocket.send_text(json.dumps({
                "type": "mode_switch",
                "payload": {
                    "mode": {
                        "id": new_mode.id,
                        "name": new_mode.name,
                        "theme": new_mode.theme.model_dump(),
                        "tabs": [tab.model_dump() for tab in new_mode.tabs],
                        "defaultMetrics": [m.model_dump() for m in new_mode.default_metrics]
                    },
                    "persona": _current_persona
                }
            }))

            # Notify frontend that response is starting
            await websocket.send_text(json.dumps({
                "type": "chat_start",
                "payload": {}
            }))

            # Send a welcome message for the new mode
            welcome = f"Presto-Change-O! I'm now your {new_mode.name} assistant. How can I help you today?"
            await websocket.send_text(json.dumps({
                "type": "chat_chunk",
                "payload": {"text": welcome, "done": False}
            }))
            await websocket.send_text(json.dumps({
                "type": "chat_chunk",
                "payload": {"text": "", "done": True}
            }))
            return

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

        # Build messages with conversation history using current mode's system prompt
        # Include persona context in system prompt for AI awareness
        current_mode = get_current_mode()
        messages = [SystemMessage(content=build_system_prompt(current_mode, _current_persona))]
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
