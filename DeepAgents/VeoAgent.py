import os
import time
from google import genai
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

def load_canonical_ontology(role_name):
    """Loads the ontology file to refresh agent context."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "Canon", f"{role_name}_Ontology.md")
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            print(f"✅ {role_name} Ontology Refreshed ({len(content)} chars)")
            return content
    except FileNotFoundError:
        print(f"⚠️ Warning: Ontology for {role_name} not found at {path}")
        return ""

# Refresh Context
cinematographer_canon = load_canonical_ontology("Cinematographer")

def refine_prompt_with_thinking(raw_prompt):
    """Uses a Reasoning Model to refine the prompt based on the Cinematographer Ontology."""
    print("🧠 Cinematographer is thinking... (Refining Prompt)")
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-3-pro-preview",
        temperature=0.7,
        model_kwargs={"thinking_mode": "high"}
    )
    
    system_prompt = f"""You are the **Cinematographer Agent**. 
    Your goal is to translate a raw concept into a perfect prompt for the Google Veo Video Generation Model.
    
    **YOUR BRAIN (ONTOLOGY):**
    {cinematographer_canon}
    
    **TASK:**
    1. Analyze the user's request: "{raw_prompt}"
    2. Consult your Ontology regarding Lighting, Composition, Camera Movement, and Atmosphere.
    3. Output ONLY the optimized prompt for Veo. Do not include explanations.
    """
    
    response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=raw_prompt)])
    optimized_prompt = response.content.strip()
    print(f"✨ Optimized Prompt: {optimized_prompt}")
    return optimized_prompt

# Initialize Google Gen AI Client for Vertex AI
# Uses Application Default Credentials (ADC) from gcloud auth
project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
location = "us-central1" # Veo is available in us-central1

if not project_id:
    print("Error: GOOGLE_CLOUD_PROJECT not found in .env")
    exit(1)

print(f"Initializing Vertex AI Client for project: {project_id}")
client = genai.Client(vertexai=True, project=project_id, location=location)

def generate_video(model_name, prompt, output_file="output_video.mp4"):
    """Generates a video using the specified model."""
    print(f"\n--- Generating Video with {model_name} ---")
    print(f"Prompt: {prompt}")
    print("Waiting for generation (this may take a minute)...")

    try:
        # Generate content
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config={
                'response_mime_type': 'video/mp4' 
            }
        )
        
        # Check if we got a valid response
        # The structure of response might vary depending on the model/backend
        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            part = response.candidates[0].content.parts[0]
            
            if part.inline_data and part.inline_data.data:
                with open(output_file, "wb") as f:
                    f.write(part.inline_data.data)
                print(f"✅ Video saved to {output_file}")
            else:
                # Sometimes the video is a URI if it's large or on Vertex
                print(f"⚠️ Response received. Part: {part}")
        else:
            print("⚠️ Response received but no content parts found.")

    except Exception as e:
        print(f"❌ Error generating video: {e}")

if __name__ == "__main__":
    # Target model
    model_name = "veo-3.1-fast-generate-001" 
    
    # Example usage
    raw_input = "A cinematic drone shot of a futuristic city at sunset, cyberpunk style"
    
    # PHASE 1: THINKING / REFINEMENT
    # Translating raw input into Ontologically correct Veo prompt
    optimized_prompt = refine_prompt_with_thinking(raw_input)
    
    # Create output directory following best practices (separate folder for artifacts)
    output_dir = os.path.join(os.path.dirname(__file__), "generated_videos")
    os.makedirs(output_dir, exist_ok=True)
    
    # Timestamp the filename to avoid overwriting
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    output_path = os.path.join(output_dir, f"veo_test_{timestamp}.mp4")

    # PHASE 2: GENERATION
    generate_video(model_name, optimized_prompt, output_file=output_path)
    
    print(f"VeoAgent configured for {model_name} using Google Gen AI SDK.")
