import os
import sys
import uuid
from dotenv import load_dotenv
# from langchain_anthropic import ChatAnthropic
from langchain_google_vertexai import ChatVertexAI
from langchain.tools import tool
from deepagents import create_deep_agent

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from DeepAgents.CommercialAgents.confidence_agent.prompts import CONFIDENCE_INSTRUCTIONS
from DeepAgents.CommercialAgents.research_agent.agent import run_research_task
from DeepAgents.agent_brain import AgentMemory

# Load environment variables
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.env"))
load_dotenv(env_path)

@tool
def consult_research_agent(topic: str) -> str:
    """Consults the Research Agent to gather evidence, fact-check claims, or retrieve detailed information about a specific topic.
    Use this to verify statements found in the content you are auditing.
    """
    print(f"\\n⚖️ Confidence Agent > 📞 Calling Research Agent to verify: {topic}")
    result = run_research_task(topic)
    if result:
        return result
    return "Research Agent found no conclusive evidence."

def create_confidence_agent():
    """Creates and returns the Confidence Agent."""
    
    # Initialize the model
    # Switching to Vertex AI for consistency and reliability
    model = ChatVertexAI(
        model="gemini-2.0-flash-exp", 
        temperature=0.0
    )
    
    # Create the Deep Agent
    agent = create_deep_agent(
        model=model,
        tools=[consult_research_agent], 
        system_prompt=CONFIDENCE_INSTRUCTIONS,
    )
    
    return agent

def run_confidence_audit(content_to_audit: str):
    """Executes a confidence audit with memory and research integration."""
    memory = AgentMemory()
    
    print(f"\\n⚖️ Confidence Audit Task: Auditing content...")
    
    # 1. BRAIN CHECK: Have we audited similar content or established rules?
    print("🧠 Checking Memory for Audit Rules/History...")
    try:
        past_audits = memory.recall("audit rules for commercial content", limit=2)
        context_str = ""
        if past_audits:
            print(f"💡 Found past audit insights!")
            for res in past_audits:
                 if hasattr(res, "text"):
                     context_str += f"- {res.text[:300]}...\n"
                     print(f"   Context: {res.text[:100]}...")
    except Exception as e:
        print(f"⚠️ Memory Warning: {e}")
        context_str = ""

    # 2. CREATE AGENT
    agent = create_confidence_agent()
    
    # 3. RUN AGENT
    # We augment the prompt with memory context
    initial_msg = f"Audit the following content for accuracy, safety, and brand alignment. Content: '{content_to_audit}'"
    if context_str:
        initial_msg += f"\n\nCONSIDER PAST AUDIT INSIGHTS:\n{context_str}"

    config = {"configurable": {"thread_id": f"confidence_{uuid.uuid4()}"}}
    print("🚀 Starting Audit Stream...")
    
    final_report = ""
    
    for event in agent.stream(
        {"messages": [("user", initial_msg)]}, 
        config=config
    ):
        for key in event:
            val = event[key]
            msgs = []
            if isinstance(val, dict) and "messages" in val:
                msgs = val["messages"]
                if hasattr(msgs, "value"): msgs = msgs.value
            elif hasattr(val, "messages"):
                msgs = val.messages
            
            if msgs and isinstance(msgs, list):
                msg = msgs[-1]
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                        for tc in msg.tool_calls:
                            print(f"👉 Tool Call: {tc['name']} ({tc['args']})")
                if hasattr(msg, "content") and msg.content:
                    final_report = msg.content

    # 4. MEMORIZE
    if final_report:
        print("\n🛡️ --- AUDIT REPORT ---")
        print(final_report)
        print("-----------------------")
        print(f"\n🧠 Memorizing Audit Decision...")
        memory.memorize(
            f"Audit Report on content '{content_to_audit[:50]}...': {final_report}", 
            "ConfidenceAgent",
            tags=["audit_report"]
        )
        print("✅ Audit stored in Long-Term Memory.")
        return final_report
    else:
        print("❌ No audit report produced.")
        return None

if __name__ == "__main__":
    print("Initializing Confidence Agent...")
    
    if len(sys.argv) > 1:
        # Check if arg is file or raw text
        arg = sys.argv[1]
        content = arg
        if os.path.exists(arg):
            try:
                with open(arg, 'r', encoding='utf-8') as f:
                    content = f.read()
            except:
                pass # Treat as raw text
        
        run_confidence_audit(content)
    else:
        print("Please provide content or a file path to audit.")
