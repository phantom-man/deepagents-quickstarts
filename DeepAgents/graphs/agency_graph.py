"""
Main Orchestration Graph for DeepAgents.
Implements the Director -> Researcher -> Validator -> Director loop.
"""
# pylint: disable=no-name-in-module, import-outside-toplevel, unused-import, broad-exception-caught, unused-argument, wrong-import-position

# --- Path Setup to resolve 'DeepAgents' package ---
import sys
import os
try:
    # Add Repo Root to Path (One level up from 'graphs', two levels up?)
    # File is at DeepAgents/graphs/agency_graph.py
    # Repo root is ../../
    current_dir = os.path.dirname(os.path.abspath(__file__))
    deepagents_root = os.path.dirname(os.path.dirname(current_dir))
    if deepagents_root not in sys.path:
        sys.path.insert(0, deepagents_root)
except Exception:
    pass

import operator
import logging
import json
import re
from typing import Annotated, TypedDict, List, Literal, Union, Any, Optional

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic

# Import our Agents (as tools/nodes)
from DeepAgents.CommercialAgents.director_agent.agent import create_director_agent
from DeepAgents.CommercialAgents.research_agent.agent import run_research_task
from DeepAgents.CommercialAgents.confidence_agent.agent import create_confidence_agent
from DeepAgents.CommercialAgents.cinematographer_agent.agent import (
    create_cinematographer_agent,
)
from DeepAgents.CommercialAgents.composer_agent.agent import (
    run_composer_task,
    create_composer_agent,
)
from DeepAgents.editor_tools import merge_video_audio_logic

# Setup Logger
logger = logging.getLogger("DeepGraph")


# --- 1. The State (Shared Memory) ---
class AgentState(TypedDict):
    """The shared memory of the team."""

    # The conversation history (Standard LangGraph)
    messages: Annotated[List[BaseMessage], operator.add]

    # Structured Data
    directive: str  # The original user request
    director_plan: str  # The Output from Director (Text Plan)
    research_data: str  # The Output from Researcher
    validation_report: str  # The Output from Confidence Agent
    validation_score: int  # 0-10 Score
    validation_status: str  # "PENDING", "APPROVED", "REJECTED"

    # Production Assets
    video_assets: Annotated[List[str], operator.add]  # Path s(Strings) - APPEND Mode
    audio_assets: Annotated[List[str], operator.add]  # Path (Strings) - APPEND Mode
    final_output: str  # Final merged file path

    # Loop Control
    revision_count: int


# --- 2. The Config Schema (Dynamic Toggles in LangSmith) ---
class GraphConfig(TypedDict):
    """Configuration schema for the graph."""
    require_validation: bool
    max_revisions: int
    model_provider: Literal["Anthropic", "Google", "Replicate"]
    # Production Toggles
    skip_production: bool  # If True, stops after planning
    parallel_production: bool  # If True, runs Audio/Video same time
    merge_output: bool  # If True, runs the Editor
    output_filename: str  # Configurable filename


# --- 3. The Nodes (Workers) ---


async def director_node(state: AgentState, config: RunnableConfig):
    """
    The Director plans the content.
    If returning from a rejection, it refines the plan based on critique.
    """
    logger.info("🎬 NODE: Director")

    # extracting config (optional usage)
    conf = config.get("configurable", {})
    provider = conf.get("model_provider", "Anthropic")

    # 1. Get Context
    directive = state.get("directive", "")
    critique = state.get("validation_report", "")
    plan = state.get("director_plan", "")

    # 2. Check if this is a Revision
    revision_count = state.get("revision_count", 0)

    messages = []
    if revision_count > 0 and critique:
        # Rejection refinement
        prompt = (
            "Your previous plan was REJECTED by the Audit Agent.\n"
            f"CRITIQUE: {critique}\n"
            f"ORIGINAL PLAN: {plan}\n\n"
            "TASK: Rewrite the Creative Directive to address the critique. "
            f"Maintain the original goal: {directive}"
        )
        messages = [HumanMessage(content=prompt)]
    else:
        # Fresh Plan
        # If we have messages in state, use them, otherwise use directive
        if not directive and state["messages"]:
            last_msg = state["messages"][-1]
            if hasattr(last_msg, "content"):
                directive = last_msg.content
            elif isinstance(last_msg, dict):
                directive = last_msg.get("content", "")
            else:
                directive = str(last_msg)

        prompt = f"Create a Creative Directive for: {directive}"
        messages = [HumanMessage(content=prompt)]

    # 3. Invoke Director Agent
    # We use the factory we debugged earlier
    agent = create_director_agent(provider=provider)

    # Convert 'agent' (CompiledGraph) to a simple invoker or run it
    # Director agent expects {"messages": []}
    response_state = await agent.ainvoke({"messages": messages})

    # Extract AIMessage
    final_msg = response_state["messages"][-1]

    # Robust extraction (Handle both AIMessage object and serialized dict)
    if hasattr(final_msg, "content"):
        content = final_msg.content
    elif isinstance(final_msg, dict):
        content = final_msg.get("content", "")
    else:
        content = str(final_msg)

    return {
        "messages": [final_msg],
        "director_plan": content,
        "directive": directive,  # Persist if empty
    }


