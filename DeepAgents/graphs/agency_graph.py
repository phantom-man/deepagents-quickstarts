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
from pathlib import Path
from typing import Annotated, TypedDict, List, Literal, Union, Any, Optional

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END
from langgraph.types import Command
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

from DeepAgents.system_config import SystemConfiguration
from DeepAgents.agent_brain import AgentComms

# Setup Logger
logger = logging.getLogger("DeepGraph")
sys_conf = SystemConfiguration()

# Global AgentComms for progress updates
_graph_comms = None

def _get_comms() -> AgentComms:
    """Get or create AgentComms instance for progress updates."""
    global _graph_comms
    if _graph_comms is None:
        _graph_comms = AgentComms()
        _graph_comms.connect()
    return _graph_comms

def _emit_progress(agent_name: str, status: str):
    """Emit progress update via AgentComms for GUI polling."""
    try:
        comms = _get_comms()
        comms.send_message(agent_name, "GUI", status)
    except Exception:
        pass  # Non-critical, don't fail if comms unavailable


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


def _parse_handoff(content: str) -> Optional[tuple[str, str]]:
    """
    Parse HANDOFF patterns from agent tool output.
    Returns (target_agent, directive) or None if no handoff.
    """
    import re
    # Pattern: HANDOFF:agent_name:directive
    match = re.search(r"HANDOFF:(director|researcher|validator|composer|cinematographer|editor|end):(.+)", content, re.IGNORECASE | re.DOTALL)
    if match:
        return (match.group(1).lower(), match.group(2).strip())
    return None


def _extract_handoffs_and_content(messages: List[Any]) -> tuple[List[tuple[str, str]], str]:
    """
    Extract handoffs and content from agent response messages.
    Returns (list of handoffs, combined content string).
    """
    handoffs = []
    content_parts = []
    
    for msg in messages:
        # Check for tool messages (ToolMessage contains tool output)
        if hasattr(msg, "type") and msg.type == "tool":
            tool_content = msg.content if hasattr(msg, "content") else str(msg)
            handoff = _parse_handoff(tool_content)
            if handoff:
                handoffs.append(handoff)
        elif hasattr(msg, "content"):
            # Collect AI message content
            raw = msg.content
            if isinstance(raw, list):
                for block in raw:
                    if isinstance(block, dict) and "text" in block:
                        content_parts.append(block["text"])
                    elif isinstance(block, str):
                        content_parts.append(block)
            elif isinstance(raw, str):
                content_parts.append(raw)
    
    final_content = "\n".join(content_parts) if content_parts else ""
    return handoffs, final_content


def _route_from_handoffs(
    handoffs: List[tuple[str, str]], 
    state_update: dict, 
    default_target: str,
    logger_context: str
) -> Command:
    """
    Common routing logic based on handoffs.
    Returns a Command with the appropriate goto target.
    """
    if handoffs:
        targets = [h[0] for h in handoffs]
        logger.info("[%s] Delegating to: %s", logger_context, targets)
        
        # Priority order for multiple handoffs
        if "end" in targets:
            return Command(update=state_update, goto=END)
        elif "director" in targets:
            return Command(update=state_update, goto="director")
        elif "validator" in targets:
            return Command(update=state_update, goto="validator")
        elif "researcher" in targets:
            return Command(update=state_update, goto="researcher")
        elif "cinematographer" in targets:
            return Command(update=state_update, goto="cinematographer")
        elif "composer" in targets:
            return Command(update=state_update, goto="composer")
        elif "editor" in targets:
            return Command(update=state_update, goto="editor")
    
    # Default routing
    logger.info("[%s] No handoff, routing to: %s", logger_context, default_target)
    if default_target == "end":
        return Command(update=state_update, goto=END)
    return Command(update=state_update, goto=default_target)


