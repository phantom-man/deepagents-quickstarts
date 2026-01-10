import logging
from typing import List, Any

from langchain_core.language_models import BaseChatModel
from langgraph.prebuilt import create_react_agent

logger = logging.getLogger("DeepAgentFactory")

# Try to import from the installed 'deepagents' package
try:
    from deepagents.graph import create_deep_agent as _lib_create_deep_agent
    HAS_DEEPAGENTS_LIB = True
except ImportError:
    HAS_DEEPAGENTS_LIB = False
    _lib_create_deep_agent = None

def create_deep_agent(model: BaseChatModel, tools: List[Any], system_prompt: str, checkpointer: Any = None) -> Any:
    """
    Factory to create a DeepAgent. 
    Prefers the installed 'deepagents' library implementation if available (for full middleware support).
    Falls back to a simple LangGraph prebuilt agent if not.
    
    Args:
        model: The LLM/ChatModel instance.
        tools: List of tools available to the agent.
        system_prompt: The system instructions (Ontology).
        checkpointer: Optional LangGraph checkpoint saver for persistence/time-travel.
        
    Returns:
        A compiled LangGraph runnable (or DeepAgent equivalent).
    """
    if HAS_DEEPAGENTS_LIB and _lib_create_deep_agent:
        # The library version supports efficient middleware chains
        return _lib_create_deep_agent(
            model=model,
            tools=tools,
            system_prompt=system_prompt,
            name="deep_agent_instance",
            checkpointer=checkpointer
        )
    
    logger.warning("Falling back to simple create_react_agent (deepagents lib not found)")
    # Simple fallback
    return create_react_agent(model, tools, state_modifier=system_prompt, checkpointer=checkpointer)
