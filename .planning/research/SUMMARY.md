# Project Research Summary

**Project:** Presto-Change-O
**Domain:** AI-powered multi-industry simulation dashboard
**Researched:** 2026-01-15
**Confidence:** HIGH

## Executive Summary

Presto-Change-O is a technically ambitious project combining real-time voice (Azure gpt-realtime), LLM-driven tool calling (model-router), dynamic theming, and AI-generated visualizations. Research confirms this is achievable with the specified stack, but reveals critical architectural decisions that must be made correctly upfront.

**Key insight:** The Azure OpenAI Realtime API does NOT connect directly to browsers — it requires a FastAPI backend as a relay. This shapes the entire architecture. All real-time communication (voice, chat, tool results) should flow through a single WebSocket connection to avoid synchronization issues.

**The recommended approach:**
1. Build WebSocket infrastructure first — everything depends on it
2. Use Zustand for state management (not Redux) — better for real-time dashboards
3. Use CSS custom properties for theming — enables runtime mode switching without page reload
4. Use WebRTC (not WebSocket) for browser-to-Azure voice — significantly lower latency
5. Cache generated modes server-side — regeneration on each switch is too slow

**Critical risks:**
- Authentication chain complexity (DefaultAzureCredential fails silently)
- gpt-realtime 30-minute session limit (no warning event)
- Model Router may route to models that don't support structured output
- Content filtering false positives on industry terminology

## Key Findings

### Recommended Stack

The stack is well-defined with verified 2026 versions:

**Backend (Python):**
- FastAPI 0.115+ with WebSocket support
- `azure-ai-projects` 1.0.0 (stable July 2025)
- `openai[realtime]` 2.15+ for voice streaming
- `sse-starlette` 3.1.2 for text streaming

**Frontend (React):**
- React 19.2.3 + Vite 7.3.1
- Zustand 5.0.10 for state (not Redux)
- Recharts 3.6.0 for charts (not gpt-image-1-mini for every chart)
- TanStack Query 5.90+ for server state

**Core technologies:**
- `azure-ai-projects` 1.0.0: Azure Foundry SDK — connects to project endpoint for all models
- `openai[realtime]`: Voice streaming — handles gpt-realtime WebSocket connection
- `zustand`: State management — minimal boilerplate, excellent for real-time dashboard state

### Expected Features

**Must have (table stakes):**
- Conversation history with scroll — users expect to review past exchanges
- Real-time response streaming — sub-500ms time-to-first-token expected
- Visual feedback during processing — loading states, typing indicators
- Dashboard visualization panel — without this, it's just a chatbot

**Should have (competitive):**
- Natural Language Mode Switching — UNIQUE differentiator, no major competitor does this
- Voice-Visual Synchronization — emerging "wow factor" feature
- Seeded Persona Consistency — creates believable demo without real data

**Defer (v2+):**
- Dynamic Industry Generation — complex, defer until core mode switching works
- Advanced tool calling patterns — start with simple single-tool flows

### Architecture Approach

Three-tier architecture with clear boundaries:

**Major components:**
1. **React Frontend** — presentation, local state (Zustand), WebSocket client
2. **FastAPI Backend** — orchestration, session management, Azure relay, mode storage
3. **Azure AI Services** — model-router (LLM), gpt-realtime (voice), gpt-image-1-mini (images)

**Critical architectural decision:** Single WebSocket connection for all real-time streams (voice audio, chat messages, tool results). Separate connections create synchronization nightmares.

### Critical Pitfalls

Top 5 pitfalls that could derail the project:

1. **DefaultAzureCredential chain failures** — Use explicit credentials during development (InteractiveBrowserCredential), not DefaultAzureCredential
2. **gpt-realtime 30-minute session limit** — Implement session heartbeat and proactive reconnection at ~28 minutes
3. **WebSocket vs WebRTC latency** — Use WebRTC for browser-to-Azure voice, not WebSocket relay
4. **Model Router ignores structured output** — Use direct model deployment for structured output requirements
5. **Content filter false positives** — Pre-screen prompts, configure custom filters, implement fallback responses

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Foundation & Infrastructure
**Rationale:** Everything depends on WebSocket and Azure client working correctly. Authentication pitfalls must be resolved before any feature work.
**Delivers:** Project skeleton, WebSocket infrastructure, Azure client with working auth
**Addresses:** Table stakes (connection, error handling)
**Avoids:** Pitfalls 1.1-1.3, 10.1-10.2 (authentication, API version issues)

