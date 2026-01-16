# Architecture Research: Presto-Change-O

**Researched:** 2026-01-15
**Domain:** Real-time voice + chat + visualization dashboard
**Confidence:** HIGH

## Executive Summary

Real-time voice + chat + visualization systems are structured around three core layers: a React frontend handling UI state and real-time streams, a Python backend orchestrating LLM interactions and business logic, and Azure AI services providing voice/text/image generation. The architecture follows an event-driven pattern where WebSocket connections enable bidirectional streaming for both chat and voice, with tool calls from the LLM triggering visualization updates on the frontend.

The key architectural insight is that the Azure OpenAI Realtime API does not connect directly to end users - it requires a middle-tier service to terminate audio streams. This means the FastAPI backend acts as a relay and orchestrator, not just an API gateway. For Presto-Change-O specifically, mode switching (industry transformations) is handled through CSS custom properties and React context, allowing runtime theme changes without page reloads.

**Primary recommendation:** Build a three-tier architecture with clear boundaries: React handles presentation and local state, FastAPI handles orchestration and session management, Azure handles AI inference. Use WebSocket for all real-time streams (voice, chat, tool results).

## System Architecture

### High-Level Component Diagram

```
+------------------+     +-------------------+     +----------------------+
|                  |     |                   |     |                      |
|  React Frontend  |<--->|  FastAPI Backend  |<--->|  Azure AI Services   |
|                  |     |                   |     |                      |
+------------------+     +-------------------+     +----------------------+
        |                        |                         |
        v                        v                         v
+------------------+     +-------------------+     +----------------------+
| - Chat Panel     |     | - WebSocket Hub   |     | - model-router (LLM) |
| - Voice Toggle   |     | - Session Manager |     | - gpt-realtime       |
| - Dashboard      |     | - Mode Controller |     | - gpt-image-1-mini   |
| - Theme Context  |     | - Tool Executor   |     | - Bing Grounding     |
| - State (Zustand)|     | - Mode Storage    |     +----------------------+
+------------------+     +-------------------+
```

### Component Boundaries

| Component | Responsibility | Talks To | Data Owned |
|-----------|---------------|----------|------------|
| **Chat Panel** | Message display, input handling | Backend (WebSocket) | Message history (local) |
| **Voice Module** | Audio capture, playback, VAD | Backend (WebSocket) | Audio buffers |
| **Dashboard** | Visualization rendering, animations | State store | Current visualization state |
| **Theme Context** | Industry colors, CSS variables | React tree | Theme configuration |
| **State Store (Zustand)** | Global state management | All frontend components | Session state, mode config |
| **WebSocket Hub** | Connection management, message routing | Frontend, Azure | Active connections |
| **Session Manager** | User sessions, persona data | WebSocket Hub, Storage | Session metadata |
| **Mode Controller** | Industry mode logic, generation | Azure LLM, Storage | Mode definitions |
| **Tool Executor** | LLM tool call handling | Azure LLM, Dashboard | Tool results |
| **Mode Storage** | Persist generated modes | Mode Controller | Cached mode configs |

### Data Flow Diagrams

#### Chat Interaction Flow
```
User Input --> React Chat --> WebSocket --> FastAPI --> model-router
                                                           |
                                                           v
Dashboard <-- WebSocket <-- FastAPI <-- Tool Call Response + Message
```

#### Voice Interaction Flow
```
Microphone --> Web Audio API --> WebSocket --> FastAPI --> gpt-realtime
                                                              |
                                                              v
Speaker <-- Audio Buffer <-- WebSocket <-- FastAPI <-- Audio + Tool Calls
```

#### Mode Switch Flow
```
"Presto-Change-O, you're a bank"
        |
        v
FastAPI receives command --> Check mode cache
        |                           |
        v (miss)                    v (hit)
Generate mode config         Load cached config
        |                           |
        v                           v
Store in cache              Return config
        |__________________________|
                    |
                    v
Frontend receives config --> Update Zustand --> Apply CSS variables
                                                      |
                                                      v
                                             Dashboard re-renders
```

