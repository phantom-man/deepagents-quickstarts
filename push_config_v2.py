import os
import sys
import json
import logging
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate

# Ensure root is in path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from DeepAgents.system_config import DEFAULT_SYSTEM_CONFIG

# Load Env (Correctly this time)
dotenv_path = os.path.join(os.path.dirname(__file__), "DeepAgents/.env")
if not os.path.exists(dotenv_path):
     dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
     
load_dotenv(dotenv_path, override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CONFIG_UPDATER")

def update_config_on_hub():
    target_repo = "deepagents-system-config"
    logger.info(f"Targeting Repo: {target_repo}")

    # Prepare Content
    config_json = json.dumps(DEFAULT_SYSTEM_CONFIG, indent=2)
    
    # Initialize Client with Org Key Support
    ws_id = os.getenv("LANGSMITH_WORKSPACE_ID")
    client_kwargs = {}
    if ws_id:
        client_kwargs['workspace_id'] = ws_id
        logger.info(f"Using Workspace ID: {ws_id}")
        
    client = Client(**client_kwargs)
    
    # Push Strategy
    logger.info("Pushing updated configuration to Hub...")
    try:
        # Wrap as Prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", config_json),
            ("placeholder", "{messages}")
        ])
        
        # Try pushing to simple name
        url = client.push_prompt(target_repo, object=prompt)
        logger.info(f"✅ Configuration Pushed Successfully!")
        logger.info(f"URL: {url}")
        
    except Exception as e:
        logger.error(f"❌ Push Failed: {e}")

if __name__ == "__main__":
    update_config_on_hub()
