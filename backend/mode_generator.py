"""
Mode Generator using Azure AI Inference
Generates complete Mode configurations for arbitrary industries using LLM for creative
decisions and algorithms for color derivation.
"""

import asyncio
import json
import os
import logging
from typing import Optional

from azure.ai.inference.models import SystemMessage, UserMessage

from auth import get_inference_client
from color_utils import derive_theme_palette
from modes import Mode, ModeTheme, ModeTab, ModeMetric

# Model deployment - use same as chat
MODEL_DEPLOYMENT = os.getenv("AZURE_MODEL_DEPLOYMENT", "gpt-5-mini")

logger = logging.getLogger(__name__)

# System prompt for mode generation - requests JSON output
GENERATION_SYSTEM_PROMPT = """You are a mode configuration generator for a multi-industry dashboard app.
Generate a complete configuration for the requested industry.

You MUST respond with valid JSON only. No other text. Use this exact structure:
{
  "industry_name": "Display Name",
  "industry_id": "snake_case_id",
  "company_name": "Company Name",
  "tagline": "Company tagline/slogan",
  "primary_color": "#HexColor",
  "personality_traits": ["trait1", "trait2", "trait3"],
  "tabs": [
    {"id": "dashboard", "label": "Dashboard", "icon": "📊"},
    {"id": "tab2", "label": "Tab 2", "icon": "📋"},
    {"id": "settings", "label": "Settings", "icon": "⚙️"}
  ],
  "default_metrics": [
    {"label": "Metric 1", "value": "$1,234", "unit": null},
    {"label": "Metric 2", "value": "567", "unit": "/day"}
  ],
  "welcome_message": "Welcome message here",
  "system_prompt_fragment": "AI context for this industry"
}

Guidelines:
- company_name: IMPORTANT - If the user specifies a company name (like "H-E-B", "Walmart", "Joe's Tacos"), use EXACTLY that name. Only make up a fictional name if no company name was provided.
- primary_color: Choose a color that represents this industry (hex format, e.g., "#4CAF50"). If it's a real company, try to use their brand color.
- tabs: Include 4-5 relevant tabs. Always include "dashboard" as the first tab and "settings" as the last tab.
- default_metrics: Include exactly 4 key metrics/KPIs relevant to this industry with realistic pre-formatted values.
- personality_traits: 3-5 traits that define how the AI assistant should behave for this industry.
- system_prompt_fragment: Additional context for the AI including industry jargon, common questions, and domain knowledge. 2-3 sentences.
- welcome_message: Friendly greeting when entering this mode. Should feel warm and industry-appropriate.

Be creative but realistic. The dashboard should feel purpose-built for this industry.
Choose colors that have industry associations (e.g., green for eco/health, blue for finance/trust, purple for luxury)."""

# Standard visualization tools context added to all generated system prompts
TOOLS_CONTEXT = """
You have access to visualization tools to display data in the dashboard:
- show_chart: Display charts (line, bar, pie, area) with data points
- show_metrics: Display key metrics/KPIs in the metrics panel

IMPORTANT: When you use a visualization tool, you MUST ALWAYS also provide a brief text response describing what you're showing.

For historical data (trends over time, usage patterns, etc.), generate plausible data going back 12 months with monthly data points, showing realistic patterns. This is a demo app - create compelling visualizations!

CHART PREFERENCE: For time-series data (anything "over time"), always use LINE charts with 12 monthly data points. Use BAR charts only for comparing discrete categories. Use PIE charts for showing composition/breakdown."""


def _build_full_system_prompt(config: dict) -> str:
    """
    Build the complete system prompt for the AI assistant in this mode.

    Combines the LLM-generated fragment with personality traits and standard tools context.
    """
    traits_text = ", ".join(config.get("personality_traits", []))
    industry_name = config.get("industry_name", "general")

    return f"""You are a helpful assistant for a {industry_name.lower()} dashboard. {config.get("system_prompt_fragment", "")}

Your personality: {traits_text}

Keep responses clear, professional, and concise. Speak naturally like a friendly {industry_name.lower()} expert.
{TOOLS_CONTEXT}"""


async def generate_mode(industry: str, full_request: str = "") -> Optional[Mode]:
    """
    Generate a complete Mode configuration for an arbitrary industry.

    Uses Azure AI Inference to generate JSON configuration, then parses it.
    Colors are derived algorithmically from the LLM-suggested primary color
    for speed and better color harmony.

    Args:
        industry: The industry to generate a mode for, e.g., "pet store", "law firm"
        full_request: The full user request, which may contain a specific company name

    Returns:
        Mode object ready to be used by the application, or None if generation fails.

    Raises:
        No exceptions - errors are logged and None is returned for graceful fallback.
    """
    try:
        logger.info(f"Generating mode for industry: {industry}")

        # Get the inference client (same as chat.py uses)
        client = get_inference_client()

        # Call Azure AI Inference (run in thread since client is sync)
        logger.info("Calling Azure AI Inference for mode generation...")

        # Use full request if available, otherwise just the industry
        user_prompt = full_request if full_request else f"Generate a dashboard configuration for: {industry}"

        def _call_llm():
            return client.complete(
                model=MODEL_DEPLOYMENT,
                messages=[
                    SystemMessage(content=GENERATION_SYSTEM_PROMPT),
                    UserMessage(content=user_prompt)
                ],
            )

        response = await asyncio.to_thread(_call_llm)

        # Extract the response content
        content = response.choices[0].message.content
        if not content:
            logger.error("Azure AI Inference returned empty response")
            return None

        logger.info(f"Received response ({len(content)} chars), parsing JSON...")

        # Parse JSON from response (strip any markdown code blocks if present)
        json_str = content.strip()
        if json_str.startswith("```"):
            # Remove markdown code block markers
            lines = json_str.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            json_str = "\n".join(lines)

        config = json.loads(json_str)

        logger.info(f"Generated config for: {config.get('industry_name', 'unknown')}")

        # Derive full theme palette algorithmically from primary color
        primary_color = config.get("primary_color", "#4CAF50")
        theme_palette = derive_theme_palette(primary_color)

        # Build the Mode object
        tabs = config.get("tabs", [])
        metrics = config.get("default_metrics", [])

        mode = Mode(
            id=config.get("industry_id", industry.lower().replace(" ", "_")),
            name=config.get("industry_name", industry.title()),
            company_name=config.get("company_name", f"{industry.title()} Co."),
            tagline=config.get("tagline", f"Your trusted {industry} partner"),
            theme=ModeTheme(**theme_palette),
            tabs=[ModeTab(id=t.get("id"), label=t.get("label"), icon=t.get("icon", "📋")) for t in tabs],
            system_prompt=_build_full_system_prompt(config),
            default_metrics=[
                ModeMetric(label=m.get("label"), value=m.get("value"), unit=m.get("unit"))
                for m in metrics
            ],
        )

        logger.info(f"Mode generation complete: {mode.name} (id={mode.id})")
        return mode

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response for '{industry}': {e}")
        logger.error(f"Response content: {content[:500] if content else 'None'}...")
        return None
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
