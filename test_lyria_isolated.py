
import os
import replicate
import requests
from dotenv import load_dotenv

# Load from DeepAgents folder
env_path = os.path.join(os.path.dirname(__file__), 'DeepAgents', '.env')
load_dotenv(env_path)

def test_lyria():
    print("🎵 Testing Google Lyria-2...")
    try:
        output = replicate.run(
            "google/lyria-2:bb621623ee2772c96d300b2a303c9e444b482f6b0fafcc7424923e1429971120",
            input={
                "prompt": "An upbeat electro-swing track with brass inputs and a catchy rhythm.",
                "negative_prompt": "low quality, static, noise"
            }
        )
        print(f"✅ Lyria Output: {output}")
        
        # Save it
        if output:
            response = requests.get(output)
            with open("lyria_test_output.wav", "wb") as f: # Assuming wav, will check header usually
                f.write(response.content)
            print("💾 Saved to lyria_test_output.wav")
            return "lyria_test_output.wav"
            
    except Exception as e:
        print(f"❌ Lyria Failed: {e}")
        return None

if __name__ == "__main__":
    test_lyria()
