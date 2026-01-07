import os
import sys
import argparse
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_vertexai import ChatVertexAI

# Brain Integration
try:
    from agent_brain import AgentMemory, AgentComms
except ImportError:
    print("❌ Could not import agent_brain.")
    sys.exit(1)

# Load Environment
load_dotenv()

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
                temperature=0.2, # Lower temperature for engineering precision
                location="us-central1"
            )
        except Exception as e:
            print(f"⚠️ LLM Init Failed: {e}")
            self.llm = None

    def load_ontology(self):
        try:
            path = os.path.join(os.path.dirname(__file__), "Canon", "Copilot_Ontology.md")
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except:
            return "Ontology Check Failed."

    def recall_technical_context(self, query):
        """Retrieves technical constraints or past solutions."""
        print(f"🔍 Searching Engineering Logs for: '{query}'...")
        memories = self.memory.recall(query, limit=5)
        if memories:
            print(f"💡 Found {len(memories)} relevant value(s).")
            return [m['text'] for m in memories]
        return []

    def log_learning(self, insight, tags=None):
        """The 'Learning Loop': Stores a permanent record of a technical discovery."""
        if not tags: tags = ["engineering", "fix"]
        
        full_text = f"ENGINEERING LOG: {insight}"
        success = self.memory.memorize(full_text, self.role, tags)
        if success:
            print(f"💾 Knowledge Secured: '{insight[:50]}...'")
        else:
            print("❌ Failed to secure knowledge.")

    def analyze_situation(self, problem_statement):
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
            print(f"\n🛠️ ENGINEERING DIRECTIVE:\n{response.content}\n")
            return response.content
        else:
            print("⚠️ Brain offline (LLM). Cannot analyze.")
            return None

    def check_messages(self):
        """Checks if other agents need help."""
        if not self.comms_active: return
        
        msgs = self.comms.check_inbox(self.role)
        if msgs:
            print(f"📩 Received {len(msgs)} requests.")
            for m in msgs:
                print(f"   From {m['sender']}: {m['content'][:50]}...")
                # Here we could auto-solve, but for now just log it
                self.log_learning(f"Issue reported by {m['sender']}: {m['content']}", ["report"])

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
        
    if not (args.learn or args.solve or args.listen):
        print("Usage: Copilot.py --learn 'text' | --solve 'problem' | --listen")