## Component Details

### Frontend Architecture (React + Vite)

#### State Management: Zustand

Zustand is the recommended choice for this dashboard because:
- Minimal boilerplate, no Provider wrapper required
- Excellent for real-time data (external source integration)
- Performant - avoids React Context re-render issues
- Middleware support for persistence and devtools

**Store Structure:**
```typescript
interface AppStore {
  // Session
  sessionId: string;
  persona: PersonaData | null;

  // Mode
  currentMode: IndustryMode | null;
  modeLoading: boolean;

  // Chat
  messages: ChatMessage[];

  // Voice
  voiceEnabled: boolean;
  isListening: boolean;
  isSpeaking: boolean;

  // Dashboard
  visualizations: Visualization[];
  animatingChart: string | null;

  // Actions
  setMode: (mode: IndustryMode) => void;
  addMessage: (message: ChatMessage) => void;
  updateVisualization: (viz: Visualization) => void;
  // ...
}
```

#### Dynamic Theming: CSS Custom Properties

Use CSS custom properties with Tailwind CSS v4 for runtime theme switching:

```css
/* themes.css */
:root {
  --color-primary: 59 130 246;      /* blue default */
  --color-secondary: 99 102 241;
  --color-accent: 236 72 153;
  --color-background: 255 255 255;
  --color-surface: 249 250 251;
}

.theme-banking {
  --color-primary: 30 64 175;       /* deep blue */
  --color-accent: 34 197 94;        /* green */
}

.theme-healthcare {
  --color-primary: 20 184 166;      /* teal */
  --color-accent: 244 63 94;        /* red */
}

.theme-insurance {
  --color-primary: 79 70 229;       /* indigo */
  --color-accent: 251 146 60;       /* orange */
}
```

**Theme Switching:**
```typescript
// On mode change, apply class to root element
document.documentElement.classList.remove('theme-banking', 'theme-healthcare', ...);
document.documentElement.classList.add(`theme-${mode.themeKey}`);
```

#### WebSocket Management

Single WebSocket connection for all real-time streams:

```typescript
// websocket.ts
class AppWebSocket {
  private ws: WebSocket | null = null;
  private handlers: Map<string, Handler[]> = new Map();

  connect(sessionId: string) {
    this.ws = new WebSocket(`ws://localhost:8000/ws/${sessionId}`);
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.dispatch(data.type, data.payload);
    };
  }

  // Message types: chat, voice_audio, tool_result, mode_update, etc.
  send(type: string, payload: any) {
    this.ws?.send(JSON.stringify({ type, payload }));
  }

  on(type: string, handler: Handler) {
    // Register handlers per message type
  }
}
```

### Backend Architecture (FastAPI)

#### Module Structure

Use APIRouter for clean separation:

```python
# Directory structure
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, routers included
│   ├── config.py            # Pydantic settings
│   ├── dependencies.py      # Shared dependencies (auth, etc.)
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── chat.py          # Chat endpoints
│   │   ├── voice.py         # Voice WebSocket
│   │   ├── modes.py         # Mode management
│   │   └── health.py        # Health checks
│   ├── services/
│   │   ├── __init__.py
│   │   ├── azure_client.py  # Azure AI client wrapper
│   │   ├── session.py       # Session management
│   │   ├── mode_generator.py # Mode generation logic
│   │   └── tool_executor.py # Tool call handling
│   ├── models/
│   │   ├── __init__.py
│   │   ├── messages.py      # Pydantic models for messages
│   │   ├── modes.py         # Mode configuration models
│   │   └── tools.py         # Tool definitions
│   └── storage/
│       ├── __init__.py
│       └── mode_cache.py    # Mode persistence
├── tests/
├── requirements.txt
└── Dockerfile
```

#### WebSocket Hub Pattern

Central WebSocket manager for coordinating streams:

```python
# services/websocket_hub.py
class WebSocketHub:
    def __init__(self):
        self.connections: dict[str, WebSocket] = {}
        self.sessions: dict[str, SessionState] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.connections[session_id] = websocket
        self.sessions[session_id] = SessionState()

    async def broadcast_to_session(self, session_id: str, message: dict):
        if ws := self.connections.get(session_id):
            await ws.send_json(message)

    async def handle_message(self, session_id: str, data: dict):
        msg_type = data.get("type")
        if msg_type == "chat":
            await self.handle_chat(session_id, data)
        elif msg_type == "voice_audio":
            await self.handle_voice(session_id, data)
        elif msg_type == "mode_switch":
            await self.handle_mode_switch(session_id, data)
