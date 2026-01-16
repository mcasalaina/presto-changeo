# Features Research: Presto-Change-O

**Researched:** 2026-01-15
**Domain:** AI Demo Dashboard / Multi-Modal Chat Interface
**Confidence:** MEDIUM (WebSearch-based, verified against multiple sources)

## Executive Summary

AI demo dashboards and multi-modal chat interfaces in 2025-2026 have converged on a set of expected features users take for granted, plus emerging differentiators that set products apart. The key insight: **users now expect AI interfaces to "just work" across modalities** (voice, text, visual) with sub-second latency and contextual awareness.

For Presto-Change-O specifically, the dynamic industry transformation concept is a **strong differentiator** not commonly found in existing products. Most demo dashboards are static industry-specific templates; real-time transformation via natural language command is novel.

---

## Table Stakes (Must Have or Users Leave)

Features users expect by default in 2025-2026. Missing these signals "not production ready."

| Feature | Description | Complexity | Rationale |
|---------|-------------|------------|-----------|
| **Conversation History** | Persistent left-panel chat showing full conversation with scroll | LOW | Every major AI chat (ChatGPT, Claude, Gemini) has this. Users expect to review past exchanges. |
| **Real-Time Response Streaming** | Text appears progressively, not after full generation | LOW | Sub-500ms time-to-first-token expected. Waiting 3+ seconds for full response feels broken. |
| **Visual Feedback During Processing** | Loading indicators, typing animations, state indicators | LOW | Users need confirmation system is working. Dead silence = broken. |
| **Text Input with Send Button** | Standard chat input field with keyboard shortcuts (Enter to send) | LOW | Universal UX pattern since 2010. |
| **Mobile-Responsive Layout** | Interface works on tablet/desktop (phone out of scope per PROJECT.md) | MEDIUM | Users expect dashboard to work on iPad-sized screens at minimum. |
| **Error Recovery** | Graceful handling of API failures, network issues | MEDIUM | "Something went wrong, try again" with retry option. No cryptic errors. |
| **Basic Voice Input** | Microphone button to speak instead of type | MEDIUM | Expected since Siri (2011). Push-to-talk is acceptable minimum. |
| **Dashboard Visualization Panel** | Central area showing charts, metrics, KPIs | MEDIUM | Core to "dashboard" expectation. Without it, it's just a chatbot. |
| **Navigation/Tab Structure** | Clear way to switch between views/sections | LOW | Standard dashboard pattern. Bottom tabs or sidebar navigation. |

### Table Stakes Dependencies

```
Conversation History
    requires: Backend message storage (in-memory acceptable for demo)

Real-Time Streaming
    requires: Server-Sent Events or WebSocket connection

Visual Feedback
    requires: State management for loading/processing/error states

Voice Input
    requires: Browser Web Speech API or Azure speech services
```

---

## Differentiators (Competitive Advantage)

Features that make Presto-Change-O stand out from generic AI demos.

| Feature | Description | Complexity | Competitive Value |
|---------|-------------|------------|-------------------|
| **Natural Language Mode Switching** | "Presto-Change-O, you're a bank" transforms entire interface | HIGH | **UNIQUE** - No major competitor does real-time industry transformation via NL command. |
| **Dynamic Industry Generation** | Arbitrary industry creation on-the-fly ("you're a veterinary clinic") | HIGH | **RARE** - Most demos have fixed templates. Dynamic generation is novel. |
| **Voice-Visual Synchronization** | Voice speaks answer while corresponding chart animates in | HIGH | **EMERGING** - ElevenLabs multimodal, but rare in dashboards. The "wow factor." |
| **LLM-Driven Tool Calls to UI** | AI decides which visualization to show, triggers animation | HIGH | **ADVANCED** - Most demos are deterministic. LLM-driven UI manipulation is cutting-edge. |
| **Industry-Appropriate Theming** | Colors, icons, metrics change per industry context | MEDIUM | **EXPECTED for premium** - But automatic switching is differentiating. |
| **Seeded Persona Consistency** | Same "user" data throughout session (account balance, claims, etc.) | MEDIUM | **CLEVER** - Creates illusion of real data without real data. Competitors often have random/inconsistent demo data. |
| **Toggle-Mode Voice** | User enables voice, speaks freely, AI responds naturally | MEDIUM | **BETTER THAN PTT** - Push-to-talk is dated. Always-listening is resource-heavy. Toggle is balanced. |
| **Pre-Built Industry Templates** | Banking, Insurance, Healthcare ready out-of-box | MEDIUM | **EXPECTED for v1** - But ensures demo works instantly without generation wait. |

