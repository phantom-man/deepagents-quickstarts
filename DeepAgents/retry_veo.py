import os
import time
from google import genai
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
location = "us-central1"
model_name = "veo-3.1-fast-generate-001"
prompt = "A cinematic drone shot of a futuristic city at sunset, cyberpunk style"

print(f"Initializing Vertex AI Client for project: {project_id}")
client = genai.Client(vertexai=True, project=project_id, location=location)

output_dir = os.path.join(os.path.dirname(__file__), "../Artifacts/Video")
os.makedirs(output_dir, exist_ok=True)

print(f"--- Starting Auto-Retry for {model_name} ---")
print("Press Ctrl+C to stop manually.")

attempt = 1
models_to_try = ["veo-3.1-fast-generate-001", "veo-2.0-generate-001"]

while True:
    timestamp = time.strftime("%H:%M:%S")
    
    for model in models_to_try:
        print(f"[{timestamp}] Attempt {attempt} ({model}): Requesting video generation...")
        
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config={'response_mime_type': 'video/mp4'}
            )
            
            if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                part = response.candidates[0].content.parts[0]
                if part.inline_data and part.inline_data.data:
                    # Success!
                    filename = f"{model}_success_{time.strftime('%Y%m%d-%H%M%S')}.mp4"
                    output_path = os.path.join(output_dir, filename)
                    with open(output_path, "wb") as f:
                        f.write(part.inline_data.data)
                    print(f"\n✅ SUCCESS! Video saved to: {output_path}")
                    exit(0) # Exit fully
                else:
                    print(f"⚠️ Response received but no inline data. Part: {part}")
            else:
                print("⚠️ Response received but no content parts.")

        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                # Quota exceeded, just continue to next model/attempt
                pass
            else:
                print(f"❌ Unexpected Error with {model}: {e}")
                # Don't exit, try next model

    print(f"⏳ Quota exceeded for all models. Retrying in 30 seconds...")
    time.sleep(30)
    attempt += 1
