"""
DeepAgents Agent Factory
Standardized factory using modern LangGraph best practices (Prebuilt ReAct Agent).
Delegates to legacy factory for models without native tool calling support.
"""
import logging
from typing import List, Any
from langchain_core.language_models import BaseChatModel
from langgraph.prebuilt import create_react_agent

logger = logging.getLogger("DeepAgentFactory")

# Try to import legacy factory for fallbacks
try:
    from DeepAgents.agent_factory_legacy import create_deep_agent as create_legacy_agent
except ImportError:
    # Fallback to local relative import if running as package
    try:
        from .agent_factory_legacy import create_deep_agent as create_legacy_agent
    except ImportError:
        logger.warning("Could not import agent_factory_legacy. Replicate models may fail.")
        create_legacy_agent = None


def create_deep_agent(model: BaseChatModel, tools: List[Any], system_prompt: str, checkpointer: Any = None) -> Any:
    """
    Factory to create a DeepAgent using the standard LangGraph ReAct pattern.
    
    Args:
        model: The LLM/ChatModel instance (must support .bind_tools if using standard path).
        tools: List of tools available to the agent.
        system_prompt: The system instructions (Ontology).
        checkpointer: Optional LangGraph checkpoint saver for persistence/time-travel.
        
    Returns:
        A compiled LangGraph runnable.
    """
    
    # Create the Deep Agent
    
    # --- MESH NETWORK INJECTION (Level 4 Agent Architecture) ---
    from DeepAgents.mesh_network import consult_agent_mesh
    from DeepAgents.agency_registry import get_agent_descriptions
    
    # 1. Inject the Tool
    if consult_agent_mesh not in tools:
        # We append it to the FRONT to encourage usage
        tools.insert(0, consult_agent_mesh)
        
    # 2. Inject Metacognition (System Prompt Header)
    # We append the registry capability to the prompt so the model knows it exists.
    # Check if not already present to avoid duplication
    if "MESH NETWORK PROTOCOL" not in system_prompt:
        mesh_instructions = f"""
## MESH NETWORK PROTOCOL (ACTIVE)
You are part of an autonomous agent mesh. You are NOT alone.
If you lack information, expertise, or capabilities, you MUST consult the Agent Registry.

**AVAILABLE PEERS:**
{get_agent_descriptions()}

**PROTOCOL:**
1. **Self-Correction**: If you are unsure, DO NOT GUESS.
2. **Delegation**: Use the `consult_agent_mesh` tool to ask questions or request assets from peers.
   - Example: `consult_agent_mesh("Researcher", "Find the specs for the Sony A7S III")`
   - Example: `consult_agent_mesh("Composer", "Generate a sad violin track")`
"""
        system_prompt = mesh_instructions + "\n" + system_prompt

    # 1. Check for Legacy/Dumb Models (No Tool Calling)
    # Replicate models generally do not support native tool binding yet.
    is_replicate = "replicate" in str(type(model)).lower()
    
    if is_replicate:
        logger.info("⚠️ Model detected as Replicate (Non-Native Tools). Routing to Legacy Factory.")
        if create_legacy_agent:
            return create_legacy_agent(model, tools, system_prompt, checkpointer)
        else:
            logger.error("Legacy Factory missing. Replicate agent will likely crash.")

    # 2. Standard Modern Path (Anthropic / OpenAI / Google GenAI)
    # Using LangGraph's prebuilt agent is the Best Practice.
    # It handles tool binding, execution loops, and state management efficiently.
    
    logger.info("✨ Creating Standard LangGraph ReAct Agent")
    
    try:
        agent = create_react_agent(
            model=model,
            tools=tools,
            prompt=system_prompt,
            checkpointer=checkpointer
        )
        return agent
        
    except Exception as e:
        logger.error(f"❌ Failed to create standard ReAct agent: {e}")
        logger.warning("Attempting fallback to Legacy Factory...")
        if create_legacy_agent:
            return create_legacy_agent(model, tools, system_prompt, checkpointer)
        raise e