async def researcher_node(state: AgentState, config: RunnableConfig):
    """
    The Researcher verifies the Director's plan.
    """
    logger.info("🔎 NODE: Researcher")
    plan = state.get("director_plan", "")

    # Call the Tool Function directly (Zero Touch wrapper)
    # Ideally, we should wrap this in an Agent loop if it was complex,
    # but run_research_task handles it.

    # We pass the plan as the "Topic" to research/verify
    # "Research the validity of this plan: ..."
    research_query = (
        "Verify the facts and feasibility of this Creative Directive:\n"
        f"{plan}"
    )

    result = run_research_task(research_query)

    return {
        "messages": [AIMessage(content=f"Research Report:\n{result}")],
        "research_data": result,
    }


def _parse_validation_output(content: Union[str, List[Any]]) -> tuple[str, int, str]:
    """
    Parses the output from the Confidence Agent.
    Handles String or List[Block] content types.
    Returns: (status, score, clean_text_summary)
    """
    # 1. Extract Clean Text
    text_content = ""
    if isinstance(content, str):
        text_content = content
    elif isinstance(content, list):
        # Handle Anthropic/LangChain content blocks
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif isinstance(block, str):
                parts.append(block)
            elif not isinstance(block, dict) and hasattr(block, "text"):  # Object style
                parts.append(block.text)
        text_content = "\n".join(parts)
    else:
        text_content = str(content)

    status = "REJECTED"
    score = 0

    try:
        # Attempt to find JSON blob if mixed with text
        json_match = re.search(r"\{.*\}", text_content, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0))
            status = data.get("status", "REJECTED").upper()
            score = int(float(data.get("score", 0)) * 10)  # Scale 0-1 to 0-10
        else:
            # Fallback for text
            upper_con = text_content.upper()
            if "ACCEPTED" in upper_con or "APPROVED" in upper_con:
                status = "APPROVED"
                score = 8
            # Heuristic for "Implicit Approval" in narrative reviews
            elif "WELL-SUITED" in upper_con or "ALIGNS WELL" in upper_con:
                status = "APPROVED"
                score = 8

    except Exception as e:
        logger.warning("Failed to parse Validation JSON: %s", e)

    return status, score, text_content


async def validator_node(state: AgentState, config: RunnableConfig):
    """
    The Confidence Agent audits the Plan + Research.
    """
    logger.info("⚖️ NODE: Validator")

    plan = state.get("director_plan", "")
    research = state.get("research_data", "")

    audit_context = f"PLAN: {plan}\n\nRESEARCH/FACTS: {research}"

    # Create Agent using Factory (ensures Hub Prompts + Tools)
    agent = create_confidence_agent(provider="Anthropic")

    # Construct input message for the agent
    msg = HumanMessage(content=f"Verify this verification request:\n{audit_context}")

    response_state = await agent.ainvoke({"messages": [msg]})
    final_msg = response_state["messages"][-1]
    # Parse output using robust helper
    status, score, clean_text = _parse_validation_output(final_msg.content)
    return {
        "messages": [final_msg],
        "validation_report": clean_text,
        "validation_status": status,
        "validation_score": score,
        "revision_count": state.get("revision_count", 0) + 1,
    }



