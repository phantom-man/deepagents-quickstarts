import os
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage

# Load environment variables from .env file
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

# Verify keys are loaded (printing partial keys for security)
tavily_key = os.getenv("TAVILY_API_KEY")
google_project = os.getenv("GOOGLE_CLOUD_PROJECT")

# Optional: LangChain Tracing
if os.getenv("LANGCHAIN_TRACING_V2") == "true":
    print("LangChain Tracing is enabled.")

print(f"Google Project: {google_project}")

if not tavily_key:
    # Tavily is optional if we just want to chat, but good to check
    pass

# Load the Director Ontology
director_ontology = load_canonical_ontology("Director")
print(f"✅ Director Ontology Loaded ({len(director_ontology)} chars)")

try:
    # Initialize the Tavily Search Tool
    tool = TavilySearch(
        api_key=tavily_key,
        max_results=5,
        search_depth="advanced",
        include_answer=True,
        include_raw_content=True
    )

    # Initialize Gemini 3 Pro Preview (Director Agent)
    model = ChatGoogleGenerativeAI(
        model="gemini-3-pro-preview",
        temperature=0.7
    )

    # --- Director Mode ---
    print("\n--- Director Agent Initialized ---")
    
    # The Task (This would normally come from the user)
    task = "We need to conceive a short scene about a robot discovering a flower in a wasteland."

    # Construct the Prompt with Ontology Injection
    messages = [
        SystemMessage(content=f"You are the Director Agent.\n\n{director_ontology}"),
        HumanMessage(content=task)
    ]
    
    print(f"Input Task: {task}")
    print("Thinking...")
    
    response = model.invoke(messages)
    
    print("\n--- Director's Vision ---")
    print(response.content)

except Exception as e:
    print(f"Error: {e}")

    
        # Integrate: Use Gemini to process the search results
        print("\n--- Generating Summary with Gemini 3 Pro ---")
        context = "\n\n".join([f"Source: {r.get('url')}\nContent: {r.get('content')}" for r in results['results']])
        prompt = f"Based on the following search results, provide a concise summary of the latest AI news:\n\n{context}"

        # LangSmith Feature: Adding tags and metadata to the run
        response = model.invoke(
            prompt, 
            config={
                "tags": ["summary", "gemini"], 
                "metadata": {"context_length": len(context)}
            }
        )
        print(response.content)
    else:
        print("No results found from Tavily.")

except Exception as e:
    print(f"An error occurred: {e}")
