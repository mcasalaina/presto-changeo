"""
Voice Handler Module
Handles voice sessions with gpt-realtime via bidirectional WebSocket relay.
Supports async visualization generation via background Chat API calls.
"""
import asyncio
import json
import logging
import os
import re
from typing import Any

import websockets
from fastapi import WebSocket

from azure.ai.inference.models import SystemMessage, UserMessage, AssistantMessage

from auth import get_azure_credential, get_inference_client
from tools import TOOL_DEFINITIONS, VOICE_TOOL_DEFINITIONS, execute_tool
from modes import get_current_mode, set_current_mode
from chat import build_system_prompt, ensure_persona, detect_mode_switch, get_session_seed
from persona import generate_persona

logger = logging.getLogger(__name__)

# Azure configuration
AZURE_ENDPOINT = os.getenv("AZURE_PROJECT_ENDPOINT", "")
REALTIME_DEPLOYMENT = os.getenv("AZURE_REALTIME_DEPLOYMENT", "gpt-realtime")
MODEL_DEPLOYMENT = os.getenv("AZURE_MODEL_DEPLOYMENT", "gpt-5-mini")
VIZ_DEPLOYMENT = os.getenv("AZURE_VIZ_DEPLOYMENT", "") or os.getenv("AZURE_MODEL_DEPLOYMENT", "gpt-5-mini")
REALTIME_API_VERSION = "2025-04-01-preview"

MAX_TRANSCRIPT_HISTORY = 20


class VoiceSessionState:
    """Tracks state for an active voice session."""

    def __init__(self):
        self.transcript_history: list[dict] = []
        self.model_is_responding: bool = False
        self.pending_visualizations: dict[str, asyncio.Task] = {}
        self.deferred_notifications: list[dict] = []

    def add_transcript(self, role: str, text: str) -> None:
        """Add a transcript entry to rolling conversation history.

        For user messages: each call adds a new complete message.
        For assistant messages: use append_assistant_delta() instead
        since transcripts arrive as streaming deltas.
        """
        if not text or not text.strip():
            return
        self.transcript_history.append({"role": role, "content": text})
        # Keep last N messages
        if len(self.transcript_history) > MAX_TRANSCRIPT_HISTORY:
            self.transcript_history.pop(0)

    def append_assistant_delta(self, text: str) -> None:
        """Append a delta chunk to the current assistant message.

        Assistant transcripts arrive as many small deltas. This accumulates
        them into a single transcript entry.
        """
        if not text:
            return
        if (self.transcript_history
                and self.transcript_history[-1]["role"] == "assistant"):
            self.transcript_history[-1]["content"] += text
        else:
            self.transcript_history.append({"role": "assistant", "content": text})
            if len(self.transcript_history) > MAX_TRANSCRIPT_HISTORY:
                self.transcript_history.pop(0)

    def get_chat_messages(self) -> list[dict]:
        """Get transcript history formatted for Chat API messages."""
        return list(self.transcript_history)

    def cancel_all_pending(self) -> None:
        """Cancel all pending background visualization tasks."""
        for vis_type, task in self.pending_visualizations.items():
            if not task.done():
                task.cancel()
                logger.info(f"Cancelled pending visualization: {vis_type}")
        self.pending_visualizations.clear()
        self.deferred_notifications.clear()


def build_realtime_tools() -> list[dict[str, Any]]:
    """
    Convert VOICE_TOOL_DEFINITIONS to gpt-realtime format.

    Uses lightweight request_visualization tool instead of heavy show_chart/show_metrics
    to minimize token generation time during voice responses.
    """
    realtime_tools = []
    for tool in VOICE_TOOL_DEFINITIONS:
        if tool.get("type") == "function":
            realtime_tools.append({
                "type": "function",
                "name": tool["function"]["name"],
                "description": tool["function"]["description"],
                "parameters": tool["function"]["parameters"]
            })
    return realtime_tools


def build_voice_system_prompt(base_prompt: str) -> str:
    """
    Modify system prompt for voice mode by replacing tool references.

    Replaces 'TOOLS: show_chart ... show_metrics' line with voice-specific
    instructions to use request_visualization and keep talking.
    """
    # Replace the TOOLS line with voice-specific instructions
    voice_tools_instruction = (
        "TOOLS: Use request_visualization to show charts or metrics. "
        "After requesting, KEEP TALKING about the data - don't wait for it to load."
    )
    # Match both pre-built mode format "TOOLS: show_chart (...) and show_metrics."
    # and generated mode format "TOOLS: show_chart(...), show_metrics. ..."
    modified = re.sub(
        r"TOOLS:.*?show_chart.*?show_metrics\..*",
        voice_tools_instruction,
        base_prompt
    )
    return modified


