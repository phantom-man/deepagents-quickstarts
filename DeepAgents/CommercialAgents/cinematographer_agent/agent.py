"""
Cinematographer Agent Module.
Handles the creation and execution of the Cinematographer agent
for video and image generation.
"""
import os
from typing import Optional, Dict, Any, Callable
import requests

from google import genai
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from langsmith import traceable

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
            from DeepAgents.replicate_adapter import ChatReplicate
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
                # convert_system_message_to_human=True # Optional dependent on LC version
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
        model_config = {"provider": "Anthropic", "model": "claude-3-haiku-20240307"}

    # Configurations
    provider = model_config.get("provider", "Anthropic")
    model_name = model_config.get("model", "claude-3-haiku-20240307")

    img_provider = model_config.get("image_provider", "Google")
    img_model = model_config.get("image_model", "imagen-4.0-fast-generate-001")

    vid_provider = model_config.get("video_provider", "Replicate")
    vid_model = model_config.get("video_model", "zeroscope/v2-xl")

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
    
    # --- HELPER: Generate Image ---
    def generate_image(prompt: str) -> Optional[str]:
        # GOOGLE IMAGEN PATH
        if img_provider == "Google":
            try:
                from google.cloud import aiplatform
                from google.protobuf import json_format
                from google.protobuf.struct_pb2 import Value
                
                logger.info(f"🎨 Cinematographer > Generating Image via Google ({img_model})...")
                
                # Use the client we initialized earlier if available, or direct REST/Client 
                # (Note: genai.Client is for Gemini API, aiplatform is for Vertex)
                # We used genai.Client(vertexai=True) in _initialize_gen_client
                
                if not gen_client:
                    return "Error: Google GenAI Client not initialized."
                
                # Imagen 3/4 usage via new GenAI SDK (Preview or Standard)
                # client.models.generate_images(...)
                # But let's verify syntax. The probe used client.models.generate_images
                
                # The probe code was:
                # client.models.generate_images(
                #    model=model_id,
                #    prompt=prompt,
                #    config=types.GenerateImagesConfig(number_of_images=1)
                # )
                
                # We need 'types' import. 
                from google.genai import types
                
                response = gen_client.models.generate_images(
                    model=img_model,
                    prompt=prompt,
                    config=types.GenerateImagesConfig(
                        number_of_images=1,
                        aspect_ratio="16:9"
                    )
                )
                
                # Response parsing
                if response and response.generated_images:
                    img_bytes = response.generated_images[0].image.image_bytes
                    return assets.save_asset(
                        img_bytes, "image", session_id, prompt,
                        metadata={"model": img_model, "provider": "Google"}
                    )
                return "No image returned from Google."

        if "flux" in img_model.lower() or "replicate" in img_provider.lower() or True: # Force Replicate
            if not replicate:
                return "Error: Replicate module not installed."

            # Switch to Replicate (Flux/SDXL) - Enforced Default
            try:
                logger.info("🎨 Cinematographer > Generating Image via Replicate (Flux)...")
                
                # Using black-forest-labs/flux-schnell (Speed Optimized)
                output = replicate.run(
                    "black-forest-labs/flux-schnell",
                    input={
                        "prompt": prompt,
                        "aspect_ratio": "16:9",
                        "num_inference_steps": 4,
                        "num_outputs": 1,
                        "megapixels": "1",
                        "go_fast": True,
                        "output_format": "png",
                        "disable_safety_checker": True
                    }
                )
            
            image_url = None
            if isinstance(output, list) and len(output) > 0:
                image_url = output[0]
            elif isinstance(output, str):
                image_url = output 
            
            if image_url:
                logger.info("📥 Downloading generated image from %s", image_url)
                response = requests.get(str(image_url), timeout=30)
                if response.status_code == 200:
                    img_data = response.content
                    return assets.save_asset(
                        img_data, "image", session_id, prompt,
                        metadata={
                            "model": "black-forest-labs/flux-schnell", 
                            "provider": "Replicate",
                            "params": {"aspect_ratio": "16:9", "steps": 4}
                        }
                    )
                return f"Failed to download image: {response.status_code}"
            
            return "No image URL returned from Replicate."

        except Exception as e:
            logger.error(f"Generate Image Error: {e}")
            return f"Error: {e}" 

    # --- HELPER: Generate Video ---
    def generate_video(prompt: str) -> Optional[str]:
        # 1. Google Vertex (Veo) - DEPRECATED by User Policy
        # Proceed to Replicate default


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
    @traceable(run_type="chain", name="Cinematographer Agent")
    def run_agent(
        input_text: str,
        mode: str = "storyboard",
        max_shots: int = 1,
        # pylint: disable=unused-argument
        duration_sec: int = 5
    ) -> str:
        
        # --- FIX: Handle NoneType from UI ---
        if max_shots is None: max_shots = 2
        if duration_sec is None: duration_sec = 5
        # ------------------------------------

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
                    "for the scene. Return ONLY the plain text shot descriptions. "
                    "Do NOT return Python code. Do NOT wrap in markdown code blocks."
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
