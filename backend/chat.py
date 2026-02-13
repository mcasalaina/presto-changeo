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

# Response cache: {cache_key: {"response": str, "tool_results": list, "timestamp": float}}
# Cache key is hash of (mode_id, normalized_query)
_response_cache: dict = {}
_CACHE_MAX_SIZE = 50  # Max cached responses
_CACHE_TTL_SECONDS = 300  # 5 minutes


def _normalize_query(text: str) -> str:
    """Normalize query for cache lookup - lowercase, strip whitespace, remove punctuation."""
    import re
    return re.sub(r'[^\w\s]', '', text.lower().strip())


def _get_cache_key(mode_id: str, query: str) -> str:
    """Generate cache key from mode and normalized query."""
    normalized = _normalize_query(query)
    return hashlib.md5(f"{mode_id}:{normalized}".encode()).hexdigest()


def _get_cached_response(mode_id: str, query: str) -> dict | None:
    """Get cached response if available and not expired."""
    import time
    cache_key = _get_cache_key(mode_id, query)
    if cache_key in _response_cache:
        cached = _response_cache[cache_key]
        if time.time() - cached["timestamp"] < _CACHE_TTL_SECONDS:
            logger.info(f"Cache HIT for query: {query[:50]}...")
            return cached
        else:
            # Expired - remove from cache
            del _response_cache[cache_key]
    return None


def _cache_response(mode_id: str, query: str, response: str, tool_results: list) -> None:
    """Cache a response for future reuse."""
    import time
    global _response_cache

    # Evict oldest entries if cache is full
    if len(_response_cache) >= _CACHE_MAX_SIZE:
        oldest_key = min(_response_cache.keys(), key=lambda k: _response_cache[k]["timestamp"])
        del _response_cache[oldest_key]

    cache_key = _get_cache_key(mode_id, query)
    _response_cache[cache_key] = {
        "response": response,
        "tool_results": tool_results,
        "timestamp": time.time()
    }
    logger.info(f"Cached response for query: {query[:50]}...")


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


def clear_cache() -> None:
    """Clear the response cache."""
    global _response_cache
    _response_cache.clear()
    logger.info("Response cache cleared")


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

Use these EXACT values when creating charts or responding about customer data."""
        else:
            persona_context = ""

    # Add universal rules that apply to ALL modes - kept brief for speed
    universal_rules = """

RULES: Never say "sample/demo/hypothetical". One sentence max with charts. Use profile values. No zeros."""

    if persona_context:
        return f"{base}\n\n{persona_context}{universal_rules}"
    return base


async def _detect_mode_switch_intent(text: str) -> dict | None:
    """
    Use LLM to detect if the user wants to switch modes.
    Returns {"industry": str, "company_name": str | None} if detected, None otherwise.

    Extracts both the industry type and any specific company name the user mentions.
    Examples:
    - "Presto, you're a bank" → {"industry": "banking", "company_name": None}
    - "Presto, you're Wells Fargo" → {"industry": "banking", "company_name": "Wells Fargo"}
    - "Presto, you're a florist called Rose Garden" → {"industry": "florist", "company_name": "Rose Garden"}
    """
    client = get_inference_client()

    try:
        response = client.complete(
            model=MODEL_DEPLOYMENT,
            messages=[
                SystemMessage(content="""Detect mode switch requests. If user says "presto [industry]" or similar, extract the industry AND any specific company name.

Respond with JSON: {"industry": "...", "company_name": "..."} or just "NONE" if no mode switch.

Rules:
- "industry" should be the TYPE of business (e.g., "banking", "florist", "pet store", "restaurant")
- "company_name" should be the specific company name if the user mentions one, or null if they don't
- If the user names a well-known company (like Wells Fargo, Allstate, Target), infer the industry from it
- If the user says something like "you're X" where X is clearly a company name (not just an industry), extract it as company_name

