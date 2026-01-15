"""
Performance Enhancement Round Table Module.
This module simulates a round-table discussion where agents introduce themselves
and request resources or tools to enhance their performance.
"""

import json
import logging
from DeepAgents.replicate_adapter import ChatReplicate
from langchain_google_vertexai import ChatVertexAI
# from langchain_google_genai import ChatGoogleGenerativeAI # Deprecated
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv("DeepAgents/.env")

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PerformanceTable")

# Use Replicate Llama 3 70B as default brain
try:
    llm = ChatReplicate(
        model="meta/meta-llama-3-70b-instruct",
        model_kwargs={"temperature": 0.8}
    )
except Exception:
    # Fallback
    llm = ChatVertexAI(
        model="gemini-2.0-flash-exp",
        temperature=0.8,
    )
    )

AGENTS = [
    {"name": "Director", "role": "Orchestrator, strategic, polite but firm."},
    {"name": "Cinematographer", "role": "Visuals expert, enthusiastic about imagery."},
    {"name": "Composer", "role": "Audio expert, creative, melodic."},
    {"name": "Research", "role": "Factual, precise, digging for info."},
    {"name": "Copilot", "role": "Engineering lead, practical, technical."},
]

def convene_performance_table():
    """Convenes the round table for introductions and performance requests."""
    logger.info("🎙️ Convening Round Table: Performance Enhancement...")

    prompt = f"""
    You are simulating a round-table discussion between AI Agents.
    
    Participants:
    {json.dumps(AGENTS, indent=2)}
    
    Goal:
    1. The 'Director' should open the meeting.
    2. Each agent (including the Director) must INTRODUCE themselves by Agent Name and Title/Role.
    3. Each agent must state their specific RESPONSIBILITIES.
    4. Each agent must REQUEST specific tools, resources, or upgrades that would help enhance their performance.
    
    The conversation should be professional, constructive, and tailored to their specific domains (Video, Audio, Code, Research).
    
    Output format:
    A valid JSON list of objects, where each object represents a turn in the conversation:
    [
      {{"speaker": "Director", "text": "Welcome team...", "voice_choice": "en-US-Studio-M"}},
      {{"speaker": "Copilot", "text": "I am the Copilot...", "voice_choice": "en-US-Neural2-D"}}
    ]
    
    Note: 'voice_choice' should be consistent with previous choices if known, or suitable for the persona.
    
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
        with open("DeepAgents/performance_enhancement_transcript.json", "w", encoding="utf-8") as f:
            json.dump(dialogue, f, indent=2)
        logger.info("✅ Transcript saved to DeepAgents/performance_enhancement_transcript.json")
        return dialogue
    # pylint: disable=broad-exception-caught
    except Exception as e:
        logger.error("Failed to parse JSON: %s", e)
        return []

if __name__ == "__main__":
    convene_performance_table()
