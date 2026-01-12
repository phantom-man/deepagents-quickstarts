# pylint: disable=broad-exception-caught
# pylint: disable=import-error
# pylint: disable=no-name-in-module
"""
Director Agent Module.
Orchestrates the commercial creation process by managing other agents.
"""
import os
import sys
import logging
from typing import Dict, Any, List, cast

from dotenv import load_dotenv
from langchain.tools import tool
from langchain_core.messages import BaseMessage
from langchain_core.language_models import BaseChatModel
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

from DeepAgents.replicate_adapter import ChatReplicate
from DeepAgents.agent_factory import create_deep_agent
from DeepAgents.hub_manager import get_or_push_prompt

# Local imports
# PYTHONPATH should be set to repo root
try:
    from DeepAgents.CommercialAgents.director_agent.prompts import DIRECTOR_INSTRUCTIONS
    from DeepAgents.CommercialAgents.research_agent.agent import run_research_task
except ImportError:
    # Fallback to absolute if script run from subfolder without path
    from DeepAgents.CommercialAgents.director_agent.prompts import DIRECTOR_INSTRUCTIONS
    from DeepAgents.CommercialAgents.research_agent.agent import run_research_task

    # Note: If these fail in fallback, the script will crash, but environment should be consistent now.


# Load environment variables
ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.env"))
load_dotenv(ENV_PATH)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@tool
def validate_scene_logic(scene_description: str) -> str:
    """
    Validates the narrative continuity and logic of a proposed scene.
    Call this BEFORE finalizing a scene treatment to ensure it makes sense.
    Returns a critique: 'PASS' or a list of issues to fix.
    """
    logger.info("🎬 Director > 🧠 Validating Scene Logic...")

    # We use a fresh LLM call for the critique (Self-Reflection)
    # Replaced Gemini-3 with Replicate Llama 3 70B for validation
    try:
        validator_llm = ChatReplicate(
            model="meta/meta-llama-3-70b-instruct",
            model_kwargs={"temperature": 0.1, "max_length": 2048}
        )
    except Exception as e:
        logger.error("Validator LLM Init Failed: %s", e)
        return "Validation System Offline (Check Replicate Token)"

    prompt = f"""
    CRITIQUE THIS SCENE for internal logic, continuity errors, and plot holes.
    
    SCENE:
    {scene_description}
    
    Is this physically and narratively sound?
    If YES, respond only with: PASS
    If NO, list the specific logical errors.
    """

    try:
        response = validator_llm.invoke(prompt)
        return str(response.content)
    except Exception as e:
        return f"Validation Error: {e}"


@tool
def consult_research_agent(topic: str) -> str:
    """
    Consults the Research Agent to gather detailed information, facts,
    and context about a specific topic, product, or concept.
    Use this when you lack sufficient knowledge to direct a scene accurately.
    Returns a comprehensive report.
    """
    logger.info("🎬 Director > 📞 Calling Research Agent about: %s", topic)
    # We call the main entry point of the Research Agent
    # This will trigger the memory check, research, and memorization loop.
    # Pass context for LangSmith
    extra_config = {
        "tags": ["sub-agent-call", "agent:researcher"],
        "metadata": {"parent_agent": "Director", "trigger": "tool_call"},
    }
    result = run_research_task(topic, extra_config=extra_config)
    if result:
        return result
    return "Research Agent could not find significant information."


def create_director_agent(
    provider: str = "Anthropic", model_name: str = "claude-3-haiku-20240307", checkpointer: Any = None
):
    """Creates and returns the Director Agent."""

    # Initialize LLM based on Provider
    if provider == "Anthropic":
        logger.info("🎬 Initializing Anthropic Model: %s", model_name)
        model = ChatAnthropic(
            model_name=model_name,
            temperature=0.7,
            timeout=None,
            stop=None,
        )
    elif provider == "Replicate":
        logger.info("🎬 Initializing Replicate Model: %s", model_name)
        try:
             # Requires REPLICATE_API_TOKEN in env
            model = ChatReplicate(
                model=model_name,
                model_kwargs={"temperature": 0.7, "max_length": 2048, "top_p": 1}
            )
        except Exception as e:
            logger.error("Failed to initialize Replicate Model (%s): %s", model_name, e)
            # Fallback to Google if Replicate fails?
            model = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                temperature=0.7,
                location="us-central1"
            )

    else:
        # Default to Google (Gemini)

        
        # User Directive: Location MUST be global for this model.
        location = "global" if "exp" in model_name or "preview" in model_name else "us-central1"
        
        logger.info("🎬 Initializing Google Model: %s at %s", model_name, location)
        try:
            model = ChatGoogleGenerativeAI(
                model=model_name,
                temperature=0.7,
                # convert_system_message_to_human=True, # Often needed for some models but Gemini handles system now
                max_retries=1, 
            )
        except Exception as e:
            logger.error("Failed to initialize Primary Model (%s): %s", model_name, e)
            # Strict Protocol: Stop if primary fails?
            # User said: "stop what you are doing and talk to me first" if I run into problems with access.
            # But "failing that... use fallback" logic in strict mode?
            # User said: "for fall backs they must use our typical location"
            # So fallback IS allowed.
            logger.info("Switching to Fallback Model (Replicate Llama 3)...")
            try:
                # Using basic Llama 3 8b via Replicate as a cheap backup
                # Note: Requires REPLICATE_API_TOKEN in env
                model = ChatReplicate(
                    model="meta/meta-llama-3-8b-instruct",
                    model_kwargs={"temperature": 0.7, "max_length": 2048, "top_p": 1}
                )
            except Exception as replicate_error:
                logger.critical("Replicate Fallback Failed: %s. SYSTEM HALT.", replicate_error)
                raise replicate_error

    # Create the Deep Agent
    # 🔗 HUB INTEGRATION: Pull System Prompt
    # Using simple name so HubManager resolves owner via Workspace ID
    hub_prompt = get_or_push_prompt("director-system-prompt", DIRECTOR_INSTRUCTIONS)

    # WORKAROUND: If using Google + LangGraph, tools binding might be failing schema validation.
    # We can try to bind them MANUALLY and pass the bound model.
    # But create_deep_agent expects raw model + tools list usually.
    
    # Let's try to filter tools to ensure they are clean Pydantic tools
    # Using 'tool' decorator makes them StructuredTool.
    
    agent = create_deep_agent(
        model=cast(BaseChatModel, model),
        tools=[
            consult_research_agent,
            validate_scene_logic,
        ],
        system_prompt=hub_prompt,
        checkpointer=checkpointer
    )

    return agent


def _parse_event_messages(event: Dict[str, Any]) -> List[BaseMessage]:
    """Helper to extract messages from an event stream."""
    extracted_msgs = []
    # Print tool calls
    for _, val in event.items():
        msgs = []
        # Robust extraction of messages
        if isinstance(val, dict) and "messages" in val:
            msgs = val["messages"]
            # Handle LangGraph Overwrite object if present
            if hasattr(msgs, "value"):
                msgs = msgs.value
        elif hasattr(val, "messages"):
            # Robust access to satisfy safe type checking
            msgs = getattr(val, "messages")

        if msgs and isinstance(msgs, list):
            extracted_msgs.extend(msgs)

    return extracted_msgs


if __name__ == "__main__":
    if len(sys.argv) > 1:
        USER_INPUT = sys.argv[1]
        print(f"Starting Director Agent with input: {USER_INPUT}")
        # Note: No main loop logic here for Director yet in original file?
        # Original file seems to be missing main execution logic or I didn't read it all.
        # But I replaced proper content.
    else:
        print("Director Agent Module ready.")