```

#### Azure Integration Pattern

Async client wrapper for Azure AI services:

```python
# services/azure_client.py
class AzureAIClient:
    def __init__(self, config: Settings):
        self.credential = InteractiveBrowserCredential()
        self.endpoint = config.azure_endpoint
        self.project = config.azure_project

    async def chat_completion(
        self,
        messages: list[dict],
        tools: list[dict] | None = None
    ) -> AsyncIterator[ChatChunk]:
        """Stream chat completion with tool support."""
        # Use model-router deployment
        async for chunk in self._stream_completion(
            deployment="model-router",
            messages=messages,
            tools=tools
        ):
            yield chunk

    async def realtime_session(self, session_id: str) -> RealtimeSession:
        """Create Azure Realtime API session for voice."""
        # Returns session object that handles gpt-realtime
        pass

    async def generate_image(self, prompt: str) -> bytes:
        """Generate chart/visualization image."""
        # Use gpt-image-1-mini deployment
        pass
```

### Azure AI Integration

#### Realtime API Architecture

Based on official Microsoft documentation, the architecture for voice:

```
Browser Audio --> FastAPI WebSocket --> Azure Realtime API (WebSocket)
                        |                        |
                        |<-- Tool Calls <--------|
                        |                        |
                        |<-- Audio Response <----|
                        |
                        v
Tool Executor --> Execute Tool --> Update Dashboard
```

**Key Configuration (session.update):**
```json
{
  "type": "session.update",
  "session": {
    "voice": "alloy",
    "instructions": "You are a helpful assistant for [industry]. Keep responses brief.",
    "input_audio_format": "pcm16",
    "turn_detection": {
      "type": "server_vad",
      "threshold": 0.5,
      "silence_duration_ms": 200,
      "create_response": true
    },
    "tools": [
      {
        "type": "function",
        "name": "show_chart",
        "description": "Display a chart on the dashboard",
        "parameters": {...}
      },
      {
        "type": "function",
        "name": "update_metric",
        "description": "Update a metric value",
        "parameters": {...}
      }
    ]
  }
}
```

**Voice Activity Detection:** Use `server_vad` for natural conversation flow. The server automatically detects speech boundaries and triggers responses.

#### Tool Calling Flow

```
1. LLM decides to call tool (e.g., show_chart)
2. Azure sends function_call event to backend
3. Backend executes tool:
   - Generates chart (gpt-image-1-mini or client-side)
   - Prepares visualization data
4. Backend sends tool_result to Azure
5. Azure generates spoken response about the chart
6. Backend forwards:
   - Audio stream to frontend for playback
   - Visualization data to frontend for rendering
7. Frontend renders chart, plays audio simultaneously
```

### Mode System Architecture

#### Mode Configuration Schema

```typescript
interface IndustryMode {
  id: string;
  name: string;                    // "Banking", "Healthcare", etc.
  description: string;

  // Theme
  theme: {
    key: string;                   // CSS class suffix
    primary: string;               // HSL or RGB values
    secondary: string;
    accent: string;
    background: string;
  };

  // Navigation
  tabs: {
    id: string;
    label: string;
    icon: string;
  }[];

