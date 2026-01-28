"""
Push corrected system config to LangSmith Hub.
Fixes the video model ID from 'replicate/zeroscope-v2-xl' to 'replicate/anotherjesse/zeroscope-v2-xl'.
"""

import json
import os

from dotenv import load_dotenv

# Load environment
load_dotenv(os.path.join(os.path.dirname(__file__), "DeepAgents/.env"), override=True)

from langchain_core.prompts import ChatPromptTemplate
from langsmith import Client

# Get the correct config from system_config.py
from DeepAgents.system_config import DEFAULT_SYSTEM_CONFIG


def push_config():
    """Push the corrected config to Hub."""
    ws_id = os.getenv("LANGSMITH_WORKSPACE_ID")
    api_key = os.getenv("LANGCHAIN_API_KEY")

    if not ws_id or not api_key:
        raise ValueError("Missing LANGSMITH_WORKSPACE_ID or LANGCHAIN_API_KEY")

    client = Client(api_key=api_key, workspace_id=ws_id)

    # Convert config to JSON string
    config_json = json.dumps(DEFAULT_SYSTEM_CONFIG, indent=2)

    # Create a ChatPromptTemplate with the config as content
    prompt = ChatPromptTemplate.from_messages([("system", config_json)])

    # Push to Hub - using the exact name
    repo_name = "deepagents-system-config"

    print(f"Pushing corrected config to Hub: {repo_name}")
    agents = DEFAULT_SYSTEM_CONFIG.get("agents", {})  # type: ignore[union-attr]
    cinematographer = agents.get("Cinematographer", {})  # type: ignore[union-attr]
    capabilities = cinematographer.get("capabilities", [])  # type: ignore[union-attr]
    if capabilities and len(capabilities) > 0:
        models = capabilities[0].get("models", [])  # type: ignore[union-attr]
        if models and len(models) > 0:
            print(f"Video model ID in config: {models[0].get('id', 'unknown')}")

    # Push the prompt
    url = client.push_prompt(repo_name, object=prompt)
    print(f"Pushed successfully! URL: {url}")

    # Clear the local cache
    cache_file = os.path.join(
        os.path.dirname(__file__),
        "DeepAgents/.cache/prompts/deepagents-system-config.txt",
    )
    if os.path.exists(cache_file):
        os.remove(cache_file)
        print(f"Cleared local cache: {cache_file}")


if __name__ == "__main__":
    push_config()