async def director_node(
    state: AgentState, config: RunnableConfig
) -> Command[Literal["director", "researcher", "validator", "cinematographer", "composer", "editor", "__end__"]]:
    """
    The Director plans the content and delegates to appropriate agents.
    Uses Command for dynamic routing based on tool calls.
    """
    logger.info("🎬 NODE: Director")
    _emit_progress("Director", "Starting creative planning...")

    conf = config.get("configurable", {})
    sys_prov, sys_model = sys_conf.get_agent_params("Director")
    provider = conf.get("model_provider", sys_prov)

    # 1. Get Context
    directive = state.get("directive", "")
    critique = state.get("validation_report", "")
    plan = state.get("director_plan", "")
    revision_count = state.get("revision_count", 0)
    video_assets = state.get("video_assets", []) or []
    audio_assets = state.get("audio_assets", []) or []

    # 2. Build prompt
    if revision_count > 0 and critique:
        prompt = (
            "Your previous plan was REJECTED by the Audit Agent.\n"
            f"CRITIQUE: {critique}\n"
            f"ORIGINAL PLAN: {plan}\n\n"
            "TASK: Rewrite the Creative Directive to address the critique. "
            f"Maintain the original goal: {directive}"
        )
    else:
        if not directive and state["messages"]:
            last_msg = state["messages"][-1]
            if hasattr(last_msg, "content"):
                directive = last_msg.content
            elif isinstance(last_msg, dict):
                directive = last_msg.get("content", "")
            else:
                directive = str(last_msg)
            prompt = directive

    base_directive = prompt

    def _summarize_assets(label: str, assets: List[str]) -> str:
        lines = []
        for idx, asset in enumerate(assets, 1):
            if not isinstance(asset, str):
                lines.append(f"{idx}. [invalid asset reference]")
                continue
            display = asset
            if asset.startswith("http"):
                display = asset
            else:
                try:
                    display = Path(asset).name
                except Exception:
                    display = asset
            lines.append(f"{idx}. {display}")
        return f"{label} ({len(assets)}):\n" + "\n".join(lines)

    progress_sections: List[str] = []
    outstanding: List[str] = []

    if video_assets:
        progress_sections.append(_summarize_assets("Video assets delivered", video_assets))
    else:
        outstanding.append("No video clips captured yet. Begin by delegating to the Cinematographer.")

    if audio_assets:
        progress_sections.append(_summarize_assets("Audio assets delivered", audio_assets))
    else:
        outstanding.append("Audio/Music not generated. Once visuals satisfy the directive, delegate to the Composer with explicit musical guidance.")

    if video_assets and audio_assets:
        outstanding.append("Video and audio assets are available. Delegate to the Editor with the exact asset references when ready to merge.")

    progress_text = ""
    if progress_sections:
        progress_text = "CURRENT DELIVERABLES:\n" + "\n\n".join(progress_sections) + "\n\n"
    if outstanding:
        progress_text += "OUTSTANDING WORK:\n" + "\n".join(f"- {item}" for item in outstanding) + "\n\n"

    control_prompt = (
        "DIRECTOR CONTROL PROTOCOL (MANDATORY):\n"
        "- Use your delegate_to_* tools to move work between agents.\n"
        "- Delegate to the Cinematographer ONE clip at a time; wait for their handoff before issuing the next assignment.\n"
        "- When visuals satisfy the plan, delegate_to_composer with a precise music directive referencing timing/energy.\n"
        "- Once both video_assets and audio_assets are populated, delegate_to_editor with the asset references or signal_task_complete if the workflow should end.\n"
        "- Do not assume automatic routing—explicitly choose the next agent every time."
    )

    prompt = (
        f"{control_prompt}\n\n"
        f"{progress_text}PRIMARY DIRECTIVE:\n{base_directive}"
    )

    # 3. Invoke Director Agent (with mesh tools)
    agent = create_director_agent(provider=provider)
    response_state = await agent.ainvoke({"messages": [HumanMessage(content=prompt)]})
    all_messages = response_state.get("messages", [])
    
    # 4. Parse handoffs and content
    handoffs, final_content = _extract_handoffs_and_content(all_messages)
    final_msg = all_messages[-1] if all_messages else AIMessage(content=final_content)

    state_update = {
        "messages": [final_msg],
        "director_plan": final_content,
        "directive": directive,
    }
    
    # 5. Route based on handoffs or default
    skip_prod = conf.get("skip_production", False)
    default_target = "end" if skip_prod else "cinematographer"
    
    return _route_from_handoffs(handoffs, state_update, default_target, "Director")


