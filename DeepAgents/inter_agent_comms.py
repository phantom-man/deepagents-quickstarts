from langchain_core.tools import tool
from DeepAgents.agency_registry import get_agent_descriptions, find_agent_for_task

@tool
def discover_agents(query: str = "all") -> str:
    """
    Explore the capabilities of other Agents in the system.
    Use this if you have a task that you cannot perform yourself, 
    to find out who CAN perform it.
    
    Args:
        query: Either 'all' to list everyone, or a specific task description (e.g., "make music").
        
    Returns:
        A list of agents and their skills, or a specific recommendation.
    """
    if query.lower() == "all" or query == "":
        return get_agent_descriptions()
    else:
        return find_agent_for_task(query)
