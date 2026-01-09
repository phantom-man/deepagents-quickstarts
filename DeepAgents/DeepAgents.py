# pylint: disable=invalid-name
"""
DeepAgents Core Execution Script.
Orchestrates the Director Agent (Apollo) who manages the production pipeline.
"""
import os
import sys
import argparse
import logging
from dotenv import load_dotenv

# Import the Brain
try:
    from agent_brain import AgentMemory
except ImportError:
    try:
        from DeepAgents.agent_brain import AgentMemory
    except ImportError:
        AgentMemory = None

# Import Agent Factories
# Ensuring imports work from root or subfolder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from DeepAgents.CommercialAgents.director_agent.agent import create_director_agent
except (ImportError, ModuleNotFoundError):
    # Fallback if DeepAgents.py shadows the package name
    sys.path.append(os.path.dirname(__file__))
    from CommercialAgents.director_agent.agent import create_director_agent

# Load environment variables
load_dotenv()

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DeepAgents-Orchestrator")


def main():
    """Main execution entry point."""
    parser = argparse.ArgumentParser(description="DeepAgents Production Studio")
    parser.add_argument(
        "--task", type=str, help="The production task for the Director."
    )
    parser.add_argument("task_positional", nargs="?", help="Positional task input")
    parser.add_argument(
        "--provider", type=str, default="Google", help="LLM Provider (Google/Anthropic)"
    )
    # Defaults to the powerful Gemini 3 Pro Preview (now verified working with global location)
    parser.add_argument(
        "--model", type=str, default="gemini-3-pro-preview", help="Model Name"
    )

    args = parser.parse_args()

    # Handle task input priority
    task_input = args.task or args.task_positional
    if not task_input:
        print("Please provide a task via --task or as an argument.")
        # If interactive mode is needed:
        # task_input = input("Enter Production Task: ")
        return

    print("\n🎬 --- DEEPAGENTS STUDIOS: PRODUCTION STARTED ---")
    print(f"📋 Task: {task_input}")

    # 1. Initialize The Brain (Memory)
    brain = None
    if AgentMemory:
        print("🧠 Connecting to Studio Memory...")
        brain = AgentMemory()

    # 2. Recall any past lessons for the Studio
    lesson_text = "No specific lessons."
    if brain:
        lessons = brain.recall("Director strategy content production", limit=2)
        if lessons:
            lesson_text = "\n".join([f"- {m.get('text','')}" for m in lessons])
            print(f"🧠 Studio Memory: Retrieved {len(lessons)} production lessons.")

    # 3. Create the Director Agent (Apollo)
    # Apollo is equipped with tools to call Research, Music, and Editor.
    print(f"🤖 Initializing Director (Apollo) on {args.provider}...")
    director = create_director_agent(provider=args.provider, model_name=args.model)

    # 4. Execute the Task
    print("🎬 Apollo is directing...")

    config = {"configurable": {"thread_id": "production_run_LotR_002"}}

    # We inject the memory into the user prompt as context
    final_prompt = (
        f"TASK: {task_input}\n\n"
        f"STUDIO MEMORY (Learn from this): {lesson_text}\n"
        "Execute the production. Use your tools (Research, Compose, Merge) to create the final video asset."
    )

    try:
        # Stream the output
        for event in director.stream(
            {"messages": [("user", final_prompt)]}, config=config  # type: ignore
        ):
            # Parse LangGraph events
            for key, value in event.items():
                if key == "agent":
                    # Assistant Message
                    if "messages" in value:
                        msg = value["messages"][-1]
                        if hasattr(msg, "content"):
                            print(f"\n[APOLLO]: {msg.content}")
                elif key == "tools":
                    # Tool Output
                    if "messages" in value:
                        msg = value["messages"][-1]
                        print(f"\n[TOOL RESULT]: {msg.content[:200]}...")

        print("\n✅ Production Sequence Complete.")

    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Production Failed: %s", e)
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