# --- 4. The Router (Conditional Edges) ---


def validation_router(
    state: AgentState, config: RunnableConfig
) -> Union[
    Literal["director", "cinematographer", "composer", "production_branch", "end"],
    List[str],
]:
    """
    Decides the next step based on validation status and configuration.
    """
    logger.info("🔀 ROUTER: Validation Check")

    # 1. Read Config
    conf = config.get("configurable", {})
    require_validation = conf.get("require_validation", True)
    max_revs = conf.get("max_revisions", 3)
    skip_prod = conf.get("skip_production", False)
    parallel = conf.get("parallel_production", True)

    # 2. Check Loop Limits
    revs = state.get("revision_count", 0)
    if revs > max_revs:
        # Force exit to avoid infinite loop
        logger.warning("⚠️ Max revisions (%s) reached. Forcing proceed.", max_revs)
        if skip_prod:
            return "end"
        return ["cinematographer", "composer"] if parallel else "cinematographer"

    # 3. Check Status
    # Default to SKIPPED if validator was removed
    status = state.get("validation_status", "SKIPPED")

    # If valid logic says REJECTED, go back
    # Implicitly approve SKIPPED status
    if require_validation and status != "APPROVED" and status != "SKIPPED":
        logger.info("❌ Plan Rejected. sending back to Director.")
        return "director"

    # Proceed to Production
    logger.info("✅ Plan Approved (or Skipped validation). Proceeding to Production.")

    if skip_prod:
        return "end"

    # Parallel branch logic is handled by returning list in LangGraph usually,
    # but here we use a conditional map to a 'fork' node or router returns multiple?
    # LangGraph Configurable Edges return a single node key usually.
    # To run parallel, we point to multiple nodes if the framework supports it
    # (StateGraph does via mapping).

    # Actually, to run parallel in LangGraph:
    # We return a list of nodes from the router, OR we point to a "parallel_scheduler" node.
    # But standard way: Router -> [Node A, Node B]

    if parallel:
        return ["cinematographer", "composer"]

    # Serial: Cine then Composer
    return "cinematographer"  # which points to composer


def cine_router(state: AgentState, config: RunnableConfig) -> Literal["composer", "editor"]:
    """Decides if Cine goes to Composer (Serial) or Editor (Parallel)."""
    conf = config.get("configurable", {})
    parallel = conf.get("parallel_production", True)
    if parallel:
        return "editor"
    return "composer"


# --- Production Nodes ---


async def cinematographer_node(state: AgentState, config: RunnableConfig):
    """
    Executes the Visual Directive.
    """
    logger.info("🎥 NODE: Cinematographer")
    plan = state.get("director_plan", "")

    # Safety: Ensure plan is string
    if not isinstance(plan, str):
        if isinstance(plan, list):
            # Try to join or take last
            plan = str(plan[-1]) if plan else ""
        else:
            plan = str(plan)

    # We invoke the agent generator logic
    # But for graph simplicity, we use the synchronous helper tailored for this
    # run_cinematographer_task(plan) returns a string path or error
    try:
        from DeepAgents.CommercialAgents.cinematographer_agent.agent import (
            run_cinematographer_task,
        )

        # Parse mode from plan? Or just basic
        # We pass the WHOLE plan. The Agent (LLM) parses it.
        result = run_cinematographer_task(plan)

        # Extract path
        # Heuristic: Check for 'Saved: path' or return raw
        path = (
            result
            if "Artifacts" in result or "C:" in result or "http" in result
            else None
        )

        assets = []
        if path:
            # Clean up the string to get just the path if verbose

            match = re.search(
                r"(https?://[^\s\)]+|[A-Za-z]:\\[^\s\)]+|/Users/[^\s\)]+|Artifacts[^\s\)]+)", result
            )
            if match:
                clean_path = match.group(1)
                assets.append(clean_path)
            else:
                assets.append(path)  # Hope for best

        return {
            "messages": [AIMessage(content=f"Visuals Created: {result}")],
            "video_assets": assets,
        }
    except Exception as e:
        logger.error("Cinematography Failed: %s", e)
        return {"messages": [AIMessage(content=f"Visual Error: {e}")]}