async def _generate_visualization_background(
    session_state: VoiceSessionState,
    vis_type: str,
    description: str,
    websocket: WebSocket,
    realtime_ws: Any,
) -> None:
    """
    Background task: call Chat Completions API to generate actual chart/metrics data.

    1. Builds Chat API request with conversation context + full TOOL_DEFINITIONS
    2. Calls inference API (non-streaming, via asyncio.to_thread)
    3. Extracts tool calls, runs execute_tool()
    4. Sends tool_result to frontend
    5. Queues notification for voice model
    """
    try:
        current_mode = get_current_mode()
        persona = ensure_persona(current_mode.id)
        system_prompt = build_system_prompt(current_mode, persona)

        # Build messages: system prompt + conversation transcript + visualization request
        messages = [SystemMessage(content=system_prompt)]
        for msg in session_state.get_chat_messages():
            if msg["role"] == "user":
                messages.append(UserMessage(content=msg["content"]))
            else:
                messages.append(AssistantMessage(content=msg["content"]))

        # Add explicit instruction for what to generate
        if vis_type == "chart":
            messages.append(UserMessage(content=f"Show me a chart: {description}. Use the show_chart tool."))
        else:
            messages.append(UserMessage(content=f"Show me metrics: {description}. Use the show_metrics tool."))

        logger.info(f"Background viz: calling Chat API ({VIZ_DEPLOYMENT}) with {len(messages)} messages for '{description}'")

        client = get_inference_client()

        # Run synchronous API call in thread to avoid blocking event loop
        response = await asyncio.to_thread(
            client.complete,
            model=VIZ_DEPLOYMENT,
            messages=messages,
            tools=TOOL_DEFINITIONS,
        )

        # Check if task was cancelled while waiting
        if asyncio.current_task().cancelled():
            return

        # Extract tool calls from response
        choice = response.choices[0]
        tool_results = []

        if choice.message.tool_calls:
            for tool_call in choice.message.tool_calls:
                tool_name = tool_call.function.name
                try:
                    arguments = json.loads(tool_call.function.arguments)
                    result = execute_tool(tool_name, arguments)
                    tool_results.append({"tool": tool_name, "result": result})
                    logger.info(f"Background viz: executed {tool_name}")
                except json.JSONDecodeError as e:
                    logger.error(f"Background viz: failed to parse args for {tool_name}: {e}")

        if not tool_results:
            logger.warning(f"Background viz: no tool calls in response for '{description}'")
            return

        # Send tool results to frontend
        for tr in tool_results:
            try:
                await websocket.send_text(json.dumps({
                    "type": "tool_result",
                    "tool": tr["tool"],
                    "result": tr["result"]
                }))
                logger.info(f"Background viz: sent {tr['tool']} result to frontend")
            except Exception as e:
                logger.error(f"Background viz: failed to send to frontend: {e}")
                return

        # Build a summary for the voice model notification
        summary_parts = []
        for tr in tool_results:
            if tr["tool"] == "show_chart":
                summary_parts.append(f"A {tr['result'].get('chart_type', '')} chart titled '{tr['result'].get('title', '')}' is now showing on the dashboard.")
            elif tr["tool"] == "show_metrics":
                metric_names = [m.get("label", "") for m in tr["result"].get("metrics", [])]
                summary_parts.append(f"Metrics are now showing: {', '.join(metric_names)}.")
        summary = " ".join(summary_parts)

        # Queue notification for voice model
        await _notify_voice_model(session_state, realtime_ws, summary)

    except asyncio.CancelledError:
        logger.info(f"Background viz cancelled for '{description}'")
        raise
    except Exception as e:
        logger.error(f"Background viz error for '{description}': {e}")
    finally:
        # Remove from pending
        session_state.pending_visualizations.pop(vis_type, None)


async def _notify_voice_model(
    session_state: VoiceSessionState,
    realtime_ws: Any,
    summary: str,
) -> None:
    """
    Notify the voice model that visualization data is now showing.

    If model is idle: inject context and trigger response immediately.
    If model is speaking: defer notification until response.done fires.
    """
    if not summary:
        return

    notification = {
        "summary": summary,
    }

    if session_state.model_is_responding:
        # Defer until model finishes current response
        session_state.deferred_notifications.append(notification)
        logger.info("Voice model busy - deferred visualization notification")
    else:
        # Send immediately
        await _send_notification(realtime_ws, notification)


