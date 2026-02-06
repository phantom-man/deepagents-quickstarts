"""
Mesh Network Communication Layer.
Implements the "Zero Touch" agent-to-agent communication tool.
"""

import importlib
import logging

from langchain_core.tools import tool

from DeepAgents.agency_registry import AGENCY_REGISTRY

logger = logging.getLogger("MeshNetwork")


@tool
def consult_agent_mesh(target_agent: str, request: str) -> str:
    """
    Universal Agent Communication Tool.
    Use this to ask ANY other agent in the system for help, data, or assets.
    """
    logger.info("📡 MESH CALL: %s -> '%s'", target_agent, request)

    # 1. Resolve Target
    # Try direct key match first
    registry_key = None
    if target_agent.lower() in AGENCY_REGISTRY:
        registry_key = target_agent.lower()
    else:
        # Initial fuzzy match
        for key, data in AGENCY_REGISTRY.items():
            if target_agent.lower() in key:  # e.g. "research" in "research_agent"
                registry_key = key
                break
            name = data.get("name", "")
            role = data.get("role", "")
            if isinstance(name, str) and target_agent.lower() in name.lower():
                registry_key = key
                break
            if isinstance(role, str) and target_agent.lower() in role.lower():
                registry_key = key
                break

    if not registry_key:
        available = list(AGENCY_REGISTRY.keys())
        return f"❌ ERROR: Could not identify agent '{target_agent}'. Available: {available}"

    agent_metadata = AGENCY_REGISTRY[registry_key]
    module_path = agent_metadata["module"]
    entry_point_name = agent_metadata["entry_point"]
    
    # Ensure module_path and entry_point_name are strings
    if not isinstance(module_path, str) or not isinstance(entry_point_name, str):
        return f"❌ ERROR: Invalid registry entry for '{registry_key}'"

    logger.info(
        "🔗 Routing to: %s (%s.%s)", registry_key, module_path, entry_point_name
    )

    # 2. Dynamic Import
    try:
        mod = importlib.import_module(module_path)
        entry_func = getattr(mod, entry_point_name)
    except Exception as e:
        logger.error("Failed to load module: %s", e)
        return f"❌ SYSTEM ERROR: Failed to load agent module {module_path}: {e}"

    # 3. Dynamic Invocation
    try:
        if "director" in registry_key:
            # Graph Factory
            agent_graph = entry_func()  # call create_director_agent()
            response = agent_graph.invoke({"messages": [("user", request)]})
            return response["messages"][-1].content

        # Functional Agents (Researcher, Composer, etc.)
        return entry_func(request)

    except Exception as e:
        logger.error("Mesh Invocation Failed: %s", e, exc_info=True)
        return f"❌ AGENT CRASH: The agent '{target_agent}' failed. Error: {e}"
