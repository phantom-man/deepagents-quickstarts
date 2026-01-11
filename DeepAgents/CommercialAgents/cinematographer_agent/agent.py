"""
Cinematographer Agent Module.
Handles the creation and execution of the Cinematographer agent
for video and image generation.
"""
import os
import logging
from typing import Optional, Dict, Any, Callable

from google import genai
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic

# Local imports
from DeepAgents.agent_brain import logger
from DeepAgents.asset_manager import AssetManager

try:
    from DeepAgents.CommercialAgents.cinematographer_agent.prompts import CINEMATOGRAPHER_INSTRUCTIONS
except ImportError:
    # Fallback to absolute if script run from subfolder
    from DeepAgents.CommercialAgents.cinematographer_agent.prompts import CINEMATOGRAPHER_INSTRUCTIONS

# Handle optional dependencies
try:
    import replicate
except ImportError:
    replicate = None

def _initialize_llm(provider: str, model_name: str) -> Any:
    """Initialize the LLM based on provider."""
    try:
        if provider == "Replicate":
            # Requires REPLICATE_API_TOKEN in env
            from langchain_community.chat_models import ChatReplicate
            return ChatReplicate(
                model=model_name,
                model_kwargs={"temperature": 0.7, "max_length": 2048, "top_p": 1}
            )

        if provider == "Google":
            project = os.getenv("GOOGLE_CLOUD_PROJECT")
            # Force global for preview models
            location = "global" if "exp" in model_name or "preview" in model_name else os.getenv("GOOGLE_CLOUD_LOCATION")
            
            return ChatGoogleGenerativeAI(
                model=model_name, 
                temperature=0.7,
                project=project,
                location=location
            )
        if provider == "Anthropic":
            return ChatAnthropic(
                model_name=model_name,
                temperature=0.7,
                timeout=None,
                stop=None
            )
        # Default fallback
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-pro-001",
            project=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION")
        )
    except Exception as e: # pylint: disable=broad-exception-caught
        logger.error("Cinematographer LLM Init Failed: %s", e)
        return None

def _initialize_gen_client() -> Optional[genai.Client]:
    """Initialize Google GenAI Client."""
    try:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        location = "us-central1"
        if project_id:
            return genai.Client(vertexai=True, project=project_id, location=location)
    except Exception as e: # pylint: disable=broad-exception-caught
        logger.error("GenAI Client Init Failed: %s", e)
    return None