  // Dashboard
  metrics: {
    id: string;
    label: string;
    format: string;               // "currency", "percentage", "number"
    defaultValue: number;
  }[];

  // Persona
  personaSchema: {
    fields: { name: string; type: string; generator: string }[];
  };

  // LLM Context
  systemPrompt: string;
  availableTools: string[];
}
```

#### Mode Generation Pipeline

```
Command "Presto-Change-O, you're a [X]"
        |
        v
Parse industry from command
        |
        v
Check mode cache ----> (hit) --> Return cached mode
        |
        v (miss)
Call model-router with:
  - Industry name
  - Schema for mode config
  - Bing grounding for industry research
        |
        v
Validate generated config
        |
        v
Store in cache
        |
        v
Return to frontend
```

## Recommended Project Structure

### Frontend (React + Vite + TypeScript)

```
frontend/
├── public/
│   └── assets/              # Static images, icons
├── src/
│   ├── components/
│   │   ├── chat/
│   │   │   ├── ChatPanel.tsx
│   │   │   ├── MessageList.tsx
│   │   │   ├── MessageInput.tsx
│   │   │   └── index.ts
│   │   ├── voice/
│   │   │   ├── VoiceToggle.tsx
│   │   │   ├── AudioVisualizer.tsx
│   │   │   └── index.ts
│   │   ├── dashboard/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── MetricCard.tsx
│   │   │   ├── ChartContainer.tsx
│   │   │   ├── Gauge.tsx
│   │   │   └── index.ts
│   │   ├── navigation/
│   │   │   ├── TabBar.tsx
│   │   │   └── index.ts
│   │   └── ui/              # Shared UI primitives
│   │       ├── Button.tsx
│   │       ├── Card.tsx
│   │       ├── Spinner.tsx
│   │       └── index.ts
│   ├── features/
│   │   ├── mode/
│   │   │   ├── ModeContext.tsx
│   │   │   ├── useMode.ts
│   │   │   └── modeUtils.ts
│   │   └── session/
│   │       ├── SessionProvider.tsx
│   │       └── useSession.ts
│   ├── hooks/
│   │   ├── useWebSocket.ts
│   │   ├── useAudio.ts
│   │   └── useVisualization.ts
│   ├── services/
│   │   ├── api.ts           # REST API calls
│   │   └── websocket.ts     # WebSocket client
│   ├── store/
│   │   ├── index.ts         # Zustand store
│   │   ├── slices/
│   │   │   ├── chatSlice.ts
│   │   │   ├── voiceSlice.ts
│   │   │   ├── dashboardSlice.ts
│   │   │   └── modeSlice.ts
│   │   └── types.ts
│   ├── styles/
│   │   ├── index.css        # Tailwind imports
│   │   └── themes.css       # Industry theme definitions
│   ├── types/
│   │   ├── api.ts
│   │   ├── mode.ts
│   │   └── messages.ts
│   ├── utils/
│   │   ├── audio.ts
│   │   └── formatting.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── vite-env.d.ts
├── index.html
├── package.json
├── tsconfig.json
├── tailwind.config.js
└── vite.config.ts
```

### Backend (FastAPI + Python)

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry
│   ├── config.py            # Pydantic settings
│   ├── dependencies.py      # Shared deps (auth, db)
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── websocket.py     # Main WebSocket endpoint
│   │   ├── modes.py         # Mode CRUD endpoints
│   │   ├── sessions.py      # Session management
│   │   └── health.py        # Health/ready checks
│   ├── services/
│   │   ├── __init__.py
│   │   ├── azure/
│   │   │   ├── __init__.py
│   │   │   ├── client.py    # Base Azure client
│   │   │   ├── chat.py      # model-router service
│   │   │   ├── realtime.py  # gpt-realtime service
│   │   │   └── images.py    # gpt-image-1-mini service
│   │   ├── websocket_hub.py # Connection management
│   │   ├── session_manager.py
│   │   ├── mode_generator.py
│   │   └── tool_executor.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── messages.py      # WebSocket message schemas
│   │   ├── modes.py         # Mode config schemas
│   │   ├── sessions.py      # Session schemas
│   │   └── tools.py         # Tool definitions
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── mode_cache.py    # File/Redis mode storage
│   │   └── session_store.py # Session persistence
│   └── tools/
│       ├── __init__.py
│       ├── registry.py      # Tool registration
│       ├── chart_tools.py   # Chart generation tools
│       └── metric_tools.py  # Metric update tools
├── tests/
│   ├── __init__.py
│   ├── test_websocket.py
│   ├── test_modes.py
│   └── conftest.py
├── requirements.txt
├── Dockerfile
└── .env.example
```

