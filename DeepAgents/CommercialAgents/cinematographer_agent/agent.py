# pylint: disable=broad-exception-caught
# pylint: disable=import-error
# pylint: disable=no-name-in-module
# pylint: disable=unused-variable
"""
Cinematographer Agent (Visual Specialist).
Responsible for:
1. Breaking down scripts into shots (Storyboard).
2. Generating Images (Flux/Imagen).
3. Generating Video (Veo/Replicate).
4. Consulting Composer for Audio/Sync.
5. Merging Logic (via Tool Calls).
"""
import os
import logging
import requests
import json
from typing import Optional, Any, Callable, Dict, List, Union

from dotenv import load_dotenv
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    SystemMessage,
    AIMessage,
    ToolMessage,
)
from langchain_core.language_models import BaseChatModel
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

# from langchain_google_vertexai import ChatVertexAI # Deprecated
from langchain_core.tools import tool, StructuredTool
from langsmith import traceable

# Internal Data Structures
from DeepAgents.asset_manager import AssetManager
import replicate
from DeepAgents.hub_manager import get_or_push_prompt
from DeepAgents.model_schemas import get_model_schema, parse_schema_output
from DeepAgents.CommercialAgents.cinematographer_agent.prompts import (
    CINEMATOGRAPHER_INSTRUCTIONS,
)
from DeepAgents.inter_agent_comms import discover_agents
from DeepAgents.system_config import SystemConfiguration

# Cross-Agent Imports (REMOVED per strict isolation policy)
# try:
#     from DeepAgents.CommercialAgents.composer_agent.agent import run_composer_task
# except ImportError:
#     logging.warning("Could not import Composer Agent directly. Cross-agent calls may fail.")
#     def run_composer_task(request_description: str) -> str: return "Error: Composer Interface Unavailable."

# Load Env
ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.env"))
load_dotenv(ENV_PATH)

logging.basicConfig(level=logging.INFO)
# Suppress noisy OpenTelemetry attribute warnings
logging.getLogger("opentelemetry.attributes").setLevel(logging.ERROR)
logger = logging.getLogger(__name__)


def _initialize_llm(provider: str, model_name: str) -> Optional[BaseChatModel]:
    """Initialize the LLM/Chat Model."""
    # Raise exceptions if initialization fails. DO NOT FALLBACK.
    if provider.lower() == "google":
        # Upgrade to GenerativeAI SDK (Vertex Mode)
        return ChatGoogleGenerativeAI(
            model=model_name,
            vertexai=True,
            project=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location="us-central1",
            temperature=0.7,
            max_output_tokens=2048,
        )
    if provider.lower() == "anthropic":
        return ChatAnthropic(model_name=model_name, temperature=0.7)  # type: ignore
    # Default fallback
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-001",
        vertexai=True,
        project=os.getenv("GOOGLE_CLOUD_PROJECT"),
        location="us-central1",
        temperature=0.7,
    )


def _initialize_gen_client() -> Any:
    """Initialize Google GenAI Client (for Imagen/Veo)."""
    try:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        location = "us-central1"
        if project_id:
            # Import strictly inside function to avoid heavy deps if unused
            import google.genai as genai

            return genai.Client(vertexai=True, project=project_id, location=location)
    except Exception as e:
        logger.error("GenAI Client Init Failed: %s", e)
    return None


def _parse_model_string(
    model_str: str,
    default_provider: str = "Google",
    default_model: str = "gemini-1.5-flash",
) -> tuple:
    """Parses 'provider/model' string."""
    if "/" in model_str:
        parts = model_str.split("/", 1)
        return parts[0], parts[1]
    return default_provider, model_str or default_model


