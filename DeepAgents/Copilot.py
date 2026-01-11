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
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatReplicate

# Add Repo Root to Path
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

# Brain Integration
try:
    # pylint: disable=unused-import
    from agent_brain import AgentMemory, AgentComms
    # If run as script in root, this is fine if PYTHONPATH set
except ImportError:
    try:
        from DeepAgents.agent_brain import AgentMemory, AgentComms
    except ImportError:
        # Fallback to local memory manager if agent_brain is missing
        try:
             # pylint: disable=import-outside-toplevel
            from DeepAgents.memory_manager import AgentMemoryManager
        except ImportError:
            print("❌ Critical: Memory dependencies missing.")
            sys.exit(1)
        # Mock old classes if missing to prevent attribute errors
        AgentMemory = None # type: ignore
        AgentComms = None # type: ignore

# Load Environment
load_dotenv()

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CopilotAgent: # pylint: disable=too-many-instance-attributes
    """
    The Engineer & Orchestrator Agent.
    Responsible for maintaining the system, remembering architectural patterns,
    and solving technical blockers.
    """
    def __init__(self):
        print("🔧 --- INITIALIZING COPILOT AGENT ---")

        # Initialize Memory Manager
        # We prefer the robust AgentMemoryManager for learning logging
        try:
             # pylint: disable=import-outside-toplevel, redefined-outer-name
            from DeepAgents.memory_manager import AgentMemoryManager
            self.memory_manager = AgentMemoryManager("Copilot")
            self.learnings = self.memory_manager.recall_recent(limit=5)
            print(f"🧠 Memory Loaded:\n{self.learnings}")
        except ImportError as e:
            print(f"⚠️ Memory Manager Import Failed: {e}")
            self.memory_manager = None
            self.learnings = ""
        except Exception as e:
             print(f"⚠️ Memory Manager Init Failed: {e}")
             self.memory_manager = None
             self.learnings = ""

        # Legacy Brain Support (Optional)
        self.memory = None # Placeholder if legacy code references it
        self.comms = None
        self.comms_active = False

        if AgentComms:
            self.comms = AgentComms(password="d1204l0723")
            self.comms_active = self.comms.connect()

        self.role = "Copilot"
        self.ontology = self.load_ontology()

        # Initialize LLM (Engineer Brain)
        try:
            # Switched to Replicate (Llama 3 70B) per architectural decision 2026-01-10
            self.llm = ChatReplicate(
                model="meta/meta-llama-3-70b-instruct",
                model_kwargs={"temperature": 0.2, "max_length": 4096}
            )
        except Exception as e:
            print(f"⚠️ Replicate LLM Init Failed: {e}. Falling back to Google.")
            try:
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-1.5-pro-001",
                    temperature=0.2,
                    project=os.getenv("GOOGLE_CLOUD_PROJECT"),
                    location=os.getenv("GOOGLE_CLOUD_LOCATION")
                )
            except Exception as e2:
                 print(f"⚠️ Fallback LLM Init Failed: {e2}")
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
        if not self.memory_manager:
            return []
            
        print(f"🔍 Searching Engineering Logs for: '{query}'...")
        # Use Memory Manager's search_learnings (returns formatted string, we need list or just use string)
        # Actually search_learnings returns a string based on the code we saw.
        # But analyze_situation expects a list to join.
        # Let's adapt.
        
        # Access underlying knowledge store if possible, or parse string. 
        # Easier: Modify recall_technical_context to standard usage of memory_manager.
        
        # Reading memory_manager.py again: search_learnings returns " - Item \n - Item"
        # So we can just call it and split lines.
        results_str = self.memory_manager.search_learnings(query)
        if results_str:
            return [line.strip("- ") for line in results_str.strip().split("\n") if line.strip()]
        return []

    def log_learning(self, insight: str, tags: Optional[List[str]] = None) -> None:
        """
        The 'Learning Loop': Stores a permanent record of a technical discovery.
        """
        if not self.memory_manager:
            print("❌ Memory Manager not initialized. Cannot log.")
            return

        full_text = f"ENGINEERING LOG: {insight}"
        if tags:
             full_text += f" [Tags: {', '.join(tags)}]"
             
        try:
            self.memory_manager.record_learning(full_text)
            print(f"💾 Knowledge Secured: '{insight[:50]}...'")
        except Exception as e:
            print(f"❌ Failed to secure knowledge: {e}")

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
