import os

from dotenv import load_dotenv
from google import genai

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
location = "us-central1"

print(f"Initializing Vertex AI Client for project: {project_id}")
client = genai.Client(vertexai=True, project=project_id, location=location)

models_to_test = [
    "veo-3.1-fast-generate-001",  # The one we want (0.10/sec)
    "veo-3.1-generate-001",  # Standard (0.20/sec)
    "veo-2.0-generate-001",  # Older version
]

user_prompt = "A cinematic drone shot of a futuristic city at sunset, cyberpunk style"
output_dir = os.path.join(os.path.dirname(__file__), "../Artifacts/Video")
os.makedirs(output_dir, exist_ok=True)

print("\n--- Starting Quota Probe ---")

for model_name in models_to_test:
    print(f"\nTesting model: {model_name}...")
    try:
        # Save to a dummy file
        output_file = os.path.join(output_dir, f"probe_{model_name}.mp4")

        # Determine duration based on model capabilities (Veo 3.0+ supports 4s, 6s, 8s)
        # We assume default or simple config
        response = client.models.generate_content(
            model=model_name,
            contents=user_prompt,
            config={"response_mime_type": "video/mp4"},
        )

        # Check success
        if response.candidates and response.candidates[0].content:
            print(f"✅ SUCCESS! Model {model_name} is active.")
            if response.candidates[0].content.parts:
                part = response.candidates[0].content.parts[0]
                if part.inline_data and part.inline_data.data:
                    with open(output_file, "wb") as f:
                        f.write(part.inline_data.data)
                    print(f"   Video saved to {output_file}")
            break  # Stop after first success
        else:
            print(f"⚠️ Response empty for {model_name}")

    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg and "RESOURCE_EXHAUSTED" in error_msg:
            print(f"❌ Quota exceeded for {model_name} (Limit is still 0)")
        elif "404" in error_msg:
            print(f"❌ Model not found/available: {model_name}")
        else:
            print(f"❌ Error: {error_msg}")

print("\n--- Probe Complete ---")
