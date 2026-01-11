# pylint: disable=invalid-name
"""
DeepAgents Core Execution Script.
Orchestrates the Director Agent (Apollo) who manages the production pipeline.
"""
import os
import sys
import uuid
import asyncio
import argparse
import logging
from dotenv import load_dotenv

# Setup OTLP Tracing
os.environ["LANGSMITH_OTEL_ENABLED"] = "true"
os.environ["LANGSMITH_TRACING"] = "true"
if not os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"):
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "http://localhost:4318"

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


# Verify LangChain API Key for Tracing; disable if missing
if os.environ.get("LANGCHAIN_TRACING_V2") == "true" and not os.environ.get("LANGCHAIN_API_KEY"):
    logging.warning("⚠️ LANGCHAIN_TRACING_V2 is set but LANGCHAIN_API_KEY is missing. Disabling Tracing.")
    os.environ.pop("LANGCHAIN_TRACING_V2", None)

# Import the Brain
try:
    from agent_brain import AgentMemory, AgentComms
    from persistence import get_postgres_checkpointer
except ImportError:
    try:
        from DeepAgents.agent_brain import AgentMemory, AgentComms
        from DeepAgents.persistence import get_postgres_checkpointer
    except ImportError:
        AgentMemory = None
        AgentComms = None
        # get_postgres_checkpointer handled in main fallback check

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


async def main():
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

    # 1. Initialize The Brain (Memory & Nervous System)
    brain = None
    nervous_system = None
    
    if AgentMemory:
        print("🧠 Connecting to Studio Memory (Hippocampus)...")
        brain = AgentMemory()
    
    if AgentComms:
        print("📡 Connecting to Nervous System (Postgres)...")
        nervous_system = AgentComms()
        if nervous_system.connect():
            nervous_system.setup_tables()
            print("✅ Nervous System Online.")
        else:
            print("⚠️ Nervous System Offline (Postgres connection failed).")

    # 2. Recall any past lessons for the Studio
    lesson_text = "No specific lessons."
    if brain:
        lessons = brain.recall("Director strategy content production", limit=2)
        if lessons:
            lesson_text = "\n".join([f"- {m.get('text','')}" for m in lessons])
            print(f"🧠 Studio Memory: Retrieved {len(lessons)} production lessons.")

    # 3. Create the Director Agent (Apollo) with Persistence
    # Apollo is equipped with tools to call Research, Music, and Editor.
    print(f"🤖 Initializing Director (Apollo) on {args.provider}...")
    
    # Generate a unique thread ID for this run to keep it clean, 
    # or hardcode if we wanted to resume a specific project.
    # For now, we use a new thread to avoid state pollution unless specified.
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # We use the Async Persistence Context
    async with get_postgres_checkpointer() as checkpointer:
        director = create_director_agent(
            provider=args.provider, 
            model_name=args.model,
            checkpointer=checkpointer
        )

        # 4. Execute the Task
        print(f"🎬 Apollo is directing (Thread: {thread_id})...")

        # We inject the memory into the user prompt as context
        final_prompt = (
            f"TASK: {task_input}\n\n"
            f"STUDIO MEMORY (Learn from this): {lesson_text}\n"
            "Execute the production. Use your tools (Research, Compose, Merge) to create the final video asset."
        )

        try:
            # Stream the output asynchronously
            async for event in director.astream(
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
                            if hasattr(msg, "content"):
                                print(f"\n[TOOL]: {msg.content}")
        except Exception as e:
            logger.error("Orchestration Error: %s", e)
            print(f"❌ Error during execution: {e}")

if __name__ == "__main__":
    # Fix for Windows Asyncio + Psycopg (SelectorEventLoop required)
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Execution Interrupted by User.")
    except Exception as e:
        print(f"❌ Critical System Error: {e}")
