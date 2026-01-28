"""
LangGraph Application Entry Point - Lazy Loading Edition

This module uses lazy initialization to avoid slow startup times.
Graphs are only created when first accessed, not at import time.
"""

import os
import sys
from functools import lru_cache

from dotenv import load_dotenv

# Ensure root (one level up) is in path so "DeepAgents" package resolves correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv()

# --- Lazy Import Helpers ---
# These defer heavy imports until actually needed


@lru_cache(maxsize=1)
def _get_langgraph_imports():
    """Lazy load LangGraph components."""
    from langchain_core.messages import AIMessage
    from langgraph.graph import END, MessagesState, StateGraph

    return StateGraph, MessagesState, END, AIMessage


@lru_cache(maxsize=1)
def _get_system_config():
    """Lazy load SystemConfiguration."""
    from DeepAgents.system_config import SystemConfiguration

    return SystemConfiguration()


@lru_cache(maxsize=1)
def _get_agent_factories():
    """Lazy load all agent factory functions."""
    try:
        from DeepAgents.CommercialAgents.cinematographer_agent.agent import (
            create_cinematographer_agent,
        )
        from DeepAgents.CommercialAgents.composer_agent.agent import (
            create_composer_agent,
        )
        from DeepAgents.CommercialAgents.confidence_agent.agent import (
            create_confidence_agent,
        )
        from DeepAgents.CommercialAgents.director_agent.agent import (
            create_director_agent,
        )
        from DeepAgents.CommercialAgents.research_agent.agent import (
            create_research_agent,
        )

        return {
            "director": create_director_agent,
            "research": create_research_agent,
            "composer": create_composer_agent,
            "confidence": create_confidence_agent,
            "cinematographer": create_cinematographer_agent,
        }
    except ImportError as e:
        print(f"Import failed. Path: {sys.path}. Error: {e}")
        raise


# --- Graph Factory Wrappers (To prevent startup crashes) ---
def _safe_create(name, factory_func, **kwargs):
    """Safely create a graph, returning an error graph on failure."""
    StateGraph, MessagesState, END, AIMessage = _get_langgraph_imports()
    try:
        return factory_func(**kwargs)
    except Exception as e:
        err_msg = str(e)
        print(f"CRITICAL ERROR creating graph '{name}': {err_msg}")

        # Dummy Graph
        def error_node(state):
            return {"messages": [AIMessage(content=f"Error loading {name}: {err_msg}")]}

        bg = StateGraph(MessagesState)
        bg.add_node("error", error_node)
        bg.set_entry_point("error")
        return bg.compile()


# --- Lazy Graph Factories ---
# Each graph is created ONLY when first accessed via the property


@lru_cache(maxsize=1)
def _create_director_graph():
    """Lazy factory for Director graph."""
    sys_conf = _get_system_config()
    factories = _get_agent_factories()
    d_prov, d_mod = sys_conf.get_agent_params("Director")
    return _safe_create(
        "Director",
        factories["director"],
        provider=d_prov,
        model_name=d_mod,
        checkpointer=None,
    )


@lru_cache(maxsize=1)
def _create_composer_graph():
    """Lazy factory for Composer graph (wrapped in StateGraph)."""
    StateGraph, MessagesState, END, AIMessage = _get_langgraph_imports()
    sys_conf = _get_system_config()
    factories = _get_agent_factories()

    try:
        c_prov, c_mod = sys_conf.get_agent_params("Composer")

        # This returns a RunnableLambda, NOT a Graph
        composer_runnable = factories["composer"](
            model_config={"provider": c_prov, "model": c_mod}
        )

        def composer_node_adapter(state):
            # RunnableLambda expects a dict, which MessagesState is compatible with
            return composer_runnable.invoke(state)

        # Build Graph
        builder = StateGraph(MessagesState)
        builder.add_node("composer", composer_node_adapter)
        builder.set_entry_point("composer")
        builder.add_edge("composer", END)

        return builder.compile()

    except Exception as e:
        err_msg = str(e)
        print(f"FAILED to wrap Composer: {err_msg}")

        def err_node(state):
            return {"messages": [AIMessage(content=f"Composer Failed: {err_msg}")]}

        g = StateGraph(MessagesState)
        g.add_node("error", err_node)
        g.set_entry_point("error")
        return g.compile()


@lru_cache(maxsize=1)
def _create_confidence_graph():
    """Lazy factory for Confidence graph."""
    sys_conf = _get_system_config()
    factories = _get_agent_factories()
    conf_prov, conf_mod = sys_conf.get_agent_params("Confidence")
    return _safe_create(
        "Confidence", factories["confidence"], provider=conf_prov, model_name=conf_mod
    )


@lru_cache(maxsize=1)
def _create_cinematographer_graph():
    """Lazy factory for Cinematographer graph (wrapped in StateGraph)."""
    StateGraph, MessagesState, END, AIMessage = _get_langgraph_imports()
    factories = _get_agent_factories()

    try:
        # Get the cinematographer function
        cinema_func = factories["cinematographer"](model_config=None)

        def run_cinema_node(state):
            if not state.get("messages"):
                return {"messages": [AIMessage(content="No input provided.")]}

            user_input = state["messages"][-1].content
            final_output = []

            # Consume the generator
            for msg_type, content in cinema_func(input_text=user_input):
                if msg_type == "output":
                    final_output.append(content)

            result_text = (
                "\n\n".join(final_output) if final_output else "No output generated."
            )
            return {"messages": [AIMessage(content=result_text)]}

        # Build Graph
        builder = StateGraph(MessagesState)
        builder.add_node("cinematographer", run_cinema_node)
        builder.set_entry_point("cinematographer")
        builder.add_edge("cinematographer", END)
        return builder.compile()

    except Exception as e:
        err_msg = str(e)
        print(f"FAILED to wrap Cinematographer: {err_msg}")

        def err_node(state):
            return {
                "messages": [AIMessage(content=f"Cinematographer Failed: {err_msg}")]
            }

        g = StateGraph(MessagesState)
        g.add_node("error", err_node)
        g.set_entry_point("error")
        return g.compile()


# --- Module-Level Graph Accessors ---
# These call the lazy factories which use @lru_cache to only create once.
# Note: LangGraph CLI will still trigger creation during startup introspection,
# but subsequent accesses reuse the cached instances.

director_graph = _create_director_graph()
composer_graph = _create_composer_graph()
confidence_graph = _create_confidence_graph()
cinematographer_graph = _create_cinematographer_graph()
