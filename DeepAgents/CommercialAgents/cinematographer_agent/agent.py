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
from typing import Optional, Any, Callable, Dict, List

from dotenv import load_dotenv
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.language_models import BaseChatModel
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

# from langchain_google_vertexai import ChatVertexAI # Deprecated
from langchain_core.tools import StructuredTool
from langsmith import traceable

# Internal Data Structures
from DeepAgents.asset_manager import AssetManager
from DeepAgents.agent_brain import AgentComms
import replicate
from DeepAgents.model_schemas import get_model_schema, parse_schema_output
from DeepAgents.CommercialAgents.cinematographer_agent.prompts import (
    CINEMATOGRAPHER_INSTRUCTIONS,
)
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

    def _generate_video_vertex(prompt: str, duration: int = 8) -> str:
        """
        Generates a video using Google Vertex AI Veo models.
        Returns local file path (and cloud link).
        
        Note: Veo 3.1 only supports durations of 4, 6, or 8 seconds.
        """
        logger.info(f"[VIDEO-VERTEX] Generating with Veo: {vid_model}")
        
        if not gen_client:
            return "Error: Google GenAI client not initialized. Check GOOGLE_CLOUD_PROJECT."
        
        try:
            from google.genai import types
            import time
            
            # Veo 3.1 only supports 4, 6, or 8 seconds - snap to nearest valid
            valid_durations = [4, 6, 8]
            if duration not in valid_durations:
                # Snap to nearest valid duration
                original = duration
                duration = min(valid_durations, key=lambda x: abs(x - duration))
                logger.warning(f"[VIDEO-VERTEX] Duration {original}s not supported, using {duration}s")
            
            # Veo generation config
            config = types.GenerateVideosConfig(
                aspect_ratio="16:9",
                number_of_videos=1,
                duration_seconds=duration,
                enhance_prompt=True,  # Let Veo optimize the prompt
            )
            
            logger.info(f"[VIDEO-VERTEX] Prompt: {prompt[:80]}...")
            logger.info(f"[VIDEO-VERTEX] Config: duration={duration}s, aspect=16:9")
            
            # Start async generation
            operation = gen_client.models.generate_videos(
                model=vid_model,
                prompt=prompt,
                config=config,
            )
            
            # Poll for completion (Veo is async)
            logger.info("[VIDEO-VERTEX] Waiting for video generation...")
            max_wait = 300  # 5 minutes max
            poll_interval = 10
            elapsed = 0
            
            while not operation.done and elapsed < max_wait:
                time.sleep(poll_interval)
                elapsed += poll_interval
                logger.info(f"[VIDEO-VERTEX] Still generating... ({elapsed}s elapsed)")
                operation = gen_client.operations.get(operation)
            
            if not operation.done:
                return f"Error: Video generation timed out after {max_wait}s"
            
            # Check for result
            if operation.response and operation.response.generated_videos:
                video = operation.response.generated_videos[0]
                video_uri = video.video.uri if hasattr(video.video, 'uri') else None
                
                if video_uri:
                    logger.info(f"[VIDEO-VERTEX] Video ready: {video_uri}")
                    
                    # Download and save
                    resp = requests.get(video_uri, timeout=120)
                    if resp.status_code == 200:
                        path = assets.save_asset(
                            resp.content,
                            "video",
                            session_id,
                            prompt,
                            metadata={"model": vid_model, "provider": "VertexAI-Veo"},
                        )
                        if path:
                            return f"Saved: {path}{_get_cloud_url(path)}"
                        return "Error: Failed to save Veo video."
                    return f"Error: Failed to download video (HTTP {resp.status_code})"
                    
                # Try getting bytes directly
                if hasattr(video.video, 'video_bytes') and video.video.video_bytes:
                    path = assets.save_asset(
                        video.video.video_bytes,
                        "video",
                        session_id,
                        prompt,
                        metadata={"model": vid_model, "provider": "VertexAI-Veo"},
                    )
                    if path:
                        return f"Saved: {path}{_get_cloud_url(path)}"
                    return "Error: Failed to save Veo video bytes."
                    
            return f"Error: Veo returned no video data. Operation: {operation}"
            
        except Exception as e:
            logger.error(f"[VIDEO-VERTEX] Veo generation failed: {e}")
            return f"Error: Veo video generation failed: {e}"

    def _generate_video(prompt: str, duration: int = 5) -> str:
        """
        Generates a video clip (5-10s) based on the prompt.
        Uses dynamic schema-based prompt optimization from LangSmith Hub.
        Supports Replicate AND Vertex AI (Veo) models.
        Returns local file path (and cloud link).
        """
        logger.info(f"[VIDEO] Generating Video: {prompt[:60]}...")
        
        # Check if this is a Vertex AI model (Veo)
        is_vertex_model = vid_model.startswith("veo-") or "veo" in vid_model.lower()
        
        if is_vertex_model:
            # Use Vertex AI for Veo models
            return _generate_video_vertex(prompt, duration)
        
        if vid_provider.lower() != "replicate":
            return "Error: Only Replicate and Vertex AI (Veo) supported for video currently."

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
            
            # Emit progress so UI knows we're waiting on API
            try:
                comms = AgentComms()
                comms.connect()
                model_short = vid_model.split("/")[-1].split(":")[0]
                comms.send_message("Cinematographer", "GUI", f"Calling {model_short} API (this may take 1-3 minutes)...")
                comms.close()
            except Exception:
                pass  # Non-critical
            
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
            description="Generates a single video clip from a text prompt. Call this MULTIPLE TIMES if you need to generate multiple segments. Each call = one clip.",
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
            # System prompt that supports multi-segment video generation
            sys_msg = SystemMessage(
                content=f"{ontology}\n\n"
                f"## MULTI-SEGMENT VIDEO INSTRUCTIONS\n"
                f"If the directive contains MULTIPLE segments (e.g., Segment 1, Segment 2, Segment 3), "
                f"you MUST call generate_video ONCE for EACH segment.\n"
                f"- Extract each segment's Visual Prompt\n"
                f"- Call generate_video for Segment 1\n"
                f"- Call generate_video for Segment 2\n"
                f"- Continue until all segments are generated\n\n"
                f"Each tool call creates ONE video clip. The Editor will concatenate them automatically.\n"
                f"DO NOT combine multiple segments into one call - that produces poor results."
            )
            messages = [sys_msg, HumanMessage(content=input_text)]

        final_report = []
        # FAIL FAST MODE: Single Pass Execution (No Retry Loops)
        # We try to reason -> act -> finalize. Any error crashes the agent.

        # 1. Reason / Plan
        yield ("thinking", "🧠 Reasoning...")
        try:
            response = llm_with_tools.invoke(messages)
            messages.append(response)  # Add AI response to history
        except Exception as e:
            logger.error(f"LLM Inference Error: {e}")
            yield ("error", f"LLM Error: {e}")
            return

        # 2. Check for Tool Calls - MULTI-VIDEO SUPPORT
        all_generated_assets = []  # Collect all video paths
        
        if response.tool_calls:
            total_calls = len(response.tool_calls)
            yield ("thinking", f"🎬 Generating {total_calls} video segment(s)...")
            
            for idx, tool_call in enumerate(response.tool_calls, 1):
                tool_name = tool_call["name"]
                args = tool_call["args"]
                tool_id = tool_call["id"]

                yield ("thinking", f"🔧 Executing {tool_name} ({idx}/{total_calls})...")

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

                # Extract and collect asset paths (no HITL interrupt - collect all first)
                tr_str = str(tool_result)
                if (
                    "http" in tr_str
                    or "c:\\" in tr_str.lower()
                    or "/users/" in tr_str.lower()
                    or "Saved:" in tr_str
                ):
                    # Extract Best Identifier
                    import re

                    url_match = re.search(r"(https?://[^\s\)]+)", tr_str)
                    path_match = re.search(
                        r"([A-Za-z]:\\[^\s\)]+|/Users/[^\s\)]+)", tr_str
                    )

                    asset_path = tr_str  # Default fallback
                    if url_match:
                        asset_path = url_match.group(1).rstrip(".,)")
                    elif path_match:
                        asset_path = path_match.group(1).rstrip(".,)")

                    all_generated_assets.append(asset_path)
                    yield ("output", f"**Segment {idx}/{total_calls} Generated**: {asset_path}")

            # Report all generated assets
            if all_generated_assets:
                yield ("output", f"**Total Videos Generated**: {len(all_generated_assets)}")
                for i, asset in enumerate(all_generated_assets, 1):
                    yield ("video_asset", asset)  # Emit each asset for collection
                    
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
        
    Returns:
        String containing all generated video paths (supports multi-segment)
    """
    logger.info("[CINEMA] Cinematographer Consulted: %s", request_description)
    
    # Log model configuration if provided
    if model_id:
        logger.info("[CINEMA] Using model from GUI: %s", model_id)
    if model_params:
        logger.info("[CINEMA] Model params: %s", model_params)
    
    try:
        from DeepAgents.approval_manager import is_asset_rejected

        # TODO: Pass model_id and model_params to the agent/tools
        # For now, the agent uses system config. Future: override with GUI config.
        agent_gen = create_cinematographer_agent()

        final_output = ""
        video_assets = []  # Collect ALL generated video paths

        # Run generator
        for status, content in agent_gen(request_description):
            if status == "done":
                final_output = content
            elif status == "video_asset":
                # Multi-segment support: collect each video path
                video_assets.append(content)
                logger.info(f"[CINEMA] Video segment collected: {content}")
            elif status == "review_required":
                # Legacy HITL path - collect for potential review
                if not is_asset_rejected(content):
                    video_assets.append(content)
            elif status == "output":
                # Log output messages
                logger.info(f"[CINEMA] Output: {content}")

        # Build result string with all video paths
        if video_assets:
            # Multi-video: Return all paths as comma-separated for regex extraction
            result_parts = [f"Generated {len(video_assets)} video segment(s):"]
            for i, asset in enumerate(video_assets, 1):
                result_parts.append(f"Segment {i}: {asset}")
            return "\n".join(result_parts)
        elif final_output:
            return str(final_output)
        else:
            return "Error: No video assets generated"

    except Exception as e:
        logger.error("Cinematographer Task Failed: %s", e)
        return f"Error: {e}"


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        print(run_cinematographer_task(sys.argv[1]))
    else:
        print("Cinematographer Agent ready. Pass arg to test.")
