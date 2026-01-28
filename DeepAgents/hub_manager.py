"""
Hub Manager Module (Restored Strict-Simple).
Restored to the logic that was proven to work in 'test_hub_lookup.py'.
"""

import logging
import os

from dotenv import load_dotenv
from langsmith import Client

# Load Env Forcefully (Override system env to ensure .env is Truth)
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"), override=True)

logger = logging.getLogger("HubManager")


def get_or_push_prompt(repo_name: str, default_content: str) -> str:
    """
    Retrieves a prompt from LangSmith Hub using the Simple Name strategy.

    CRITICAL: Requires LANGSMITH_WORKSPACE_ID to be set in .env for Organization Keys.
    """

    # 1. Environment Verification
    ws_id = os.getenv("LANGSMITH_WORKSPACE_ID")
    api_key = os.getenv("LANGCHAIN_API_KEY")

    # Debug Key State
    masked_key = (
        f"{api_key[:5]}...{api_key[-4:]}" if api_key and len(api_key) > 10 else "None"
    )
    logger.info(f"HubManager: [KEY] Active Key: {masked_key} | Workspace: {ws_id}")

    if not ws_id:
        logger.error(
            "[ERROR] LANGSMITH_WORKSPACE_ID is missing from environment variables."
        )
        logger.error(
            "   For Organization Keys, this ID is required to define the 'Owner' context."
        )
        raise ValueError(
            "LANGSMITH_WORKSPACE_ID not set. Cannot authenticate Hub requests."
        )

    # 2. Strategy: Use SIMPLE NAME. The SDK uses the Workspace ID to resolve the owner.
    target = repo_name

    # --- CACHE LOGIC: START ---
    cache_dir = os.path.join(os.path.dirname(__file__), ".cache", "prompts")
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, f"{repo_name}.txt")

    # ALWAYS pull from Hub to ensure cache is synchronized with Source of Truth.
    # The ~50s server startup time already dominates, so Hub latency is negligible.
    # Cache is only used as fallback if Hub is unreachable.
    logger.info(f"HubManager: [CONTEXT] Active (Workspace: {ws_id})")
    logger.info(f"HubManager: Attempting Strict Pull for '{target}'...")

    # Explicitly pass configuration to the Client to bypass environment variable caching/timing issues.
    # We verified via inspection that 'workspace_id' is a valid parameter in this SDK version.
    client_kwargs = {}
    if api_key:
        client_kwargs["api_key"] = api_key
    if ws_id:
        client_kwargs["workspace_id"] = ws_id

    client = Client(**client_kwargs)

    try:
        # Pull Attempt
        prompt_obj = client.pull_prompt(target)

        # Logic to extract string content
        content = None
        if hasattr(prompt_obj, "messages") and len(prompt_obj.messages) > 0:
            first_msg = prompt_obj.messages[0]
            if hasattr(first_msg, "prompt") and hasattr(first_msg.prompt, "template"):
                content = first_msg.prompt.template
            elif hasattr(first_msg, "content"):
                content = first_msg.content

        if not content and hasattr(prompt_obj, "template"):
            content = prompt_obj.template

        if not content:
            # Fallback string conversion
            content = str(prompt_obj)

        logger.info(f"HubManager: [SUCCESS] '{target}'. Saving to cache.")

        # Save to Cache
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as exc:
            logger.warning(f"HubManager: Failed to write cache: {exc}")

        return content

    except Exception as e:
        logger.error(f"HubManager: [FAILED] to pull '{target}': {e}")

        # Last Resort Fallback to Cache if available
        if os.path.exists(cache_file):
            logger.warning(f"HubManager: [FALLBACK] Using cache for '{target}'.")
            with open(cache_file, "r", encoding="utf-8") as f:
                return f.read()

        if default_content:
            logger.warning(
                f"HubManager: [FALLBACK] Returning local default for '{target}'."
            )
            return default_content

        raise e


def get_or_push_configuration(repo_name: str, default_json: str) -> str:
    """
    Retrieves a JSON Configuration string from LangSmith Hub.
    Treats the configuration as a System Message in a ChatPromptTemplate.
    """
    try:
        # Use existing logic to get content
        content = get_or_push_prompt(repo_name, default_json)
        return content
    except Exception as e:
        logger.error(f"HubManager: Config Pull Failed: {e}")
        # Fallback to default for config specifically to avoid app crash
        return default_json