### Phase 2: Chat Interface & LLM Integration
**Rationale:** Proves backend/Azure integration works. Chat is simpler than voice, validates tool calling flow.
**Delivers:** Working chat panel, message streaming, basic tool calling
**Uses:** model-router, Zustand, TanStack Query
**Addresses:** Conversation history, real-time streaming
**Avoids:** Pitfalls 3.3-3.5, 6.1-6.2 (streaming, async patterns)

### Phase 3: Dashboard & Visualization
**Rationale:** Tool calls need somewhere to render. Dashboard components required before tool-to-UI flow.
**Delivers:** Dashboard layout, chart components, tool → visualization flow
**Implements:** Dashboard panel, metrics display, chart animations
**Uses:** Recharts, CSS custom properties for theming foundation

### Phase 4: Mode System & Theming
**Rationale:** Mode switching is the core differentiator. Requires dashboard foundation from Phase 3.
**Delivers:** Pre-built modes (Banking, Insurance, Healthcare), mode switching, theming
**Addresses:** Industry theming, mode persistence, seeded personas
**Avoids:** Pitfall 9.1 (prompt injection in mode generation)

### Phase 5: Voice Integration
**Rationale:** Most complex feature. Requires all other infrastructure stable. 30-minute session limit needs careful handling.
**Delivers:** Toggle-mode voice, voice-visual sync
**Uses:** gpt-realtime, WebRTC connection
**Avoids:** Pitfalls 2.1-2.7 (session limits, VAD issues, transcription bugs)

### Phase 6: Dynamic Mode Generation
**Rationale:** Advanced feature building on stable mode system. Defer until core modes work.
**Delivers:** Arbitrary industry generation on-demand
**Addresses:** Dynamic mode generation requirement
**Avoids:** Pitfall 9.1 (mode injection) with proper validation

### Phase 7: Polish & Testing
**Rationale:** Integration testing, edge cases, Playwright verification
**Delivers:** Tested, production-ready demo
**Uses:** Playwright for automated testing

### Phase 8: Caching & Performance
**Rationale:** Optimization after core features work
**Delivers:** Image caching, mode caching, performance improvements

### Phase Ordering Rationale

- **Phase 1 before all:** WebSocket + auth is foundation for everything
- **Phase 2 before 3:** Need LLM working before tool calls can update dashboard
- **Phase 3 before 4:** Dashboard must exist before modes can customize it
- **Phase 4 before 5:** Mode context needed for voice system prompts
- **Phase 5 requires 2-4:** Voice + visual sync needs all previous pieces
- **Phase 6 after 4:** Dynamic generation builds on stable mode infrastructure
- **Phases 7-8 last:** Polish and optimization after features work

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 5 (Voice):** gpt-realtime has many documented issues, needs careful implementation
- **Phase 6 (Dynamic Generation):** Prompt engineering for reliable mode generation

Phases with standard patterns (skip research-phase):
- **Phase 1 (Foundation):** Well-documented FastAPI + React patterns
- **Phase 2 (Chat):** Standard LLM chat implementation
- **Phase 3 (Dashboard):** Standard React dashboard patterns

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Verified against PyPI, npm, official docs |
| Features | MEDIUM | Novel combination, less direct precedent |
| Architecture | HIGH | Based on official Microsoft documentation |
| Pitfalls | HIGH | Documented in official known issues, Q&A |

**Overall confidence:** HIGH

### Gaps to Address

1. **gpt-image-1-mini for charts:** Research suggests Recharts may be better for most charts, with AI image generation for special cases. Validate during Phase 3.

2. **Voice latency requirements:** Need to validate WebRTC achieves <200ms latency in practice during Phase 5.

3. **Mode generation reliability:** Prompt engineering for consistent mode configs needs experimentation during Phase 6.

## Sources

### Primary (HIGH confidence)
- Azure AI Projects SDK 1.0.0 — [PyPI](https://pypi.org/project/azure-ai-projects/)
- Azure OpenAI Realtime Quickstart — [Microsoft Learn](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/realtime-audio-quickstart)
- Azure OpenAI Function Calling — [Microsoft Learn](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/function-calling)
- FastAPI WebSockets — [Official Docs](https://fastapi.tiangolo.com/advanced/websockets/)

### Secondary (MEDIUM confidence)
- State Management 2025 — Zustand recommended for dashboards
- React Chart Libraries 2025 — Recharts confirmed as top choice
- Azure Known Issues — [Microsoft Learn](https://learn.microsoft.com/en-us/azure/ai-foundry/reference/foundry-known-issues)

### Tertiary (LOW confidence)
- Dynamic theming patterns — community articles, needs validation

---
*Research completed: 2026-01-15*
*Ready for roadmap: yes*
