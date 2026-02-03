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
from modes import Mode, get_mode, get_current_mode, set_current_mode, store_generated_mode
from persona import generate_persona
from mode_generator import generate_mode

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


def ensure_persona(mode_id: str) -> dict:
    """Ensure persona is generated for the given mode. Returns the persona."""
    global _current_persona
    if not _current_persona:
        from persona import generate_persona
        _current_persona = generate_persona(mode_id, get_session_seed())
        logger.info(f"Generated initial persona: {_current_persona.get('name', 'Unknown')}")
    return _current_persona


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
        transactions = persona.get('recent_transactions', [])
        persona_context = f"""
Current Customer Profile:
- Name: {persona.get('name')}
- Member Since: {persona.get('member_since')}
- Checking Balance: ${persona.get('checking_balance', 0):,.2f}
- Savings Balance: ${persona.get('savings_balance', 0):,.2f}
- Credit Score: {persona.get('credit_score')}
- Credit Limit: ${persona.get('credit_limit', 0):,.2f}
- Recent Transactions: {len(transactions)}

Use these EXACT values when creating charts or responding about balances."""
    elif mode.id == "insurance":
        policies = persona.get('active_policies', [])
        policy_details = "\n".join([
            f"  - {p.get('type')}: ${p.get('coverage', 0):,.2f} coverage, ${p.get('premium', 0):,.2f}/mo premium"
            for p in policies
        ])
        pending_claims = len([c for c in persona.get('claims_history', []) if c.get('status') == 'pending'])
        persona_context = f"""
Current Customer Profile:
- Name: {persona.get('name')}
- Member Since: {persona.get('member_since')}
- Active Policies: {len(policies)}
- Total Coverage: ${persona.get('total_coverage', 0):,.2f}
- Monthly Premium: ${persona.get('monthly_premium', 0):,.2f}
- Pending Claims: {pending_claims}

Policy Breakdown:
{policy_details}

Use these EXACT values when creating charts or responding about coverage."""
    elif mode.id == "healthcare":
        appointments = persona.get('upcoming_appointments', [])
        prescriptions = persona.get('active_prescriptions', [])
        persona_context = f"""
Current Patient Profile:
- Name: {persona.get('name')}
- Member ID: {persona.get('member_id')}
- Primary Care Provider: {persona.get('primary_care_provider')}
- Plan Name: {persona.get('plan_name')}
- Deductible: ${persona.get('deductible', 0):,.2f}
- Deductible Met: ${persona.get('deductible_met', 0):,.2f}
- Out-of-Pocket Max: ${persona.get('out_of_pocket_max', 0):,.2f}
- Out-of-Pocket Spent: ${persona.get('out_of_pocket_spent', 0):,.2f}
- Upcoming Appointments: {len(appointments)}
- Active Prescriptions: {len(prescriptions)}

Use these EXACT values when creating charts or responding about health data."""
    else:
        # Generic persona context for dynamically generated modes
        if persona.get('name'):
            persona_context = f"""
Current Customer Profile:
- Name: {persona.get('name')}
- Customer Since: {persona.get('customer_since', 'Unknown')}
- Account Value: ${persona.get('account_value', 0):,.2f}
- Recent Activity: {persona.get('recent_activity_count', 0)} items
- Loyalty Points: {persona.get('loyalty_points', 0):,}
- Status: {persona.get('status', 'Standard')}

Use these values when creating charts or responding about customer data."""
        else:
            persona_context = ""

    return f"{base}\n\n{persona_context}" if persona_context else base