### Monorepo Root

```
presto-changeo/
├── frontend/                # React app (structure above)
├── backend/                 # FastAPI app (structure above)
├── .planning/               # GSD planning files
│   ├── PROJECT.md
│   ├── research/
│   │   └── ARCHITECTURE.md  # This file
│   └── phases/
├── .env.example             # Environment template
├── .gitignore
├── docker-compose.yml       # Local dev orchestration
└── README.md
```

## Build Order / Dependencies

### Phase Dependencies

Based on this architecture, components must be built in dependency order:

```
Phase 1: Foundation
├── Backend skeleton (FastAPI + config + health)
├── Frontend skeleton (Vite + React + routing)
├── WebSocket infrastructure (both ends)
└── Azure client wrapper (auth working)

Phase 2: Chat Core
├── Chat UI components (depends on: Phase 1 frontend)
├── Chat WebSocket handler (depends on: Phase 1 WebSocket)
├── model-router integration (depends on: Phase 1 Azure client)
└── Basic message flow working

Phase 3: Dashboard
├── Dashboard layout components (depends on: Phase 1 frontend)
├── Zustand store setup (depends on: Phase 2 for message types)
├── Tool definitions (depends on: Phase 2 LLM integration)
└── Tool call -> visualization flow

Phase 4: Voice
├── Audio capture/playback (depends on: Phase 1 frontend)
├── gpt-realtime integration (depends on: Phase 1 Azure client)
├── Voice WebSocket relay (depends on: Phase 2 WebSocket patterns)
└── Voice + tool sync (depends on: Phase 3 tool flow)

Phase 5: Mode System
├── Mode schema + storage (depends on: Phase 2 LLM for generation)
├── Theme CSS system (depends on: Phase 1 frontend)
├── Mode generation pipeline (depends on: Phase 2 LLM)
├── Command parsing (depends on: Phase 2/4 for input channels)
└── Pre-built modes (depends on: mode infrastructure)
```

### Critical Path

The minimum viable path to demonstrate the core experience:

1. **WebSocket connection** - Everything else depends on this
2. **Chat message flow** - Proves backend/Azure integration
3. **Single tool call** - Proves LLM can trigger frontend updates
4. **Basic voice** - Proves Realtime API integration
5. **One mode switch** - Proves the magic moment works

### Parallel Work Streams

After Phase 1, these can proceed in parallel:
- UI polish (pure frontend)
- Additional tools (backend + frontend)
- Pre-built mode configs (content, not code)
- Audio visualization (frontend only)

## Real-Time Streaming Patterns

### WebSocket Message Protocol

Standardized message format for all WebSocket communication:

```typescript
interface WebSocketMessage {
  type: MessageType;
  payload: unknown;
  timestamp: number;
  sessionId: string;
}

type MessageType =
  // Client -> Server
  | 'chat_message'
  | 'voice_audio_chunk'
  | 'voice_start'
  | 'voice_stop'
  | 'mode_switch_request'

  // Server -> Client
  | 'chat_response_start'
  | 'chat_response_chunk'
  | 'chat_response_end'
  | 'voice_audio_response'
  | 'voice_transcript'
  | 'tool_call_start'
  | 'tool_call_result'
  | 'mode_update'
  | 'error';
```

