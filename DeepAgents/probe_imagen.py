import os
import google.auth
from google import genai
from dotenv import load_dotenv

# Load env for safety, though we rely on ADC
load_dotenv()

PROJECT_ID = "crafty-hook-483415-b3"
LOCATION = "us-central1"
# Imagen 3 model
MODEL_ID = "imagen-3.0-generate-001"

print(f"--- Probing Image Generation (Storyboard Mode) ---")
print(f"Project: {PROJECT_ID}")

try:
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
    
    print(f"Requesting IMAGE from {MODEL_ID}...")
    response = client.models.generate_image(
        model=MODEL_ID,
        prompt="A cinematic storyboard sketch of a robot discovering a gentle flower in a harsh wasteland, detailed, atmospheric",
        config={'aspect_ratio': '16:9'}
    )
    
    if response.generated_images:
        image = response.generated_images[0]
        output_file = "storyboard_test.png"
        image.save(output_file)
        print(f"✅ SUCCESS! Image saved to {output_file}")
    else:
        print("⚠️ No images returned.")

except Exception as e:
    print(f"❌ IMAGE GENERATION FAILED: {e}")