def create_cinematographer_agent(
    model_config: Optional[Dict[str, Any]] = None,
    # pylint: disable=unused-argument
    brain: Any = None,
    session_id: str = "default"
) -> Callable:
    """
    Factory to create the Cinematographer Agent runner.
    """
    if model_config is None:
        model_config = {"provider": "Replicate", "model": "meta/meta-llama-3-8b-instruct"}

    # Configurations
    provider = model_config.get("provider", "Replicate")
    model_name = model_config.get("model", "meta/meta-llama-3-8b-instruct")

    # img_provider = model_config.get("image_provider", "Google") # Unused currently effectively
    img_model = model_config.get("image_model", "imagen-3.0-generate-001")

    vid_provider = model_config.get("video_provider", "Google")
    vid_model = model_config.get("video_model", "veo-2.0-generate-001")

    # Asset Manager
    assets = AssetManager()

    # 1. Initialize Brain LLM
    llm = _initialize_llm(provider, model_name)
    if not llm:
        # If LLM init fails, return a dummy function that reports error
        return lambda *args, **kwargs: "Error: LLM Initialization Failed"

    # 2. Initialize Generative Client
    gen_client = _initialize_gen_client()
    ontology = CINEMATOGRAPHER_INSTRUCTIONS
    
    # Import Replicate and Requests for Image Generation
    import replicate
    import requests
    from io import BytesIO

    # --- HELPER: Generate Image ---
    def generate_image(prompt: str) -> Optional[str]:
        # Switch to Replicate (Flux/SDXL) due to Google Imagen Quotas
        try:
            logger.info("🎨 Cinematographer > Generating Image via Replicate (Flux)...")
            
            # Using black-forest-labs/flux-schnell (Speed Optimized)
            # Documentation: https://replicate.com/black-forest-labs/flux-schnell/api
            output = replicate.run(
                "black-forest-labs/flux-schnell",
                input={
                    "prompt": prompt,
                    "aspect_ratio": "16:9",  # Options: 1:1, 16:9, 21:9, 3:2, 2:3, 4:5, 5:4, 3:4, 4:3, 9:16, 9:21
                    "num_inference_steps": 4, # 1-4 for Schnell (it is fast)
                    "num_outputs": 1,
                    "megapixels": "1", # Options: "1", "0.25"
                    "go_fast": True, # Optimize for speed (fp8)
                    "output_format": "png", # png for lossless quality
                    # "seed": 42, # Optional: for determinism
                    "disable_safety_checker": True
                }
            )
            # Output is usually a list of file outputs (URLs or streams)
            
            error_msg = None
            image_url = None

            if isinstance(output, list) and len(output) > 0:
                image_url = output[0]
            elif isinstance(output, str):
                image_url = output # Some models return just the string URL
            
            if image_url:
                # Download the image bytes
                logger.info("📥 Downloading generated image from %s", image_url)
                response = requests.get(str(image_url))
                if response.status_code == 200:
                    img_data = response.content
                    # Save Asset
                    path = assets.save_asset(
                        img_data, "image", session_id, prompt,
                        metadata={
                            "model": "black-forest-labs/flux-schnell", 
                            "provider": "Replicate",
                            "params": {"aspect_ratio": "16:9", "steps": 4, "format": "png"}
                        }
                    )
                    return path
                else:
                    error_msg = f"Failed to download image: {response.status_code}"
            else:
                error_msg = "No image URL returned from Replicate."

            if error_msg:
                logger.error(error_msg)
                return error_msg

        except Exception as e:
            logger.error(f"Generate Image Error: {e}")
            return f"Error: {e}" 
            
    # --- HELPER: Generate Video ---
    def generate_video(prompt: str, image_path: Optional[str] = None) -> Optional[str]:
            return None
        except Exception as e: # pylint: disable=broad-exception-caught
            return f"Image Gen Error: {e}"

    # --- HELPER: Generate Video ---
    def generate_video(prompt: str) -> Optional[str]:
        # 1. Google Vertex (Veo)
        if vid_provider == "Google":
            if not gen_client:
                return "Error: No GenAI Client"
            try:
                # Veo generation prompt
                response = gen_client.models.generate_content(
                    model=vid_model,
                    contents=prompt,
                    config={
                        'response_mime_type': 'video/mp4'
                    }
                )
                candidates = response.candidates
                if candidates and candidates[0].content and candidates[0].content.parts:
                    part = candidates[0].content.parts[0]
                    if part.inline_data and part.inline_data.data:
                        path = assets.save_asset(
                            part.inline_data.data, "video", session_id, prompt,
                            metadata={"model": vid_model}
                        )
                        return path
                return None
            except Exception as e: # pylint: disable=broad-exception-caught
                return f"Video Gen Error: {e}"

        # 2. Replicate (Zeroscope, AnimateDiff, etc.)
        if vid_provider == "Replicate":
            if not replicate:
                return "Error: Replicate module not installed."
            try:
                # Prepare Inputs
                input_args = {"prompt": prompt}

                # Clean extra args from config
                # We need to map config keys like 'num_frames' to input args
                for k, v in model_config.items():
                    # Filter for known input keys of Zeroscope/AnimateDiff
                    if k in [
                        "num_frames", "fps", "width", "height",
                        "steps", "guidance_scale", "motion_module"
                    ]:
                        input_args[k] = v

                logger.info("Calling Replicate Video (%s) with args: %s",
                           vid_model, list(input_args.keys())) # Fixed logger format
                output = replicate.run(vid_model, input=input_args)

                # Replicate usually returns a URL list or single URL
                if isinstance(output, list):
                    output = output[0]

                if output:
                    # Enforce string type for URL/Path handling
                    data_to_save = str(output)
                    path = assets.save_asset(
                        data_to_save, "video", session_id, prompt,
                        metadata={
                            "model": vid_model,
                            "provider": "Replicate"
                        }
                    )
                    return path
                return None
            except Exception as e: # pylint: disable=broad-exception-caught
                logger.error("Replicate Video Error: %s", e)
                return f"Replicate Video Gen Error: {e}"

        return "Error: Unknown Video Provider"

    # 2. Define the Runner Function
    def run_agent(
        input_text: str,
        mode: str = "storyboard",
        max_shots: int = 1,
        # pylint: disable=unused-argument
        duration_sec: int = 5
    ) -> str:
        logger.info(
            "🎥 Cinematographer receiving input: %s... Mode: %s",
            input_text[:50], mode
        )

        # A. Analyze / Storyboard Phase
        messages = [
            SystemMessage(
                content=(
                    f"{ontology}\n\n"
                    f"Create a visual description for {max_shots} distinct shot(s) "
                    "for the scene. Return ONLY the shot descriptions."
                )
            ),
            HumanMessage(content=input_text)
        ]

        try:
            # Use LLM to refine the prompt
            response = llm.invoke(messages)
            visual_plan = str(response.content)

            # --- LUMIERE UPGRADE: Physics & Optics Critique ---
            logger.info("🔭 Lumiere > Analyzing Visual Physics...")
            critique_msg = [
                SystemMessage(content=(
                    "You are a Physics & Optics Simulator. Analyze this visual plan for "
                    "impossible geometries, conflicting lighting, or likely AI artifacts. "
                    "Rewrite the prompt to be safe, physically grounded, and render-ready. "
                    "Return ONLY the refined prompt."
                )),
                HumanMessage(content=visual_plan)
            ]
            refined_response = llm.invoke(critique_msg)
            visual_plan = str(refined_response.content)
            logger.info("🔭 Physics Check Passed. Refined Plan: %s...", visual_plan[:50])
            # --------------------------------------------------

            output_report = f"**Visual Analysis**:\n{visual_plan}\n\n"

            # Basic Implementation: Just use the plan as a single prompt for now to ensure reliability
            shots_to_generate = [visual_plan[:400]] # Default: single shot

            if max_shots > 1:
                # Repeat generation call N times.
                shots_to_generate = [visual_plan[:400]] * max_shots

            for idx, gen_prompt in enumerate(shots_to_generate):
                suffix = f" (Shot {idx+1}/{max_shots})" if max_shots > 1 else ""

                # Generate Image (Storyboard)
                img_path = generate_image(gen_prompt)
                if img_path and "Error" not in img_path:
                    output_report += f"**Storyboard Image{suffix}**:\nFile: `{img_path}`\n"
                elif img_path:
                    output_report += f"**Image Status{suffix}**: {img_path}\n"

                # Generate Video (Motion)
                if mode in ("video", "both"):
                    # Veo usually handles duration via internal config or prompt nuances
                    vid_path = generate_video(gen_prompt)
                    if vid_path and "Error" not in vid_path:
                        output_report += f"**Video Generated{suffix}**:\nFile: `{vid_path}`\n"
                    elif vid_path:
                        output_report += f"**Video Status{suffix}**: {vid_path}\n"

            return output_report

        except Exception as e: # pylint: disable=broad-exception-caught
            logger.error("Cinematographer Error: %s", e)
            return f"Error: {e}"

    return run_agent
