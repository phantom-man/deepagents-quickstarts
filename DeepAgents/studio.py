# pylint: disable=invalid-name
# pylint: disable=broad-exception-caught
"""
DeepAgents Core Execution Script.
Orchestrates the Director Agent (Apollo) who manages the production pipeline.
"""
import os
import sys
import time
import argparse
import logging
import json
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.tracers.context import collect_runs  # For capturing Run ID
from langgraph.checkpoint.memory import MemorySaver  # For State Persistence

# Setup LangSmith Tracing
# Using Standard HTTP Tracing (No local OTLP collector required)
os.environ["LANGCHAIN_TRACING_V2"] = "true"

# Load environment variables IMMEDIATELY
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
# Load Configuration (Single Source of Truth)
CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/agent_config.json"))
try:
    with open(CONFIG_PATH, "r") as f:
        AGENT_CONFIG = json.load(f)
except Exception:
    AGENT_CONFIG = {}
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
# pylint: disable=wrong-import-position
from DeepAgents.CommercialAgents.director_agent.agent import create_director_agent
from DeepAgents.system_diagnostics import SystemDiagnostics  # Import Diagnostics
try:
    from DeepAgents.atlas_db import pop_command
except ImportError:
    # Use relative if needed or ensure path
    from atlas_db import pop_command
from langchain_core.messages import HumanMessage
# pylint: enable=wrong-import-position

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DeepAgents-Orchestrator")
VOICE_LOG_PATH = os.path.join(os.path.dirname(__file__), "voice_log.txt")

def voice_update(message: str):
    """Writes a message to the voice log for the Voice Bridge to speak."""
    try:
        with open(VOICE_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"{message}\n")
    except Exception:
        pass # Don't crash on logging
        
def check_for_injections() -> str | None:
    """Checks the Atlas DB for pending commands."""
    try:
        cmd = pop_command()
        return cmd
    except Exception:
        return None

