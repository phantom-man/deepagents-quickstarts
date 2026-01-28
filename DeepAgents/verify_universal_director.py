"""
Verification script for the Universal Creative Director capability.
Tests if the Director Agent can handle a prompt for a Music Video content plan.
"""

import asyncio
import logging
import os
import sys

# Ensure repo root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langchain_core.messages import HumanMessage

from DeepAgents.CommercialAgents.director_agent.agent import create_director_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def verify_universal_director():
    logger.info("🎬 Verifying Universal Creative Director Capability...")

    # Create the agent using Anthropic Claude 3 Haiku
    # Matches user directive to use Anthropic Haiku
    try:
        agent = create_director_agent(
            provider="Anthropic", model_name="claude-3-haiku-20240307"
        )
        logger.info("✅ Director Agent Created (Anthropic/Claude-3-Haiku)")
    except Exception as e:
        logger.error(f"❌ Failed to create agent: {e}")
        return

    # A non-commercial prompt to test "Universal" capability
    prompt_text = "Create a content plan for a music video. The song is a sad ballad called 'Rainy Days'. Visual style should be black and white, film noir."

    logger.info(f"📝 Prompt: {prompt_text}")

    input_message = HumanMessage(content=prompt_text)

    logger.info("🚀 Invoking Agent...")
    try:
        # Prepare valid LangGraph state
        initial_state = {"messages": [input_message]}

        # Invoke the compiled graph
        # We need to handle async invocation if the compiled graph is async.
        # StateGraph.compile() returns a CompiledGraph, which has .invoke() and .ainvoke().
        # Since we are in an async function, we can use .ainvoke() or wrap .invoke().

        # Standard synchronous invoke for simplicity in this script unless async is forced
        # But wait, create_director_agent is synchronous function returning compiled graph.

        result = await agent.ainvoke(initial_state)

        # Extract the final response
        messages = result["messages"]
        last_message = messages[-1]

        print("\n" + "=" * 50)
        print("🎬 DIRECTOR AGENT RESPONSE")
        print("=" * 50)
        print(last_message.content)
        print("=" * 50 + "\n")

        logger.info("✅ Agent invoked successfully.")

    except Exception as e:
        logger.error(f"❌ Error during invocation: {e}")


if __name__ == "__main__":
    asyncio.run(verify_universal_director())