### Streaming Chat Pattern

```typescript
// Frontend handling
ws.on('chat_response_start', () => {
  store.startTypingIndicator();
});

ws.on('chat_response_chunk', (chunk) => {
  store.appendToCurrentMessage(chunk.text);
});

ws.on('chat_response_end', () => {
  store.finalizeCurrentMessage();
});

ws.on('tool_call_result', (result) => {
  store.updateVisualization(result.visualization);
  store.animateChart(result.chartId);
});
```

### Voice Audio Streaming

```typescript
// Frontend: capture and send audio
const audioContext = new AudioContext({ sampleRate: 24000 });
const mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
const source = audioContext.createMediaStreamSource(mediaStream);
const processor = audioContext.createScriptProcessor(4096, 1, 1);

processor.onaudioprocess = (event) => {
  const pcm16 = float32ToPcm16(event.inputBuffer.getChannelData(0));
  ws.send('voice_audio_chunk', { audio: pcm16 });
};

// Frontend: receive and play audio
ws.on('voice_audio_response', (data) => {
  const pcm16 = new Int16Array(data.audio);
  const float32 = pcm16ToFloat32(pcm16);
  playAudioBuffer(float32);
});
```

### Backend Relay Pattern

```python
# Backend: relay between frontend and Azure Realtime
async def handle_voice_session(session_id: str, frontend_ws: WebSocket):
    azure_session = await azure_client.realtime_session(session_id)

    async def frontend_to_azure():
        async for message in frontend_ws.iter_json():
            if message["type"] == "voice_audio_chunk":
                await azure_session.send_audio(message["payload"]["audio"])

    async def azure_to_frontend():
        async for event in azure_session.events():
            if event.type == "response.audio.delta":
                await frontend_ws.send_json({
                    "type": "voice_audio_response",
                    "payload": {"audio": event.audio}
                })
            elif event.type == "response.function_call":
                result = await execute_tool(event.function_call)
                await azure_session.send_tool_result(result)
                await frontend_ws.send_json({
                    "type": "tool_call_result",
                    "payload": result
                })

    await asyncio.gather(frontend_to_azure(), azure_to_frontend())
```

### Connection Resilience

```typescript
// Frontend: reconnection with exponential backoff
class ResilientWebSocket {
  private reconnectAttempts = 0;
  private maxAttempts = 5;
  private baseDelay = 1000;

  async connect() {
    try {
      this.ws = new WebSocket(this.url);
      this.reconnectAttempts = 0;
    } catch (error) {
      await this.handleReconnect();
    }
  }

  private async handleReconnect() {
    if (this.reconnectAttempts >= this.maxAttempts) {
      this.onFatalError();
      return;
    }

    const delay = this.baseDelay * Math.pow(2, this.reconnectAttempts);
    this.reconnectAttempts++;

    await sleep(delay);
    await this.connect();
  }
}
```

## Anti-Patterns to Avoid

### 1. Direct Browser-to-Azure Realtime Connection

**Why it's tempting:** Simpler architecture, fewer hops
**Why it fails:**
- Cannot execute tools server-side
- Cannot persist conversation history
- Cannot coordinate with chat
- Exposes Azure credentials to client

**Do instead:** Always relay through FastAPI backend

### 2. Separate WebSocket Connections per Feature

**Why it's tempting:** Cleaner separation of concerns
**Why it fails:**
- Connection overhead
- Synchronization complexity
- More failure modes
- Harder to coordinate tool results with voice/chat

**Do instead:** Single WebSocket with message type routing

### 3. REST for Real-Time Updates

