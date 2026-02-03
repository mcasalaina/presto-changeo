# Phase 7: Dynamic Generation - Research

**Researched:** 2026-02-02
**Domain:** LLM-driven dynamic UI generation, structured output, image generation, color theory
**Confidence:** HIGH

## Summary

Dynamic mode generation requires orchestrating multiple AI capabilities to transform arbitrary industry requests into complete, coherent dashboard configurations. The core challenge is achieving perceived instant response while generating structured data (theme, tabs, metrics, persona) that is mathematically consistent and industry-appropriate.

The established approach combines: (1) Pydantic-defined schemas with Azure OpenAI Structured Outputs for reliable JSON generation, (2) parallel async API calls for latency optimization, (3) color theory algorithms rather than LLM-generated colors for speed, and (4) optional deferred image generation with caching for icons/logos.

**Primary recommendation:** Use Azure OpenAI Structured Outputs with Pydantic models to generate Mode configurations, parallelize independent API calls with asyncio, derive theme colors algorithmically from a single LLM-suggested primary color, and defer image generation to background tasks with aggressive caching.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Azure OpenAI SDK | 1.42.0+ | Structured output generation | Native Pydantic support, 100% schema adherence |
| Pydantic | 2.8.2+ | Schema definition | Auto JSON schema generation, validation |
| asyncio | stdlib | Parallel API orchestration | Best for I/O bound LLM calls |
| Faker | 25.0+ | Seeded persona data | Already in use, deterministic generation |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| color-mix() CSS | Native | Theme color derivation | Generate tints/shades from primary |
| gpt-image-1-mini | Azure | Icon/logo generation | Background task, cached results |
| Redis/in-memory | - | Response caching | Cache generated modes by industry |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Structured Outputs | Function Calling | Function calling is for tools; response_format is for direct structured responses |
| asyncio.gather() | asyncio.TaskGroup | TaskGroup is Python 3.11+, gather() more portable |
| Algorithmic colors | LLM color generation | LLM colors add 1-2s latency, often poor harmony |
| gpt-image-1 | gpt-image-1-mini | Mini is faster (critical for perceived speed), lower quality acceptable for icons |

**Installation:**
```bash
pip install openai>=1.42.0 pydantic>=2.8.2 faker>=25.0.0
```

## Architecture Patterns

### Recommended Project Structure
```
backend/
  mode_generator.py     # Dynamic mode generation logic
  generation_schemas.py # Pydantic models for LLM output
  color_utils.py        # Algorithmic color palette generation
  modes.py              # Extended with generated mode storage
```

### Pattern 1: Structured Output with Pydantic
**What:** Define exact output schema as Pydantic model, Azure OpenAI guarantees schema adherence
**When to use:** Any LLM call that needs reliable JSON structure
**Example:**
```python
from pydantic import BaseModel
from openai import AzureOpenAI

class GeneratedModeConfig(BaseModel):
    """Schema for LLM-generated mode configuration."""
    industry_name: str
    primary_color: str  # Hex color, e.g. "#1E88E5"
    personality_traits: list[str]
    tab_definitions: list[TabDefinition]
    sample_metrics: list[MetricDefinition]
    system_prompt_fragment: str

# Use with Azure OpenAI
client = AzureOpenAI(...)
completion = client.beta.chat.completions.parse(
    model="gpt-5-mini",  # or model-router
    messages=[
        {"role": "system", "content": GENERATION_SYSTEM_PROMPT},
        {"role": "user", "content": f"Generate dashboard config for: {industry}"}
    ],
    response_format=GeneratedModeConfig,
)
config = completion.choices[0].message.parsed  # Validated Pydantic object
```

### Pattern 2: Parallel Async Generation
**What:** Fire independent LLM calls simultaneously, await all results
**When to use:** Multiple generation tasks with no dependencies
**Example:**
```python
import asyncio
from openai import AsyncAzureOpenAI

async def generate_mode_complete(industry: str) -> Mode:
    async_client = AsyncAzureOpenAI(...)

    # Fire all independent calls in parallel
    config_task = generate_config(async_client, industry)
    persona_task = generate_persona_template(async_client, industry)

    config, persona_template = await asyncio.gather(
        config_task,
        persona_task
    )

    # Derive theme colors algorithmically (instant, no API call)
    theme = derive_theme_palette(config.primary_color)

    return assemble_mode(config, theme, persona_template)
```