def create_cinematographer_agent(
    model_config: Optional[Dict[str, Any]] = None,
    # pylint: disable=unused-argument
    brain: Any = None,
    session_id: str = "default",
) -> Callable:
    """
    Factory to create the Cinematographer Agent runner with Tool Support.
    Returns a Generator Function `run_agent`.
    """
    # Load System Config
    sys_conf = SystemConfiguration()
    agent_name = "Cinematographer"

    # 1. Determine Intelligence Model (Logic/LLM)
    # Priority: Runtime Arg > System Config > Default
    llm_provider, llm_model_name = "Google", "gemini-2.0-flash-001"

    if model_config and "provider" in model_config:
        llm_provider = model_config["provider"]
        llm_model_name = model_config.get("model", llm_model_name)
    else:
        # Query System Config
        config_model_str = sys_conf.get_agent_intelligence(agent_name)
        llm_provider, llm_model_name = _parse_model_string(
            config_model_str, "Google", "gemini-2.0-flash-001"
        )

    # 2. Determine Capability Models (Image/Video)
    img_cap = sys_conf.get_capability_model(agent_name, "image_generation")
    if img_cap:
        img_provider, img_model = _parse_model_string(
            img_cap["id"], "Google", "imagen-3.0-generate-001"
        )
    else:
        img_provider, img_model = "Google", "imagen-3.0-generate-001"

    vid_cap = sys_conf.get_capability_model(agent_name, "video_generation")
    if vid_cap:
        vid_provider, vid_model = _parse_model_string(
            vid_cap["id"], "Replicate", "zeroscope-v2-xl"
        )
    else:
        vid_provider, vid_model = "Replicate", "zeroscope-v2-xl"

    logger.info(
        f"Cinematographer Config: LLM={llm_provider}/{llm_model_name} | IMG={img_provider}/{img_model} | VID={vid_provider}/{vid_model}"
    )

    # Asset Manager & Replicate
    assets = AssetManager()
    # replicate module is imported globally

    # 1. Initialize Brain LLM
    llm = _initialize_llm(llm_provider, llm_model_name)
    if not llm:
        return lambda *args, **kwargs: "Error: LLM Initialization Failed"

    # 2. Initialize Generative Client
    gen_client = _initialize_gen_client()

    # 3. Pull Prompt
    ontology = CINEMATOGRAPHER_INSTRUCTIONS

    # --- DEFINE TOOLS (Closures to access config/state) ---

    def _get_cloud_url(local_path: str) -> str:
        """Helper to extract Cloud URL from metadata if available."""
        if not local_path or not os.path.exists(local_path + ".json"):
            return ""
        try:
            with open(local_path + ".json", "r") as f:
                meta = json.load(f)
            url = meta.get("cloud_url")
            return f" (Link: {url})" if url else ""
        except:
            return ""

    def _generate_image(prompt: str) -> str:
        """
        Generates a photorealistic image based on the prompt.
        Returns local file path (and cloud link).
        """
        logger.info(f"🎨 Generating Image: {prompt[:40]}...")
        # Google Strategy
        if img_provider == "Google" and gen_client:
            try:
                from google.genai import types

                response = gen_client.models.generate_images(
                    model=img_model,
                    prompt=prompt,
                    config=types.GenerateImagesConfig(
                        number_of_images=1, aspect_ratio="16:9"
                    ),
                )
                if response and response.generated_images:
                    img_bytes = response.generated_images[0].image.image_bytes
                    path = assets.save_asset(
                        img_bytes,
                        "image",
                        session_id,
                        prompt,
                        metadata={"model": img_model, "provider": "Google"},
                    )
                    if path:
                        return f"Saved: {path}{_get_cloud_url(path)}"
                    return "Error: Failed to save Google Image."
            except Exception as e:
                logger.error(f"Google Image Gen Failed: {e}")
                # Fallback to Replicate

        # Replicate Strategy (Flux/SDXL)
        try:
            output = replicate.run(
                "black-forest-labs/flux-schnell",
                input={
                    "prompt": prompt,
                    "aspect_ratio": "16:9",
                    "num_inference_steps": 4,
                    "output_format": "png",
                    "disable_safety_checker": True,
                },
            )
            image_url = output[0] if isinstance(output, list) else output
            if image_url:
                resp = requests.get(str(image_url), timeout=30)
                if resp.status_code == 200:
                    path = assets.save_asset(
                        resp.content,
                        "image",
                        session_id,
                        prompt,
                        metadata={"model": "flux-schnell", "provider": "Replicate"},
                    )
                    if path:
                        return f"Saved: {path}{_get_cloud_url(path)}"
                    return "Error: Failed to save Replicate Image."
        except Exception as e:
            return f"Error Generating Image: {e}"
        return "Error: Image Generation returned no data."

    def _generate_video(prompt: str, duration: int = 5) -> str:
        """
        Generates a video clip (5-10s) based on the prompt.
        Uses dynamic schema-based prompt optimization from LangSmith Hub.
        Returns local file path (and cloud link).
        """
        logger.info(f"[VIDEO] Generating Video: {prompt[:60]}...")
        if vid_provider.lower() != "replicate":
            return "Error: Only Replicate supported for video currently."

        try:
            # Dynamic Prompt Optimization via Model Schema
            optimized_prompt = prompt
            try:
                # Get model-specific schema from Hub
                schema_template = get_model_schema(
                    "Cinematographer",
                    "video_generation",
                    f"replicate/{vid_model}"
                )
                
                # Use LLM to optimize prompt according to schema
                optimization_prompt = schema_template.format(input_text=prompt)
                optimization_response = llm.invoke([HumanMessage(content=optimization_prompt)])
                
                # Parse the structured output
                parsed = parse_schema_output(optimization_response.content, vid_model)
                if parsed.get("VISUAL_PROMPT"):
                    optimized_prompt = parsed["VISUAL_PROMPT"]
                    logger.info(f"[SCHEMA] Optimized prompt: {optimized_prompt[:60]}...")
                else:
                    logger.info("[SCHEMA] No VISUAL_PROMPT in response, using original")
                    
            except Exception as schema_error:
                logger.warning(f"[SCHEMA] Optimization failed ({schema_error}), using original prompt")
            
            # Map common args based on model
            input_args: Dict[str, Any] = {"prompt": optimized_prompt}
            
            # Model-specific parameters
            if "wan" in vid_model.lower():
                # Wan models use different parameters
                input_args["num_frames"] = 81  # ~5 seconds at 16fps
                input_args["resolution"] = "480p"
                logger.info(f"[VIDEO] Using Wan model parameters: {input_args}")
            elif "ray" in vid_model.lower() or "luma" in vid_model.lower():
                # Luma Ray models
                input_args["duration"] = "5s"
                logger.info(f"[VIDEO] Using Luma Ray parameters: {input_args}")
            elif "zeroscope" in vid_model.lower():
                input_args["num_frames"] = 24
                logger.info(f"[VIDEO] Using Zeroscope parameters: {input_args}")

            logger.info(f"[VIDEO] Calling Replicate model: {vid_model}")
            output = replicate.run(vid_model, input=input_args)
            video_url = output[0] if isinstance(output, list) else output

            if video_url:
                logger.info(f"[VIDEO] Video generated, saving: {video_url}")
                path = assets.save_asset(
                    str(video_url),
                    "video",
                    session_id,
                    prompt,
                    metadata={"model": vid_model, "provider": "Replicate", "optimized_prompt": optimized_prompt},
                )
                if path:
                    return f"Saved: {path}{_get_cloud_url(path)}"
                return "Error: Failed to save Video."
        except Exception as e:
            logger.error(f"[VIDEO] Video generation error: {e}")
            return f"Error Generating Video: {e}"
        return "Error: Video Generation returned no data."

    # Wrap as LangChain Tools
    tools = [
        StructuredTool.from_function(
            func=_generate_image,
            name="generate_image",
            description="Generates a static image. Use ONLY if explicitly asked for a still/photo/picture.",
        ),
        StructuredTool.from_function(
            func=_generate_video,
            name="generate_video",
            description="YOU MUST CALL THIS TOOL. Generates a video clip from a text prompt. This is your PRIMARY and MANDATORY tool. Call it immediately with the visual prompt you received.",
        ),
    ]

    # Bind Tools to LLM with FORCED TOOL EXECUTION
    # tool_choice="any" maps to Gemini's FunctionCallingConfig(mode='ANY')
    # This MANDATES the model MUST call one of the provided tools.
    try:
        llm_with_tools = llm.bind_tools(tools, tool_choice="any")
        logger.info("[TOOL BINDING] Cinematographer tools bound with tool_choice='any' (forced execution)")
    except Exception as e:
        logger.error(f"Failed to bind tools to LLM ({llm_provider}): {e}")
        llm_with_tools = llm

    # 4. Define Agent Runner (Generator with ReAct Loop)
    @traceable(run_type="chain", name="Cinematographer Agent")
    def run_agent(
        input_text: str,
        mode: str = "storyboard",
        max_shots: int = 1,
        duration_sec: int = 5,
        resume_history: List[BaseMessage] = None,
        user_feedback: str = None,
    ):
        """
        Generator that yields status updates while running the ReAct loop.
        Supports HITL (Human-in-the-Loop) via resume_history.
        """
        # yield ("thinking", "🎥 Cinematographer initializing...")

        # Initial System Prompt or Resume
        if resume_history:
            messages = resume_history
            yield ("thinking", "🔄 Resuming session with user feedback...")
            if user_feedback:
                if user_feedback == "APPROVED":
                    messages.append(
                        HumanMessage(
                            content="✅ User APPROVED the asset. You may proceed."
                        )
                    )
                else:
                    messages.append(
                        HumanMessage(
                            content=f"❌ User REJECTED the asset. Feedback: {user_feedback}. Please refactor your approach and try again."
                        )
                    )
        else:
            yield ("thinking", "🎥 Cinematographer initializing...")
            # FORCEFUL system prompt requiring immediate tool execution
            sys_msg = SystemMessage(
                content=f"{ontology}\n\n"
                f"IMMEDIATE ACTION REQUIRED: Call generate_video NOW with the following prompt. "
                f"Do NOT describe what you will do. Do NOT plan. Just call the tool."
            )
            messages = [sys_msg, HumanMessage(content=input_text)]

        final_report = []
        # FAIL FAST MODE: Single Pass Execution (No Retry Loops)
        # We try to reason -> act -> finalize. Any error crashes the agent.

        # 1. Reason / Plan
        yield ("thinking", f"🧠 Reasoning...")
        try:
            response = llm_with_tools.invoke(messages)
            messages.append(response)  # Add AI response to history
        except Exception as e:
            logger.error(f"LLM Inference Error: {e}")
            yield ("error", f"LLM Error: {e}")
            return

        # 2. Check for Tool Calls
        if response.tool_calls:
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                args = tool_call["args"]
                tool_id = tool_call["id"]

                yield ("thinking", f"🔧 Executing {tool_name}...")

                # Execute Tool (Fail Fast: No Try/Except to hide errors)
                tool_result = "Error: Tool not found"
                selected_tool = next((t for t in tools if t.name == tool_name), None)

                if selected_tool:
                    # We allow the tool to raise exception if it fails
                    try:
                        tool_result = selected_tool.invoke(args)
                    except Exception as te:
                        # Report and Die
                        err_msg = f"FATAL: Tool {tool_name} failed: {te}"
                        logger.error(err_msg)
                        yield ("error", err_msg)
                        return

                # Add Result to History
                messages.append(
                    ToolMessage(content=str(tool_result), tool_call_id=tool_id)
                )

                # HITL INTERRUPT: Stream Asset paths if detected
                tr_str = str(tool_result)
                if (
                    "http" in tr_str
                    or "c:\\" in tr_str.lower()
                    or "/users/" in tr_str.lower()
                    or "Saved:" in tr_str
                ):
                    # Extract Best Identifier (Prioritize Cloud URL for LangSmith/Remote compatibility)
                    import re

                    url_match = re.search(r"(https?://[^\s\)]+)", tr_str)
                    path_match = re.search(
                        r"([A-Za-z]:\\[^\s\)]+|/Users/[^\s\)]+)", tr_str
                    )

                    review_target = tr_str  # Default fallback
                    if url_match:
                        review_target = url_match.group(1).rstrip(".,)")
                    elif path_match:
                        review_target = path_match.group(1).rstrip(".,)")

                    yield ("output", f"**Asset Pending Review**: {review_target}")
                    yield ("review_required", review_target)
                    yield ("state_dump", messages)  # Export state for Resume
                    return  # HALT EXECUTION FOR APPROVAL

            # 3. Finalize (One interpretation pass after tools)
            yield ("thinking", "📝 Finalizing Report...")
            try:
                final_res = llm_with_tools.invoke(messages)

                # Format final answer
                final_content = final_res.content
                if isinstance(final_content, list):
                    flat_text = []
                    for block in final_content:
                        if isinstance(block, dict) and "text" in block:
                            flat_text.append(block["text"])
                        elif isinstance(block, str):
                            flat_text.append(block)
                        else:
                            flat_text.append(str(block))
                    final_content = "\n".join(flat_text)

                yield ("done", final_content)
                return final_content
            except Exception as e:
                yield ("error", f"Finalization Error: {e}")
                return

        else:
            # NO TOOL CALLS -> FINAL ANSWER
            final_content = response.content
            if isinstance(final_content, list):
                # Flatten Anthropic content blocks
                flat_text = []
                for block in final_content:
                    if isinstance(block, dict) and "text" in block:
                        flat_text.append(block["text"])
                    elif isinstance(block, str):
                        flat_text.append(block)
                    else:
                        flat_text.append(str(block))
                final_content = "\n".join(flat_text)

            yield ("done", final_content)
            return final_content

    return run_agent


