"""
Mode Generator using Azure OpenAI Structured Outputs
Generates complete Mode configurations for arbitrary industries using LLM for creative
decisions and algorithms for color derivation.
"""

import os
import logging
from typing import Optional

from openai import AsyncAzureOpenAI
from azure.identity import AzureCliCredential, InteractiveBrowserCredential, ChainedTokenCredential

from generation_schemas import GeneratedModeConfig
from color_utils import derive_theme_palette
from modes import Mode, ModeTheme, ModeTab, ModeMetric

logger = logging.getLogger(__name__)

# System prompt for mode generation
GENERATION_SYSTEM_PROMPT = """You are a mode configuration generator for a multi-industry dashboard app.
Generate a complete configuration for the requested industry.

Guidelines:
- primary_color: Choose a color that represents this industry (hex format, e.g., "#4CAF50")
- tabs: Include 4-5 relevant tabs. Always include "dashboard" as the first tab and "settings" as the last tab.
- default_metrics: Include exactly 4 key metrics/KPIs relevant to this industry with realistic pre-formatted values.
- personality_traits: 3-5 traits that define how the AI assistant should behave for this industry.
- system_prompt_fragment: Additional context for the AI including industry jargon, common questions, and domain knowledge. 2-3 sentences.
- welcome_message: Friendly greeting when entering this mode. Should feel warm and industry-appropriate.

Be creative but realistic. The dashboard should feel purpose-built for this industry.
Choose colors that have industry associations (e.g., green for eco/health, blue for finance/trust, purple for luxury).
"""

# Standard visualization tools context added to all generated system prompts
TOOLS_CONTEXT = """
You have access to visualization tools to display data in the dashboard:
- show_chart: Display charts (line, bar, pie, area) with data points
- show_metrics: Display key metrics/KPIs in the metrics panel

IMPORTANT: When you use a visualization tool, you MUST ALWAYS also provide a brief text response describing what you're showing.

For historical data (trends over time, usage patterns, etc.), generate plausible data going back 12 months with monthly data points, showing realistic patterns. This is a demo app - create compelling visualizations!

CHART PREFERENCE: For time-series data (anything "over time"), always use LINE charts with 12 monthly data points. Use BAR charts only for comparing discrete categories. Use PIE charts for showing composition/breakdown."""


def _build_full_system_prompt(config: GeneratedModeConfig) -> str:
    """
    Build the complete system prompt for the AI assistant in this mode.

    Combines the LLM-generated fragment with personality traits and standard tools context.
    """
    traits_text = ", ".join(config.personality_traits)

    return f"""You are a helpful assistant for a {config.industry_name.lower()} dashboard. {config.system_prompt_fragment}

Your personality: {traits_text}

Keep responses clear, professional, and concise. Speak naturally like a friendly {config.industry_name.lower()} expert.
{TOOLS_CONTEXT}"""


async def generate_mode(industry: str) -> Optional[Mode]:
    """
    Generate a complete Mode configuration for an arbitrary industry.

    Uses Azure OpenAI Structured Outputs with the GeneratedModeConfig schema to guarantee
    100% schema adherence. Colors are derived algorithmically from the LLM-suggested
    primary color for speed and better color harmony.

    Args:
        industry: The industry to generate a mode for, e.g., "pet store", "law firm"

    Returns:
        Mode object ready to be used by the application, or None if generation fails.

    Raises:
        No exceptions - errors are logged and None is returned for graceful fallback.
    """
    try:
        logger.info(f"Generating mode for industry: {industry}")

        # Get Azure credential using chained approach (CLI first, then browser fallback)
        credential = ChainedTokenCredential(
            AzureCliCredential(),
            InteractiveBrowserCredential(),
        )

        # Get the Azure OpenAI endpoint from environment
        endpoint = os.getenv("AZURE_PROJECT_ENDPOINT")
        if not endpoint:
            logger.error("AZURE_PROJECT_ENDPOINT environment variable not set")
            return None

        # Create async Azure OpenAI client
        # Using get_bearer_token_provider for Azure AD auth
        from azure.identity import get_bearer_token_provider
        token_provider = get_bearer_token_provider(
            credential,
            "https://cognitiveservices.azure.com/.default"
        )

        client = AsyncAzureOpenAI(
            azure_endpoint=endpoint,
            azure_ad_token_provider=token_provider,
            api_version="2024-08-01-preview",
        )

        # Call Azure OpenAI with structured outputs
        logger.info("Calling Azure OpenAI with Structured Outputs...")
        completion = await client.beta.chat.completions.parse(
            model="model-router",
            messages=[
                {"role": "system", "content": GENERATION_SYSTEM_PROMPT},
                {"role": "user", "content": f"Generate a dashboard configuration for: {industry}"}
            ],
            response_format=GeneratedModeConfig,
        )

        # Extract the parsed config (guaranteed to match schema)
        config = completion.choices[0].message.parsed
        if config is None:
            logger.error("Azure OpenAI returned None for parsed response")
            return None

        logger.info(f"Generated config for: {config.industry_name}")

        # Derive full theme palette algorithmically from primary color
        theme_palette = derive_theme_palette(config.primary_color)

        # Build the Mode object
        mode = Mode(
            id=config.industry_id,
            name=config.industry_name,
            theme=ModeTheme(**theme_palette),
            tabs=[ModeTab(id=t.id, label=t.label, icon=t.icon) for t in config.tabs],
            system_prompt=_build_full_system_prompt(config),
            default_metrics=[
                ModeMetric(label=m.label, value=m.value, unit=m.unit)
                for m in config.default_metrics
            ],
        )

        logger.info(f"Mode generation complete: {mode.name} (id={mode.id})")
        return mode

    except Exception as e:
        logger.error(f"Mode generation failed for '{industry}': {e}")
        return None


if __name__ == "__main__":
    import asyncio

    async def test_generation():
        print("Testing mode generation for 'pet store'...")
        mode = await generate_mode("pet store")
        if mode:
            print(f"Generated mode: {mode.name}")
            print(f"Theme primary: {mode.theme.primary}")
            print(f"Tabs: {[t.label for t in mode.tabs]}")
            print(f"Metrics: {[m.label for m in mode.default_metrics]}")
        else:
            print("Generation failed")

    asyncio.run(test_generation())