### Pattern 3: Algorithmic Color Palette from Primary
**What:** Given one primary color, derive full palette mathematically
**When to use:** Always for theme generation (faster than LLM)
**Example:**
```python
def derive_theme_palette(primary_hex: str) -> ModeTheme:
    """Generate complete theme from single primary color."""
    # CSS color-mix() will handle this on frontend
    # Backend just stores primary, frontend derives:
    # --theme-primary: {primary}
    # --theme-primary-dark: color-mix(in oklch, var(--theme-primary) 70%, black)
    # --theme-primary-light: color-mix(in oklch, var(--theme-primary) 30%, white)

    # For backend consistency, compute:
    from colorsys import rgb_to_hls, hls_to_rgb

    r, g, b = hex_to_rgb(primary_hex)
    h, l, s = rgb_to_hls(r/255, g/255, b/255)

    return ModeTheme(
        primary=primary_hex,
        secondary=rgb_to_hex(*hls_to_rgb((h + 0.5) % 1.0, l, s * 0.8)),  # Complementary
        background="#f8fafc" if l > 0.5 else "#1e293b",  # Light/dark based on primary
        surface="#ffffff" if l > 0.5 else "#334155",
        text="#0f172a" if l > 0.5 else "#f8fafc",
        text_muted="#64748b"
    )
```

### Pattern 4: Mathematical Data Consistency
**What:** Generate base values, derive dependent values mathematically
**When to use:** Any generated data where totals must match sums
**Example:**
```python
def generate_consistent_metrics(industry: str, seed: int) -> list[ModeMetric]:
    """Generate metrics where numbers are internally consistent."""
    fake = Faker()
    fake.seed_instance(seed)

    # For a retail store example:
    # Generate individual line items first
    category_sales = [
        fake.pyfloat(min_value=1000, max_value=10000)
        for _ in range(4)
    ]

    # Derive total FROM the parts (not generated separately)
    total_sales = sum(category_sales)

    return [
        ModeMetric(label="Electronics", value=f"${category_sales[0]:,.2f}"),
        ModeMetric(label="Clothing", value=f"${category_sales[1]:,.2f}"),
        ModeMetric(label="Groceries", value=f"${category_sales[2]:,.2f}"),
        ModeMetric(label="Other", value=f"${category_sales[3]:,.2f}"),
        ModeMetric(label="Total Sales", value=f"${total_sales:,.2f}"),  # Sum, not generated
    ]
```

### Anti-Patterns to Avoid
- **LLM for color generation:** Adds 1-2 seconds latency, often produces clashing colors. Use algorithmic derivation from single primary.
- **Sequential API calls:** Each LLM call adds 1-3 seconds. Parallelize with asyncio.gather().
- **Generating totals independently:** LLMs struggle with math. Always compute totals from parts.
- **Synchronous image generation:** DALL-E/gpt-image calls take 3-10+ seconds. Defer to background.
- **No caching:** Same industry request generates identical results. Cache aggressively.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON schema validation | Manual parsing/validation | Pydantic + Structured Outputs | 100% schema adherence guaranteed |
| Color palette harmony | HSL/RGB math from scratch | color-mix() in OKLCH space | Perceptually uniform, browser-native |
| Parallel API calls | Threading/multiprocessing | asyncio with AsyncAzureOpenAI | I/O bound, no GIL issues |
| Consistent fake data | Random generation | Faker with seed_instance() | Deterministic, already in use |
| LLM response caching | File-based cache | Redis SemanticCache or in-memory dict | Semantic similarity matching |

**Key insight:** The temptation is to have the LLM generate everything (colors, data, totals). This is slow and error-prone. Use LLM for creative decisions (industry personality, tab names, metric ideas), use algorithms for derivation (colors from primary, totals from parts).

## Common Pitfalls

### Pitfall 1: LLM Math Errors
**What goes wrong:** LLM generates metrics where totals don't match sums
**Why it happens:** LLMs don't perform arithmetic, they predict tokens
**How to avoid:** Generate parts first, compute totals programmatically
**Warning signs:** "Total claims: $15,000" but individual claims sum to $12,350

