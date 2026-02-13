"""
Image Generator using Azure AI FLUX-1.1-pro
Generates background and hero images for dynamically created modes.
"""

import asyncio
import base64
import logging
import os
from pathlib import Path

import httpx

from auth import get_azure_credential

logger = logging.getLogger(__name__)

# Directory for generated images
IMAGES_DIR = Path(__file__).parent / "generated_images"

# Azure configuration
IMAGE_DEPLOYMENT = os.getenv("AZURE_IMAGE_DEPLOYMENT", "FLUX-1.1-pro")

# Cognitive Services scope for bearer token
_TOKEN_SCOPE = "https://cognitiveservices.azure.com/.default"


def _get_image_url() -> str:
    """
    Build the Azure OpenAI images/generations URL for the FLUX deployment.

    Format: https://<resource>/openai/deployments/<deployment>/images/generations?api-version=2024-06-01
    """
    endpoint = os.getenv("AZURE_PROJECT_ENDPOINT", "")
    base = endpoint.rstrip("/").removesuffix("/models")
    deployment = os.getenv("AZURE_IMAGE_DEPLOYMENT", IMAGE_DEPLOYMENT)
    return f"{base}/openai/deployments/{deployment}/images/generations?api-version=2024-06-01"


async def _get_bearer_token() -> str:
    """Get a bearer token for Azure AI services."""
    credential = get_azure_credential()
    token = await asyncio.to_thread(credential.get_token, _TOKEN_SCOPE)
    return token.token


async def _generate_image(
    client: httpx.AsyncClient,
    token: str,
    prompt: str,
    size: str,
) -> bytes | None:
    """
    Call Azure AI images/generations endpoint and return PNG bytes.

    Returns None on failure.
    """
    url = _get_image_url()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "prompt": prompt,
        "size": size,
        "n": 1,
    }

    try:
        response = await client.post(
            url,
            json=payload,
            headers=headers,
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()

        # Handle response: could have base64 data or a URL
        image_data = data.get("data", [])
        if not image_data:
            logger.error("Image generation returned no data")
            return None

        item = image_data[0]

        # Try base64 first
        b64 = item.get("b64_json")
        if b64:
            return base64.b64decode(b64)

        # Try URL
        image_url = item.get("url")
        if image_url:
            img_response = await client.get(image_url, timeout=30.0)
            img_response.raise_for_status()
            return img_response.content

        logger.error("Image response has neither b64_json nor url")
        return None

    except httpx.HTTPStatusError as e:
        logger.error(f"Image generation HTTP error: {e.response.status_code} - {e.response.text[:500]}")
        return None
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        return None


async def generate_mode_images(
    mode_id: str,
    industry_name: str,
    company_name: str,
    primary_color: str,
) -> dict[str, str | None]:
    """
    Generate background, hero, and chat images for a dynamically created mode.

    Generates three images in parallel:
    - Background (1024x768): subtle abstract texture for dashboard panel
    - Hero (768x768): professional industry illustration for visualization area
    - Chat (768x1024): dark, muted texture for chat sidebar

    Saves PNGs to backend/generated_images/ and returns URL paths.
    Returns None values on failure (non-fatal).

    Args:
        mode_id: Unique mode identifier for file naming
        industry_name: Industry display name (e.g., "Florist")
        company_name: Company display name
        primary_color: Hex color for the theme

    Returns:
        {"background_image": "/images/...", "hero_image": "/images/...", "chat_image": "/images/..."}
        Values are None if generation failed.
    """
    result: dict[str, str | None] = {
        "background_image": None,
        "hero_image": None,
        "chat_image": None,
    }

    try:
        # Ensure output directory exists
        IMAGES_DIR.mkdir(parents=True, exist_ok=True)

        token = await _get_bearer_token()

        bg_prompt = (
            f"Abstract subtle background texture for a {industry_name.lower()} business dashboard. "
            f"Soft, muted tones inspired by {primary_color}. "
            f"Minimal, low-contrast, professional. No text, no logos, no people. "
            f"Suitable as a background behind overlaid text and UI elements."
        )

        hero_prompt = (
            f"Professional, modern illustration representing the {industry_name.lower()} industry. "
            f"Clean design with colors inspired by {primary_color}. "
            f"No text, no logos. Suitable as a hero image for a {company_name} business dashboard."
        )

        chat_prompt = (
            f"Dark abstract watercolor texture with rich {industry_name.lower()} themed elements. "
            f"Deep jewel tones with accents of {primary_color}. "
            f"Moody but colorful, like a dark wallpaper. No text, no logos, no people. "
            f"Painterly, artistic, atmospheric."
        )

        logger.info(f"Generating images for mode '{mode_id}' ({industry_name})...")

        async with httpx.AsyncClient() as client:
            bg_task = _generate_image(client, token, bg_prompt, "1024x768")
            hero_task = _generate_image(client, token, hero_prompt, "768x768")
            chat_task = _generate_image(client, token, chat_prompt, "768x1024")

            bg_bytes, hero_bytes, chat_bytes = await asyncio.gather(
                bg_task, hero_task, chat_task
            )

        # Save background image
        if bg_bytes:
            bg_path = IMAGES_DIR / f"{mode_id}_background.png"
            bg_path.write_bytes(bg_bytes)
            result["background_image"] = f"/images/{mode_id}_background.png"
            logger.info(f"Saved background image: {bg_path}")
        else:
            logger.warning(f"Background image generation failed for mode '{mode_id}'")

        # Save hero image
        if hero_bytes:
            hero_path = IMAGES_DIR / f"{mode_id}_hero.png"
            hero_path.write_bytes(hero_bytes)
            result["hero_image"] = f"/images/{mode_id}_hero.png"
            logger.info(f"Saved hero image: {hero_path}")
        else:
            logger.warning(f"Hero image generation failed for mode '{mode_id}'")

        # Save chat image
        if chat_bytes:
            chat_path = IMAGES_DIR / f"{mode_id}_chat.png"
            chat_path.write_bytes(chat_bytes)
            result["chat_image"] = f"/images/{mode_id}_chat.png"
            logger.info(f"Saved chat image: {chat_path}")
        else:
            logger.warning(f"Chat image generation failed for mode '{mode_id}'")

    except Exception as e:
        logger.error(f"Image generation failed for mode '{mode_id}': {e}")

    return result
