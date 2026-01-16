# Stack Research: Presto-Change-O

**Researched:** 2026-01-15
**Domain:** Azure Foundry + React Real-Time Voice Applications with Tool Calling
**Confidence:** HIGH (verified against official docs and current package versions)

## Summary

This stack enables building an AI-powered multi-industry simulation dashboard with real-time voice interaction, LLM-driven tool calling, and dynamic chart visualization. The architecture uses FastAPI as the backend orchestrator connecting to Azure AI Foundry services, with React handling the frontend dashboard and voice UI.

**Primary recommendation:** Use the official OpenAI Python SDK (v2.15+) with Azure endpoints for all LLM interactions including realtime voice. Use WebSockets for bidirectional voice streaming and SSE for text/tool streaming. Use Zustand for lightweight state management and Recharts for declarative charting.

---

## Core Stack

### Backend (Python)

| Library | Version | Purpose | Rationale | Confidence |
|---------|---------|---------|-----------|------------|
| `fastapi` | 0.115+ | Web framework | Async-native, WebSocket/SSE support, best Python REST framework | HIGH |
| `azure-ai-projects` | 1.0.0 | Azure Foundry SDK | Official SDK for Azure AI Foundry project access | HIGH |
| `azure-identity` | 1.25.1 | Azure authentication | InteractiveBrowserCredential, DefaultAzureCredential, managed identity | HIGH |
| `openai` | 2.15.0 | OpenAI/Azure OpenAI client | Official SDK with `[realtime]` extras for voice streaming | HIGH |
| `sse-starlette` | 3.1.2 | Server-Sent Events | Production-ready SSE for FastAPI streaming responses | HIGH |
| `uvicorn` | 0.34+ | ASGI server | Standard async server for FastAPI | HIGH |
| `websockets` | 14.0+ | WebSocket support | Required for realtime audio streaming | HIGH |

**Installation:**
```bash
pip install "fastapi[standard]" azure-ai-projects azure-identity "openai[realtime]" sse-starlette uvicorn websockets
```

### Frontend (React + Vite)

| Library | Version | Purpose | Rationale | Confidence |
|---------|---------|---------|-----------|------------|
| `react` | 19.2.3 | UI framework | Latest stable, required for modern hooks | HIGH |
| `react-dom` | 19.2.3 | DOM rendering | Paired with React | HIGH |
| `vite` | 7.3.1 | Build tool | Fast HMR, native ESM, decided by project | HIGH |
| `zustand` | 5.0.10 | State management | Tiny (3KB), no boilerplate, perfect for dashboard state | HIGH |
| `@tanstack/react-query` | 5.90.17 | Server state | Async state, caching, background refetch for API calls | HIGH |
| `recharts` | 3.6.0 | Charts | React-native D3 wrapper, declarative, good docs | HIGH |

**Installation:**
```bash
npm create vite@latest presto-changeo -- --template react-ts
cd presto-changeo
npm install zustand @tanstack/react-query recharts react-is
```

---

## Azure Foundry Integration

### Project Connection

The `azure-ai-projects` SDK (v1.0.0, stable as of July 2025) provides unified access to Azure AI Foundry projects.

**Endpoint format:** `https://{ai-services-account-name}.services.ai.azure.com/api/projects/{project-name}`

```python
from azure.ai.projects import AIProjectClient
from azure.identity import InteractiveBrowserCredential, DefaultAzureCredential

# For local development (interactive browser login)
credential = InteractiveBrowserCredential()

# For production (managed identity)
# credential = DefaultAzureCredential()

project_client = AIProjectClient(
    endpoint="https://aipmaker-project.services.ai.azure.com/api/projects/aipmaker-project",
    credential=credential
)
```