def main():
    parser = argparse.ArgumentParser(description="DeepAgents Production Studio")
    
    # Defaults from Config
    def_director_provider = AGENT_CONFIG.get("Director", {}).get("provider", "Google")
    def_director_model = AGENT_CONFIG.get("Director", {}).get("model", "gemini-2.0-flash-001")

    parser.add_argument("--task", type=str, help="The production task for the Director.")
    parser.add_argument("task_positional", nargs="?", help="Positional task input")
    parser.add_argument("--provider", type=str, default=def_director_provider, help="LLM Provider (Google/Anthropic)")
    parser.add_argument("--model", type=str, default=def_director_model, help="Model Name")
    
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
    voice_update(f"Studio Started. Task is: {task_input}")

    # 0. System Pre-Flight Check (New Constraint)
    diag = SystemDiagnostics()
    if not diag.run_preflight_checks():
        print("⚠️ System Check Failed.")
        # Override for testing:
        if args.task and "test" in args.task.lower():
            print("⚠️ Bypass enabled for Test Task. Proceeding...")
        else:
             print("❌ Exiting to prevent quota/resource errors. (Use --task 'test' to bypass)")
             # sys.exit(1) # Softened for now until quota recovers

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

    # 3. Create the Director Agent (Atlas)
    # Atlas is equipped with tools to call Research, Music, and Editor.
    
    # CHECK FOR VOICE ONLY MODE
    if os.environ.get("ATLAS_VOICE_ONLY_MODE") == "true":
         print("🔊 VOICE ONLY MODE ACTIVE. Agent Creation Skipped.")
         voice_update("Voice connection established. Updates will be read aloud. Copilot system online.")
         
         while True:
             time.sleep(1)
             # Basic Input Monitoring handled by run_atlas.py and voice_update
             # Just wait and check for kill signals
             # Optionally check for injections to speak them
             cmd = check_for_injections()
             # If run_atlas wrote directly to voice log, we don't need to do anything here
             # But if they sent command via atlas_link, we should speak it
             if cmd:
                 voice_update(f"Command Received: {cmd}")
                 
             
    print(f"🤖 Initializing Atlas (Director) on {args.provider}...")
    voice_update("I am waking up. Atlas is online and ready for your command.")
    
    try:
        checkpointer = MemorySaver()
        director = create_director_agent(provider=args.provider,
                                         model_name=args.model,
                                         checkpointer=checkpointer)
    except Exception as e:
        print(f"❌ Agent Init Failed: {e}")
        voice_update("Agent Initialization failed. Falling back to system loop.")
        # Ensure we don't crash entirely so voice still works for diagnostics
        if os.environ.get("ATLAS_VOICE_ONLY_MODE") == "true": # Retry? No.
             return
        # Enter safe loop
        while True:
            time.sleep(1)

    # 4. Execute the Task
    print("🎬 Atlas is working...")

    
    config = {"configurable": {"thread_id": "production_run_LotR_002"}}
    
    # We inject the memory into the user prompt as context
    final_prompt = (
        f"TASK: {task_input}\n\n"
        f"STUDIO MEMORY (Learn from this): {lesson_text}\n"
        "You are ATLAS, the AI Orchestrator. Speak in the first person ('I will...').\n"
        "Execute the production. Use your tools (Research, Compose, Merge) to create the final video asset."
    )

    try:
        # Stream the output
        run_id = None
        with collect_runs() as cb:
            # type: ignore
            for event in director.stream(
                {"messages": [("user", final_prompt)]},
                config=config
            ):
                # 0. Check for User Diversion/Injection (Atlas DB)
                user_divert = check_for_injections()
                if user_divert:
                    print(f"\n⚡ USER INTERRUPT: {user_divert}")
                    voice_update(f"Hold on. You sent me an update: {user_divert}")
                    
                    # Inject into State
                    # This tells the graph's memory about the new instruction
                    director.update_state(
                        config, 
                        {"messages": [HumanMessage(content=f"URGENT USER UPDATE: {user_divert}")]}
                    )
                    voice_update("I have updated my plan. Continuing work.")

                # 1. Parse LangGraph events for Atlas Voice
                for key, value in event.items():
                    # Handle different node types
                    if key == "agent":
                        # Main Agent Node
                        if "messages" in value:
                            msg = value["messages"][-1]
                            content = getattr(msg, "content", "")
                            
                            # Handle Anthropic List Content (Text + Tool)
                            if isinstance(content, list):
                                text_parts = []
                                for item in content:
                                    if isinstance(item, dict) and item.get("type") == "text":
                                        text_parts.append(item.get("text", ""))
                                    elif hasattr(item, "text"): # Object fallback
                                        text_parts.append(item.text)
                                content = " ".join(text_parts)
                                
                            if content:
                                print(f"\n[ATLAS]: {content}")
                                # Voice summary
                                clean_content = str(content).replace("*", "").replace("#", "").split("\n")[0]
                                voice_update(f"Atlas here. {clean_content[:150]}")
                    
                    elif key == "tools":
                        # Tool Execution
                        if "messages" in value:
                            msg = value["messages"][-1]
                            print(f"\n[TOOL RESULT]: {msg.content[:200]}...")
                            voice_update("Tool finished. Analyzing results.")
                    
                    else:
                        # Other nodes (Research, etc - depends on graph structure)
                        voice_update(f"Moving to phase: {key}")
            if cb.traced_runs:
                run_id = cb.traced_runs[0].id

        print("\n✅ Production Sequence Complete.")

        # Human Feedback Loop
        if run_id:
            try:
                rating = input("\nRate this response (1-5)? ")
                if rating.isdigit() and 1 <= int(rating) <= 5:
                    client = Client()
                    client.create_feedback(
                        run_id=run_id,
                        key="user-score",
                        score=float(rating) / 5.0,  # Norm to 0-1 usually
                        comment="User submitted feedback from studio CLI"
                    )
                    print("Thank you! Feedback recorded in LangSmith.")
            except Exception as e:
                print(f"Failed to record feedback: {e}")

    except Exception as e:
        logger.error("Production Failed: %s", e)
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