def run_cinematographer_task(
    request_description: str,
    model_id: str = None,
    model_params: dict = None
) -> str:
    """
    Synchronous entry point for external agents (Director).
    Handles HITL via ApprovalManager.
    
    Args:
        request_description: The visual directive/plan from Director
        model_id: Optional model ID from GUI (e.g., "wan-video/wan-2.5-t2v-fast")
        model_params: Optional dict of model parameters from GUI schema
    """
    logger.info("[CINEMA] Cinematographer Consulted: %s", request_description)
    
    # Log model configuration if provided
    if model_id:
        logger.info("[CINEMA] Using model from GUI: %s", model_id)
    if model_params:
        logger.info("[CINEMA] Model params: %s", model_params)
    
    try:
        from DeepAgents.approval_manager import is_asset_approved, is_asset_rejected

        # TODO: Pass model_id and model_params to the agent/tools
        # For now, the agent uses system config. Future: override with GUI config.
        agent_gen = create_cinematographer_agent()

        final_output = ""
        pending_assets = []

        # Run generator
        for status, content in agent_gen(request_description):
            if status == "done":
                final_output = content
            elif status == "review_required":
                # Check DB
                if is_asset_approved(content):
                    logger.info("HITL: Auto-approving previously verified asset.")
                elif is_asset_rejected(content):
                    return f"HITL_REJECTED: The user rejected asset {content}. Please generate a new one."
                else:
                    pending_assets.append(content)
            elif status == "output":
                pass

        # Post-Run HITL Check
        if pending_assets:
            # If any asset remains unapproved, we must halt the Director
            # We return the FIRST pending asset to avoid flooding
            asset = pending_assets[0]

            # FIX: If we have an asset but no final text output (early exit), use the asset message.
            if not final_output:
                logger.info("Auto-resolving output for generated asset: %s", asset)
                final_output = f"Visual Asset Created: {asset}"

            # HITL DISABLED: Always proceed
            # if not is_asset_approved(asset):
            #      return f"HITL_REVIEW_REQUIRED: {asset}"

        return str(final_output)

    except Exception as e:
        logger.error("Cinematographer Task Failed: %s", e)
        return f"Error: {e}"


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        print(run_cinematographer_task(sys.argv[1]))
    else:
        print("Cinematographer Agent ready. Pass arg to test.")