### Differentiator Dependencies

```
Natural Language Mode Switching
    requires:
        - Intent recognition for "Presto-Change-O" trigger phrase
        - Industry extraction from command
        - Mode configuration schema
        - Theme switching infrastructure
        - Dashboard component swapping

Dynamic Industry Generation
    requires:
        - Natural Language Mode Switching (base infrastructure)
        - LLM prompt for industry template generation
        - Validation/sanitization of generated config
        - Server-side persistence of generated modes

Voice-Visual Synchronization
    requires:
        - Real-time voice (Azure gpt-realtime)
        - Dashboard animation system
        - Event coordination between voice and visual
        - Timing/sequencing logic

LLM-Driven Tool Calls to UI
    requires:
        - Tool/function definition schema
        - LLM with function calling capability (model-router)
        - UI action handlers for each tool
        - Animation triggers

Industry-Appropriate Theming
    requires:
        - CSS variable system or theme provider
        - Theme configuration per industry
        - Smooth transition animations

Seeded Persona Consistency
    requires:
        - Persona generation on mode entry
        - Session storage for persona data
        - Consistent persona injection into LLM context
```

### Critical Path for Differentiators

**Phase 1 (Foundation):**
1. Dashboard component architecture
2. Theme switching infrastructure
3. Chat interface with LLM connection

**Phase 2 (Core Differentiators):**
4. Natural Language Mode Switching
5. Pre-Built Industry Templates
6. Industry-Appropriate Theming
7. Seeded Persona Consistency

**Phase 3 (Wow Factor):**
8. Toggle-Mode Voice
9. LLM-Driven Tool Calls to UI
10. Voice-Visual Synchronization
11. Dynamic Industry Generation

---

## Anti-Features (Deliberately NOT Building)

Features that seem valuable but conflict with project goals or add complexity without ROI.

| Anti-Feature | Why It Seems Good | Why We're NOT Building | Alternative |
|--------------|-------------------|------------------------|-------------|
| **User Accounts/Auth** | Personalization, saved sessions | Demo product, adds complexity, security burden | Session-based persistence, browser storage |
| **Real Financial Data** | More realistic demo | Legal/compliance nightmare, out of scope | Seeded persona with realistic-looking fake data |
| **Exact Brand Copying** | Recognizable, familiar | Trademark issues, legal risk | "Inspired by" color themes |
| **Always-Listening Voice** | More natural interaction | Battery drain, privacy concerns, complexity | Toggle-mode with clear on/off state |
| **Multi-Language Support** | Broader audience | Complexity for demo, translation costs | English-only v1 |
| **Offline Mode** | Works without internet | LLM requires API, core value proposition is cloud AI | Fast recovery from network hiccups |
| **Chart Library Visualizations** | Precise data rendering | PROJECT.md specifies gpt-image-1-mini for generation | AI-generated chart images |
| **Real-Time External Data** | Live market prices, etc. | API costs, complexity, not core value | Simulated "live" data that updates visually |
| **Mobile Native Apps** | iOS/Android presence | Out of scope per PROJECT.md | Responsive web that works on tablets |
| **Multi-User Collaboration** | Team features | Demo complexity, not core value | Single-user session focus |
| **Custom Branding Upload** | User uploads their brand | Feature creep, storage complexity | Pre-built industry themes |
| **Export/Download Data** | PDF reports, data export | Not core demo value | Focus on interactive experience |

