# Agent Guidelines for Presto-Change-O

This document provides context for AI agents working on this codebase.

## Project Overview

Presto-Change-O is an AI-powered demo that transforms a dashboard interface based on natural language commands. The core interaction: user says "Presto-Change-O, you're a [industry]" and the entire UI adapts.

## Architecture

```
┌─────────────────┐     WebSocket      ┌─────────────────┐
│    Frontend     │◄──────────────────►│     Backend     │
│  React + Vite   │    JSON messages   │     FastAPI     │
│  localhost:5173 │                    │  localhost:8000 │
└─────────────────┘                    └────────┬────────┘
                                                │
                                                ▼
                                       ┌─────────────────┐
                                       │   Azure AI      │
                                       │   Foundry       │
                                       │   (gpt-5-mini)  │
                                       └─────────────────┘
```

## Key Files

### Backend (Python)

| File | Purpose |
|------|---------|
| `backend/main.py` | FastAPI app, WebSocket endpoint, message routing |
| `backend/chat.py` | LLM chat handler, streaming responses |
| `backend/auth.py` | Azure authentication (CLI + browser fallback) |
| `backend/.env` | Configuration (AZURE_PROJECT_ENDPOINT, AZURE_MODEL_DEPLOYMENT) |

### Frontend (TypeScript/React)

| File | Purpose |
|------|---------|
| `frontend/src/App.tsx` | Main component, chat UI, message handling |
| `frontend/src/App.css` | All styles (single file for now) |
| `frontend/src/hooks/useWebSocket.ts` | WebSocket hook with reconnection |
| `frontend/src/lib/websocket.ts` | WebSocket utilities, connection management |
| `frontend/src/components/` | UI components (TypingIndicator, etc.) |

## WebSocket Protocol

All messages are JSON with `type` and `payload` fields.

### Client → Server

```json
{"type": "chat", "payload": {"text": "user message"}}
{"type": "clear_chat", "payload": {}}
```

### Server → Client

```json
{"type": "chat_start", "payload": {}}
{"type": "chat_chunk", "payload": {"text": "...", "done": false}}
{"type": "chat_chunk", "payload": {"text": "", "done": true}}
{"type": "chat_error", "payload": {"error": "message"}}
```

## Model Constraints (gpt-5-mini)

The current model has specific limitations:

- **No `max_tokens` parameter** - use `max_completion_tokens` or omit entirely
- **No `temperature` parameter** - only default (1.0) is supported
- Streaming works normally with `stream=True`

## Testing

### Manual Testing

1. Ensure Azure CLI is logged in: `az login`
2. Start backend: `cd backend && python -m uvicorn main:app --reload`
3. Start frontend: `cd frontend && npm run dev`
4. Open http://localhost:5173
5. Verify green connection status dot
6. Send a chat message and verify streaming response

### Backend Smoke Test

```bash
cd backend
python -c "
from auth import get_inference_client
from chat import MODEL_DEPLOYMENT
from azure.ai.inference.models import SystemMessage, UserMessage

client = get_inference_client()
response = client.complete(
    model=MODEL_DEPLOYMENT,
    messages=[
        SystemMessage(content='Test'),
        UserMessage(content='Say hello'),
    ],
)
print(response.choices[0].message.content)
"
```

### Frontend Build Check

```bash
cd frontend && npm run build
```

## Common Issues

### "Failed to invoke the Azure CLI"
Run `az login` to authenticate.

### "unsupported_parameter: max_tokens"
The gpt-5-mini model doesn't support `max_tokens`. Remove it or use `max_completion_tokens`.

### "temperature does not support 0.7"
The gpt-5-mini model only supports temperature=1. Remove the temperature parameter.

### Garbled streaming text
The frontend uses callback-based message handling (not state-based) to avoid React batching issues. If streaming appears broken, check that `onMessage` callback is being used, not `lastMessage` state.

## Planning Documents

The `.planning/` directory contains project planning:

- `PROJECT.md` - Core requirements and constraints
- `ROADMAP.md` - Phase breakdown and progress
- `STATE.md` - Current position and session continuity
- `REQUIREMENTS.md` - Detailed requirements
- `phases/` - Per-phase plans and summaries

## Code Style

- **Frontend**: TypeScript strict mode, React functional components, hooks
- **Backend**: Python type hints, async/await, minimal dependencies
- **Commits**: Conventional commits (feat, fix, docs, etc.)

## Commit Policy

**Do NOT commit and push until changes are verified by the user.** Always:
1. Make the code changes
2. Wait for user to test and confirm the changes work
3. Only then commit and push when explicitly asked

## Current Status

Check `.planning/STATE.md` for current phase and next steps. As of last update:
- Phase 1 (Foundation): Complete
- Phase 2 (Chat Interface): Complete
- Phase 3 (Dashboard): Not started
