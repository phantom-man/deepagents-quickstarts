import os
import time

from dotenv import load_dotenv

# Load env vars before imports that might check them
load_dotenv("DeepAgents/.env")

# Force usage of API Key by removing Vertex AI Project ID
# This prevents 'google-genai' from trying to use Vertex OAuth behavior
if "GOOGLE_CLOUD_PROJECT" in os.environ:
    del os.environ["GOOGLE_CLOUD_PROJECT"]
if "GOOGLE_CLOUD_LOCATION" in os.environ:
    del os.environ["GOOGLE_CLOUD_LOCATION"]

from DeepAgents.memory_manager import AgentMemoryManager


def verify():
    print("--- Starting Memory Verification ---")

    # 1. Initialize
    agent = AgentMemoryManager("VerificationBot")

    # 2. Log Interaction (Postgres)
    print("Writing to Postgres History...")
    agent.log_interaction("Test Prompt", "Test Response")
    time.sleep(1)  # Allow for DB commit if async (it's not but safe)

    # 3. Recall (Postgres)
    print("Reading from Postgres History...")
    history = agent.recall_recent(limit=1)
    if "Test Prompt" in history:
        print("✅ Postgres History Verification Passed")
    else:
        print(f"❌ Postgres History Verification Failed. Got: {history}")

    # 4. Record Learning (LanceDB)
    print("Writing to LanceDB (Embedding)...")
    try:
        agent.record_learning("The sun is a star.")
        # 5. Search (LanceDB)
        print("Searching LanceDB...")
        results = agent.search_learnings("What is the sun?")
        if "star" in results:
            print("✅ LanceDB Knowledge Verification Passed")
        else:
            print(
                f"❌ LanceDB Verification Failed (Result might be empty if embedding failed). Got: {results}"
            )
    except Exception as e:
        print(f"❌ LanceDB Error: {e}")


if __name__ == "__main__":
    verify()