**Confidence:** HIGH - Verified against [Microsoft Learn documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/quickstarts/get-started-code) and [PyPI package page](https://pypi.org/project/azure-ai-projects/).

### Model Access via OpenAI SDK

Azure AI Foundry uses the standard OpenAI SDK with Azure-specific configuration.

```python
from openai import OpenAI, AsyncOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

credential = DefaultAzureCredential()
token_provider = get_bearer_token_provider(
    credential,
    "https://cognitiveservices.azure.com/.default"
)

# Synchronous client
client = OpenAI(
    base_url="https://aipmaker-project.openai.azure.com/openai/v1/",
    api_key=token_provider()  # Or use API key directly
)

# Async client (recommended for FastAPI)
async_client = AsyncOpenAI(
    base_url="https://aipmaker-project.openai.azure.com/openai/v1/",
    api_key=token_provider()
)
```

---

## Real-Time Voice (gpt-realtime)

### SDK Setup

The OpenAI Python SDK v2.x includes realtime support via `pip install openai[realtime]`.

**Supported models:** `gpt-4o-realtime-preview`, `gpt-realtime`, `gpt-realtime-mini`
**API version:** `2025-04-01-preview` or later (recommend `2025-08-28`)

### WebSocket Connection Pattern

```python
import asyncio
import base64
from openai import AsyncOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

async def realtime_voice_session():
    credential = DefaultAzureCredential()
    token_provider = get_bearer_token_provider(
        credential,
        "https://cognitiveservices.azure.com/.default"
    )

    endpoint = "https://aipmaker-project.openai.azure.com"
    deployment = "gpt-realtime"  # Your deployment name

    # Convert HTTPS to WSS for WebSocket
    base_url = endpoint.replace("https://", "wss://").rstrip("/") + "/openai/v1"

    client = AsyncOpenAI(
        websocket_base_url=base_url,
        api_key=token_provider()
    )

    async with client.realtime.connect(model=deployment) as connection:
        # Configure session
        await connection.session.update(session={
            "instructions": "You are a helpful assistant for industry simulations.",
            "output_modalities": ["audio", "text"],
            "audio": {
                "input": {
                    "format": {"type": "audio/pcm", "rate": 24000},
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.5,
                        "silence_duration_ms": 200,
                        "create_response": True
                    }
                },
                "output": {
                    "voice": "alloy",
                    "format": {"type": "audio/pcm", "rate": 24000}
                }
            }
        })

        # Process events
        async for event in connection:
            if event.type == "response.output_audio.delta":
                audio_bytes = base64.b64decode(event.delta)
                yield audio_bytes  # Stream to client
            elif event.type == "response.output_text.delta":
                yield event.delta
```

**Audio specifications:**
- Format: PCM (Pulse Code Modulation)
- Sample rate: 24,000 Hz
- Encoding: Base64 in transit
- Available voices: alloy, echo, fable, onyx, nova, shimmer

**Confidence:** HIGH - Verified against [Azure OpenAI Realtime Quickstart](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/realtime-audio-quickstart).

---

## Tool Calling (Function Calling)

### Standard Pattern

Tool calling uses the `tools` parameter (not deprecated `functions`).

```python
from openai import AsyncOpenAI
import json

tools = [
    {
        "type": "function",
        "function": {
            "name": "update_chart",
            "description": "Update a dashboard chart with new data",
            "parameters": {
                "type": "object",
                "properties": {
                    "chart_id": {
                        "type": "string",
                        "description": "The ID of the chart to update"
                    },
                    "data": {
                        "type": "array",
                        "items": {"type": "object"},
                        "description": "New data points for the chart"
                    },
                    "chart_type": {
                        "type": "string",
                        "enum": ["line", "bar", "area", "pie"],
                        "description": "Type of chart visualization"
                    }
                },
                "required": ["chart_id", "data"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_industry_scenario",
            "description": "Generate a new industry simulation scenario",
            "parameters": {
                "type": "object",
                "properties": {
                    "industry": {
                        "type": "string",
                        "enum": ["healthcare", "finance", "retail", "manufacturing"]
                    },
                    "complexity": {
                        "type": "string",
                        "enum": ["simple", "moderate", "complex"]
                    }
                },
                "required": ["industry"]
            }
        }
    }
]

async def chat_with_tools(client: AsyncOpenAI, messages: list):
    response = await client.chat.completions.create(
        model="model-router",  # Your deployment
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )

    message = response.choices[0].message

    if message.tool_calls:
        for tool_call in message.tool_calls:
            func_name = tool_call.function.name
            func_args = json.loads(tool_call.function.arguments)

            # Execute function and get result
            result = await execute_tool(func_name, func_args)

            # Add tool response to messages
            messages.append(message)
            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": func_name,
                "content": json.dumps(result)
            })

        # Get final response with tool results
        final = await client.chat.completions.create(
            model="model-router",
            messages=messages
        )
        return final.choices[0].message.content

    return message.content
```

**Key parameters:**
- `tool_choice="auto"` - Model decides when to call functions (default)
- `tool_choice="none"` - Never call functions
- `tool_choice={"type": "function", "function": {"name": "..."}}` - Force specific function
- `parallel_tool_calls=False` - Ensure at most one tool call per turn

**Limitation:** Function descriptions limited to 1,024 characters.

**Confidence:** HIGH - Verified against [Azure OpenAI Function Calling docs](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/function-calling).

---

## Image Generation (gpt-image-1-mini)

### API Usage

```python
from openai import AsyncOpenAI

async def generate_chart_image(client: AsyncOpenAI, prompt: str):
    response = await client.images.generate(
        model="gpt-image-1-mini",  # Your deployment name
        prompt=prompt,
        size="1024x1024",  # Or 1024x1536, 1536x1024
        quality="medium",  # low, medium, high
        n=1,
        output_format="png"  # or "jpeg"
    )

    return response.data[0].url  # or .b64_json if requested
```

**Notes:**
- Available sizes: 1024x1024 (fastest), 1024x1536, 1536x1024
- Quality levels: low (fastest), medium, high (default)
- gpt-image-1 series requires limited access application
- Square images generate faster

**Recommendation:** For dashboard charts, prefer Recharts over generated images. Use gpt-image-1-mini for creative visualizations, industry-specific imagery, or when users request custom graphics.

**Confidence:** MEDIUM - API verified against [Azure OpenAI Image Generation docs](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/dall-e-quickstart), but gpt-image-1-mini specifics may vary by deployment.

---

## Streaming Architecture

### Backend: FastAPI WebSocket + SSE

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import asyncio
import json

app = FastAPI()

# WebSocket for bidirectional voice
@app.websocket("/ws/voice")
async def voice_websocket(websocket: WebSocket):
    await websocket.accept()

    # Initialize realtime session
    async with realtime_client.connect(model="gpt-realtime") as connection:
        # Forward audio from client to Azure
        async def receive_audio():
            while True:
                audio_data = await websocket.receive_bytes()
                await connection.input_audio_buffer.append(audio=audio_data)

        # Forward responses from Azure to client
        async def send_responses():
            async for event in connection:
                if event.type == "response.output_audio.delta":
                    await websocket.send_bytes(base64.b64decode(event.delta))
                elif event.type == "response.function_call_arguments.done":
                    await websocket.send_json({
                        "type": "tool_call",
                        "name": event.name,
                        "arguments": event.arguments
                    })

        await asyncio.gather(receive_audio(), send_responses())

# SSE for text streaming (non-voice interactions)
@app.get("/api/chat/stream")
async def chat_stream(prompt: str):
    async def generate():
        response = await client.chat.completions.create(
            model="model-router",
            messages=[{"role": "user", "content": prompt}],
            stream=True
        )
        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield {
                    "event": "message",
                    "data": json.dumps({"content": chunk.choices[0].delta.content})
                }

    return EventSourceResponse(generate())
```

### Frontend: React WebSocket + SSE Consumption

```typescript
// Voice WebSocket hook
function useVoiceConnection() {
  const wsRef = useRef<WebSocket | null>(null);
  const { addToolCall, setTranscript } = useDashboardStore();

  const connect = useCallback(() => {
    wsRef.current = new WebSocket('ws://localhost:8000/ws/voice');

    wsRef.current.onmessage = (event) => {
      if (event.data instanceof Blob) {
        // Audio data - play it
        playAudio(event.data);
      } else {
        const data = JSON.parse(event.data);
        if (data.type === 'tool_call') {
          addToolCall(data);
        } else if (data.type === 'transcript') {
          setTranscript(data.text);
        }
      }
    };
  }, []);

  const sendAudio = useCallback((audioData: ArrayBuffer) => {
    wsRef.current?.send(audioData);
  }, []);

  return { connect, sendAudio };
}

// SSE for text streaming
async function* streamChat(prompt: string) {
  const response = await fetch(`/api/chat/stream?prompt=${encodeURIComponent(prompt)}`);
  const reader = response.body?.getReader();
  const decoder = new TextDecoder();

  while (reader) {
    const { done, value } = await reader.read();
    if (done) break;

    const text = decoder.decode(value);
    const lines = text.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        yield data.content;
      }
    }
  }
}
```

**Confidence:** HIGH - Patterns verified against [FastAPI WebSocket docs](https://fastapi.tiangolo.com/advanced/websockets/) and [sse-starlette](https://pypi.org/project/sse-starlette/).

---

## State Management

### Zustand Store for Dashboard

```typescript
import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';

