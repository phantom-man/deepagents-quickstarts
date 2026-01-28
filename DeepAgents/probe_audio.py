import os

from dotenv import load_dotenv
from google import genai

load_dotenv()
project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
location = "us-central1"

print(f"Testing Audio Generation in project {project_id}...")
client = genai.Client(vertexai=True, project=project_id, location=location)

models_to_test = ["gemini-2.0-flash-exp", "gemini-2.5-flash"]

for model_id in models_to_test:
    print(f"\n--- Testing {model_id} ---")
    try:
        response = client.models.generate_content(
            model=model_id,
            contents="Generate a short 5-second audio clip of a jazz saxophone solo.",
            config={"response_mime_type": "audio/wav"},
        )
        # Check if we got audio back
        if response.candidates and response.candidates[0].content.parts:
            part = response.candidates[0].content.parts[0]
            # Check for inline data (blob)
            if hasattr(part, "inline_data") and part.inline_data:
                print("✅ SUCCESS: Model returned inline data (likely audio).")
                with open(f"test_audio_{model_id}.wav", "wb") as f:
                    f.write(part.inline_data.data)
                    print(f"   Saved to test_audio_{model_id}.wav")
            else:
                print("⚠️ Model returned text (or other) instead of audio data.")
                print(f"   Response: {part.text}")
        else:
            print("❌ No candidates returned.")

    except Exception as e:
        print(f"❌ Error testing {model_id}: {e}")
