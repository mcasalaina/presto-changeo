# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-01-15)

**Core value:** Dynamic industry simulation that feels real. The interface must convincingly transform into any industry on command, with the AI providing contextually appropriate responses and visualizations.
**Current focus:** Phase 7 - Dynamic Generation

## Current Position

Phase: 7 of 8 (Dynamic Generation)
Plan: 1 of 3 complete in phase
Status: In progress
Last activity: 2026-02-03 - Completed 07-01-PLAN.md (Generation Infrastructure)

Progress: [########--] ~79%

## Performance Metrics

**Velocity:**
- Total plans completed: 15
- Average duration: ~6.1 minutes
- Total execution time: ~91 minutes

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Foundation | 2/2 | ~8 min | ~4 min |
| 2. Chat Interface | 2/2 | ~5 min | ~2.5 min |
| 3. Dashboard | 3/3 | ~20 min | ~6.5 min |
| 4. Mode System | 3/3 | ~14 min | ~4.7 min |
| 5. Persona | 2/2 | ~32 min | ~16 min |
| 6. Voice | 2/3 | ~9 min | ~4.5 min |
| 7. Dynamic Generation | 1/3 | ~3 min | ~3 min |

**Recent Trend:**
- Last 5 plans: 07-01 (~3m), 06-01 (~5m), 06-02 (~4m), 05-02 (~25m), 05-01 (~7m)
- Trend: Generation infrastructure completed quickly

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

| Plan | Decision | Rationale |
|------|----------|-----------|
| 01-01 | Exponential backoff for WebSocket (1s, 2s, 4s... max 30s) | Industry standard for connection stability |
| 01-02 | Use FastAPI lifespan context manager | Modern pattern, deprecated on_event |
| 01-02 | Lazy credential initialization | No auth on import, only when needed |
| 01-02 | Cache credential globally | Single browser popup per session |
| 01-02 | CORS for localhost:5173 | Standard Vite dev port |
| 02-01 | JSON message protocol with type/payload | Consistent, extensible format for all message types |
| 02-01 | chat_start before streaming | Frontend can show typing indicator immediately |
| 02-01 | Separate chat_error type | Clean error handling without mixing with content |
| 03-02 | Tools return arguments as-is for frontend rendering | Backend doesn't process visualization data |
| 03-02 | tool_result message type for visualization data | Consistent with existing message protocol |
| 03-01 | Dark theme for dashboard (#0f172a) | Matches layout prototype space theme |
| 03-01 | Cyan accent color for metrics (#22d3ee) | High contrast, consistent with prototype |
| 03-03 | CSS-only bar charts | gpt-image-1-mini will generate real charts later |
| 03-03 | Light theme dashboard | User feedback during verification |
| 03-03 | Hide metrics when chart shown | Full width for visualization display |
| 04-01 | CSS custom properties for theming | Enables runtime theme switching via JavaScript |
| 04-01 | color-mix() for derived colors | Creates darker shades and opacity variants from primary |
| 04-01 | Type parity frontend/backend | Mode interfaces match Pydantic models |
| 04-02 | Regex normalization for trigger detection | Handles variations like Presto-Change-O, presto change o |
| 04-02 | Module-level mode state | Matches conversation_history pattern for simplicity |
| 04-02 | Clear history on mode switch | Fresh context for new industry |
| 04-03 | snake_case to camelCase in mode_switch handler | Backend uses text_muted, frontend uses textMuted |
| 04-03 | Clear messages on mode switch | Backend sends fresh welcome via chat_chunk |
| 05-01 | Faker seed_instance() not class-level Faker.seed() | Multi-session isolation for concurrent users |
| 05-01 | Module-level _current_persona state | Matches conversation_history pattern for simplicity |
| 05-01 | Fixed demo-session seed for MVP | TODO: derive from WebSocket connection ID in production |
| 06-01 | Raw websockets library over openai realtime client | Azure auth incompatibility with openai library |
| 06-01 | Bidirectional relay pattern | Backend maintains connection to gpt-realtime, relays audio |
| 06-01 | server_vad with 500ms silence detection | Natural conversation flow without twitchy detection |
| 06-02 | ScriptProcessorNode over AudioWorklet | Simpler implementation for MVP, widely supported |
| 06-02 | 500ms timeout for isSpeaking detection | Balances responsiveness with avoiding UI flicker |
| 06-02 | 24kHz sample rate for audio | Matches gpt-realtime requirements |
| 07-01 | HLS color space for complementary calculation | colorsys is stdlib, produces good color harmony |
| 07-01 | Lightness > 0.5 threshold for light/dark scheme | Simple heuristic for detecting primary color brightness |
| 07-01 | 80% saturation for secondary color | Prevents garish complementary colors |

### Pending Todos

None.

### Blockers/Concerns

None.

## Session Continuity

Last session: 2026-02-03
Stopped at: Completed 07-01-PLAN.md (Generation Infrastructure)
Resume file: None

## Completed Plans

| Plan | Summary | Date |
|------|---------|------|
| 01-01 | Vite React TypeScript shell with WebSocket client | 2026-01-15 |
| 01-02 | Python backend with FastAPI, WebSocket, and Azure auth | 2026-01-16 |
| 02-01 | Chat handler with Azure LLM streaming via WebSocket | 2026-01-16 |
| 02-02 | Frontend streaming chat with typing indicator | 2026-01-18 |
| 03-01 | Dashboard layout with metrics panel and visualization area | 2026-01-18 |
| 03-02 | LLM tool definitions with show_chart and show_metrics | 2026-01-18 |
| 03-03 | Tool integration with ChartRenderer and end-to-end visualization | 2026-01-18 |
| 04-01 | Mode infrastructure with TypeScript/Pydantic types and CSS theming | 2026-01-18 |
| 04-02 | Pre-built modes with Presto-Change-O detection and WebSocket switching | 2026-01-18 |
| 04-03 | React ModeContext integration with dynamic tabs and theming | 2026-01-19 |
| 05-01 | Faker-based seeded persona generation with AI system prompt integration | 2026-01-19 |
| 06-01 | gpt-realtime WebSocket handler with bidirectional audio relay and tool calling | 2026-01-18 |
| 06-02 | useVoice hook with mic capture, WebSocket audio streaming, and playback queue | 2026-01-19 |
| 07-01 | Pydantic schemas for LLM structured output and algorithmic color palette derivation | 2026-02-03 |
