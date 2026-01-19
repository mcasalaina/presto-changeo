---
phase: 03-dashboard
plan: 02
subsystem: backend
tags: [azure-openai, function-calling, tools, websocket, streaming]

dependency-graph:
  requires: [02-01-chat-handler, 02-01-websocket-routing]
  provides: [tool-definitions, tool-execution, tool-result-messages]
  affects: [03-03-frontend-visualization]

tech-stack:
  added: []
  patterns: [function-calling, tool-streaming, incremental-accumulation]

key-files:
  created:
    - backend/tools.py
  modified:
    - backend/chat.py

decisions:
  - id: tool-passthrough
    decision: "Tools return arguments as-is for frontend rendering"
    rationale: "Backend doesn't need to process visualization data - frontend renders it"

  - id: streaming-tool-accumulation
    decision: "Accumulate tool call data incrementally from streaming chunks"
    rationale: "Azure OpenAI streams tool calls in fragments that must be assembled"

  - id: tool-result-protocol
    decision: "Send tool_result message type with tool name and result payload"
    rationale: "Consistent with existing message protocol, allows frontend to dispatch by tool"

metrics:
  duration: ~2 min
  completed: 2026-01-18
---

# Phase 03 Plan 02: LLM Tool Definitions Summary

**Azure OpenAI function calling with show_chart and show_metrics tools for dashboard visualizations via WebSocket tool_result messages.**

## What Was Built

### Task 1: Tool Definitions Module

Created `backend/tools.py` with:

- `TOOL_DEFINITIONS` list with 2 tools in Azure OpenAI function format:
  - `show_chart`: Display charts (line, bar, pie, area) with title and data array
  - `show_metrics`: Display KPI metrics with label, value, and unit
- `execute_tool(name, arguments)` function that returns tool arguments for frontend rendering

Tool schema example:
```python
{
    "type": "function",
    "function": {
        "name": "show_chart",
        "description": "Display a chart or visualization...",
        "parameters": {
            "type": "object",
            "properties": {
                "chart_type": {"type": "string", "enum": ["line", "bar", "pie", "area"]},
                "title": {"type": "string"},
                "data": {"type": "array", "items": {...}}
            },
            "required": ["chart_type", "title", "data"]
        }
    }
}
```

### Task 2: Chat Handler Tool Integration

Updated `backend/chat.py` with:

- Import `TOOL_DEFINITIONS` and `execute_tool` from tools module
- Pass `tools=TOOL_DEFINITIONS` to LLM streaming call
- Handle incremental tool call accumulation from streaming chunks:
  - Track tool calls by index in a dictionary
  - Accumulate id, name, and arguments as they stream
- Execute completed tools via `execute_tool()`
- Send `tool_result` messages to frontend via WebSocket

Updated system prompt to describe available visualization tools.

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Tools return arguments as-is | Frontend renders visualizations, backend just passes data through |
| Incremental tool accumulation | Azure streams tool calls in fragments that must be assembled |
| tool_result message type | Consistent with chat_chunk/chat_start/chat_error protocol |
| Updated system prompt | LLM needs to know what tools are available and when to use them |

## Commits

| Hash | Type | Description |
|------|------|-------------|
| 7b7c51f | feat | Create tool definitions module |
| c37b0e4 | feat | Integrate tools into chat handler |

## Verification Results

- [x] `python -c "from tools import TOOL_DEFINITIONS"` succeeds
- [x] `python -c "from chat import handle_chat_message"` succeeds
- [x] TOOL_DEFINITIONS contains show_chart and show_metrics
- [x] execute_tool function exists and returns result
- [x] chat.py imports and uses tools
- [x] No Python syntax errors

## Deviations from Plan

None - plan executed exactly as written.

## Next Phase Readiness

### Provides for Plan 03-03 (Frontend Visualization)

- Tool result messages sent via WebSocket
- Message protocol for visualizations defined

### Message Protocol Reference

**Tool result from backend:**
```json
{
    "type": "tool_result",
    "payload": {
        "tool": "show_chart",
        "result": {
            "chart_type": "bar",
            "title": "Monthly Sales",
            "data": [
                {"label": "Jan", "value": 100},
                {"label": "Feb", "value": 150}
            ]
        }
    }
}
```

**Metrics tool result:**
```json
{
    "type": "tool_result",
    "payload": {
        "tool": "show_metrics",
        "result": {
            "metrics": [
                {"label": "Total Users", "value": 1234, "unit": "users"},
                {"label": "Revenue", "value": 50000, "unit": "$"}
            ]
        }
    }
}
```

## Files

```
backend/
  tools.py  # NEW - Tool definitions and execute_tool function
  chat.py   # MODIFIED - Tool integration with streaming accumulation
```
