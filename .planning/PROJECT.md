# Presto-Change-O

## What This Is

A demo website that simulates fully interactive AI-driven interfaces across industries. Users speak a command like "Presto-Change-O, you're a bank" and the entire interface transforms — colors, charts, data, and behavior — to simulate that industry. Chat and voice interact with the central dashboard through LLM-driven tool calls, with charts animating in response to questions.

## Core Value

**Dynamic industry simulation that feels real.** The interface must convincingly transform into any industry on command, with the AI providing contextually appropriate responses and visualizations.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Left-panel chat interface with conversation history and input field
- [ ] Toggle-mode voicebot (user enables voice, speaks freely, voice responds with short answers)
- [ ] Central interactive dashboard with metrics, status indicators, and visualizations
- [ ] Bottom navigation tabs that adapt per industry mode
- [ ] Mode switching via natural language command ("Presto-Change-O, you're a [industry]")
- [ ] Pre-built modes: Banking (checking, savings, mortgage), Insurance (life, auto, home), Healthcare (coverage, usage, claims)
- [ ] Dynamic mode generation for any arbitrary industry on-demand
- [ ] Industry-appropriate color theming (inspired by major players, not exact copies)
- [ ] LLM-driven tool calls that animate charts into the central area
- [ ] Voice + visual sync: voicebot speaks short answer while chart appears
- [ ] Seeded persona: consistent simulated user data within a mode session
- [ ] Quick transition with loading spinner when switching/generating modes
- [ ] Server-side persistence of generated modes for reuse
- [ ] Caching of generated styles and images

### Out of Scope

- Real financial/healthcare data integration — simulation only
- Multi-user accounts or authentication beyond Azure credential flow
- Mobile-native apps — web-only for this demo
- Exact brand copying — inspired by, not replicating, real company themes

## Context

**Layout Reference:** `./layout_prototype.png` shows the target design:
- Left: Chat panel with conversation history, input at bottom
- Center/Right: Interactive dashboard with mode selectors, metrics/gauges, central visualization
- Bottom: Navigation tabs (adapt per industry)

**Azure Foundry Resources:**
- Project: `aipmaker-project` at `https://aipmaker-project-resource.services.ai.azure.com/api/projects/aipmaker-project`
- Models:
  - `model-router` — Core LLM for conversation and tool orchestration
  - `gpt-image-1-mini` — Generate charts/graphs as images
  - `gpt-realtime` — Voice interaction
- Foundry Agents with Bing grounding for web search (style research, etc.)

**Tech Stack:**
- Frontend: React + Vite
- Backend: Python (FastAPI) serving API
- Voice: Azure gpt-realtime with toggle mode
- Auth: Managed identity + InteractiveBrowserCredential

## Constraints

- **Azure Foundry**: Must use the specified project and model deployments
- **Auth**: InteractiveBrowserCredential for user login, managed identity where applicable
- **Environment**: .env file for configuration (never committed), venv for Python dependencies
- **Caching**: Generated styles and images must be cached for reuse
- **LLM-Driven**: All interactions driven by LLM, not heuristics or deterministic rules

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| React + Vite frontend | Modern, fast, good for interactive dashboards | — Pending |
| FastAPI backend | Python ecosystem for Azure SDK, async support | — Pending |
| Toggle-mode voice | Balance between always-listening complexity and push-to-talk friction | — Pending |
| Seeded persona data | Consistent user experience within session without pre-built data files | — Pending |
| Server-side mode persistence | Share generated modes across sessions/users | — Pending |
| gpt-image-1-mini for charts | Generate visualizations dynamically rather than charting libraries | — Pending |

---
*Last updated: 2026-01-15 after initialization*