Examples:
- "Presto, you're a bank" → {"industry": "banking", "company_name": null}
- "Presto, you're Wells Fargo" → {"industry": "banking", "company_name": "Wells Fargo"}
- "hey presto changeo be a florist" → {"industry": "florist", "company_name": null}
- "Presto, you're Joe's Tacos" → {"industry": "restaurant", "company_name": "Joe's Tacos"}
- "Presto change-o, you're a pet store called Paws & Claws" → {"industry": "pet store", "company_name": "Paws & Claws"}
- "Transform into Allstate" → {"industry": "insurance", "company_name": "Allstate"}
- "Presto, you're McCormick" → {"industry": "spice manufacturing", "company_name": "McCormick"}
- "What's my balance?" → NONE"""),
                UserMessage(content=text)
            ],
        )

        result = response.choices[0].message.content.strip()
        logger.info(f"Mode switch detection result: '{result}' for input: '{text[:50]}...'")

        if result.upper() == "NONE" or not result:
            return None

        # Parse JSON response
        json_str = result
        if json_str.startswith("```"):
            lines = json_str.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            json_str = "\n".join(lines)

        try:
            parsed = json.loads(json_str)
            industry = parsed.get("industry", "").lower().strip()
            company_name = parsed.get("company_name")
            if company_name and isinstance(company_name, str):
                company_name = company_name.strip()
            else:
                company_name = None

            if not industry:
                return None

            logger.info(f"Parsed intent: industry='{industry}', company_name='{company_name}'")
            return {"industry": industry, "company_name": company_name}
        except json.JSONDecodeError:
            # Fallback: treat the whole response as industry name (backward compat)
            industry = result.lower().strip()
            logger.info(f"Fallback intent parse: industry='{industry}', no company_name")
            return {"industry": industry, "company_name": None}

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


def _override_company_name(mode: Mode, new_company_name: str) -> Mode:
    """Create a copy of a mode with an overridden company name and updated system prompt."""
    new_system_prompt = mode.system_prompt.replace(mode.company_name, new_company_name)

    return mode.model_copy(update={
        "company_name": new_company_name,
        "system_prompt": new_system_prompt,
    })


async def detect_mode_switch(text: str, websocket: WebSocket | None = None) -> Mode | None:
    """
    Detect if the user is requesting a mode switch using LLM intent detection.
    Returns the Mode object if detected, None otherwise.

    Uses semantic understanding instead of keyword matching to handle
    variations in how users phrase mode switch requests.

    If the user specifies a company name, that name will be used regardless of
    whether the mode is pre-built, cached, or newly generated.

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

    intent = await _detect_mode_switch_intent(text)
    if not intent:
        # Clear the loading indicator if we showed it but this wasn't actually a mode switch
        if _quick_presto_check(text) and websocket:
            await websocket.send_text(json.dumps({
                "type": "mode_generating_cancel",
                "payload": {}
            }))
        return None

    industry = intent["industry"]
    user_company_name = intent.get("company_name")

    logger.info(f"Mode switch intent: industry='{industry}', company_name='{user_company_name}'")

    # Map common industry names to pre-built modes
    industry_lower = industry.lower()
    base_mode = None

    # Banking mode
    if any(word in industry_lower for word in ["bank", "banking", "financial", "finance"]):
        base_mode = get_mode("banking")

    # Insurance mode
    elif any(word in industry_lower for word in ["insurance", "insurer", "policy", "claims"]):
        base_mode = get_mode("insurance")

    # Healthcare mode
    elif any(word in industry_lower for word in ["health", "healthcare", "medical", "hospital", "doctor", "clinic"]):
        base_mode = get_mode("healthcare")

    else:
        # Check if we already have this mode (previously generated)
        mode_id = industry.replace(" ", "_").replace("-", "_")
        base_mode = get_mode(mode_id)

    if base_mode:
        if user_company_name:
            # User specified a company name - override it on the cached/pre-built mode
            logger.info(f"Overriding company_name '{base_mode.company_name}' -> '{user_company_name}' on mode '{base_mode.id}'")
            mode = _override_company_name(base_mode, user_company_name)
            store_generated_mode(mode)
            return mode
        logger.info(f"Using existing mode '{base_mode.id}' (company: {base_mode.company_name})")
        return base_mode

    # Notify that we're generating a new mode (this takes time)
    if websocket:
        await websocket.send_text(json.dumps({
            "type": "mode_generating",
            "payload": {"industry": industry}
        }))

    # Try to generate a new mode for this industry
    try:
        logger.info(f"Generating mode for unknown industry: {industry}")
        new_mode = await generate_mode(industry, text, company_name=user_company_name)
        if new_mode:
            store_generated_mode(new_mode)
            logger.info(f"Generated and stored mode: {new_mode.name} (id={new_mode.id}, company={new_mode.company_name})")
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
    new_mode = await detect_mode_switch(text, websocket)
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
                    "defaultMetrics": [m.model_dump() for m in new_mode.default_metrics],
                    "background_image": new_mode.background_image,
                    "hero_image": new_mode.hero_image,
                    "chat_image": new_mode.chat_image,
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

    # Check cache for this query
    current_mode = get_current_mode()
    cached = _get_cached_response(current_mode.id, text)
    if cached:
        # Cache hit - replay cached response without calling LLM
        await websocket.send_text(json.dumps({
            "type": "chat_start",
            "payload": {}
        }))

        # Send cached text response
        if cached["response"]:
            await websocket.send_text(json.dumps({
                "type": "chat_chunk",
                "payload": {"text": cached["response"], "done": False}
            }))

        # Send cached tool results
        for tool_result in cached["tool_results"]:
            await websocket.send_text(json.dumps({
                "type": "tool_result",
                "payload": tool_result
            }))

        # Signal completion
        await websocket.send_text(json.dumps({
            "type": "chat_chunk",
            "payload": {"text": "", "done": True}
        }))

        # Add to history for context
        add_to_history("user", text)
        if cached["response"]:
            add_to_history("assistant", cached["response"])

        logger.info(f"Returned cached response for: {text[:50]}...")
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

        # Process completed tool calls and collect results for caching
        tool_results_for_cache = []
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

                    # Collect for caching
                    tool_results_for_cache.append({"tool": tool_name, "result": result})

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

        # Cache the response for future reuse
        _cache_response(current_mode.id, text, full_response, tool_results_for_cache)

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
