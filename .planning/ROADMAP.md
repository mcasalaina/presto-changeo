# Roadmap: Presto-Change-O

## Overview

Presto-Change-O is an AI-powered multi-industry simulation dashboard. The journey starts with foundational infrastructure (WebSocket, Azure auth), builds the chat interface, then dashboard visualization, followed by the core mode-switching system with theming. Voice integration adds the "wow factor," dynamic mode generation enables arbitrary industries, and finally caching optimizes performance. Each phase delivers a complete, verifiable capability.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation** - Project skeleton, WebSocket infrastructure, Azure auth
- [x] **Phase 2: Chat Interface** - Working chat with streaming AI responses
- [x] **Phase 3: Dashboard** - Central dashboard with visualization and metrics
- [x] **Phase 4: Mode System** - Pre-built modes with dynamic theming
- [ ] **Phase 5: Persona** - Seeded personas with industry-appropriate data
- [ ] **Phase 6: Voice** - Toggle-mode voice with visual synchronization
- [ ] **Phase 7: Dynamic Generation** - Generate arbitrary industry modes on-demand
- [ ] **Phase 8: Caching** - Performance optimization with caching and error recovery

## Phase Details

### Phase 1: Foundation
**Goal**: Project skeleton with WebSocket infrastructure and Azure client with working auth
**Depends on**: Nothing (first phase)
**Requirements**: (Infrastructure - enables all other phases)
**Success Criteria** (what must be TRUE):
  1. Project builds without errors (frontend + backend)
  2. Development servers run locally (Vite + FastAPI)
  3. WebSocket connection established between frontend and backend
  4. Azure client authenticates successfully with InteractiveBrowserCredential
**Research**: Unlikely (well-documented FastAPI + React patterns)
**Plans**: TBD

Plans:
- [ ] 01-01: TBD

### Phase 2: Chat Interface
**Goal**: Working chat panel with streaming AI responses
**Depends on**: Phase 1
**Requirements**: CHAT-01, CHAT-02, CHAT-03, CHAT-04
**Success Criteria** (what must be TRUE):
  1. User can view conversation history with scroll
  2. User can type and send messages (Enter to send)
  3. AI responses stream progressively in real-time
  4. Loading and typing indicators show during processing
**Research**: Unlikely (standard LLM chat implementation)
**Plans**: TBD

Plans:
- [ ] 02-01: TBD

### Phase 3: Dashboard
**Goal**: Central dashboard with visualization area and metrics
**Depends on**: Phase 2
**Requirements**: DASH-01, DASH-02, DASH-03, DASH-04
**Success Criteria** (what must be TRUE):
  1. User sees central dashboard panel with visualization area
  2. User sees metrics, status indicators, and KPIs
  3. User can navigate via bottom tabs
  4. AI tool calls can render visualizations with animation
**Research**: Unlikely (standard React dashboard patterns)
**Plans**: TBD

Plans:
- [ ] 03-01: TBD

### Phase 4: Mode System
**Goal**: Pre-built industry modes with dynamic theming
**Depends on**: Phase 3
**Requirements**: MODE-01, MODE-02, MODE-03
**Success Criteria** (what must be TRUE):
  1. User can switch modes via "Presto-Change-O, you're a [industry]" command
  2. Banking, Insurance, Healthcare modes available and functional
  3. Interface applies industry-appropriate color theming on mode switch
  4. Tabs adapt content per industry mode
**Research**: Likely (prompt engineering for mode context)
**Research topics**: CSS custom property theming, mode config schema, industry color palettes
**Plans**: TBD

Plans:
- [ ] 04-01: TBD

### Phase 5: Persona
**Goal**: Seeded personas with consistent industry-appropriate fake data
**Depends on**: Phase 4
**Requirements**: PERS-01, PERS-02
**Success Criteria** (what must be TRUE):
  1. System generates seeded persona on mode switch
  2. Persona data is consistent within session (same balances/claims on refresh)
  3. Data is industry-appropriate (bank balances for banking, claims for insurance)
**Research**: Unlikely (standard data generation patterns)
**Plans**: TBD

Plans:
- [ ] 05-01: TBD

### Phase 6: Voice
**Goal**: Toggle-mode voice with voice-visual synchronization
**Depends on**: Phase 5
**Requirements**: VOIC-01, VOIC-02, VOIC-03, VOIC-04
**Success Criteria** (what must be TRUE):
  1. User can enable toggle-mode voice and speak freely
  2. AI voice responds with short spoken answers
  3. Voice response syncs with visual (chart appears as voice speaks)
  4. User can mute voice output to prevent feedback
**Research**: Likely (gpt-realtime has many documented issues)
**Research topics**: gpt-realtime session management, WebRTC vs WebSocket, 30-minute limit handling, VAD configuration
**Plans**: TBD

Plans:
- [ ] 06-01: TBD

### Phase 7: Dynamic Generation
**Goal**: Generate arbitrary industry modes on-demand
**Depends on**: Phase 6
**Requirements**: MODE-04
**Success Criteria** (what must be TRUE):
  1. User can request arbitrary industry (e.g., "you're a pet store")
  2. System generates appropriate theme, tabs, and persona data
  3. Generated mode is usable immediately
**Research**: Likely (prompt engineering for reliable mode generation)
**Research topics**: Mode config validation, generation prompt templates, caching generated modes
**Plans**: TBD

Plans:
- [ ] 07-01: TBD

### Phase 8: Caching
**Goal**: Production-ready performance with caching and error recovery
**Depends on**: Phase 7
**Requirements**: PERF-01, PERF-02, PERF-03, PERF-04
**Success Criteria** (what must be TRUE):
  1. User sees loading spinner during mode switching/generation
  2. Generated styles and images are cached for reuse
  3. Generated modes persist server-side for future use
  4. System recovers gracefully from API failures with retry option
**Research**: Unlikely (standard caching patterns)
**Plans**: TBD

Plans:
- [ ] 08-01: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 2/2 | Complete | 2026-01-16 |
| 2. Chat Interface | 2/2 | Complete | 2026-01-18 |
| 3. Dashboard | 3/3 | Complete | 2026-01-18 |
| 4. Mode System | 3/3 | Complete | 2026-01-18 |
| 5. Persona | 0/? | Not started | - |
| 6. Voice | 0/? | Not started | - |
| 7. Dynamic Generation | 0/? | Not started | - |
| 8. Caching | 0/? | Not started | - |
