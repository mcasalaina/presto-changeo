"""
Azure Authentication Module
Provides authentication utilities for Azure AI services.
"""
import os
import logging
from typing import Optional

from azure.identity import AzureCliCredential, InteractiveBrowserCredential, ChainedTokenCredential
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import TokenCredential
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Cached credential instance (lazy initialization)
_credential: Optional[TokenCredential] = None


def get_azure_credential() -> TokenCredential:
    """
    Get Azure credential, trying CLI first then falling back to browser.

    Tries authentication methods in order:
    1. Azure CLI (az login) - uses cached tokens
    2. Interactive browser (fallback if CLI unavailable)

    Returns a cached credential instance on subsequent calls.

    Returns:
        TokenCredential instance
    """
    global _credential

    if _credential is None:
        logger.info("Initializing Azure credentials...")
        _credential = ChainedTokenCredential(
            AzureCliCredential(),
            InteractiveBrowserCredential(),
        )
        logger.info("Azure credential chain initialized (CLI -> Browser fallback)")

    return _credential


def get_token(credential: TokenCredential, scope: str) -> str:
    """
    Get an access token for the specified scope.

    Args:
        credential: Azure credential instance
        scope: The scope to request a token for (e.g., "https://cognitiveservices.azure.com/.default")

    Returns:
        Access token string

    Raises:
        azure.core.exceptions.ClientAuthenticationError: If authentication fails
    """
    logger.info(f"Requesting token for scope: {scope}")
    token = credential.get_token(scope)
    logger.info("Token acquired successfully")
    return token.token


def get_inference_client(credential: Optional[TokenCredential] = None) -> ChatCompletionsClient:
    """
    Get Azure AI Inference ChatCompletionsClient configured for the project.

    Args:
        credential: Optional credential to use. If None, uses get_azure_credential().

    Returns:
        ChatCompletionsClient configured for aipmaker-project

    Raises:
        ValueError: If AZURE_PROJECT_ENDPOINT is not configured
        azure.core.exceptions.ClientAuthenticationError: If authentication fails
    """
    endpoint = os.getenv("AZURE_PROJECT_ENDPOINT")
    if not endpoint:
        raise ValueError(
            "AZURE_PROJECT_ENDPOINT environment variable not set. "
            "Please configure it in your .env file."
        )

    if credential is None:
        credential = get_azure_credential()

    logger.info(f"Creating ChatCompletionsClient for endpoint: {endpoint}")
    client = ChatCompletionsClient(
        endpoint=endpoint,
        credential=credential,
        credential_scopes=["https://cognitiveservices.azure.com/.default"],
    )
    logger.info("ChatCompletionsClient created successfully")

    return client
