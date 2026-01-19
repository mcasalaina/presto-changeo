---
phase: 06-voice
plan: 01
subsystem: api
tags: [websockets, gpt-realtime, audio-streaming, voice, azure]

# Dependency graph
requires:
  - phase: 04-modes
    provides: Mode system with system prompts for voice session configuration
  - phase: 05-persona
    provides: Persona context for voice AI instructions
provides:
  - Backend gpt-realtime WebSocket handler with bidirectional audio relay
  - /voice WebSocket endpoint for browser voice connections
  - Tool calling integration with visualization forwarding
affects: [06-02, frontend, voice-ui]

# Tech tracking
tech-stack:
  added: []
  patterns: [bidirectional websocket relay, asyncio task concurrency for relay loops]

key-files:
  created: [backend/voice.py]
  modified: [backend/main.py]

key-decisions:
  - "Use raw websockets library, not openai realtime client (Azure auth incompatibility)"
  - "Bidirectional relay pattern: Browser WS -> Backend -> gpt-realtime WS"
  - "Mute state handled backend-side to prevent audio forwarding"
  - "server_vad turn detection with 500ms silence for natural conversation"

patterns-established:
  - "Voice session relay: asyncio.wait with FIRST_COMPLETED for bidirectional relay"
  - "Tool result forwarding: Send to browser AND send function_call_output to gpt-realtime"

# Metrics
duration: 5min
completed: 2026-01-18
---

# Phase 06 Plan 01: Voice Backend Infrastructure Summary

**gpt-realtime WebSocket handler with bidirectional audio relay, VAD-based turn detection, and tool calling integration for visualization**

## Performance

- **Duration:** 5 min
- **Started:** 2026-01-18
- **Completed:** 2026-01-18
- **Tasks:** 3/3
- **Files modified:** 2

## Accomplishments

- Created voice.py with complete gpt-realtime WebSocket relay handler (321 lines)
- Implemented bidirectional audio streaming with asyncio task concurrency
- Added tool calling flow with execute_tool() integration and result forwarding
- Configured VAD-based turn detection for natural conversation flow

## Task Commits

Each task was committed atomically:

1. **Task 1: Create voice.py with gpt-realtime handler** - `6aa62a7` (feat)
2. **Task 2: Add /voice WebSocket endpoint to main.py** - `5c343b2` (feat)
3. **Task 3: Add websockets dependency** - No commit (dependency already present in requirements.txt)

## Files Created/Modified

- `backend/voice.py` - gpt-realtime WebSocket handler with bidirectional audio relay
- `backend/main.py` - Added /voice WebSocket endpoint and startup log message

## Decisions Made

1. **Use raw websockets library** - The openai library's realtime client is not compatible with Azure authentication; raw websockets with Bearer token header works correctly
2. **Bidirectional relay pattern** - Backend maintains connection to gpt-realtime, relays audio between browser and API
3. **Mute state in backend** - When muted, backend stops forwarding audio but keeps gpt-realtime connection alive
4. **server_vad configuration** - threshold: 0.5, prefix_padding_ms: 300, silence_duration_ms: 500 for responsive but not twitchy detection

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

**Environment variable may be needed.** If not already set:
- `AZURE_REALTIME_DEPLOYMENT` - Name of the gpt-realtime deployment (defaults to "gpt-realtime")

The existing `AZURE_PROJECT_ENDPOINT` is used for the WebSocket connection host.

## Next Phase Readiness

- Backend voice infrastructure complete
- Ready for Plan 06-02: Frontend voice UI integration
- Browser needs to:
  - Connect to ws://localhost:8000/voice
  - Send audio as base64 pcm16 in `{"type": "audio", "data": "..."}` messages
  - Handle incoming transcript, audio, tool_result, and status messages
  - Implement AudioContext for playback of received audio

---
*Phase: 06-voice*
*Completed: 2026-01-18*