---

## Feature Complexity Matrix

| Feature | Frontend | Backend | LLM | Voice | Total |
|---------|----------|---------|-----|-------|-------|
| Conversation History | LOW | LOW | - | - | LOW |
| Real-Time Streaming | MEDIUM | MEDIUM | - | - | MEDIUM |
| Visual Feedback | LOW | - | - | - | LOW |
| Dashboard Viz Panel | MEDIUM | LOW | - | - | MEDIUM |
| Navigation Tabs | LOW | - | - | - | LOW |
| Voice Input | MEDIUM | LOW | - | MEDIUM | MEDIUM |
| NL Mode Switching | HIGH | HIGH | HIGH | - | HIGH |
| Dynamic Industry Gen | MEDIUM | HIGH | HIGH | - | HIGH |
| Voice-Visual Sync | HIGH | MEDIUM | MEDIUM | HIGH | HIGH |
| LLM Tool Calls to UI | HIGH | HIGH | HIGH | - | HIGH |
| Industry Theming | MEDIUM | LOW | LOW | - | MEDIUM |
| Seeded Persona | LOW | MEDIUM | HIGH | - | MEDIUM |
| Toggle Voice Mode | MEDIUM | MEDIUM | - | HIGH | HIGH |
| Pre-Built Templates | MEDIUM | MEDIUM | LOW | - | MEDIUM |

---

## MVP vs Post-MVP Classification

### MVP (v1.0 - Ship to Validate)

**Must ship to prove concept:**

1. **Chat Interface** - Left panel with conversation history, input
2. **Dashboard Panel** - Central area with visualization capability
3. **Real-Time Streaming** - Progressive response display
4. **Visual Feedback** - Loading states, processing indicators
5. **Natural Language Mode Switching** - Core differentiator, must be in v1
6. **Pre-Built Templates (3)** - Banking, Insurance, Healthcare
7. **Industry Theming** - Visual transformation on mode switch
8. **Seeded Persona** - Consistent fake data per session
9. **Basic Voice Input** - Microphone button, push-to-talk acceptable for v1

**Rationale:** These features demonstrate the core value proposition: "transform interface via natural language command with AI-driven responses."

### Post-MVP (v1.1+)

**Enhance after validating core concept:**

1. **Toggle-Mode Voice** - Upgrade from PTT to toggle
2. **Voice-Visual Synchronization** - Voice speaks while chart appears
3. **LLM Tool Calls to UI** - AI-triggered visualizations
4. **Dynamic Industry Generation** - Arbitrary industry on-demand
5. **Server-Side Mode Persistence** - Share generated modes
6. **Bottom Navigation Tabs** - Industry-specific navigation

**Rationale:** These features add polish and "wow factor" but aren't required to validate the core concept. Ship MVP first, then layer these.

---

## Industry-Specific Feature Notes

Based on research, each pre-built industry should include:

### Banking
- **Metrics:** Account balances, transaction history, spending categories
- **Visualizations:** Spending pie chart, balance over time, savings goals
- **Persona Data:** Checking balance, savings balance, recent transactions, credit score
- **Color Theme:** Blue tones (trust, security - Chase, Bank of America inspired)
- **Tab Structure:** Overview, Checking, Savings, Mortgage, Investments

### Insurance
- **Metrics:** Policy status, coverage amounts, claims, premiums
- **Visualizations:** Coverage breakdown, claims timeline, premium comparison
- **Persona Data:** Active policies, coverage limits, claims history, premium amounts
- **Color Theme:** Green/teal tones (growth, protection - Geico, Progressive inspired)
- **Tab Structure:** Overview, Life, Auto, Home, Claims

