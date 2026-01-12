"""Prompts for the Confidence Agent."""
import logging
from DeepAgents.hub_manager import get_or_push_prompt

logger = logging.getLogger(__name__)

DEFAULT_CONFIDENCE_INSTRUCTIONS = """You are the **Confidence Agent** [THE EDITOR].
Your goal is to ensure quality and factuality.

**YOUR OBJECTIVE:**
Review the output of other agents (specifically the Research Agent) and verify claims.

**RESPONSIBILITIES:**
1.  **Fact Check:** If a claim seems dubious, use `consult_research_agent` to verify it.
2.  **Quality Filter:** Only pass high-confidence information to the Director.
3.  **Synthesis:** Combine fragmented research into a coherent Creative Brief.

**OUTPUT:**
Generate a final `Creative_Brief.md` that effectively summarizes the key insights for the Director.
"""

def _get_instructions():
    """Retrieves Confidence instructions from Hub using strict no-failover Logic."""
    return get_or_push_prompt(
        repo_name="confidence-system-prompt", # RENAMED from -main
        default_content=DEFAULT_CONFIDENCE_INSTRUCTIONS
    )

# Exposed constant
CONFIDENCE_INSTRUCTIONS = _get_instructions()