async def composer_node(state: AgentState, config: RunnableConfig):
    """
    Executes the Audio Directive.
    """
    logger.info("🎻 NODE: Composer")
    plan = state.get("director_plan", "")

    # Safety: Ensure plan is string
    if not isinstance(plan, str):
        if isinstance(plan, list):
            # Try to join or take last
            plan = str(plan[-1]) if plan else ""
        else:
            plan = str(plan)

    try:
        result = run_composer_task(plan)
        # Ensure result is string
        result = str(result)
        assets = []
        # Heuristic extraction
        match = re.search(
            r"(https?://[^\s\)]+|[A-Za-z]:\\[^\s\)]+|/Users/[^\s\)]+|Artifacts[^\s\)]+)", result
        )
        if match:
            assets.append(match.group(1))

        return {
            "messages": [AIMessage(content=f"Audio Created: {result}")],
            "audio_assets": assets,
        }
    except Exception as e:
        logger.error("Composition Failed: %s", e)
        return {"messages": [AIMessage(content=f"Audio Error: {e}")]}


async def editor_node(state: AgentState, config: RunnableConfig):
    """
    Merges the assets.
    """
    logger.info("✂️ NODE: Editor (Merge)")

    # Read Config
    conf = config.get("configurable", {})
    do_merge = conf.get("merge_output", True)
    fname = conf.get("output_filename", "final_cut.mp4")

    if not do_merge:
        return {"messages": [AIMessage(content="Merge skipped by config.")]}

    v_assets = state.get("video_assets", [])
    a_assets = state.get("audio_assets", [])

    if not v_assets or not a_assets:
        return {
            "messages": [
                AIMessage(content="Skipping Merge: Missing Video or Audio assets.")
            ]
        }

    # Take the latest
    # Since we use 'operator.add' (list concat), we might have multiples if looped.
    # Strategy: Use ALL videos (sequence) and LAST audio.

    final_audio = a_assets[-1]

    # Filter for valid strings
    valid_videos = [v for v in v_assets if isinstance(v, str) and len(v) > 3]

    if not valid_videos:
        return {
            "messages": [AIMessage(content="Skipping Merge: No valid video paths.")]
        }

    res_path = merge_video_audio_logic(
        video_paths=valid_videos, audio_path=final_audio, output_name=fname
    )

    return {
        "messages": [AIMessage(content=f"FINAL CUT: {res_path}")],
        "final_output": res_path,
    }


# --- 5. The Graph (Assembly) ---

workflow = StateGraph(AgentState)

# Nodes
workflow.add_node("director", director_node)
# workflow.add_node("researcher", researcher_node) # SKIPPING RESEARCHER
# workflow.add_node("validator", validator_node) # SKIPPING VALIDATOR
workflow.add_node("cinematographer", cinematographer_node)
workflow.add_node("composer", composer_node)
workflow.add_node("editor", editor_node)

# Edges
workflow.set_entry_point("director")
# workflow.add_edge("director", "researcher") # SKIPPING RESEARCHER
# workflow.add_edge("researcher", "validator") # SKIPPING VALIDATOR

# Conditional Edge (Router)
workflow.add_conditional_edges(
    "director", # Direct to Validation Router (which skips to Production)
    validation_router,
    # path_map dictionary used to map return values to node names
    {

        "director": "director",
        "cinematographer": "cinematographer",
        "composer": "composer",
        "end": END,
        # Handling the list output for parallel execution requires mapping individual keys
        # But 'add_conditional_edges' expects specific structure for standard execution.
        # When returning a list ["A", "B"], LangGraph (v0.1+) automatically fans out.
        # We just need to ensure the targets exist in the graph.
        "production_branch": "cinematographer",
    },
)

# Parallel Convergence
# If Parallel, Cine -> Editor. If Serial, Cine -> Composer -> Editor.
workflow.add_conditional_edges(
    "cinematographer",
    cine_router,
    {"composer": "composer", "editor": "editor"}
)
workflow.add_edge("composer", "editor")

# Final
workflow.add_edge("editor", END)

# Compile for execution
app = workflow.compile()
