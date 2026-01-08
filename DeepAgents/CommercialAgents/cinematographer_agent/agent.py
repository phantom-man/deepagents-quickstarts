import os
import time
from google import genai
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_vertexai import ChatVertexAI
from langchain_anthropic import ChatAnthropic

from DeepAgents.agent_brain import logger
from DeepAgents.asset_manager import AssetManager

def create_cinematographer_agent(model_config=None, brain=None, session_id="default"):
    """
    Factory to create the Cinematographer Agent runner.
    """
    if model_config is None:
        model_config = {"provider": "Google", "model": "gemini-1.5-pro"}

    # Configurations
    provider = model_config.get("provider", "Google")
    model_name = model_config.get("model", "gemini-1.5-pro")
    
    img_provider = model_config.get("image_provider", "Google")
    img_model = model_config.get("image_model", "imagen-3.0-generate-001")
    
    vid_provider = model_config.get("video_provider", "Google")
    vid_model = model_config.get("video_model", "veo-2.0-generate-001")

    # Asset Manager
    assets = AssetManager()

    # 1. Initialize Brain LLM (for Storyboarding)
    try:
        if provider == "Google":
            llm = ChatVertexAI(model_name=model_name, temperature=0.7)
        elif provider == "Anthropic":
            llm = ChatAnthropic(
                model_name=model_name, 
                temperature=0.7, 
                timeout=None, stop=None
            )
        else:
            llm = ChatVertexAI(model_name="gemini-1.5-pro")
    except Exception as e:
        logger.error(f"Cinematographer LLM Init Failed: {e}")
        return None

    # 2. Initialize Generative Client (Vertex)
    # We use google-genai SDK for Imagen/Veo as per previous patterns
    gen_client = None
    try:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        location = "us-central1"
        if project_id:
            gen_client = genai.Client(vertexai=True, project=project_id, location=location)
    except Exception as e:
        logger.error(f"GenAI Client Init Failed: {e}")

    # load ontology
    try:
        ontology_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../../Canon/Cinematographer_Ontology.md"
        )
        if os.path.exists(ontology_path):
            with open(ontology_path, "r", encoding="utf-8") as f:
                ontology = f.read()
        else:
            ontology = "You are a Cinematographer Agent."
    except Exception as e:
        ontology = "You are a Cinematographer Agent."

    # --- HELPER: Generate Image ---
    def generate_image(prompt):
        if not gen_client: return "Error: No GenAI Client"
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
                # Save Asset
                path = assets.save_asset(img_data, "image", session_id, prompt, metadata={"model": img_model})
                return path
            return None
        except Exception as e:
            return f"Image Gen Error: {e}"

    # --- HELPER: Generate Video ---
    def generate_video(prompt):
        if not gen_client: return "Error: No GenAI Client"
        try:
            # Veo generation prompt
            response = gen_client.models.generate_content(
                model=vid_model,
                contents=prompt,
                config={
                    'response_mime_type': 'video/mp4'
                }
            )
            # Veo usually returns a URI or inline data. 
            # SDK might vary, handling inline data primarily
            if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                part = response.candidates[0].content.parts[0]
                if part.inline_data:
                     # Save Asset
                    path = assets.save_asset(part.inline_data.data, "video", session_id, prompt, metadata={"model": vid_model})
                    return path
            return None
        except Exception as e:
             return f"Video Gen Error: {e}"


    # 2. Define the Runner Function
    def run_agent(input_text, mode="storyboard"):
        logger.info(f"🎥 Cinematographer receiving input: {input_text[:50]}...")
        
        # A. Analyze / Storyboard Phase
        messages = [
            SystemMessage(content=f"{ontology}\n\nCreate a visual description for the scene."),
            HumanMessage(content=input_text)
        ]
        
        try:
            # Use LLM to refine the prompt
            response = llm.invoke(messages)
            visual_plan = response.content
            
            output_report = f"**Visual Analysis**:\n{visual_plan}\n\n"
            
            # B. Generate Assets if requested
            # We assume the LLM output contains a distinct PROMPT section or we just use the plan
            # For simplicity, we'll ask the LLM to give us a clean prompt in a second pass or regex
            # But let's just use the visual plan as the prompt for now, or truncated
            
            gen_prompt = visual_plan[:400] # Limit prompt length
            
            # Generate Image (Storyboard)
            img_path = generate_image(gen_prompt)
            if img_path and "Error" not in img_path:
                output_report += f"**Storyboard Image**:\nFile: `{img_path}`\n"
            elif img_path:
                output_report += f"**Image Status**: {img_path}\n"
                
            # Generate Video (Motion) - Only if explicitly asked or defaults?
            # Creating video is expensive/slow, maybe optional?
            # For now, let's do it if mode says so
            if mode == "video":
                vid_path = generate_video(gen_prompt)
                if vid_path and "Error" not in vid_path:
                    output_report += f"**Video Generated**:\nFile: `{vid_path}`\n"
                elif vid_path:
                    output_report += f"**Video Status**: {vid_path}\n"
            
            return output_report
            
        except Exception as e:
            logger.error(f"Cinematographer Error: {e}")
            return f"Error: {e}"

    return run_agent
