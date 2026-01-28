import logging
import os
import sys

from dotenv import load_dotenv

# Setup path and environment
sys.path.append(os.getcwd())
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestOrpheusAudio")

# Note: compose_tool was removed - use run_composer_task or create_composer_agent instead
from DeepAgents.CommercialAgents.composer_agent.agent import run_composer_task


def main():
    print("🎻 Testing Orpheus (Composer Agent) - AUDIO/MUSIC MODE...")

    # We set strict env var to ensure Replicate is picked up if available
    token = os.getenv("REPLICATE_API_TOKEN")
    if not token:
        logger.warning(
            "⚠️ REPLICATE_API_TOKEN not found in env. Audio generation might be mocked or fail."
        )
    else:
        logger.info("✅ Replicate Token Detected.")

    # We specifically ask for Audio/Music file to trigger the tool
    # The agent prompt is "Compose a short electronic melody"
    # If the agent is smart, it should use 'generate_music_audio'
    prompt = "Generate a 10-second audio clip of an 8-bit chiptune melody. Use the music generation tool."
    print(f"🎵 Task: {prompt}")

    try:
        result = run_composer_task(prompt)
        print("\n✅ Result:")
        print(result)

    except Exception as e:
        logger.error(f"Test Failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
