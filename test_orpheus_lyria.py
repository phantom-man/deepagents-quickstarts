import logging
import os
import sys

from dotenv import load_dotenv

sys.path.append(os.getcwd())
if os.path.exists("DeepAgents/.env"):
    load_dotenv("DeepAgents/.env")
else:
    load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestOrpheusLyria")

# Note: compose_tool was removed - use run_composer_task or create_composer_agent instead
from DeepAgents.CommercialAgents.composer_agent.agent import run_composer_task


def main():
    print("🎻 Testing Orpheus (Composer Agent) - PRIORITY: LYRIA-2...")

    # We ask for a generic music prompt.
    # Orpheus should default to Lyria-2 -> Cascade if needed.
    prompt = "Compose a heroic orchestral theme for a space adventure."
    print(f"🎵 Task: {prompt}")

    try:
        result = run_composer_task(prompt)
        print("\n✅ Result:")
        print(result)

    except Exception as e:
        logger.error(f"Test Failed: {e}")


if __name__ == "__main__":
    main()