async def researcher_node(
    state: AgentState, config: RunnableConfig
) -> Command[Literal["director", "researcher", "validator", "cinematographer", "composer", "editor", "__end__"]]:
    """
    The Researcher verifies the Director's plan.
    Uses Command for dynamic routing.
    """
    logger.info("🔎 NODE: Researcher")
    _emit_progress("Researcher", "Researching and verifying facts...")
    plan = state.get("director_plan", "")

    research_query = (
        "Verify the facts and feasibility of this Creative Directive:\n" f"{plan}"
    )

    result = run_research_task(research_query)

    state_update = {
        "messages": [AIMessage(content=f"Research Report:\n{result}")],
        "research_data": result,
    }
    
    # Default: After research, go to validator for approval
    return _route_from_handoffs([], state_update, "validator", "Researcher")


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


async def validator_node(
    state: AgentState, config: RunnableConfig
) -> Command[Literal["director", "researcher", "validator", "cinematographer", "composer", "editor", "__end__"]]:
    """
    The Confidence Agent audits the Plan + Research.
    Uses Command for dynamic routing based on approval/rejection.
    """
    logger.info("⚖️ NODE: Validator")
    _emit_progress("Confidence", "Validating plan quality...")

    conf = config.get("configurable", {})
    max_revs = conf.get("max_revisions", 3)
    skip_prod = conf.get("skip_production", False)
    
    plan = state.get("director_plan", "")
    research = state.get("research_data", "")

    audit_context = f"PLAN: {plan}\n\nRESEARCH/FACTS: {research}"

    # Create Agent using Factory (ensures Hub Prompts + Tools)
    agent = create_confidence_agent(provider="Anthropic")

    msg = HumanMessage(content=f"Verify this verification request:\n{audit_context}")

    response_state = await agent.ainvoke({"messages": [msg]})
    final_msg = response_state["messages"][-1]
    
    # Parse output using robust helper
    status, score, clean_text = _parse_validation_output(final_msg.content)
    revision_count = state.get("revision_count", 0) + 1
    
    state_update = {
        "messages": [final_msg],
        "validation_report": clean_text,
        "validation_status": status,
        "validation_score": score,
        "revision_count": revision_count,
    }
    
    # Routing logic based on validation result
    if revision_count > max_revs:
        logger.warning("⚠️ Max revisions (%s) reached. Forcing proceed.", max_revs)
        default_target = "end" if skip_prod else "cinematographer"
        return _route_from_handoffs([], state_update, default_target, "Validator")
    
    if status == "REJECTED":
        logger.info("❌ Plan Rejected. Sending back to Director.")
        return Command(update=state_update, goto="director")
    
    # APPROVED or SKIPPED - proceed to production
    logger.info("✅ Plan Approved. Proceeding to Production.")
    default_target = "end" if skip_prod else "cinematographer"
    return _route_from_handoffs([], state_update, default_target, "Validator")


# --- 4. The Router (Conditional Edges) ---

# --- 4. LEGACY ROUTERS (Deprecated - Command pattern now handles routing) ---
# These are kept for reference but no longer used in the mesh architecture.

# def validation_router(...): # DEPRECATED - validator_node uses Command
# def cine_router(...): # DEPRECATED - cinematographer_node uses Command


# --- Production Nodes ---