### Pitfall 2: Slow Perceived Response
**What goes wrong:** User says "Presto-Change-O, you're a pet store" and waits 5+ seconds
**Why it happens:** Sequential LLM calls, synchronous image generation
**How to avoid:** Parallelize calls, defer images, stream text response immediately
**Warning signs:** TTFT > 500ms, total generation > 3 seconds

### Pitfall 3: Color Palette Clashes
**What goes wrong:** LLM-generated colors don't work together visually
**Why it happens:** LLMs don't understand color theory or accessibility
**How to avoid:** LLM suggests primary only, derive palette algorithmically
**Warning signs:** Low contrast text, garish color combinations

### Pitfall 4: Schema Validation Failures
**What goes wrong:** Generated JSON missing required fields or wrong types
**Why it happens:** Using JSON mode instead of Structured Outputs
**How to avoid:** Always use `response_format` with Pydantic model
**Warning signs:** KeyError on accessing generated data, type mismatches

### Pitfall 5: Non-Deterministic Persona Data
**What goes wrong:** Same session shows different customer data on refresh
**Why it happens:** Unseeded random generation
**How to avoid:** Use Faker.seed_instance() with session-derived seed
**Warning signs:** Customer name changes, balances fluctuate randomly

### Pitfall 6: Image Generation Blocking UI
**What goes wrong:** Dashboard frozen while generating industry icon
**Why it happens:** Waiting for gpt-image-1 response in main flow
**How to avoid:** Use placeholder, generate in background, update when ready
**Warning signs:** 3-10 second delays after mode switch

## Code Examples

Verified patterns from official sources:

### Azure OpenAI Structured Outputs (from Microsoft Learn)
```python
# Source: https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/structured-outputs
from pydantic import BaseModel
from openai import AzureOpenAI
import os

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-08-01-preview"
)

class ModeConfig(BaseModel):
    industry_name: str
    primary_color: str
    tabs: list[str]
    personality: str

completion = client.beta.chat.completions.parse(
    model="gpt-5-mini",
    messages=[
        {"role": "system", "content": "Generate dashboard configuration."},
        {"role": "user", "content": "Create config for a pet store dashboard"}
    ],
    response_format=ModeConfig,
)

config = completion.choices[0].message.parsed
print(config.industry_name)  # "Pet Store"
print(config.primary_color)  # "#4CAF50"
```

### Async Parallel API Calls
```python
# Source: OpenAI community best practices
import asyncio
from openai import AsyncAzureOpenAI

async def generate_mode_async(industry: str):
    client = AsyncAzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2024-08-01-preview"
    )

    # Fire both calls simultaneously
    async def get_config():
        return await client.beta.chat.completions.parse(
            model="gpt-5-mini",
            messages=[{"role": "user", "content": f"Config for {industry}"}],
            response_format=ModeConfig
        )

    async def get_metrics():
        return await client.beta.chat.completions.parse(
            model="gpt-5-mini",
            messages=[{"role": "user", "content": f"KPIs for {industry}"}],
            response_format=MetricsList
        )

    config, metrics = await asyncio.gather(get_config(), get_metrics())
    return config.choices[0].message.parsed, metrics.choices[0].message.parsed
```

### CSS color-mix() Palette Derivation
```css
/* Source: MDN Web Docs - color-mix() */
:root {
  --theme-primary: #1E88E5;

  /* Derived colors using color-mix in OKLCH for perceptual uniformity */
  --theme-primary-dark: color-mix(in oklch, var(--theme-primary) 70%, black);
  --theme-primary-light: color-mix(in oklch, var(--theme-primary) 30%, white);
  --theme-primary-10: color-mix(in oklch, var(--theme-primary) 10%, white);

  /* Complementary (rotate hue 180 degrees in oklch) */
  --theme-secondary: oklch(from var(--theme-primary) l c calc(h + 180));
}
```

