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
from langchain_core.tools import tool, StructuredTool
from langsmith import traceable

# Internal Data Structures
from DeepAgents.asset_manager import AssetManager
import replicate
from DeepAgents.hub_manager import get_or_push_prompt
from DeepAgents.CommercialAgents.cinematographer_agent.prompts import (
    CINEMATOGRAPHER_INSTRUCTIONS,
)

# Cross-Agent Imports
try:
    from DeepAgents.CommercialAgents.composer_agent.agent import run_composer_task
except ImportError:
    logging.warning("Could not import Composer Agent directly. Cross-agent calls may fail.")
    def run_composer_task(req): return "Error: Composer Interface Unavailable."

# Load Env
ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.env"))
load_dotenv(ENV_PATH)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _initialize_llm(provider: str, model_name: str) -> Optional[BaseChatModel]:
    """Initialize the LLM/Chat Model."""
    try:
        if provider == "Google":
            from langchain_google_genai import ChatGoogleGenerativeAI

            return ChatGoogleGenerativeAI(
                model=model_name,
                temperature=0.7,
                max_output_tokens=2048,
            )
        if provider == "Anthropic":
            return ChatAnthropic(
                model_name=model_name, temperature=0.7, timeout=None, stop=None
            )
        # Default fallback
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-pro-001",
        )
    except Exception as e:
        logger.error("Cinematographer LLM Init Failed: %s", e)
        return None


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
    if model_config is None:
        model_config = {"provider": "Anthropic", "model": "claude-3-haiku-20240307"}

    # Configurations
    provider = model_config.get("provider", "Anthropic")
    model_name = model_config.get("model", "claude-3-haiku-20240307")

    img_provider = model_config.get("image_provider", "Google")
    img_model = model_config.get("image_model", "imagen-4.0-fast-generate-001")

    vid_provider = model_config.get("video_provider", "Replicate")
    vid_model = model_config.get("video_model", "zeroscope/v2-xl")

    # Asset Manager & Replicate
    assets = AssetManager()
    # replicate module is imported globally

    # 1. Initialize Brain LLM
    llm = _initialize_llm(provider, model_name)
    if not llm:
        return lambda *args, **kwargs: "Error: LLM Initialization Failed"

    # 2. Initialize Generative Client
    gen_client = _initialize_gen_client()
    
    # 3. Pull Prompt
    ontology = get_or_push_prompt("cinematographer-system-prompt", CINEMATOGRAPHER_INSTRUCTIONS)

    # --- DEFINE TOOLS (Closures to access config/state) ---

    def _generate_image(prompt: str) -> str:
        """
        Generates a photorealistic image based on the prompt. 
        Returns local file path.
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
                    return assets.save_asset(
                        img_bytes, "image", session_id, prompt,
                        metadata={"model": img_model, "provider": "Google"}
                    )
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
                    return assets.save_asset(
                        resp.content, "image", session_id, prompt,
                        metadata={"model": "flux-schnell", "provider": "Replicate"}
                    )
        except Exception as e:
            return f"Error Generating Image: {e}"
        return "Error: Image Generation returned no data."

    def _generate_video(prompt: str, duration: int = 4) -> str:
        """
        Generates a video clip (2-4s) based on the prompt.
        Returns local file path.
        """
        logger.info(f"🎥 Generating Video: {prompt[:40]}...")
        if vid_provider != "Replicate":
             return "Error: Only Replicate supported for video currently."
             
        try:
            # Map common args
            input_args = {"prompt": prompt}
            # Add specific args if model requires (simple mapping for now)
            if "zeroscope" in vid_model:
                input_args["num_frames"] = 24
            
            output = replicate.run(vid_model, input=input_args)
            video_url = output[0] if isinstance(output, list) else output
            
            if video_url:
                return assets.save_asset(
                    str(video_url), "video", session_id, prompt,
                    metadata={"model": vid_model, "provider": "Replicate"}
                )
        except Exception as e:
            return f"Error Generating Video: {e}"
        return "Error: Video Generation returned no data."

    def _consult_composer(request: str) -> str:
        """
        Consults the Composer Agent (Orpheus) for music/audio.
        Use this if the director asks for a music video or specific audio sync.
        Returns path to audio file or description.
        """
        logger.info(f"🎻 Consulting Composer: {request}")
        return run_composer_task(request)

    # Wrap as LangChain Tools
    tools = [
        StructuredTool.from_function(
            func=_generate_image,
            name="generate_image",
            description="Generates a photorealistic image/storyboard frame. Input: Detailed visual prompt."
        ),
        StructuredTool.from_function(
            func=_generate_video,
            name="generate_video",
            description="Generates a short video clip (MAX 4s). Input: Visual description of motion."
        ),
        StructuredTool.from_function(
            func=_consult_composer,
            name="consult_composer",
            description="Call Composer Agent for music/audio. Input: Description of music needed."
        )
    ]

    # Bind Tools to LLM
    try:
        llm_with_tools = llm.bind_tools(tools)
    except Exception as e:
        logger.error(f"Failed to bind tools to LLM ({provider}): {e}")
        llm_with_tools = llm

    # 4. Define Agent Runner (Generator with ReAct Loop)
    @traceable(run_type="chain", name="Cinematographer Agent")
    def run_agent(
        input_text: str,
        mode: str = "storyboard",
        max_shots: int = 1,      
        duration_sec: int = 5,   
    ):
        """
        Generator that yields status updates while running the ReAct loop.
        """
        yield ("thinking", "🎥 Cinematographer initializing...")
        
        # Initial System Prompt
        sys_msg = SystemMessage(content=f"{ontology}\n\nCurrent Mode context: {mode}. You have tools to generate assets. USE THEM.")
        messages = [sys_msg, HumanMessage(content=input_text)]
        
        final_report = []
        MAX_STEPS = 10
        step_count = 0

        while step_count < MAX_STEPS:
            step_count += 1
            try:
                # INVOKE LLM
                yield ("thinking", f"🧠 Reasoning (Step {step_count})...")
                response = llm_with_tools.invoke(messages)
                messages.append(response) # Add AI response to history

                # CHECK FOR TOOL CALLS
                if response.tool_calls:
                    for tool_call in response.tool_calls:
                        tool_name = tool_call["name"]
                        args = tool_call["args"]
                        tool_id = tool_call["id"]
                        
                        yield ("thinking", f"🔧 Executing {tool_name}...")
                        
                        # Execute Tool
                        tool_result = "Error: Tool not found"
                        selected_tool = next((t for t in tools if t.name == tool_name), None)
                        
                        if selected_tool:
                            try:
                                tool_result = selected_tool.invoke(args)
                            except Exception as te:
                                tool_result = f"Tool Execution Error: {te}"
                        
                        # Add Result to History
                        messages.append(ToolMessage(content=str(tool_result), tool_call_id=tool_id))
                        
                        # Stream Asset paths if detected
                        if "http" in str(tool_result) or "c:\\" in str(tool_result).lower() or "/users/" in str(tool_result).lower():
                             yield ("output", f"**Asset Generated**: {tool_result}")
                             final_report.append(f"Asset: {tool_result}")
                        else:
                             # Just info
                             pass

                else:
                    # NO TOOL CALLS -> FINAL ANSWER
                    yield ("done", response.content)
                    return response.content

            except Exception as e:
                logger.error(f"ReAct Loop Error: {e}")
                yield ("error", f"Agent Error: {e}")
                return
        
        yield ("done", "Agent reached max steps.")

    return run_agent


def run_cinematographer_task(request_description: str) -> str:
    """
    Synchronous entry point for external agents (Director).
    """
    logger.info("🎬 Cinematographer Consulted: %s", request_description)
    try:
        agent_gen = create_cinematographer_agent()
        
        # Run generator to completion and collect output
        final_output = ""
        for status, content in agent_gen(request_description):
            if status == "done":
                final_output = content
            elif status == "output":
                pass
        
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
