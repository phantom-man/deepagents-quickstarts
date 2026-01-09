# pylint: disable=broad-exception-caught
# pylint: disable=invalid-name
"""
Copilot Agent Script.
The Engineer & Orchestrator Agent.
Responsible for maintaining the system, remembering architectural patterns,
and solving technical blockers.
"""
import os
import sys
import argparse
import logging
from typing import Optional, List
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_google_vertexai import ChatVertexAI

# Brain Integration
try:
    from agent_brain import AgentMemory, AgentComms
    # If run as script in root, this is fine if PYTHONPATH set
except ImportError:
    try:
        from DeepAgents.agent_brain import AgentMemory, AgentComms
    except ImportError:
        print("❌ Could not import agent_brain.")
        sys.exit(1)

# Load Environment
load_dotenv()

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CopilotAgent:
    """
    The Engineer & Orchestrator Agent.
    Responsible for maintaining the system, remembering architectural patterns,
    and solving technical blockers.
    """
    def __init__(self):
        print("🔧 --- INITIALIZING COPILOT AGENT ---")
        self.memory = AgentMemory()
        self.comms = AgentComms(password="d1204l0723")
        self.comms_active = self.comms.connect()
        self.role = "Copilot"
        self.ontology = self.load_ontology()

        # Initialize LLM (Engineer Brain)
        try:
            self.llm = ChatVertexAI(
                model="gemini-2.0-flash-001",
                temperature=0.2,  # Lower temperature for engineering precision
                location="us-central1"
            )
        except Exception as e:
            print(f"⚠️ LLM Init Failed: {e}")
            self.llm = None

    def load_ontology(self) -> str:
        """Loads the Copilot Ontology."""
        try:
            path = os.path.join(os.path.dirname(__file__), "Canon", "Copilot_Ontology.md")
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except OSError:
            return "Ontology Check Failed."

    def recall_technical_context(self, query: str) -> List[str]:
        """Retrieves technical constraints or past solutions."""
        print(f"🔍 Searching Engineering Logs for: '{query}'...")
        memories = self.memory.recall(query, limit=5)
        if memories:
            print(f"💡 Found {len(memories)} relevant value(s).")
            # Handle different return types if memory backend changed (text vs dict)
            results = []
            for m in memories:
                if isinstance(m, dict):
                    results.append(m.get('text', ''))
                elif hasattr(m, 'text'):
                    results.append(m.text)
                else:
                    results.append(str(m))
            return results
        return []

    def log_learning(self, insight: str, tags: Optional[List[str]] = None) -> None:
        """
        The 'Learning Loop': Stores a permanent record of a technical discovery.
        """
        if not tags:
            tags = ["engineering", "fix"]

        full_text = f"ENGINEERING LOG: {insight}"
        success = self.memory.memorize(full_text, self.role, tags)
        if success:
            print(f"💾 Knowledge Secured: '{insight[:50]}...'")
        else:
            print("❌ Failed to secure knowledge.")

    def analyze_situation(self, problem_statement: str) -> Optional[str]:
        """Consults Memory + Ontology to propose a solution."""
        recalled = self.recall_technical_context(problem_statement)
        context_str = "\n".join([f"- {m}" for m in recalled])

        prompt = f"""
        You are the **Copilot (Engineer Agent)**.
        
        **YOUR ONTOLOGY:**
        {self.ontology}
        
        **PROJECT MEMORY (Relevant Logs):**
        {context_str if context_str else "No specific past records found."}
        
        **CURRENT PROBLEM:**
        {problem_statement}
        
        **TASK:**
        Analyze the problem based on your Ontology and Memory.
        Provide a technical solution or architectural directive.
        """

        if self.llm:
            print("🤔 Analyzing architecture...")
            response = self.llm.invoke([HumanMessage(content=prompt)])
            content_str = str(response.content)
            print(f"\n🛠️ ENGINEERING DIRECTIVE:\n{content_str}\n")
            return content_str

        print("⚠️ Brain offline (LLM). Cannot analyze.")
        return None

    def check_messages(self) -> None:
        """Checks if other agents need help."""
        if not self.comms_active:
            return

        msgs = self.comms.receive_messages(self.role)
        if msgs:
            print(f"📩 Received {len(msgs)} requests.")
            for m in msgs:
                sender = m.get('sender', 'Unknown')
                content = m.get('content', '')
                print(f"   From {sender}: {content[:50]}...")
                # Here we could auto-solve, but for now just log it
                self.log_learning(f"Issue reported by {sender}: {content}", ["report"])

# CLI Interface for the "Self"
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Copilot Agent Interface")
    parser.add_argument("--learn", help="Log a new technical insight", type=str)
    parser.add_argument("--solve", help="Ask for engineering advice", type=str)
    parser.add_argument("--listen", help="Check for agent messages", action="store_true")

    args = parser.parse_args()

    bot = CopilotAgent()

    if args.learn:
        bot.log_learning(args.learn)

    if args.solve:
        bot.analyze_situation(args.solve)

    if args.listen:
        bot.check_messages()
