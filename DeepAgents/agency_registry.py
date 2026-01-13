"""
Agency Registry.
Defines the capabilities and routing information for all agents in the mesh.
This serves as the knowledge base for the 'Discovery' tool.
"""

AGENCY_REGISTRY = {
    "director_agent": {
        "name": "Apollo (Director)",
        "role": "Orchestrator & Creative Lead",
        "description": "Orchestrates the entire production. Calls other agents. Validates creative logic.",
        "skills": [
            "Break down scripts into scenes",
            "Coordinate multiple agents",
            "Assemble final assets (Editor)",
            "Validate narrative consistency",
        ],
        "module": "DeepAgents.CommercialAgents.director_agent.agent",
        "entry_point": "create_director_agent",
        "tool_wrapper": "None (Top Level)"
    },
    "research_agent": {
        "name": "Delphi (Researcher)",
        "role": "Fact Checker & Information Retrieval",
        "description": "Searches the web (Tavily/Google) and Academic papers to find facts, stats, and context.",
        "skills": [
            "Web Search",
            "Academic Research",
            "Fact Checking",
            "Market Analysis",
        ],
        "module": "DeepAgents.CommercialAgents.research_agent.agent",
        "entry_point": "run_research_task",
        "tool_wrapper": "consult_research_agent"
    },
    "composer_agent": {
        "name": "Orpheus (Composer)",
        "role": "Audio & Music Synthesis",
        "description": "Generates music, sound effects, and lyrics. Uses Suno/Udio/Minimax.",
        "skills": [
            "Generate Music (Instrumental/Vocal)",
            "Write Lyrics",
            "Create Sound Effects",
            "Analyze Audio Style",
        ],
        "module": "DeepAgents.CommercialAgents.composer_agent.agent",
        "entry_point": "run_composer_task",
        "tool_wrapper": "consult_composer_agent"
    },
    "cinematographer_agent": {
        "name": "Lumiere (Cinematographer)",
        "role": "Visual Synthesis",
        "description": "Generates Images (Storyboards) and Video clips. Can plan shots. Handles movie, film, and scene visualization.",
        "skills": [
            "Generate Images (Flux/Imagen)",
            "Generate Video (Replicate)",
            "Storyboard Creation",
            "Visual Analysis",
            "Make Movie / Film / Scene",
        ],
        "module": "DeepAgents.CommercialAgents.cinematographer_agent.agent",
        "entry_point": "run_cinematographer_task",
        "tool_wrapper": "consult_cinematographer_agent"
    },
    "editor_tools": {
        "name": "Editor (Tool Suite)",
        "role": "Post-Production",
        "description": "Merging, Cutting, and assembling media files.",
        "skills": [
            "Merge Video and Audio",
            "Concatenate Clips",
            "Add Text Overlays",
        ],
        "module": "DeepAgents.editor_tools",
        "entry_point": "merge_video_audio",
        "tool_wrapper": "assemble_final_cut"
    }
}

def get_agent_descriptions() -> str:
    """Returns a formatted string of all agents and their skills."""
    output = "## Available Agents & Capabilities\n\n"
    for key, data in AGENCY_REGISTRY.items():
        output += f"### {data['name']}\n"
        output += f"- **Description**: {data['description']}\n"
        output += f"- **Skills**: {', '.join(data['skills'])}\n\n"
    return output

def find_agent_for_task(task_description: str) -> str:
    """
    Simple keyword matching to suggest an agent.
    (In future, this could use semantic search).
    """
    task = task_description.lower()
    matches = []
    
    for key, data in AGENCY_REGISTRY.items():
        score = 0
        # Check if skills are requested
        # We split skills into keywords to be more flexible
        for skill in data['skills']:
            # If significant words from skill appear in task
            keywords = [w for w in skill.lower().split() if len(w) > 3]
            for kw in keywords:
                if kw in task:
                    score += 1
                    
        # Check role/description
        desc_keywords = [w for w in data['description'].lower().split() if len(w) > 3]
        for kw in desc_keywords:
            if kw in task:
                score += 1
                
        if score > 0:
            matches.append((score, data['name']))
            
    matches.sort(key=lambda x: x[0], reverse=True)
    
    if matches:
        return f"Best Match: {matches[0][1]}. (Also consider: {[m[1] for m in matches[1:]]})"
    
    return "No direct match found. Try splitting the task into smaller parts or look up 'all'."