interface ChartData {
  id: string;
  type: 'line' | 'bar' | 'area' | 'pie';
  data: any[];
  title: string;
}

interface DashboardState {
  charts: Record<string, ChartData>;
  activeMode: string | null;
  isVoiceActive: boolean;
  transcript: string;
  toolCallHistory: any[];

  // Actions
  updateChart: (id: string, data: any[]) => void;
  setMode: (mode: string) => void;
  toggleVoice: () => void;
  addToolCall: (call: any) => void;
  setTranscript: (text: string) => void;
}

export const useDashboardStore = create<DashboardState>()(
  immer((set) => ({
    charts: {},
    activeMode: null,
    isVoiceActive: false,
    transcript: '',
    toolCallHistory: [],

    updateChart: (id, data) => set((state) => {
      if (state.charts[id]) {
        state.charts[id].data = data;
      }
    }),

    setMode: (mode) => set((state) => {
      state.activeMode = mode;
    }),

    toggleVoice: () => set((state) => {
      state.isVoiceActive = !state.isVoiceActive;
    }),

    addToolCall: (call) => set((state) => {
      state.toolCallHistory.push(call);
    }),

    setTranscript: (text) => set((state) => {
      state.transcript = text;
    }),
  }))
);
```

**Rationale for Zustand over alternatives:**
- Redux: Overkill for this use case, too much boilerplate
- Jotai: Better for deeply atomic state, but dashboard has interconnected state
- Context: Re-renders entire tree on updates, poor for real-time data

**Confidence:** HIGH - Zustand recommended for dashboards per [2025 state management guides](https://dev.to/hijazi313/state-management-in-2025-when-to-use-context-redux-zustand-or-jotai-2d2k).

### TanStack Query for Server State

Use TanStack Query for REST API calls (fetching saved modes, persisted sessions).

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// Fetch saved industry modes
export function useSavedModes() {
  return useQuery({
    queryKey: ['modes'],
    queryFn: () => fetch('/api/modes').then(r => r.json()),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// Save current mode
export function useSaveMode() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (mode: any) =>
      fetch('/api/modes', {
        method: 'POST',
        body: JSON.stringify(mode),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['modes'] });
    },
  });
}
```

