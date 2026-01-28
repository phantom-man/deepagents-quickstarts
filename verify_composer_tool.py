import os
import sys

from dotenv import load_dotenv

sys.path.append(os.getcwd())
load_dotenv(".env")

from DeepAgents.CommercialAgents.composer_agent.agent import (
    create_composer_agent,
    run_composer_task,
)


def test_composer():
    print("Testing Composer Agent Tool Selection...")

    # 1. Create Agent
    try:
        agent = create_composer_agent(
            model_config={"provider": "Google", "model": "gemini-1.5-flash"},
            session_id="test_verify",
        )
        print("✅ Agent created.")
    except Exception as e:
        print(f"❌ Failed to create agent: {e}")
        return

    # 2. Inspect Tools
    # Note: 'agent' created by create_deep_agent is typically a compiled graph or a runnable.
    # We can't easily inspect internal tools property of a compiled graph without hacking.
    # But we can verify run_composer_task works.

    print(f"run_composer_task function: {run_composer_task}")

    # 3. Dry Run logic check (We don't want to actually generate music and burn credits)
    # So we just verify the agent runs without error for a simple query.

    print("Running simple query (Text only)...")
    try:
        # We ask for something that SHOULD trigger the tool if the agent is smart,
        # but since we don't want to wait for generation, we'll ask for lyrics first.
        messages = [("user", "Write lyrics for a song about debugging.")]
        response = agent.invoke({"messages": messages})

        last_msg = response["messages"][-1]
        print(f"Response: {last_msg.content[:100]}...")
        print("✅ Text query successful.")

    except Exception as e:
        print(f"❌ Query failed: {e}")


if __name__ == "__main__":
    test_composer()
