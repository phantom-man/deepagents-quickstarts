
import sys
import os
import traceback
from dotenv import load_dotenv

# Ensure root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

print("--- Starting Debug Startup Crash ---")
load_dotenv()

try:
    print("1. Importing Director...")
    from DeepAgents.CommercialAgents.director_agent.agent import create_director_agent
    print("   -> Creating Director Graph...")
    director = create_director_agent()
    print("   -> Success.")

    print("2. Importing Researcher...")
    from DeepAgents.CommercialAgents.research_agent.agent import create_research_agent
    print("   -> Creating Researcher Graph...")
    researcher = create_research_agent()
    print("   -> Success.")

    print("3. Importing Composer...")
    from DeepAgents.CommercialAgents.composer_agent.agent import create_composer_agent
    print("   -> Creating Composer Graph...")
    composer = create_composer_agent()
    print("   -> Success.")

    print("4. Importing Confidence...")
    from DeepAgents.CommercialAgents.confidence_agent.agent import create_confidence_agent
    print("   -> Creating Confidence Graph...")
    confidence = create_confidence_agent()
    print("   -> Success.")

    print("5. Importing Cinematographer...")
    from DeepAgents.CommercialAgents.cinematographer_agent.agent import create_cinematographer_agent
    print("   -> Creating Cinematographer Graph...")
    cinematographer = create_cinematographer_agent()
    print("   -> Success.")
    
    print("6. Importing Agency Graph...")
    print("   -> Success.")

except Exception as e:
    print("\n\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print(f"CRITICAL FAILURE: {e}")
    traceback.print_exc()
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    sys.exit(1)

print("\n--- ALL SYSTEMS NOMINAL ---")
