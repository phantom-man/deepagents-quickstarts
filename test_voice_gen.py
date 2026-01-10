
import os
import sys
import logging
from dotenv import load_dotenv

# Load Env
env_path = os.path.join(os.path.dirname(__file__), 'DeepAgents', '.env')
load_dotenv(env_path)

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from DeepAgents.CommercialAgents.composer_agent.agent import _handle_replicate_generation
from DeepAgents.asset_manager import AssetManager

logging.basicConfig(level=logging.INFO)

# Mock Objects
class MockLLM:
    pass

class MockAssets:
    def save_asset(self, data, asset_type, session_id, prompt):
        print(f"   [MockAssetManager] Saving {asset_type} for session {session_id}...")
        return f"mock_path/{session_id}.mp3"

if __name__ == "__main__":
    print("📢 Testing Voice Generation Path...")
    res = _handle_replicate_generation(
        model_name="suno-ai/bark",
        input_text="Hello, this is a test of the voice generation system.",
        llm=MockLLM(),
        assets=MockAssets(),
        session_id="test_session"
    )
    print(f"Result: {res}")
