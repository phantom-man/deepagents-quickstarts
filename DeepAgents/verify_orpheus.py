
import os
import sys
import logging
from dotenv import load_dotenv

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DeepAgents-Orpheus-Verify")

# Load Env
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Add Root to Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from DeepAgents.CommercialAgents.composer_agent.agent import compose_tool, generate_music_audio
except ImportError as e:
    logger.error(f"Import Error: {e}")
    sys.exit(1)

def verify_orpheus():
    print("\n🎵 --- VERIFYING ORPHEUS (COMPOSER AGENT) ---")
    
    # 1. Check Token
    token = os.environ.get("REPLICATE_API_TOKEN")
    if not token:
        print("❌ REPLICATE_API_TOKEN is missing from environment/file.")
        print("⚠️ Please check your .env file.")
        return
    else:
        print("✅ REPLICATE_API_TOKEN present.")

    # 2. Run Tool Directly
    prompt = "A 4-minute cinematic song for 'The Coder's Journey'. Genre: Orchestral with Synthwave elements. Mood: Epic, Determined."
    print(f"🎹 Prompt: {prompt}")
    print("⏳ Generating Audio via Tool directly... (This guarantees audio creation)")
    
    try:
        # We call the tool directly to bypass Agent 'Thinking' and force generation
        # The tool expects (prompt, model_name) but wrapped tools handle args differently.
        # Let's inspect signature or just pass string if it's a @tool without args schema.
        # generate_music_audio is decorated.
        
        # Default model is Minimax/Music-01, but explicit is safer
        msg = generate_music_audio.invoke({"prompt": prompt, "model_name": "minimax/music-01"})
        print(f"\n🎉 Audio Generation Result: {msg}")
        
    except Exception as e:
        print(f"❌ Generation Failed: {e}")

if __name__ == "__main__":
    verify_orpheus()