**Why it's tempting:** Familiar pattern, simpler to implement
**Why it fails:**
- Polling is wasteful
- SSE is one-directional (can't send audio)
- Higher latency for tool results

**Do instead:** WebSocket for all real-time, REST only for CRUD (modes, config)

### 4. Storing Full Audio in State

**Why it's tempting:** Can replay, simpler mental model
**Why it fails:**
- Memory explosion
- Not needed (audio is ephemeral)
- Slows down state updates

**Do instead:** Stream audio through buffers, only store transcripts

### 5. Generating Themes at Runtime via LLM

**Why it's tempting:** Maximum flexibility, less pre-work
**Why it fails:**
- Latency on every mode switch
- Inconsistent results
- LLM may generate invalid CSS

**Do instead:** Generate mode configs (including theme) once, cache, apply CSS variables

## Sources

### Primary (HIGH confidence)
- [FastAPI Official Docs - Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/) - Project structure patterns
- [Microsoft Learn - Azure OpenAI Realtime API](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/realtime-audio) - Voice integration architecture, WebRTC/WebSocket patterns, tool calling support, VAD configuration
- [Tailwind CSS v4 - Theme Variables](https://tailwindcss.com/docs/theme) - CSS custom property theming

### Secondary (MEDIUM confidence)
- [FastAPI Best Practices GitHub](https://github.com/zhanymkanov/fastapi-best-practices) - Community patterns for async, configuration
- [Streaming LLMs: Reshaping API Design](https://nitishagar.medium.com/the-streaming-llms-reshaping-api-design-a9102db9b8ef) - Double-streaming architecture patterns
- [State Management in 2025 - DEV Community](https://dev.to/hijazi313/state-management-in-2025-when-to-use-context-redux-zustand-or-jotai-2d2k) - Zustand recommendation for dashboards
- [React Folder Structure 2025](https://www.robinwieruch.de/react-folder-structure/) - Feature-based organization
- [FastAPI WebSocket Patterns - Medium](https://hexshift.medium.com/how-to-incorporate-advanced-websocket-architectures-in-fastapi-for-high-performance-real-time-b48ac992f401) - WebSocket scaling, pub/sub patterns
- [Tailwind Dynamic Themes - Medium](https://medium.com/render-beyond/build-a-flawless-multi-theme-ui-using-new-tailwind-css-v4-react-dca2b3c95510) - Runtime theming with CSS variables

### Tertiary (LOW confidence, community patterns)
- [Azure Samples - aoai-realtime-audio-sdk](https://github.com/Azure-Samples/aoai-realtime-audio-sdk) - Reference implementation
- [fastapi_websocket_pubsub](https://github.com/permitio/fastapi_websocket_pubsub) - Pub/sub library option

## Confidence Assessment

| Area | Level | Reason |
|------|-------|--------|
| Overall Architecture | HIGH | Based on official docs for FastAPI, Azure Realtime API |
| WebSocket Patterns | HIGH | Official FastAPI docs + multiple verified sources |
| Azure Realtime Integration | HIGH | Microsoft Learn documentation directly |
| Voice Activity Detection | HIGH | Official Azure documentation |
| React Project Structure | MEDIUM | Community consensus, not single authoritative source |
| Zustand for State | MEDIUM | Multiple 2025 articles agree, community standard |
| Theming Approach | MEDIUM | Tailwind v4 docs + community articles |
| Build Order | MEDIUM | Derived from architecture analysis, not prescriptive source |

## Open Questions

1. **Redis vs File-based Mode Cache**
   - What we know: Both work, Redis better for multi-instance
   - What's unclear: Expected scale, deployment model
   - Recommendation: Start with file-based, add Redis if needed

2. **Audio Format for Voice**
   - What we know: Azure supports pcm16 and g711
   - What's unclear: Browser compatibility edge cases
   - Recommendation: Use pcm16 (most compatible), test Safari

3. **Tool Result Synchronization**
   - What we know: Voice + visualization should sync
   - What's unclear: Exact timing strategy for "speak while showing"
   - Recommendation: Send tool_result first, then audio; frontend coordinates

---
**Research date:** 2026-01-15
**Valid until:** 2026-02-15 (30 days - architecture patterns stable)
