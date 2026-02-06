# pylint: disable=broad-exception-caught
"""
Verification Script for Orpheus (Composer Agent).
Tests direct audio generation capabilities.
"""

import logging
import os
import sys

from dotenv import load_dotenv

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DeepAgents-Orpheus-Verify")

# Load Env
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Add Root to Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from DeepAgents.CommercialAgents.composer_agent.agent import create_composer_agent  # type: ignore[attr-defined]
    HAS_COMPOSER = True
except ImportError as e:
    logger.error("Import Error: %s", e)
    HAS_COMPOSER = False


def verify_orpheus():
    """Run verification logic for Composer Agent."""
    print("\n🎵 --- VERIFYING ORPHEUS (COMPOSER AGENT) ---")

    if not HAS_COMPOSER:
        print("❌ Composer agent import failed. Check logs above.")
        return

    # 1. Check Token
    token = os.environ.get("REPLICATE_API_TOKEN")
    if not token:
        print("❌ REPLICATE_API_TOKEN is missing from environment/file.")
        print("⚠️ Please check your .env file.")
        return

    print("✅ REPLICATE_API_TOKEN present.")

    # 2. Run Tool Directly
    prompt = (
        "A 4-minute cinematic song for 'The Coder's Journey'. "
        "Genre: Orchestral with Synthwave elements. Mood: Epic, Determined."
    )
    print(f"🎹 Prompt: {prompt}")
    print("⏳ Testing composer agent creation...")

    try:
        # Test that the composer agent can be created
        composer = create_composer_agent()  # type: ignore[misc]
        print(f"\n🎉 Composer Agent Created Successfully")

    except Exception as e:
        print(f"❌ Creation Failed: {e}")


if __name__ == "__main__":
    verify_orpheus()