async def cinematographer_node(
    state: AgentState, config: RunnableConfig
) -> Command[Literal["director", "researcher", "validator", "cinematographer", "composer", "editor", "__end__"]]:
    """
    Executes the Visual Directive.
    Uses Command for dynamic routing.
    Respects GUI configuration for model selection and parameters.
    """
    logger.info("[CINEMA] NODE: Cinematographer")
    
    # Check if cinematographer is enabled in config
    conf = config.get("configurable", {})
    if not conf.get("cinematographer_active", True):
        logger.info("[CINEMA] Skipped by configuration (inactive)")
        state_update = {
            "messages": [AIMessage(content="Cinematographer skipped (disabled in configuration)")]
        }
        handoff_reason = "Cinematographer is inactive. Decide whether to delegate to another agent or adjust the plan."
        return _route_from_handoffs([("director", handoff_reason)], state_update, "director", "Cinematographer")
    
    _emit_progress("Cinematographer", "Generating video assets...")
    plan = state.get("director_plan", "")

    # Safety: Ensure plan is string
    if not isinstance(plan, str):
        if isinstance(plan, list):
            plan = str(plan[-1]) if plan else ""
        else:
            plan = str(plan)

    # Get model configuration from GUI
    model_id = conf.get("cinematographer_model")
    model_params = conf.get("cinematographer_params", {})
    source_mode = conf.get("cinematographer_source", "model")

    if source_mode == "file":
        file_paths = conf.get("cinematographer_files") or []
        file_metadata = conf.get("cinematographer_file_metadata") or []
        assets = []
        summaries = []

        for idx, path in enumerate(file_paths, start=1):
            if not isinstance(path, str):
                continue
            normalized = os.path.normpath(path)
            if not os.path.exists(normalized):
                logger.warning("[CINEMA] Uploaded video missing on disk: %s", normalized)
                continue
            assets.append(normalized)
            meta = file_metadata[idx - 1] if idx - 1 < len(file_metadata) else {}
            parts = [f"Clip {idx}: {Path(normalized).name}"]
            if meta:
                duration = meta.get("duration_readable") or meta.get("duration_seconds")
                if duration:
                    parts.append(f"Duration {duration}")
                if meta.get("resolution"):
                    parts.append(f"Resolution {meta['resolution']}")
                if meta.get("fps"):
                    parts.append(f"FPS {meta['fps']}")
            summaries.append(" | ".join(parts))

        if not assets:
            logger.warning("[CINEMA] No valid uploaded videos found for pass-through mode")
            state_update = {
                "messages": [AIMessage(content="Cinematographer received uploaded mode but no valid video files were available.")],
                "video_assets": []
            }
            handoff_reason = "Uploaded video assets were missing. Provide corrected files or new visual guidance."
        else:
            summary_text = "\n".join(summaries) if summaries else "\n".join(assets)
            state_update = {
                "messages": [AIMessage(content=f"Using uploaded video assets ({len(assets)} clip(s)):\n{summary_text}")],
                "video_assets": assets,
            }
            handoff_reason = "Uploaded video assets are ready. Review them and decide whether to request additional clips or move on to audio."

        return _route_from_handoffs(
            [("director", handoff_reason)],
            state_update,
            "director",
            "Cinematographer"
        )
    
    try:
        from DeepAgents.CommercialAgents.cinematographer_agent.agent import (
            run_cinematographer_task,
        )

        # Pass model configuration to the task
        result = run_cinematographer_task(
            plan, 
            model_id=model_id,
            model_params=model_params
        )

        # Extract ALL video paths (support multi-segment generation)
        assets = []
        
        # Find all URLs and paths in result (supports multiple videos)
        url_matches = re.findall(r"(https?://[^\s\)\]\,]+)", result)
        path_matches = re.findall(
            r"([A-Za-z]:\\[^\s\)\]\,]+|/Users/[^\s\)\]\,]+|Artifacts[^\s\)\]\,]+)",
            result,
        )
        
        # Collect all unique paths (prefer URLs for cloud compatibility)
        seen = set()
        for url in url_matches:
            clean = url.rstrip(".,)")
            if clean not in seen:
                assets.append(clean)
                seen.add(clean)
        for path in path_matches:
            clean = path.rstrip(".,)")
            if clean not in seen:
                assets.append(clean)
                seen.add(clean)
        
        if assets:
            logger.info(f"Cinematographer produced {len(assets)} video asset(s)")
        else:
            # Fallback: try to use entire result if it looks like a path
            if "Artifacts" in result or "C:" in result or "http" in result:
                assets = [result]
                logger.warning("Using raw result as single video path")

        state_update = {
            "messages": [AIMessage(content=f"Visuals Created ({len(assets)} segments): {result}")],
            "video_assets": assets,
        }

        handoff_reason = (
            "Cinematographer delivered the requested video segments. Review coverage, then either request the next shot or delegate to the Composer."
        )
        return _route_from_handoffs([("director", handoff_reason)], state_update, "director", "Cinematographer")
        
    except Exception as e:
        logger.error("Cinematography Failed: %s", e)
        state_update = {"messages": [AIMessage(content=f"Visual Error: {e}")]}
        handoff_reason = "Cinematographer encountered an error. Provide revised instructions or choose the next action."
        return _route_from_handoffs([("director", handoff_reason)], state_update, "director", "Cinematographer")


