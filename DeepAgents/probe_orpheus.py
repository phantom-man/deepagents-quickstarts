# probe_orpheus.py
import os
import sys
import logging
from dotenv import load_dotenv

# Load env from .env file
load_dotenv(".env")

# Ensure path - Add repository root
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(repo_root)

from DeepAgents.CommercialAgents.composer_agent.agent import compose_tool, create_composer_agent

logging.basicConfig(level=logging.INFO)

def main():
    print("🎻 --- PROBING ORPHEUS (Composer Agent) ---\n")
    
    task = "Compose a 4-minute cinematic song for a 'Hero's Journey' film. Style: Orchestral, Epic, Emotional. Lyrics should be about leaving home."
    
    print(f"🎵 Task: {task}")
    print("⏳ Starting Composer Tool...\n")
    
    try:
        # We call the tool wrapper which initializes the agent and runs it
        # Note: compose_tool is a StructuredTool, utilize .run() or .invoke()
        result = compose_tool.invoke(task)
        
        print("\n✅ ORPHEUS RESULT:")
        print(result)
        
    except Exception as e:
        print(f"\n❌ ORPHEUS FAILED: {e}")

if __name__ == "__main__":
    main()
