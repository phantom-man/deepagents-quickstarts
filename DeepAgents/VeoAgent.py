import os
import time
from google import genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("Error: GOOGLE_API_KEY not found in .env")
    exit(1)

client = genai.Client(api_key=api_key)

def check_veo_availability():
    """Checks if a Veo model is visible to your API key."""
    print("Checking available models...")
    found = False
    try:
        for m in client.models.list():
            if m.name and "veo" in m.name.lower():
                print(f"✅ Found Veo model: {m.name}")
                found = True
                return m.name
    except Exception as e:
        print(f"Warning: Could not list models: {e}")
    
    if not found:
        print("❌ No 'veo' model found in your list. You may need to apply for Trusted Tester access.")
        # Fallback to a known preview name if not listed but potentially accessible
        return "veo-001" 

def generate_video(model_name, prompt):
    """Generates a video using the specified model."""
    print(f"\n--- Generating Video with {model_name} ---")
    print(f"Prompt: {prompt}")
    print("Waiting for generation (this may take a minute)...")

    try:
        # Generate content
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        
        # Check if we got a valid response
        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            part = response.candidates[0].content.parts[0]
            output_file = "output_video.mp4"
            
            if part.inline_data and part.inline_data.data:
                with open(output_file, "wb") as f:
                    f.write(part.inline_data.data)
                print(f"✅ Video saved to {output_file}")
            else:
                print("⚠️ Response received but no inline video data found.")
        else:
            print("⚠️ Response received but no content parts found.")

    except Exception as e:
        print(f"❌ Error generating video: {e}")

if __name__ == "__main__":
    # 1. Check for model name
    model_name = check_veo_availability()
    
    # 2. Run generation
    #user_prompt = "A cinematic drone shot of a futuristic city at sunset, cyberpunk style"
    #generate_video(model_name, user_prompt)