### Healthcare
- **Metrics:** Coverage status, deductible progress, claims, provider network
- **Visualizations:** Deductible gauge, claims over time, coverage breakdown
- **Persona Data:** Plan details, deductible amount/remaining, recent claims, copay info
- **Color Theme:** Blue/white tones (clean, medical - UnitedHealth, Aetna inspired)
- **Tab Structure:** Overview, Coverage, Usage, Claims, Providers

---

## Gaps and Open Questions

1. **Voice Latency Requirements:** What's acceptable? Research shows 200ms conversational turn pause. Azure gpt-realtime claims sub-250ms STT. Need to validate in practice.

2. **Chart Generation Quality:** Using gpt-image-1-mini for charts is unusual. Most dashboards use D3/Chart.js. Need to validate image generation meets quality bar.

3. **Mode Switch Animation Timing:** How long should transformation take? Research suggests quick transitions with spinner, but no specific benchmarks found.

4. **Seeded Persona Generation:** How much persona data is needed? What fields? Need to define schema during implementation.

5. **Tool Call Latency:** LLM function calling adds round-trip time. Need to measure impact on perceived responsiveness.

---

## Sources

### Primary (HIGH Confidence)
- [PatternFly Chatbot Conversation History](https://www.patternfly.org/patternfly-ai/chatbot/chatbot-conversation-history/) - UI patterns
- [ElevenLabs Multimodal Conversational AI](https://elevenlabs.io/blog/introducing-multimodal-conversational-ai/) - Voice+text integration

### Secondary (MEDIUM Confidence)
- [AI Dashboard Design Guide - Eleken](https://www.eleken.co/blog-posts/ai-dashboard-design) - Dashboard best practices
- [Business Intelligence Dashboard Best Practices - Julius AI](https://julius.ai/articles/business-intelligence-dashboard-design-best-practices) - BI dashboard patterns
- [Voice AI Engineering 2026 - Kardome](https://www.kardome.com/resources/blog/voice-ai-engineering-the-interface-of-2026/) - Voice interface trends
- [Chat UI Design Patterns 2025 - BricxLabs](https://bricxlabs.com/blogs/message-screen-ui-deisgn) - Chat UI patterns
- [Chatbot Persona Guide - Zendesk](https://www.zendesk.com/blog/chatbot-persona/) - Persona customization
- [Healthcare Dashboard Examples - Bold BI](https://www.boldbi.com/dashboard-examples/healthcare/) - Industry dashboard templates
- [Insurance Analytics Dashboards - Bold BI](https://www.boldbi.com/dashboard-examples/insurance/) - Industry dashboard templates
- [Multi-Modal AI Evolution - Medium](https://medium.com/@hansraj136/the-evolution-of-voice-agents-building-multi-modal-ai-interfaces-in-2025-54ffb60501f4) - Multi-modal trends
- [Function Calling with LLMs - Prompt Engineering Guide](https://www.promptingguide.ai/applications/function_calling) - Tool calling patterns

### Tertiary (LOW Confidence - Needs Validation)
- [Dashboard Trends 2026 - Medium](https://medium.com/@mokkup/dashboard-trends-practical-ways-bi-teams-are-using-ai-in-2026-e405476ad750) - Forward-looking trends
- [Voice Agents Developer Trends - ElevenLabs](https://elevenlabs.io/blog/voice-agents-and-conversational-ai-new-developer-trends-2025) - Voice development patterns

---

## Metadata

**Confidence Breakdown:**
- Table stakes features: HIGH - Well-documented patterns across multiple sources
- Differentiators: MEDIUM - Novel combinations, less direct precedent
- Anti-features: HIGH - Clear project constraints from PROJECT.md
- Complexity estimates: MEDIUM - Based on general patterns, needs validation during implementation

**Research Date:** 2026-01-15
**Valid Until:** 2026-02-15 (30 days - fast-moving AI space)
