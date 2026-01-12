"""
Hub Manager Module (Restored Strict-Simple).
Restored to the logic that was proven to work in 'test_hub_lookup.py'.
"""
import os
import logging
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate

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
    masked_key = f"{api_key[:5]}...{api_key[-4:]}" if api_key and len(api_key) > 10 else "None"
    logger.info(f"HubManager: 🔑 Active Key: {masked_key} | Workspace: {ws_id}")

    if not ws_id:
        logger.error("❌ LANGSMITH_WORKSPACE_ID is missing from environment variables.")
        logger.error("   For Organization Keys, this ID is required to define the 'Owner' context.")
        raise ValueError("LANGSMITH_WORKSPACE_ID not set. Cannot authenticate Hub requests.")

    # 2. Strategy: Use SIMPLE NAME. The SDK uses the Workspace ID to resolve the owner.
    target = repo_name 
    
    logger.info(f"HubManager: 🚀 Context Active (Workspace: {ws_id})")
    logger.info(f"HubManager: Attempting Strict Pull for '{target}'...")
    
    # Explicitly pass configuration to the Client to bypass environment variable caching/timing issues.
    # We verified via inspection that 'workspace_id' is a valid parameter in this SDK version.
    client_kwargs = {}
    if api_key:
        client_kwargs['api_key'] = api_key
    if ws_id:
        client_kwargs['workspace_id'] = ws_id
        
    client = Client(**client_kwargs)
    
    try:
        # Pull Attempt
        prompt_obj = client.pull_prompt(target)
        
        # Validation
        if hasattr(prompt_obj, "messages") and len(prompt_obj.messages) > 0:
             first_msg = prompt_obj.messages[0]
             if hasattr(first_msg, "prompt") and hasattr(first_msg.prompt, "template"):
                 logger.info(f"HubManager: ✅ Success for '{target}'.")
                 return first_msg.prompt.template
             if hasattr(first_msg, "content"):
                 logger.info(f"HubManager: ✅ Success for '{target}'.")
                 return first_msg.content
        
        raise ValueError(f"Prompt '{target}' retrieved but has invalid structure.")

    except Exception as e:
        logger.error(f"HubManager: ❌ Failure for '{target}'. trace: {e}")
        
        # Check for 404/400 to attempt Push (Self-Healing)
        error_str = str(e).lower()
        should_push = False
        if "404" in error_str or "not found" in error_str:
            should_push = True
        elif "no prompt owner" in error_str and ws_id:
             # If we have a workspace ID but still get this, it's very strange, but try pushing.
             should_push = True

        if should_push:
            logger.warning(f"HubManager: Prompt missing. Attempting PUSH to '{target}'...")
            try:
                prompt = ChatPromptTemplate.from_messages([
                    ("system", default_content),
                    ("placeholder", "{messages}")
                ])
                # Push to Simple Name (SDK resolves owner via Workspace ID)
                url = client.push_prompt(target, object=prompt)
                logger.info(f"HubManager: ✅ Push Success: {url}")
                return default_content
            except Exception as push_err:
                 raise RuntimeError(f"CRITICAL: Hub Push Failed: {push_err}") from push_err
        
        # Raise original error if not a missing prompt
        raise RuntimeError(f"CRITICAL: Hub Pull Failed: {e}") from e


