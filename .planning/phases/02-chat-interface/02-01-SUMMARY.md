---
phase: 02-chat-interface
plan: 01
subsystem: backend
tags: [azure-llm, websocket, streaming, chat]

dependency-graph:
  requires: [01-02-backend-server, 01-02-azure-auth]
  provides: [chat-handler, llm-streaming, websocket-routing]
  affects: [02-02-frontend-chat]

tech-stack:
  added: []
  patterns: [async-streaming, message-routing, json-protocol]

key-files:
  created:
    - backend/chat.py
  modified:
    - backend/main.py

decisions:
  - id: chat-message-protocol
    decision: "Use JSON message format with type and payload fields"
    rationale: "Consistent protocol for all WebSocket message types"

  - id: streaming-format
    decision: "chat_start -> chat_chunk (done: false)* -> chat_chunk (done: true)"
    rationale: "Frontend can show typing indicator and know when complete"

  - id: error-handling
    decision: "Send chat_error message type on LLM failures"
    rationale: "Frontend can display user-friendly error messages"

metrics:
  duration: 2m 15s
  completed: 2026-01-16
---

# Phase 02 Plan 01: Backend Chat Handler Summary

**Chat handler with Azure LLM integration and streaming WebSocket responses using model-router deployment.**

## What Was Built

### Task 1: Chat Handler with LLM Streaming

Created `backend/chat.py` with:

- `handle_chat_message(text, websocket)` async function
- Azure LLM integration via `get_inference_client()` from auth module
- Streaming response handling with `stream=True`
- Message protocol:
  - `chat_start`: Signals response beginning (for typing indicator)
  - `chat_chunk`: Streaming text chunks with `done: false`
  - `chat_chunk`: Final message with `done: true`
  - `chat_error`: Error message if LLM call fails

System prompt: "You are a helpful AI assistant for Presto-Change-O, an industry simulation dashboard."

### Task 2: WebSocket Message Routing

Updated `backend/main.py` to route messages by type:

- Added `json` import and `handle_chat_message` import
- Parse incoming JSON messages
- Route `type: "chat"` to chat handler
- Keep echo behavior for unknown types (debugging)
- Handle JSON parse errors with error response

Message format expected:
```json
{"type": "chat", "payload": {"text": "user message"}}
```

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| JSON message protocol with type/payload | Consistent, extensible format for all message types |
| chat_start before streaming | Frontend can show typing indicator immediately |
| Separate chat_error type | Clean error handling without mixing with content |
| Keep echo for unknown types | Useful for debugging during development |

## Commits

| Hash | Type | Description |
|------|------|-------------|
| e83e4f9 | feat | Create chat handler with LLM streaming |
| 7728f85 | feat | Add WebSocket message routing for chat |

## Verification Results

- [x] `python -c "from main import app"` succeeds
- [x] `python -c "from chat import handle_chat_message"` succeeds
- [x] chat.py exists with handle_chat_message function
- [x] main.py imports and uses handle_chat_message
- [x] No syntax errors in either file

## Deviations from Plan

None - plan executed exactly as written.

## Next Phase Readiness

### Provides for Plan 02-02 (Frontend Chat)

- WebSocket message routing ready for chat messages
- Streaming protocol defined and implemented
- Error handling in place

### Message Protocol Reference

**Send to backend:**
```json
{"type": "chat", "payload": {"text": "Hello, AI!"}}
```

**Receive from backend:**
```json
{"type": "chat_start", "payload": {}}
{"type": "chat_chunk", "payload": {"text": "Hello", "done": false}}
{"type": "chat_chunk", "payload": {"text": "!", "done": false}}
{"type": "chat_chunk", "payload": {"text": "", "done": true}}
```

**On error:**
```json
{"type": "chat_error", "payload": {"error": "Error message"}}
```

## Files

```
backend/
  chat.py  # NEW - Chat handler with LLM streaming
  main.py  # MODIFIED - WebSocket routing by type
```
