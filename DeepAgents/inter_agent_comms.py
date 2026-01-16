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


@tool
def delegate_to_director(directive: str) -> str:
    """
    Delegate a task back to the Director Agent (Apollo) for orchestration or re-planning.
    Call this when you need high-level coordination or the task scope has changed.
    
    Args:
        directive: The request or situation requiring Director intervention.
        
    Returns:
        Confirmation that the task has been delegated to the Director.
    """
    return f"HANDOFF:director:{directive}"


@tool
def delegate_to_researcher(query: str) -> str:
    """
    Delegate a research/fact-checking task to the Researcher Agent (Delphi).
    Call this when you need facts verified, web searches, or background information.
    
    Args:
        query: The research question or topic to investigate.
        
    Returns:
        Confirmation that the task has been delegated to the Researcher.
    """
    return f"HANDOFF:researcher:{query}"


@tool
def delegate_to_confidence(content: str) -> str:
    """
    Delegate content validation to the Confidence Agent (Validator).
    Call this when you need quality assurance, fact-checking, or approval of work.
    
    Args:
        content: The content or plan to be validated/audited.
        
    Returns:
        Confirmation that the task has been delegated to the Confidence Agent.
    """
    return f"HANDOFF:validator:{content}"


@tool
def delegate_to_composer(directive: str) -> str:
    """
    Delegate an audio/music task to the Composer Agent (Orpheus).
    Call this when you need music, sound effects, or audio generated.
    
    Args:
        directive: The creative direction for the audio/music. Be specific about mood, genre, tempo, etc.
        
    Returns:
        Confirmation that the task has been delegated to the Composer.
    """
    return f"HANDOFF:composer:{directive}"


@tool
def delegate_to_cinematographer(directive: str) -> str:
    """
    Delegate a visual/video task to the Cinematographer Agent (Lumiere).
    Call this when you need images, video, storyboards, or visual content generated.
    
    Args:
        directive: The creative direction for the visuals. Be specific about scene, style, mood, etc.
        
    Returns:
        Confirmation that the task has been delegated to the Cinematographer.
    """
    return f"HANDOFF:cinematographer:{directive}"


@tool
def delegate_to_editor(assets: str) -> str:
    """
    Delegate post-production/assembly to the Editor Agent.
    Call this when you have video and audio assets ready to be merged into a final cut.
    
    Args:
        assets: Description of the assets to be assembled (video paths, audio paths).
        
    Returns:
        Confirmation that the task has been delegated to the Editor.
    """
    return f"HANDOFF:editor:{assets}"


@tool
def signal_task_complete(result: str) -> str:
    """
    Signal that your task is complete and the workflow should end.
    Call this when you have finished your work and no further delegation is needed.
    
    Args:
        result: A summary of what was accomplished.
        
    Returns:
        Signal to end the workflow.
    """
    return f"HANDOFF:end:{result}"


# Export all tools for easy import by agents
ALL_DELEGATION_TOOLS = [
    discover_agents,
    delegate_to_director,
    delegate_to_researcher,
    delegate_to_confidence,
    delegate_to_composer,
    delegate_to_cinematographer,
    delegate_to_editor,
    signal_task_complete,
]

# Agent-specific tool sets (each agent gets discovery + others, not self)
DIRECTOR_TOOLS = [
    discover_agents,
    delegate_to_researcher,
    delegate_to_confidence,
    delegate_to_composer,
    delegate_to_cinematographer,
    delegate_to_editor,
    signal_task_complete,
]

RESEARCHER_TOOLS = [
    discover_agents,
    delegate_to_director,
    delegate_to_confidence,
    delegate_to_composer,
    delegate_to_cinematographer,
    signal_task_complete,
]

CONFIDENCE_TOOLS = [
    discover_agents,
    delegate_to_director,
    delegate_to_researcher,
    delegate_to_composer,
    delegate_to_cinematographer,
    signal_task_complete,
]

COMPOSER_TOOLS = [
    discover_agents,
    delegate_to_director,
    delegate_to_researcher,
    delegate_to_cinematographer,
    delegate_to_editor,
    signal_task_complete,
]

CINEMATOGRAPHER_TOOLS = [
    discover_agents,
    delegate_to_director,
    delegate_to_researcher,
    delegate_to_composer,
    delegate_to_editor,
    signal_task_complete,
]

EDITOR_TOOLS = [
    discover_agents,
    delegate_to_director,
    delegate_to_composer,
    delegate_to_cinematographer,
    signal_task_complete,
]
