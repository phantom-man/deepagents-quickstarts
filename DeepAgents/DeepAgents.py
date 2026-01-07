import os
import sys
import time
from dotenv import load_dotenv
from langchain_google_vertexai import ChatVertexAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.tools.tavily_search import TavilySearchResults

# Import the new Brain components
try:
    from agent_brain import AgentMemory, AgentComms
except ImportError as e:
    print(f"❌ Could not import agent_brain: {e}")
    sys.exit(1)

# Load environment variables
load_dotenv()

def load_canonical_ontology(role_name):
    """Loads the ontology file for the specific agent role."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "Canon", f"{role_name}_Ontology.md")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"⚠️ Warning: Ontology for {role_name} not found at {path}")
        return ""

def run_director_agent(task_override=None):
    print("\n🎬 --- INITIALIZING DIRECTOR AGENT ---")
    
    # 1. Connect to the Brain
    print("🧠 Connecting to Local Brain...")
    brain = AgentMemory()
    comms = AgentComms(password="d1204l0723") # Using confirmed password
    comms_active = comms.connect()
    
    if comms_active:
        comms.setup_tables()
    
    # 2. Retrieve Context (Learning)
    # The Director checks memory for relevant lessons or style preferences before starting.
    # We query for general style or past mistakes.
    query = "style preferences and technical constraints"
    print(f"🔍 Recalling memories about: '{query}'...")
    memories = brain.recall(query, limit=3)
    
    memory_context = ""
    if memories:
        memory_list = [f"- {m.get('text', '')}" for m in memories]
        memory_context = "\n".join(memory_list)
        print(f"💡 Found {len(memories)} relevant memories:\n{memory_context}")
    else:
        print("🤷 No relevant memories found searching fresh.")

    # 3. Initialize LLM
    # Switched to VertexAI to leverage the authenticated ADC credentials
    llm = ChatVertexAI(
        model="gemini-2.0-flash-001",
        temperature=0.7,
        location="us-central1"
    )
    
    # Load Ontology
    ontology = load_canonical_ontology("Director")
    
    # 4. Define the Task
    task = task_override if task_override else "We need to conceive a short scene about a robot discovering a flower in a wasteland."
    
    # 5. Construct Prompt with Memory Injection
    system_content = f"""You are the **Director Agent**.
Your goal is to conceive creative scenes and give clear instructions to your crew (Cinematographer).

**YOUR ONTOLOGY (Philosophy):**
{ontology}

**YOUR LONG-TERM MEMORY (Lessons & Preferences):**
{memory_context if memory_context else "No prior memories available."}

**INSTRUCTIONS:**
1. Analyze the input task.
2. Incorporate any relevant "Memories" (e.g., if the user prefers sci-fi, lean into that).
3. Output a clear "Director's Treatment" of the scene.
4. Conclude with a specific directive for the 'Cinematographer'.
"""

    messages = [
        SystemMessage(content=system_content),
        HumanMessage(content=task)
    ]
    
    print(f"\n📢 Input Task: {task}")
    print("🤔 Director is thinking...")
    
    response = llm.invoke(messages)
    treatment = response.content
    print(f"\n🎬 Director's Vision:\n{treatment}")
    
    # 6. Store the Decision (Learning)
    brain.memorize(f"Director Decision for '{task}': {treatment[:100]}...", "Director", ["decision", "history"])
    
    # 7. Communicate (Telepathy)
    if comms_active:
        print("\n📡 Sending orders to Cinematographer...")
        comms.send_message("Director", "Cinematographer", treatment)
        print("✅ Orders sent successfully.")
    else:
        print("\n⚠️ Comms offline. Orders written to log only.")

if __name__ == "__main__":
    run_director_agent()
