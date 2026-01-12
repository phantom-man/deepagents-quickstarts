
import os
import sys
from dotenv import load_dotenv
from langgraph.graph import StateGraph, MessagesState, END
from langchain_core.messages import AIMessage

# Ensure root (one level up) is in path so "DeepAgents" package resolves correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from DeepAgents.CommercialAgents.director_agent.agent import create_director_agent
    from DeepAgents.CommercialAgents.research_agent.agent import create_research_agent
    from DeepAgents.CommercialAgents.composer_agent.agent import create_composer_agent
    from DeepAgents.CommercialAgents.confidence_agent.agent import create_confidence_agent
    from DeepAgents.CommercialAgents.cinematographer_agent.agent import create_cinematographer_agent
except ImportError:
    # Double check path if failed
    print(f"Import failed. Path: {sys.path}")
    raise

load_dotenv()

# --- Graph Factory Wrappers (To prevent startup crashes) ---
def safe_create(name, factory_func, **kwargs):
    try:
        return factory_func(**kwargs)
    except Exception as e:
        print(f"CRITICAL ERROR creating graph '{name}': {e}")
        # Dummy Graph
        from langgraph.graph import StateGraph
        def error_node(state): return {"messages": [f"Error loading {name}: {e}"]}
        bg = StateGraph(dict)
        bg.add_node("error", error_node)
        bg.set_entry_point("error")
        return bg.compile()

# --- Initialize Graphs ---

# 1. Director
director_graph = safe_create(
    "Director", 
    create_director_agent, 
    provider="Anthropic", 
    model_name="claude-3-haiku-20240307",
    checkpointer=None
)

# 2. Researcher
# Expects: model_name, provider
researcher_graph = safe_create(
    "Researcher",
    create_research_agent,
    provider="Anthropic", 
    model_name="claude-3-haiku-20240307"
)

# 3. Composer
# Expects: model_config (dict)
# Note: create_composer_agent args might differ. Let's use kwargs carefully.
# Based on file: def create_composer_agent(model_config=None, brain=None, ... )
composer_graph = safe_create(
    "Composer",
    create_composer_agent,
    model_config={"provider": "Anthropic", "model": "claude-3-haiku-20240307"}
)

# 4. Confidence
# Expects: model_name, provider
confidence_graph = safe_create(
    "Confidence",
    create_confidence_agent,
    provider="Anthropic",
    model_name="claude-3-haiku-20240307"
)

# 5. Cinematographer
# Custom wrapper required because this agent returns a Generator, not a Graph.
def _create_cinematographer_wrapper():
    try:
        # 1. Initialize the Generator Function
        cinema_func = create_cinematographer_agent(
            model_config={
                "provider": "Anthropic", 
                "model": "claude-3-haiku-20240307",
                "image_provider": "Google",
                "video_provider": "Replicate" 
            }
        )

        # 2. Define the Graph Node
        def run_cinema_node(state: MessagesState):
            # Check if messages exist
            if not state.get("messages"):
                return {"messages": [AIMessage(content="No input provided.")]}
            
            user_input = state["messages"][-1].content
            final_output = []
            
            # Consume the generator
            # run_agent yields (type, content)
            # Default args for cinema: mode="storyboard"
            for msg_type, content in cinema_func(input_text=user_input):
                if msg_type == "output":
                    final_output.append(content)
                # We ignore 'thinking' messages for the final state output
            
            result_text = "\n\n".join(final_output) if final_output else "No output generated."
            return {"messages": [AIMessage(content=result_text)]}

        # 3. Build Graph
        builder = StateGraph(MessagesState)
        builder.add_node("cinematographer", run_cinema_node)
        builder.set_entry_point("cinematographer")
        builder.add_edge("cinematographer", END)
        return builder.compile()
        
    except Exception as e:
        print(f"FAILED to wrap Cinematographer: {e}")
        # Fallback error graph
        def err_node(s): return {"messages": [AIMessage(content=f"Cinematographer Failed: {e}")]}
        g = StateGraph(MessagesState)
        g.add_node("error", err_node)
        g.set_entry_point("error")
        return g.compile()

cinematographer_graph = _create_cinematographer_wrapper()

# Fallback: Expose director as 'graph' for legacy/default config support
# graph = director_graph

