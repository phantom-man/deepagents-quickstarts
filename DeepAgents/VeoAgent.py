import os
import time
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

def run_cinematographer_loop():
    print("\n🎥 --- CINEMATOGRAPHER AGENT STANDING BY ---")
    print("Waiting for orders from Director...")
    
    while True:
        # Check for messages
        # messages = brain.comms.get_messages(receiver="Cinematographer", unread_only=True)
        messages = comms.check_inbox(recipient="Cinematographer")
        
        if messages:
            for msg in messages:
                print(f"\n📩 Message Received from {msg['sender']}:")
                # check_inbox returns dicts with 'content'
                print(f"📄 Content: {msg['content'][:100]}...") 
                
                # 1. Refine the prompt
                refined_prompt = refine_prompt_with_thinking(msg['content'])
                
                # 2. Generate Video
                print(f"🎬 Rolling Camera on: {refined_prompt}")
                # Use Veo 2 (stable) or whatever is available, probe_veo suggested 'veo-2.0-generate-001'
                success = generate_video("veo-2.0-generate-001", refined_prompt)
                
                # 3. Report back
                if success:
                    report = f"Video generated successfully for prompt: {refined_prompt}"
                    # brain.speak(from_agent="Cinematographer", to_agent="Director", content=report)
                    comms.send_message(sender="Cinematographer", recipient="Director", content=report)
                    print("✅ Confirmation sent to Director")
                else:
                    report = f"Failed to generate video for prompt: {refined_prompt} (Resource Exhausted/Error)"
                    # brain.speak(from_agent="Cinematographer", to_agent="Director", content=report)
                    comms.send_message(sender="Cinematographer", recipient="Director", content=report)
                    print("⚠️ Failure report sent to Director")
                    
                # Store update in memory
                # brain.remember(f"Cinematographer Job: {msg['content']} -> Result: {success}")
                memory.memorize(f"Cinematographer Job: {msg['content']} -> Result: {success}", "Cinematographer", ["video_log"])
                
        else:
            time.sleep(5) # Poll every 5 seconds

if __name__ == "__main__":
    run_cinematographer_loop()