async def _send_notification(realtime_ws: Any, notification: dict) -> None:
    """Send a notification to the voice model as a context injection."""
    try:
        await realtime_ws.send(json.dumps({
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [{
                    "type": "input_text",
                    "text": f"[System: {notification['summary']} You can briefly reference the data now visible to the user.]"
                }]
            }
        }))
        await realtime_ws.send(json.dumps({
            "type": "response.create"
        }))
        logger.info(f"Sent visualization notification to voice model")
    except Exception as e:
        logger.error(f"Failed to send notification to voice model: {e}")


async def handle_voice_session(websocket: WebSocket) -> None:
    """
    Handle a voice session with bidirectional audio streaming.

    Creates a relay between the browser WebSocket and gpt-realtime API.

    Browser WebSocket messages (incoming):
    - {"type": "audio", "data": "<base64-pcm16>"}
    - {"type": "mute", "muted": true/false}
    - {"type": "stop"}

    Messages sent to browser (outgoing):
    - {"type": "status", "status": "connected"|"disconnected"|"error"}
    - {"type": "speech_started"}
    - {"type": "speech_stopped"}
    - {"type": "audio", "data": "<base64-pcm16>"}
    - {"type": "transcript", "role": "user"|"assistant", "text": "..."}
    - {"type": "tool_result", "tool": "...", "result": {...}}
    - {"type": "visualization_generating", "vis_type": "chart"|"metrics"}
    - {"type": "error", "error": "..."}
    """
    realtime_ws = None
    muted = False
    session_state = VoiceSessionState()

    try:
        # Get Azure credential and token
        credential = get_azure_credential()
        token = credential.get_token("https://cognitiveservices.azure.com/.default")

        # Build gpt-realtime WebSocket URI
        # Format: wss://{host}/openai/realtime?api-version={version}&deployment={deployment}
        # Extract host from endpoint (remove protocol and /models path)
        endpoint_host = AZURE_ENDPOINT.replace("https://", "").replace("http://", "").rstrip("/")
        # Remove /models suffix if present (chat endpoint has it, realtime doesn't use it)
        if endpoint_host.endswith("/models"):
            endpoint_host = endpoint_host[:-7]
        realtime_uri = f"wss://{endpoint_host}/openai/realtime?api-version={REALTIME_API_VERSION}&deployment={REALTIME_DEPLOYMENT}"

        logger.info(f"Connecting to gpt-realtime at: {realtime_uri}")

        # Connect to gpt-realtime with authorization header
        realtime_ws = await websockets.connect(
            realtime_uri,
            additional_headers={
                "Authorization": f"Bearer {token.token}"
            }
        )

        logger.info("Connected to gpt-realtime API")

        # Send session configuration
        current_mode = get_current_mode()
        persona = ensure_persona(current_mode.id)
        system_prompt = build_voice_system_prompt(build_system_prompt(current_mode, persona))

        session_config = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "voice": "verse",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 500
                },
                "tools": build_realtime_tools(),
                "instructions": system_prompt
            }
        }

        await realtime_ws.send(json.dumps(session_config))
        logger.info("Sent session configuration to gpt-realtime")

        # Notify browser of successful connection
        await websocket.send_text(json.dumps({
            "type": "status",
            "status": "connected"
        }))

        # Create tasks for bidirectional relay
        async def browser_to_realtime():
            """Forward browser audio to gpt-realtime."""
            nonlocal muted
            try:
                while True:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    msg_type = message.get("type")

                    if msg_type == "audio":
                        if not muted:
                            # Forward audio to gpt-realtime
                            await realtime_ws.send(json.dumps({
                                "type": "input_audio_buffer.append",
                                "audio": message.get("data", "")
                            }))

                    elif msg_type == "mute":
                        muted = message.get("muted", False)
                        logger.info(f"Mute state changed: {muted}")

                    elif msg_type == "stop":
                        logger.info("Stop requested by browser")
                        break

            except Exception as e:
                logger.error(f"Browser to realtime relay error: {e}")
                raise

        async def realtime_to_browser():
            """Forward gpt-realtime events to browser."""
            try:
                async for message in realtime_ws:
                    event = json.loads(message)
                    event_type = event.get("type", "")

                    logger.debug(f"gpt-realtime event: {event_type}")

                    if event_type == "session.created":
                        logger.info("gpt-realtime session created")

                    elif event_type == "session.updated":
                        logger.info("gpt-realtime session updated")

                    elif event_type == "response.created":
                        session_state.model_is_responding = True

                    elif event_type == "response.done":
                        session_state.model_is_responding = False
                        # Process any deferred notifications
                        if session_state.deferred_notifications:
                            notifications = session_state.deferred_notifications[:]
                            session_state.deferred_notifications.clear()
                            for notification in notifications:
                                await _send_notification(realtime_ws, notification)

                    elif event_type == "input_audio_buffer.speech_started":
                        # User started speaking - IMMEDIATELY cancel any in-progress response
                        await realtime_ws.send(json.dumps({
                            "type": "response.cancel"
                        }))
                        logger.info("User interrupted - cancelled response")
                        await websocket.send_text(json.dumps({
                            "type": "speech_started"
                        }))

                    elif event_type == "input_audio_buffer.speech_stopped":
                        # User stopped speaking
                        await websocket.send_text(json.dumps({
                            "type": "speech_stopped"
                        }))

                    elif event_type == "conversation.item.input_audio_transcription.completed":
                        # User's speech transcribed
                        transcript = event.get("transcript", "")
                        if transcript:
                            # Track transcript for Chat API context
                            session_state.add_transcript("user", transcript)

                            await websocket.send_text(json.dumps({
                                "type": "transcript",
                                "role": "user",
                                "text": transcript
                            }))

                            # Quick check if this might be a mode switch (cancel early!)
                            transcript_lower = transcript.lower()
                            might_be_mode_switch = "presto" in transcript_lower

                            if might_be_mode_switch:
                                # Cancel any in-flight response IMMEDIATELY before LLM call
                                await realtime_ws.send(json.dumps({
                                    "type": "response.cancel"
                                }))
                                logger.info("Cancelled in-flight response (possible mode switch)")

                                # Cancel pending visualizations on mode switch
                                session_state.cancel_all_pending()

                                # Send loading indicator to frontend
                                await websocket.send_text(json.dumps({
                                    "type": "mode_generating",
                                    "payload": {"industry": "new mode"}
                                }))

                            # Check for mode switch in voice transcript
                            new_mode = await detect_mode_switch(transcript, None)  # Don't pass websocket to avoid double loading
                            if new_mode:
                                logger.info(f"Voice mode switch detected: {new_mode.name}")
                                set_current_mode(new_mode.id)

                                # Cancel any pending visualizations
                                session_state.cancel_all_pending()
                                # Clear transcript history for new mode
                                session_state.transcript_history.clear()

                                # Generate persona for new mode
                                persona = generate_persona(new_mode.id, get_session_seed())
                                logger.info(f"Generated persona for voice: {persona.get('name', 'Unknown')}")

                                # Send mode_switch to browser
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
                                        "persona": persona
                                    }
                                }))

                                # Update gpt-realtime session with new instructions
                                new_system_prompt = build_voice_system_prompt(build_system_prompt(new_mode, persona))
                                await realtime_ws.send(json.dumps({
                                    "type": "session.update",
                                    "session": {
                                        "tools": build_realtime_tools(),
                                        "instructions": new_system_prompt
                                    }
                                }))
                                logger.info("Updated gpt-realtime session with new mode instructions")

                                # Trigger a new response with a welcome message context
                                await realtime_ws.send(json.dumps({
                                    "type": "conversation.item.create",
                                    "item": {
                                        "type": "message",
                                        "role": "user",
                                        "content": [{
                                            "type": "input_text",
                                            "text": f"The user just switched to {new_mode.name} mode. Greet them warmly as their new {new_mode.name} assistant. Be brief."
                                        }]
                                    }
                                }))
                                await realtime_ws.send(json.dumps({
                                    "type": "response.create"
                                }))
                                logger.info("Triggered welcome response for new mode")
                            elif might_be_mode_switch:
                                # We showed loading but it wasn't a mode switch - cancel it
                                await websocket.send_text(json.dumps({
                                    "type": "mode_generating_cancel",
                                    "payload": {}
                                }))

                    elif event_type == "response.audio.delta":
                        # Audio chunk from assistant
                        audio_data = event.get("delta", "")
                        if audio_data:
                            await websocket.send_text(json.dumps({
                                "type": "audio",
                                "data": audio_data
                            }))

                    elif event_type == "response.audio.done":
                        # Audio response complete
                        logger.info("Audio response complete")

                    elif event_type == "response.audio_transcript.delta":
                        # Assistant transcript chunk
                        transcript = event.get("delta", "")
                        if transcript:
                            # Track assistant transcript for Chat API context (accumulate deltas)
                            session_state.append_assistant_delta(transcript)

                            await websocket.send_text(json.dumps({
                                "type": "transcript",
                                "role": "assistant",
                                "text": transcript
                            }))

                    elif event_type == "response.function_call_arguments.done":
                        # Lightweight tool call completed (request_visualization)
                        call_id = event.get("call_id", "")
                        name = event.get("name", "")
                        arguments_str = event.get("arguments", "{}")

                        logger.info(f"Tool call: {name} with args: {arguments_str[:200]}")

                        try:
                            arguments = json.loads(arguments_str)

                            if name == "request_visualization":
                                vis_type = arguments.get("vis_type", "chart")
                                description = arguments.get("description", "")

                                # 1. Immediately acknowledge the tool call
                                ack_output = json.dumps({
                                    "status": "generating",
                                    "message": f"Generating {vis_type} for: {description}"
                                })
                                await realtime_ws.send(json.dumps({
                                    "type": "conversation.item.create",
                                    "item": {
                                        "type": "function_call_output",
                                        "call_id": call_id,
                                        "output": ack_output
                                    }
                                }))

                                # 2. Resume voice immediately
                                await realtime_ws.send(json.dumps({
                                    "type": "response.create"
                                }))

                                # 3. Send loading indicator to frontend
                                await websocket.send_text(json.dumps({
                                    "type": "visualization_generating",
                                    "vis_type": vis_type,
                                    "description": description
                                }))

                                # 4. Cancel previous pending visualization of same type
                                if vis_type in session_state.pending_visualizations:
                                    old_task = session_state.pending_visualizations[vis_type]
                                    if not old_task.done():
                                        old_task.cancel()
                                        logger.info(f"Cancelled previous pending {vis_type} visualization")

                                # 5. Launch background task
                                task = asyncio.create_task(
                                    _generate_visualization_background(
                                        session_state, vis_type, description,
                                        websocket, realtime_ws
                                    )
                                )
                                session_state.pending_visualizations[vis_type] = task

                                logger.info(f"Launched background {vis_type} generation for: {description}")
                            else:
                                # Fallback: handle any other tool calls directly
                                result = execute_tool(name, arguments)

                                await websocket.send_text(json.dumps({
                                    "type": "tool_result",
                                    "tool": name,
                                    "result": result
                                }))

                                await realtime_ws.send(json.dumps({
                                    "type": "conversation.item.create",
                                    "item": {
                                        "type": "function_call_output",
                                        "call_id": call_id,
                                        "output": json.dumps(result)
                                    }
                                }))

                                await realtime_ws.send(json.dumps({
                                    "type": "response.create"
                                }))

                                logger.info(f"Tool {name} executed and result sent")

                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse tool arguments: {e}")

                    elif event_type == "error":
                        # Error from gpt-realtime
                        error_info = event.get("error", {})
                        error_message = error_info.get("message", "Unknown error")
                        logger.error(f"gpt-realtime error: {error_message}")
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "error": error_message
                        }))

            except websockets.exceptions.ConnectionClosed:
                logger.info("gpt-realtime connection closed")
            except Exception as e:
                logger.error(f"Realtime to browser relay error: {e}")
                raise

        # Run both relay tasks concurrently
        browser_task = asyncio.create_task(browser_to_realtime())
        realtime_task = asyncio.create_task(realtime_to_browser())

        # Wait for either task to complete (or fail)
        done, pending = await asyncio.wait(
            [browser_task, realtime_task],
            return_when=asyncio.FIRST_COMPLETED
        )

        # Cancel remaining tasks
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Check for errors in completed tasks
        for task in done:
            if task.exception():
                raise task.exception()

    except websockets.exceptions.InvalidStatusCode as e:
        logger.error(f"Failed to connect to gpt-realtime: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "error": f"Failed to connect to voice service: {e}"
        }))
    except Exception as e:
        logger.error(f"Voice session error: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "error": str(e)
        }))
    finally:
        # Cancel all pending background tasks
        session_state.cancel_all_pending()

        # Clean up gpt-realtime connection
        if realtime_ws:
            await realtime_ws.close()
            logger.info("Closed gpt-realtime connection")

        # Notify browser of disconnection
        try:
            await websocket.send_text(json.dumps({
                "type": "status",
                "status": "disconnected"
            }))
        except Exception:
            pass  # Browser may already be disconnected

        logger.info("Voice session ended")
