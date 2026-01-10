# pylint: disable=broad-exception-caught
# pylint: disable=import-error
# pylint: disable=no-name-in-module
"""
The Round Table (DeepAgents Ruminations).
Simulates a strategic meeting between the 5 Core Agents (Atlas, Apollo, Lumiere, Delphi, Argus).
"""
import os
import sys
import datetime
import logging
from typing import Dict

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

# Ensure path visibility
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Load Env
load_dotenv()

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RoundTable")

class RoundTable:
    """Orchestrates a discussion between the DeepAgents personae."""

    def __init__(self):
        self.output_dir = os.path.join(os.path.dirname(__file__), "Ruminations")
        os.makedirs(self.output_dir, exist_ok=True)
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            project=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION")
        )
        self.roster = {
            "ATLAS": "The Engineer & Chairman. Rational, architectural, focused on structure.",
            "APOLLO": "The Director. Creative, visionary, focused on narrative flow.",
            "LUMIERE": "The Cinematographer. Visual, technical, focused on image fidelity.",
            "DELPHI": "The Researcher. Fact-based, skeptical, focused on truth and data.",
            "ARGUS": "The Confidence Agent (Safety). Protective, cautious, focused on brand safety.",
            "ORPHEUS": "The Composer. Emotional, rhythmic, focused on soundscapes and harmony."
        }
        self.ontologies = self._load_ontologies()

    def _load_ontologies(self) -> Dict[str, str]:
        """Loads the Canon files to ground the agents."""
        mapping = {
            "ATLAS": "Copilot_Ontology.md",
            "APOLLO": "Director_Ontology.md",
            "LUMIERE": "Cinematographer_Ontology.md",
            "DELPHI": "Research_Agent_Ontology.md",
            "ARGUS": "Confidence_Agent_Ontology.md",
            "ORPHEUS": "Composer_Ontology.md"
        }
        loaded = {}
        base_path = os.path.join(os.path.dirname(__file__), "../Canon")
        for agent, filename in mapping.items():
            try:
                with open(os.path.join(base_path, filename), "r", encoding="utf-8") as f:
                    loaded[agent] = f.read()
            except FileNotFoundError:
                loaded[agent] = f"You are {agent}. (Ontology file missing)."
        return loaded

    def convene_meeting(self, topic: str):
        """Runs the round table simulation."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"Meeting_At_The_Round_Table_{timestamp}.md"
        filepath = os.path.join(self.output_dir, filename)

        print(f"🏰 Convening the Round Table: {filename}")
        
        # 1. Initialize the Transcript
        transcript = [
            f"# Meeting at the Round Table: {timestamp}",
            f"**Topic:** {topic}\n",
            "---"
        ]

        # 2. Atlas Opens
        opening_prompt = f"""
        You are [ATLAS].
        Your Ontology:\n{self.ontologies['ATLAS']}
        
        SITUATION: You have called a meeting of the High Council (The Round Table).
        TOPIC: {topic}
        
        TASK: Open the meeting. Welcome [APOLLO], [LUMIERE], [DELPHI], and [ARGUS].
        State the objective clearly. Keep it professional but commanding.
        """
        response = self.llm.invoke([HumanMessage(content=opening_prompt)])
        opening_stm = response.content
        transcript.append(f"### 🛡️ [ATLAS] (Opening)\n{opening_stm}\n")
        print(f"🛡️ [ATLAS]: {opening_stm[:100]}...")
        
        # history for context
        history = f"[ATLAS]: {opening_stm}\n"

        # 3. Round Robin Discussion
        # Order: Delphi (Research) -> Apollo (Vision) -> Lumiere (Visuals) -> Orpheus (Sound) -> Argus (Safety)
        speakers = ["DELPHI", "APOLLO", "LUMIERE", "ORPHEUS", "ARGUS"]
        
        for speaker in speakers:
            print(f"⏳ Waiting for {speaker}...")
            prompt = f"""
            You are [{speaker}].
            
            YOUR ONTOLOGY:
            {self.ontologies[speaker]}
            
            CURRENT CONVERSATION:
            {history}
            
            TASK: Respond to Atlas and the group regarding the topic: '{topic}'.
            Propose improvements or request tools that would help YOUR specific role.
            Maintain your persona (Skeptical for Delphi, Visionary for Apollo, etc.).
            """
            
            response = self.llm.invoke([HumanMessage(content=prompt)])
            stmt = response.content
            transcript.append(f"### 👤 [{speaker}]\n{stmt}\n")
            print(f"👤 [{speaker}]: {stmt[:100]}...")
            history += f"\n[{speaker}]: {stmt}\n"

        # 4. Atlas Closing
        closing_prompt = f"""
        You are [ATLAS].
        
        CONVERSATION SO FAR:
        {history}
        
        TASK: Synthesize the requests. Summarize the action items. Adjourn the meeting.
        """
        response = self.llm.invoke([HumanMessage(content=closing_prompt)])
        closing_stmt = response.content
        transcript.append(f"### 🛡️ [ATLAS] (Closing)\n{closing_stmt}\n")
        print(f"🛡️ [ATLAS]: {closing_stmt[:100]}...")

        # 5. Save
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(transcript))
        
        print(f"✅ Meeting Adjourned. Log saved to {filepath}")

if __name__ == "__main__":
    rt = RoundTable()
    rt.convene_meeting("Future Improvements and Tool Requests for the DeepAgents System")
