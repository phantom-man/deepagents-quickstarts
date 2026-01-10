"""
History & Narrative Tools for Orpheus (The Composer).
Implements the 'Temporal Resonance Engine' requested during the Round Table.
These tools allow for deep narrative analysis and counterfactual history simulation.
"""

import logging
from langchain.tools import tool
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import os

# Setup Logger
logger = logging.getLogger("HistoryTools")
logging.basicConfig(level=logging.INFO)

# Initialize a dedicated model for history analysis if needed,
# or we can reuse one passed in context, but tools are usually standalone.
# We'll use a standard one here.
_HISTORY_LLM = (
    None  # Lazy initialization needed to prevent import-time crashes on network fail
)


def get_history_llm():
    # pylint: disable=global-statement
    global _HISTORY_LLM
    if _HISTORY_LLM is None:
        try:
            _HISTORY_LLM = ChatGoogleGenerativeAI(
                model="gemini-3-pro-preview", 
                temperature=0.7,
                project=os.getenv("GOOGLE_CLOUD_PROJECT"),
                location="global"
            )
        except Exception:
            _HISTORY_LLM = None
    return _HISTORY_LLM


@tool
def narrative_reconstruction(topic_or_text: str) -> str:
    """
    Deconstructs historical narratives to find underlying biases, hidden agendas,
    and the 'profound truth' beneath the official story.

    Use this when you need to understand the deeper context of a story or event
    to write more meaningful lyrics or music.

    Args:
        topic_or_text (str): The historical event, myth, or text to analyze.
    """
    logger.info("🕰️ Temporal Resonance > Reconstructing Narrative: %s", topic_or_text)

    llm = get_history_llm()
    if not llm:
        return "Error: History Engine (LLM) unavailable."

    prompt = (
        f"ANALYZE THE NARRATIVE ARCHITECTURE OF: {topic_or_text}\n\n"
        "OBJECTIVE: Peal back the layers of 'official history' or 'standard myth'.\n"
        "1. Identify the 'Victor's Bias' (who wrote this and why?).\n"
        "2. Find the silenced voices or forgotten perspectives.\n"
        "3. Determine the emotional core of the event (Tragedy? Hubris? Hope?).\n\n"
        "Output a 'Resonance Report' suitable for inspiring an epic musical composition."
    )

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        return str(response.content)
    except Exception as e:
        return f"Narrative Deconstruction Failed: {e}"


@tool
def counterfactual_simulation(event: str, divergence_point: str) -> str:
    """
    Simulates alternative history lineages based on a specific change.

    Use this to explore 'What If' scenarios to find dramatic tension for your art.

    Args:
        event (str): The historical event (e.g., "The Fall of Troy").
        divergence_point (str): The specific change (e.g., "Hector defeats Achilles").
    """
    logger.info(
        "twisted_rightwards_arrows Counterfactual > Simulating: %s | Divergence: %s",
        event,
        divergence_point,
    )

    llm = get_history_llm()
    if not llm:
        return "Error: History Engine (LLM) unavailable."

    prompt = (
        f"RUN COUNTERFACTUAL SIMULATION.\n"
        f"ANCHOR EVENT: {event}\n"
        f"DIVERGENCE POINT: {divergence_point}\n\n"
        "Trace the causal ripples of this change:\n"
        "1. Immediate Consequences (1-10 years)\n"
        "2. Cultural Shifts (How does art/music change?)\n"
        "3. The New 'Emotional Truth' of this timeline.\n"
    )

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        return str(response.content)
    except Exception as e:
        return f"Simulation Failed: {e}"