async def _detect_mode_switch_intent(text: str) -> str | None:
    """
    Use LLM to detect if the user wants to switch modes and extract the industry.
    Returns the industry name if a mode switch is detected, None otherwise.

    This replaces brittle regex matching with semantic understanding.
    The LLM understands variations like:
    - "Presto-Change-O, you're a bank"
    - "presto chango you're a health insurance company"
    - "hey presto changeo be a florist"
    - "transform into a pet store"
    """
    client = get_inference_client()

    try:
        response = client.complete(
            model=MODEL_DEPLOYMENT,
            messages=[
                SystemMessage(content="""You are a mode switch detector for the Presto-Change-O app.
Your job is to determine if the user wants to switch the app to a different industry mode.

Mode switch phrases include variations like:
- "Presto-Change-O, you're a [industry]"
- "presto chango you're a [industry]"
- "presto [industry]" (just the word presto followed by an industry)
- "presto, be a [industry]"
- "transform into a [industry]"
- "switch to [industry] mode"
- "be a [industry]"

The key trigger word is "presto" (or variations like "presto-change-o", "presto chango").
If you hear "presto" followed by ANY industry or business type, that's a mode switch request.

If the user is requesting a mode switch, respond with ONLY the industry name (e.g., "bank", "florist", "pet store", "healthcare provider").
If the user is NOT requesting a mode switch, respond with exactly "NONE".

Be generous in interpretation - if it sounds like they want to change the interface theme/industry, extract the industry."""),
                UserMessage(content=text)
            ],
        )

        result = response.choices[0].message.content.strip()
        logger.info(f"Mode switch detection result: '{result}' for input: '{text[:50]}...'")

        if result.upper() == "NONE" or not result:
            return None

        return result.lower()

    except Exception as e:
        logger.error(f"Mode switch detection failed: {e}")
        return None


def _quick_presto_check(text: str) -> bool:
    """
    Fast local check for "presto" pattern to show loading indicator immediately.
    Returns True if text looks like a mode switch command.
    """
    text_lower = text.lower()
    presto_patterns = ["presto", "presto-change-o", "presto change", "presto,", "presto!"]
    return any(pattern in text_lower for pattern in presto_patterns)