async def composer_node(
    state: AgentState, config: RunnableConfig
) -> Command[Literal["director", "researcher", "validator", "cinematographer", "composer", "editor", "__end__"]]:
    """
    Executes the Audio Directive.
    Uses Command for dynamic routing.
    Respects GUI configuration for model selection and parameters.
    """
    logger.info("[COMPOSER] NODE: Composer")
    
    # Check if composer is enabled in config
    conf = config.get("configurable", {})
    if not conf.get("composer_active", True):
        logger.info("[COMPOSER] Skipped by configuration (inactive)")
        state_update = {
            "messages": [AIMessage(content="Composer skipped (disabled in configuration)")]
        }
        handoff_reason = "Composer is inactive. Director must decide whether to proceed to Editor or adjust requirements."
        return _route_from_handoffs([("director", handoff_reason)], state_update, "director", "Composer")
    
    _emit_progress("Composer", "Generating audio/music...")
    plan = state.get("director_plan", "")

    # Safety: Ensure plan is string
    if not isinstance(plan, str):
        if isinstance(plan, list):
            plan = str(plan[-1]) if plan else ""
        else:
            plan = str(plan)

    # Get model configuration from GUI
    model_id = conf.get("composer_model")
    model_params = conf.get("composer_params", {})
    voice_source = conf.get("composer_voice_source")
    voice_file = conf.get("composer_voice_file")
    voice_model_id = conf.get("composer_voice_model")
    composer_source = conf.get("composer_source", "model")

    if composer_source == "file":
        file_paths = conf.get("composer_files") or []
        file_metadata = conf.get("composer_file_metadata") or []
        assets = []
        summaries = []

        for idx, path in enumerate(file_paths, start=1):
            if not isinstance(path, str):
                continue
            normalized = os.path.normpath(path)
            if not os.path.exists(normalized):
                logger.warning("[COMPOSER] Uploaded audio missing on disk: %s", normalized)
                continue
            assets.append(normalized)
            meta = file_metadata[idx - 1] if idx - 1 < len(file_metadata) else {}
            parts = [f"Track {idx}: {Path(normalized).name}"]
            if meta:
                duration = meta.get("duration_readable") or meta.get("duration_seconds")
                if duration:
                    parts.append(f"Duration {duration}")
                if meta.get("frame_rate"):
                    parts.append(f"Sample Rate {meta['frame_rate']} Hz")
                if meta.get("channels"):
                    parts.append(f"Channels {meta['channels']}")
            summaries.append(" | ".join(parts))

        if not assets:
            logger.warning("[COMPOSER] No valid uploaded audio found for pass-through mode")
            state_update = {
                "messages": [AIMessage(content="Composer received uploaded mode but no valid audio files were available.")],
                "audio_assets": []
            }
            handoff_reason = "Uploaded audio assets were missing. Provide corrected files or request new audio generation."
        else:
            summary_text = "\n".join(summaries) if summaries else "\n".join(assets)
            state_update = {
                "messages": [AIMessage(content=f"Using uploaded audio asset(s) ({len(assets)} track(s)):\n{summary_text}")],
                "audio_assets": assets,
            }
            handoff_reason = "Uploaded audio assets are ready. Confirm they align with the vision or request adjustments."

        return _route_from_handoffs([("director", handoff_reason)], state_update, "director", "Composer")

    try:
        # Pass model configuration to the task
        result = run_composer_task(
            plan,
            model_id=model_id,
            model_params=model_params,
            voice_source=voice_source,
            voice_file=voice_file,
            voice_model_id=voice_model_id
        )
        result = str(result)
        assets = []
        
        # Extract audio file path - look for common audio extensions and paths
        match = re.search(
            r"(https?://[^\s\)]+\.(?:wav|mp3|m4a|aac)|[A-Za-z]:\\[^\s\)]+\.(?:wav|mp3|m4a|aac)|/[^\s\)]+\.(?:wav|mp3|m4a|aac)|Artifacts[^\s\)]+\.(?:wav|mp3|m4a|aac))",
            result,
            re.IGNORECASE
        )
        if match:
            audio_path = match.group(1)
            # Normalize Windows backslashes
            audio_path = audio_path.replace('/', os.sep).replace('\\', os.sep)
            assets.append(audio_path)

        state_update = {
            "messages": [AIMessage(content=f"Audio Created: {result}")],
            "audio_assets": assets,
        }
        
        handoff_reason = "Composer delivered audio assets. Review them and decide whether to iterate or move to the Editor."
        return _route_from_handoffs([("director", handoff_reason)], state_update, "director", "Composer")
        
    except Exception as e:
        logger.error("Composition Failed: %s", e)
        state_update = {"messages": [AIMessage(content=f"Audio Error: {e}")]}
        handoff_reason = "Composer encountered an error. Provide updated musical direction or adjust the workflow."
        return _route_from_handoffs([("director", handoff_reason)], state_update, "director", "Composer")


