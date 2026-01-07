import os
import time
import argparse
import uuid
from google import genai
from dotenv import load_dotenv
from langchain_google_vertexai import ChatVertexAI
from langchain_core.messages import SystemMessage, HumanMessage
from agent_brain import AgentMemory, AgentComms

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

# Initialize Brain Components
print("🎥 Connecting to Nervous System...")
try:
    memory = AgentMemory()
    comms = AgentComms(password="d1204l0723")
    if not comms.connect():
        print("❌ Failed to connect to Nervous System (Postgres)")
        exit(1)
except Exception as e:
    print(f"❌ Brain Connection Failed: {e}")
    exit(1)

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
    
    # Switched to VertexAI/ADC and accessible model
    llm = ChatVertexAI(
        model="gemini-2.0-flash-001",
        temperature=0.7,
        location="us-central1"
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
        return False
    return True

def generate_storyboard(prompt, output_file):
    """Generates a storyboard image using Imagen 3."""
    print(f"\n--- Generating Storyboard with imagen-3.0-generate-001 ---")
    print(f"Prompt: {prompt}")

    try:
        response = client.models.generate_images(
            model="imagen-3.0-generate-001",
            prompt=prompt,
            config={'aspect_ratio': '16:9'}
        )

        if response.generated_images:
            gen_img = response.generated_images[0]
            # Handle different SDK versions for Image object
            img_data = None
            
            # Check for image property (common in new SDK)
            if hasattr(gen_img, "image") and hasattr(gen_img.image, "image_bytes"):
                img_data = gen_img.image.image_bytes
            # Check for direct image_bytes
            elif hasattr(gen_img, "image_bytes"):
                img_data = gen_img.image_bytes
            
            if img_data:
                with open(output_file, "wb") as f:
                    f.write(img_data)
                print(f"✅ Storyboard saved to {output_file}")
                return True
            else:
                 # Attempt PIL Save if available
                if hasattr(gen_img, "image") and hasattr(gen_img.image, "save"):
                    gen_img.image.save(output_file)
                    print(f"✅ Storyboard saved to {output_file}")
                    return True
                else:
                    print(f"⚠️ Image object structure unknown: {dir(gen_img)}")
                    return False
        else:
            print("⚠️ No images returned.")

    except Exception as e:
        print(f"❌ Storyboard Generation Failed: {e}")
        return False
    return False

def run_cinematographer_loop(mode="full"):
    print(f"\n🎥 --- CINEMATOGRAPHER AGENT STANDING BY (Mode: {mode.upper()}) ---")
    print("Waiting for orders from Director...")
    
    # Ensure assets directory exists
    assets_dir = os.path.join(os.path.dirname(__file__), "generated_assets")
    os.makedirs(assets_dir, exist_ok=True)
    
    while True:
        # Check for messages
        try:
            messages = comms.check_inbox(recipient="Cinematographer")
        except Exception as e:
            print(f"Connection error: {e}, retrying...")
            time.sleep(5)
            continue
        
        if messages:
            for msg in messages:
                print(f"\n📩 Message Received from {msg['sender']}:")
                print(f"📄 Content: {msg['content'][:100]}...") 
                
                # 1. Refine the prompt
                refined_prompt = refine_prompt_with_thinking(msg['content'])
                
                # Unique ID for this job
                job_id = str(uuid.uuid4())[:8]
                report_lines = []
                
                # 2. Generate Storyboard (Always if mode is storyboard or full)
                if mode in ["storyboard", "full"]:
                    sb_filename = f"storyboard_{job_id}.png"
                    sb_path = os.path.join(assets_dir, sb_filename)
                    if generate_storyboard(refined_prompt, sb_path):
                        report_lines.append(f"Storyboard created: {sb_filename}")
                        # Store in Memory
                        memory.memorize(
                            f"Created Storyboard for '{msg['content']}'", 
                            "Cinematographer", 
                            tags=["asset", "storyboard", sb_path]
                        )
                    else:
                        report_lines.append("Storyboard generation failed.")

                # 3. Generate Video (Only if mode is full)
                if mode == "full":
                    vid_filename = f"video_{job_id}.mp4"
                    vid_path = os.path.join(assets_dir, vid_filename)
                    # Note: generate_video from earlier in file needs a signature update or we handle signature mismatch
                    # Actually, the original signature was generate_video(model_name, prompt, output_file="output_video.mp4")
                    # We should match that.
                    if generate_video("veo-2.0-generate-001", refined_prompt, vid_path):
                        report_lines.append(f"Video created: {vid_filename}")
                        # Store in Memory
                        memory.memorize(
                            f"Created Video for '{msg['content']}'", 
                            "Cinematographer", 
                            tags=["asset", "video", vid_path]
                        )
                    else:
                        report_lines.append("Video generation failed.")
                elif mode == "storyboard":
                    report_lines.append("Video generation skipped (Mode: Storyboard Only).")

                # 4. Report back
                final_report = " | ".join(report_lines)
                comms.send_message(sender="Cinematographer", recipient="Director", content=final_report)
                print(f"✅ Report sent to Director: {final_report}")
                
        else:
            time.sleep(5) # Poll every 5 seconds

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cinematographer Agent")
    parser.add_argument("--mode", type=str, choices=["storyboard", "full"], default="storyboard", 
                        help="Operation mode: 'storyboard' (images only) or 'full' (images + video)")
    args = parser.parse_args()
    
    run_cinematographer_loop(mode=args.mode)