async def detect_mode_switch(text: str, websocket: WebSocket | None = None) -> Mode | None:
    """
    Detect if the user is requesting a mode switch using LLM intent detection.
    Returns the Mode object if detected, None otherwise.

    Uses semantic understanding instead of keyword matching to handle
    variations in how users phrase mode switch requests.

    Args:
        text: The user's input text
        websocket: Optional websocket to send loading notifications
    """
    # Quick local check - show loading indicator IMMEDIATELY if "presto" detected
    if _quick_presto_check(text) and websocket:
        await websocket.send_text(json.dumps({
            "type": "mode_generating",
            "payload": {"industry": "new mode"}
        }))

    industry = await _detect_mode_switch_intent(text)
    if not industry:
        # Clear the loading indicator if we showed it but this wasn't actually a mode switch
        if _quick_presto_check(text) and websocket:
            await websocket.send_text(json.dumps({
                "type": "mode_generating_cancel",
                "payload": {}
            }))
        return None

    logger.info(f"Mode switch intent detected for industry: {industry}")

    # Map common industry names to pre-built modes
    industry_lower = industry.lower()

    # Banking mode
    if any(word in industry_lower for word in ["bank", "banking", "financial", "finance"]):
        return get_mode("banking")

    # Insurance mode
    if any(word in industry_lower for word in ["insurance", "insurer", "policy", "claims"]):
        return get_mode("insurance")

    # Healthcare mode
    if any(word in industry_lower for word in ["health", "healthcare", "medical", "hospital", "doctor", "clinic"]):
        return get_mode("healthcare")

    # Check if we already have this mode (previously generated)
    mode_id = industry.replace(" ", "_").replace("-", "_")
    existing_mode = get_mode(mode_id)
    if existing_mode:
        logger.info(f"Found existing mode for '{industry}': {existing_mode.name}")
        return existing_mode

    # Notify that we're generating a new mode (this takes time)
    if websocket:
        await websocket.send_text(json.dumps({
            "type": "mode_generating",
            "payload": {"industry": industry}
        }))

    # Try to generate a new mode for this industry
    # Pass the full user request so the LLM can extract any company name mentioned
    try:
        logger.info(f"Generating mode for unknown industry: {industry}")
        new_mode = await generate_mode(industry, text)
        if new_mode:
            store_generated_mode(new_mode)
            logger.info(f"Generated and stored mode: {new_mode.name} (id={new_mode.id})")
            return new_mode
    except Exception as e:
        logger.error(f"Mode generation failed for '{industry}': {e}")

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
    new_mode = await detect_mode_switch(text)
    if new_mode:
        # Set current mode using the returned Mode object
        set_current_mode(new_mode.id)
        logger.info(f"Mode switched to: {new_mode.name}")

        # Clear conversation history on mode switch
        clear_history()

        # Generate persona for the new mode
        _current_persona = generate_persona(new_mode.id, get_session_seed())
        logger.info(f"Generated persona: {_current_persona.get('name', 'Unknown')}")

        # Send mode_switch message to frontend with persona
        await websocket.send_text(json.dumps({
            "type": "mode_switch",
            "payload": {
                "mode": {
                    "id": new_mode.id,
                    "name": new_mode.name,
                    "company_name": new_mode.company_name,
                    "tagline": new_mode.tagline,
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
                        # Get index - could be attribute or None
                        idx = getattr(tool_call, 'index', None)
                        if idx is None:
                            idx = 0

                        logger.debug(f"Tool call chunk: idx={idx}, id={getattr(tool_call, 'id', None)}, name={getattr(tool_call.function, 'name', None) if hasattr(tool_call, 'function') else None}")

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
                                old_name = tool_calls[idx]["name"]
                                new_name = tool_call.function.name
                                if old_name and old_name != new_name:
                                    logger.warning(f"Tool name change at idx {idx}: {old_name} -> {new_name}")
                                tool_calls[idx]["name"] = new_name
                            if hasattr(tool_call.function, 'arguments') and tool_call.function.arguments:
                                tool_calls[idx]["arguments"] += tool_call.function.arguments

        # Add assistant response to history
        if full_response:
            add_to_history("assistant", full_response)

        # Process completed tool calls
        logger.info(f"Processing {len(tool_calls)} tool call(s): {[(idx, tc['name']) for idx, tc in tool_calls.items()]}")
        for idx in sorted(tool_calls.keys()):
            tool_call = tool_calls[idx]
            tool_name = tool_call["name"]
            arguments_str = tool_call["arguments"]

            if tool_name and arguments_str:
                try:
                    # Strip whitespace and try to parse
                    arguments_str = arguments_str.strip()
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
                    logger.error(f"Raw arguments string: {arguments_str[:500]}")
                    # Try to extract multiple JSON objects (tool calls may be concatenated)
                    try:
                        decoder = json.JSONDecoder()
                        pos = 0
                        json_objects = []
                        while pos < len(arguments_str):
                            # Skip whitespace
                            while pos < len(arguments_str) and arguments_str[pos] in ' \t\n\r':
                                pos += 1
                            if pos >= len(arguments_str):
                                break
                            obj, end_pos = decoder.raw_decode(arguments_str, pos)
                            json_objects.append(obj)
                            pos = end_pos

                        logger.info(f"Recovered {len(json_objects)} JSON object(s) from concatenated args")

                        # Execute each based on structure (infer tool from content)
                        for obj in json_objects:
                            if "metrics" in obj:
                                inferred_tool = "show_metrics"
                            elif "chart_type" in obj:
                                inferred_tool = "show_chart"
                            else:
                                inferred_tool = tool_name  # fallback to declared name

                            logger.info(f"Executing inferred tool: {inferred_tool}")
                            result = execute_tool(inferred_tool, obj)
                            await websocket.send_text(json.dumps({
                                "type": "tool_result",
                                "payload": {
                                    "tool": inferred_tool,
                                    "result": result
                                }
                            }))
                    except Exception as e2:
                        logger.error(f"Recovery also failed: {e2}")

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