async def editor_node(
    state: AgentState, config: RunnableConfig
) -> Command[Literal["director", "researcher", "validator", "cinematographer", "composer", "editor", "__end__"]]:
    """
    Merges the assets.
    Uses Command for dynamic routing (typically ends workflow).
    """
    logger.info("✂️ NODE: Editor (Merge)")
    _emit_progress("Editor", "Merging video and audio...")

    conf = config.get("configurable", {})
    do_merge = conf.get("merge_output", True)
    fname = conf.get("output_filename", "final_cut.mp4")

    if not do_merge:
        state_update = {"messages": [AIMessage(content="Merge skipped by config.")]}
        return _route_from_handoffs([], state_update, "end", "Editor")

    v_assets = state.get("video_assets", [])
    a_assets = state.get("audio_assets", [])

    if not v_assets or not a_assets:
        state_update = {
            "messages": [
                AIMessage(content="Skipping Merge: Missing Video or Audio assets.")
            ]
        }
        return _route_from_handoffs([], state_update, "end", "Editor")

    final_audio = a_assets[-1]
    valid_videos = [v for v in v_assets if isinstance(v, str) and len(v) > 3]

    if not valid_videos:
        state_update = {
            "messages": [AIMessage(content="Skipping Merge: No valid video paths.")]
        }
        return _route_from_handoffs([], state_update, "end", "Editor")

    res_path = merge_video_audio_logic(
        video_paths=valid_videos, audio_path=final_audio, output_name=fname
    )
    
    # Upload merged video to GCS for public access
    cloud_url = None
    if res_path and not res_path.startswith("Error") and os.path.exists(res_path):
        res_path = os.path.normpath(res_path)
        try:
            from DeepAgents.asset_manager import AssetManager
            am = AssetManager()
            # Upload to GCS and get public URL
            cloud_url = am._upload_to_gcs(res_path, os.path.basename(res_path), make_public=True)
            if cloud_url:
                logger.info(f"✅ Merged video uploaded to GCS (PUBLIC): {cloud_url}")
        except Exception as upload_err:
            logger.warning(f"GCS upload failed for merged video: {upload_err}")

    # Build result message with both local and cloud URLs
    result_msg = f"FINAL MERGED VIDEO: {res_path}"
    if cloud_url:
        result_msg += f"\nCloud URL (PUBLIC): {cloud_url}"

    state_update = {
        "messages": [AIMessage(content=result_msg)],
        "final_output": cloud_url if cloud_url else res_path,  # Prefer cloud URL
    }
    
    # Editor is typically the final step
    return _route_from_handoffs([], state_update, "end", "Editor")


# --- 5. The Graph (Assembly) ---

workflow = StateGraph(AgentState)

# Nodes - ALL agents now use Command for dynamic mesh routing
workflow.add_node("director", director_node)
workflow.add_node("researcher", researcher_node)
workflow.add_node("validator", validator_node)
workflow.add_node("cinematographer", cinematographer_node)
workflow.add_node("composer", composer_node)
workflow.add_node("editor", editor_node)

# Entry Point
workflow.set_entry_point("director")

# MESH MODE: All nodes use Command for dynamic routing
# No explicit edges needed - each node returns Command(goto="next_node")
# This enables full mesh capability where any agent can route to any other

# Compile for execution
app = workflow.compile()
