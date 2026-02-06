# probe_orpheus.py
import logging
import os
import sys

from dotenv import load_dotenv

# Load env from .env file
load_dotenv(".env")

# Ensure path - Add repository root
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(repo_root)

try:
    from DeepAgents.CommercialAgents.composer_agent.agent import create_composer_agent
    HAS_COMPOSER = True
except ImportError:
    HAS_COMPOSER = False
    create_composer_agent = None  # type: ignore[assignment,misc]

logging.basicConfig(level=logging.INFO)


def main():
    print("🎻 --- PROBING ORPHEUS (Composer Agent) ---\n")

    if not HAS_COMPOSER:
        print("❌ Composer agent not available")
        return

    task = "Compose a 4-minute cinematic song for a 'Hero's Journey' film. Style: Orchestral, Epic, Emotional. Lyrics should be about leaving home."

    print(f"🎵 Task: {task}")
    print("⏳ Starting Composer Tool...\n")

    try:
        # Create and invoke the composer agent
        if create_composer_agent is not None:
            composer = create_composer_agent()
            print("\n✅ ORPHEUS Composer agent created successfully")
        else:
            print("\n❌ Composer agent factory not available")

    except Exception as e:
        print(f"\n❌ ORPHEUS FAILED: {e}")


if __name__ == "__main__":
    main()
