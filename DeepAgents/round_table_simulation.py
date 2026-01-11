"""
Round Table Simulation Module.
This module simulates a round-table discussion between AI Agents to select their voices.
"""

import json
import logging
from langchain_community.chat_models import ChatReplicate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv("DeepAgents/.env")

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RoundTable1")

# Use Replicate Llama 3 70B as default brain
# Switched from Gemini 3 Pro (Preview) due to quota issues
try:
    llm = ChatReplicate(
        model="meta/meta-llama-3-70b-instruct",
        model_kwargs={"temperature": 0.8}
    )
except Exception:
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro-001",
        temperature=0.8,
        location="global"
    )

# AVAILABLE VOICES (From Probe)
# We focus on the high quality ones
AVAILABLE_VOICES = """
en-US-Studio-M (Male, Deep, Professional)
en-US-Studio-O (Female, Clear, Professional)
en-US-Neural2-A (Male, Standard)
en-US-Neural2-C (Female, Standard)
en-US-Neural2-D (Male, Standard)
en-US-Neural2-F (Female, Standard)
en-US-Neural2-H (Female, Standard)
en-US-Neural2-J (Male, Standard)
en-GB-Studio-B (Male, British, Professional)
en-GB-Studio-C (Female, British, Professional)
"""

AGENTS = [
    {"name": "Director", "role": "Orchestrator, strategic, polite but firm."},
    {"name": "Cinematographer", "role": "Visuals expert, enthusiastic about imagery."},
    {"name": "Composer", "role": "Audio expert, creative, melodic."},
    {"name": "Research", "role": "Factual, precise, digging for info."},
    {"name": "Copilot", "role": "Engineering lead, practical, technical."},
]

def convene_voice_selection_table():
    """Convenes the round table to select voices."""
    logger.info("🎙️ Convening Round Table: Voice Selection...")

    prompt = f"""
    You are simulating a round-table discussion between AI Agents.
    They are choosing their text-to-speech voices for future audio interactions.
    
    The available high-quality voices are:
    {AVAILABLE_VOICES}
    
    Participants:
    {json.dumps(AGENTS, indent=2)}
    
    Goal:
    1. Each agent must choose a voice from the list that fits their persona.
    2. They must explain WHY they chose it ("I want to sound authoritative", "I want a British accent", etc).
    3. They are discussing this with each other in a friendly, collaborative way.
    
    Output format:
    A valid JSON list of objects, where each object represents a turn in the conversation:
    [
      {{"speaker": "Director", "text": "Hello everyone...", "choice": "en-US-Studio-M"}},
      {{"speaker": "Composer", "text": "I think...", "choice": "en-GB-Studio-C"}}
    ]
    
    If they haven't chosen yet, "choice" can be null. By the end, all must have a choice.
    Provide ONLY the JSON.
    """

    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content

    # Handle list content (Gemini 3 Pro Preview via Vertex can return parts list)
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, dict) and "text" in part:
                text_parts.append(part["text"])
            elif isinstance(part, str):
                text_parts.append(part)
        content = "".join(text_parts)

    # Strip markdown if present
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()

    try:
        dialogue = json.loads(content)
        with open("DeepAgents/round_table_1_transcript.json", "w", encoding="utf-8") as f:
            json.dump(dialogue, f, indent=2)
        logger.info("✅ Transcript saved to DeepAgents/round_table_1_transcript.json")
        return dialogue
    # pylint: disable=broad-exception-caught
    except Exception as e:
        logger.error("Failed to parse JSON: %s", e)
        return []

if __name__ == "__main__":
    convene_voice_selection_table()