---

## Charts with Recharts

### Responsive Dashboard Charts

```tsx
import {
  LineChart, Line, BarChart, Bar, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer
} from 'recharts';

interface DashboardChartProps {
  data: any[];
  type: 'line' | 'bar' | 'area';
  dataKey: string;
  title: string;
}

export function DashboardChart({ data, type, dataKey, title }: DashboardChartProps) {
  const ChartComponent = {
    line: LineChart,
    bar: BarChart,
    area: AreaChart,
  }[type];

  const DataComponent = {
    line: Line,
    bar: Bar,
    area: Area,
  }[type];

  return (
    <div className="chart-container">
      <h3>{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <ChartComponent data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Legend />
          <DataComponent
            type="monotone"
            dataKey={dataKey}
            stroke="#8884d8"
            fill="#8884d8"
          />
        </ChartComponent>
      </ResponsiveContainer>
    </div>
  );
}
```

**Why Recharts over alternatives:**
- **vs Visx:** Recharts is batteries-included, Visx requires building everything from primitives
- **vs ECharts:** Recharts is more React-native, ECharts better for massive datasets (10K+ points)
- **vs Chart.js:** Recharts has better React integration and TypeScript support

**Confidence:** HIGH - Recharts confirmed as top choice for React dashboards per [LogRocket 2025 analysis](https://blog.logrocket.com/best-react-chart-libraries-2025/).

---

## What NOT to Use

| Avoid | Reason | Use Instead |
|-------|--------|-------------|
| `functions` parameter | Deprecated since 2023-12-01-preview | `tools` parameter |
| `function_call` parameter | Deprecated | `tool_choice` parameter |
| Redux for dashboard state | Excessive boilerplate for this scale | Zustand |
| Chart.js (react-chartjs-2) | Less React-native, worse TS support | Recharts |
| Socket.io | Adds abstraction layer over WebSocket | Native WebSocket |
| Polling for real-time | Inefficient, high latency | SSE or WebSocket |
| `azure-ai-projects` hub-based endpoints | Deprecated, new SDK uses Foundry endpoints | Project endpoints |
| Python < 3.9 | Not supported by azure-ai-projects 1.0 | Python 3.9+ |
| API key in code | Security risk | Environment variables or Key Vault |

---

## Environment Variables

### Backend (.env)

```bash
# Azure AI Foundry
AZURE_OPENAI_ENDPOINT=https://aipmaker-project.openai.azure.com
AZURE_PROJECT_ENDPOINT=https://aipmaker-project.services.ai.azure.com/api/projects/aipmaker-project

# Model deployments
AZURE_OPENAI_DEPLOYMENT_CHAT=model-router
AZURE_OPENAI_DEPLOYMENT_REALTIME=gpt-realtime
AZURE_OPENAI_DEPLOYMENT_IMAGE=gpt-image-1-mini

# Optional: API key (prefer managed identity in production)
# AZURE_OPENAI_API_KEY=your-key-here
```

### Frontend (.env)

```bash
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

---

## Complete Installation Commands

### Backend Setup

```bash
# Create project
mkdir presto-changeo-backend && cd presto-changeo-backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install "fastapi[standard]" \
    azure-ai-projects==1.0.0 \
    azure-identity==1.25.1 \
    "openai[realtime]>=2.15.0" \
    sse-starlette==3.1.2 \
    uvicorn[standard] \
    websockets \
    python-dotenv

# Azure CLI login (for Entra ID auth)
az login
```

### Frontend Setup

```bash
# Create Vite React project
npm create vite@latest presto-changeo-frontend -- --template react-ts
cd presto-changeo-frontend

# Install dependencies
npm install \
    zustand@^5.0.10 \
    @tanstack/react-query@^5.90.0 \
    recharts@^3.6.0 \
    react-is

# Dev dependencies
npm install -D @types/node
```

---

## Sources

### Primary (HIGH confidence)
- [Azure AI Projects PyPI](https://pypi.org/project/azure-ai-projects/) - v1.0.0 stable
- [Azure OpenAI Realtime Quickstart](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/realtime-audio-quickstart) - Python examples
- [Azure OpenAI Function Calling](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/function-calling) - Tools parameter
- [OpenAI Python SDK Releases](https://github.com/openai/openai-python/releases) - v2.15.0
- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/) - WebSocket patterns
- [sse-starlette PyPI](https://pypi.org/project/sse-starlette/) - v3.1.2
- [Zustand npm](https://www.npmjs.com/package/zustand) - v5.0.10
- [Recharts npm](https://www.npmjs.com/package/recharts) - v3.6.0
- [TanStack Query npm](https://www.npmjs.com/package/@tanstack/react-query) - v5.90.17

### Secondary (MEDIUM confidence)
- [LogRocket React Chart Libraries 2025](https://blog.logrocket.com/best-react-chart-libraries-2025/) - Recharts recommendation
- [State Management 2025](https://dev.to/hijazi313/state-management-in-2025-when-to-use-context-redux-zustand-or-jotai-2d2k) - Zustand for dashboards

---

## Metadata

**Confidence breakdown:**
- Azure Foundry SDK: HIGH - Official docs and stable PyPI release
- Realtime Voice: HIGH - Verified with official quickstart code
- Tool Calling: HIGH - Official Microsoft documentation
- Frontend Stack: HIGH - npm package versions verified
- Architecture Patterns: HIGH - Standard documented patterns

**Research date:** 2026-01-15
**Valid until:** 2026-02-15 (30 days - stable ecosystem)
