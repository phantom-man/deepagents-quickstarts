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
from langchain_google_vertexai import ChatVertexAI
from langchain_anthropic import ChatAnthropic

# Local imports
from DeepAgents.agent_brain import logger
from DeepAgents.asset_manager import AssetManager

# Handle optional dependencies
try:
    import replicate
except ImportError:
    replicate = None

def _initialize_llm(provider: str, model_name: str) -> Any:
    """Initialize the LLM based on provider."""
    try:
        if provider == "Google":
            return ChatVertexAI(model_name=model_name, temperature=0.7)
        if provider == "Anthropic":
            return ChatAnthropic(
                model_name=model_name,
                temperature=0.7,
                timeout=None,
                stop=None
            )
        # Default fallback
        return ChatVertexAI(model_name="gemini-1.5-pro")
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

def _load_ontology() -> str:
    """Load the agent ontology."""
    try:
        ontology_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../../Canon/Cinematographer_Ontology.md"
        )
        if os.path.exists(ontology_path):
            with open(ontology_path, "r", encoding="utf-8") as f:
                return f.read()
    except Exception: # pylint: disable=broad-exception-caught
        pass
    return "You are a Cinematographer Agent."

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
        model_config = {"provider": "Google", "model": "gemini-1.5-pro"}

    # Configurations
    provider = model_config.get("provider", "Google")
    model_name = model_config.get("model", "gemini-1.5-pro")

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
    ontology = _load_ontology()

    # --- HELPER: Generate Image ---
    def generate_image(prompt: str) -> Optional[str]:
        if not gen_client:
            return "Error: No GenAI Client"
        try:
            # Call Imagen
            response = gen_client.models.generate_images(
                model=img_model,
                prompt=prompt,
                config={
                    'number_of_images': 1,
                    # 'aspect_ratio': '16:9' # optional
                }
            )
            if response.generated_images and response.generated_images[0].image:
                img_data = response.generated_images[0].image.image_bytes
                if img_data:
                    # Save Asset
                    path = assets.save_asset(
                        img_data, "image", session_id, prompt,
                        metadata={"model": img_model}
                    )
                    return path
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
