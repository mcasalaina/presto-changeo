"""
Voice Handler Module
Handles voice sessions with gpt-realtime via bidirectional WebSocket relay.
"""
import asyncio
import json
import logging
import os
from typing import Any

import websockets
from fastapi import WebSocket

from auth import get_azure_credential
from tools import TOOL_DEFINITIONS, execute_tool
from modes import get_current_mode, set_current_mode
from chat import build_system_prompt, ensure_persona, detect_mode_switch, get_session_seed
from persona import generate_persona

logger = logging.getLogger(__name__)

# Azure configuration
AZURE_ENDPOINT = os.getenv("AZURE_PROJECT_ENDPOINT", "")
REALTIME_DEPLOYMENT = os.getenv("AZURE_REALTIME_DEPLOYMENT", "gpt-realtime")
REALTIME_API_VERSION = "2025-04-01-preview"


def build_realtime_tools() -> list[dict[str, Any]]:
    """
    Convert TOOL_DEFINITIONS to gpt-realtime format.

    gpt-realtime uses a slightly different tool format than chat completions.
    The structure is the same but nested under 'function' key.
    """
    realtime_tools = []
    for tool in TOOL_DEFINITIONS:
        if tool.get("type") == "function":
            realtime_tools.append({
                "type": "function",
                "name": tool["function"]["name"],
                "description": tool["function"]["description"],
                "parameters": tool["function"]["parameters"]
            })
    return realtime_tools


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
    - {"type": "error", "error": "..."}
    """
    realtime_ws = None
    muted = False

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
        system_prompt = build_system_prompt(current_mode, persona)

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

                                # Send loading indicator to frontend
                                await websocket.send_text(json.dumps({
                                    "type": "mode_generating",
                                    "payload": {"industry": ""}
                                }))

                            # Check for mode switch in voice transcript
                            new_mode = await detect_mode_switch(transcript, websocket)
                            if new_mode:
                                logger.info(f"Voice mode switch detected: {new_mode.name}")
                                set_current_mode(new_mode.id)

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
                                            "defaultMetrics": [m.model_dump() for m in new_mode.default_metrics]
                                        },
                                        "persona": persona
                                    }
                                }))

                                # Update gpt-realtime session with new instructions
                                new_system_prompt = build_system_prompt(new_mode, persona)
                                await realtime_ws.send(json.dumps({
                                    "type": "session.update",
                                    "session": {
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
                            await websocket.send_text(json.dumps({
                                "type": "transcript",
                                "role": "assistant",
                                "text": transcript
                            }))

                    elif event_type == "response.function_call_arguments.done":
                        # Tool call completed - execute and return result
                        call_id = event.get("call_id", "")
                        name = event.get("name", "")
                        arguments_str = event.get("arguments", "{}")

                        logger.info(f"Tool call: {name} with args: {arguments_str[:100]}...")

                        try:
                            arguments = json.loads(arguments_str)
                            result = execute_tool(name, arguments)

                            # Send tool result to browser for visualization
                            await websocket.send_text(json.dumps({
                                "type": "tool_result",
                                "tool": name,
                                "result": result
                            }))

                            # Send function call output back to gpt-realtime
                            await realtime_ws.send(json.dumps({
                                "type": "conversation.item.create",
                                "item": {
                                    "type": "function_call_output",
                                    "call_id": call_id,
                                    "output": json.dumps(result)
                                }
                            }))

                            # Trigger response continuation after tool execution
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