### Streaming Response for Perceived Speed
```python
# Enable streaming for immediate user feedback
response = client.chat.completions.create(
    model="gpt-5-mini",
    messages=messages,
    stream=True  # Start showing response immediately
)

# Send first chunk to user as fast as possible
for chunk in response:
    if chunk.choices[0].delta.content:
        await websocket.send_text(json.dumps({
            "type": "chat_chunk",
            "payload": {"text": chunk.choices[0].delta.content, "done": False}
        }))
```

## State of the Art (2026)

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| JSON mode | Structured Outputs | 2024-08 | 100% schema compliance vs ~60% |
| DALL-E 3 | gpt-image-1-mini | 2025-04 | Faster, cheaper for bulk |
| Sequential calls | Parallel async | Standard | 2-3x latency reduction |
| RGB color math | OKLCH color space | CSS4 | Perceptually uniform palettes |
| Manual JSON parsing | Pydantic parse() | OpenAI SDK 1.0 | Type-safe, validated |

**New tools/patterns to consider:**
- **gpt-image-1.5**: Higher quality than gpt-image-1 with better speed/cost
- **Generative UI frameworks**: Thesys C1, CopilotKit for full UI generation (overkill for this use case)
- **Semantic caching**: Redis LangCache for similar-prompt deduplication

**Deprecated/outdated:**
- **DALL-E 3**: Scheduled for deprecation May 2026, migrate to gpt-image-1 series
- **JSON mode without schema**: Use Structured Outputs instead
- **response_format key**: Deprecated in Responses API, use text.format

## Open Questions

Things that couldn't be fully resolved:

1. **Optimal image generation timing**
   - What we know: gpt-image-1-mini is fastest (1-3s), can stream partial images
   - What's unclear: Best UX - placeholder then update, or delay switch until ready?
   - Recommendation: Start with placeholder, background generate, user likely won't notice

2. **Cache invalidation strategy**
   - What we know: Same industry should return cached mode config
   - What's unclear: When to regenerate? Time-based? User-triggered?
   - Recommendation: Start with simple dict cache, add Redis if needed later

3. **Industry color associations**
   - What we know: Blue=finance, Green=health/eco, Purple=luxury are common
   - What's unclear: Should LLM override these conventions or follow them?
   - Recommendation: Let LLM suggest, but include industry color hints in prompt

## Sources

### Primary (HIGH confidence)
- [Azure OpenAI Structured Outputs](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/structured-outputs) - Schema definition, Python SDK, limitations
- [Azure OpenAI Image Generation](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/dall-e) - gpt-image-1 series, streaming, quality settings
- [OpenAI Structured Outputs Guide](https://platform.openai.com/docs/guides/structured-outputs) - Schema adherence, Pydantic integration
- [MDN color-mix()](https://developer.mozilla.org/en-US/blog/color-palettes-css-color-mix/) - OKLCH palette generation

### Secondary (MEDIUM confidence)
- [OpenAI Latency Optimization](https://platform.openai.com/docs/guides/latency-optimization) - Streaming, token optimization (403 on fetch)
- [Parallel OpenAI Calls](https://meyerperin.org/posts/2024-02-01-openai-concurrency.html) - asyncio patterns verified against SDK docs
- [TTFT User Experience](https://medium.com/data-science-collective/what-makes-ai-feel-fast-b72a5422a959) - Target <500ms for perceived responsiveness
- [LLM Structured Data Research](https://www.preprints.org/manuscript/202506.1937) - Claude best for accuracy, GPT-4o for efficiency

### Tertiary (LOW confidence)
- [Color Psychology](https://www.ignytebrands.com/the-psychology-of-color-in-branding/) - Industry color associations (general marketing)
- [Generative UI Guide](https://dev.to/copilotkit/the-developers-guide-to-generative-ui-in-2026-1bh3) - Full UI generation patterns (beyond scope)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Azure OpenAI docs are authoritative, Pydantic integration verified
- Architecture patterns: HIGH - Patterns derived from official SDK examples
- Pitfalls: MEDIUM - Based on research and community reports, not all personally verified
- Color theory: HIGH - CSS standards and MDN documentation
- Image generation latency: MEDIUM - Based on documentation, actual latency varies

**Research date:** 2026-02-02
**Valid until:** 2026-03-15 (Azure OpenAI features evolving rapidly)
