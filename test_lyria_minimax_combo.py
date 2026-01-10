
import os
import replicate
import time
import requests
from dotenv import load_dotenv

# Load from DeepAgents folder
env_path = os.path.join(os.path.dirname(__file__), 'DeepAgents', '.env')
load_dotenv(env_path)

def test_combo():
    print("🎵 Testing Lyria -> Minimax Pipeline...")
    
    # 1. Generate Instrumental (Lyria)
    print("1. Generating Base Track with Lyria-2...")
    # Fetch dynamically
    lyria_ver = replicate.models.get("google/lyria-2").latest_version
    lyria_output = replicate.run(
        f"google/lyria-2:{lyria_ver.id}",
        input={
            "prompt": "An upbeat electro-swing track with brass inputs and a catchy rhythm.",
        }
    )
    print(f"✅ Lyria URL: {lyria_output}")
    
    # Download
    lyria_filename = "combo_base.wav"
    with open(lyria_filename, "wb") as f:
        f.write(requests.get(lyria_output).content)
    print(f"💾 Saved {lyria_filename}")

    # Wait for rate limit safety (user request)
    print("⏳ Sleeping 5s for rate limits...")
    time.sleep(5)

    # 2. Add Vocals (Minimax)
    print("2. Adding Vocals with Minimax...")
    try:
        # Fetch latest version dynamically
        minimax_model = replicate.models.get("minimax/music-01")
        version = minimax_model.latest_version
        print(f"   Using Minimax Version: {version.id}")
        
        minimax_output = replicate.run(
            f"minimax/music-01:{version.id}",
            input={
                "song_path": open(lyria_filename, "rb"),
                "lyrics": "Neon lights in the city night / driving fast we feel the light / never gonna stop / until we reach the top",
                "model_name": "music_01"
            }
        )
        print(f"✅ Minimax Output: {minimax_output}")
        
         # Download
        final_filename = "combo_final.mp3"
        with open(final_filename, "wb") as f:
            f.write(requests.get(minimax_output).content)
        print(f"💾 Saved {final_filename}")
        
    except Exception as e:
        print(f"❌ Minimax Failed (Likely duration or codec issue): {e}")

if __name__ == "__main__":
    test_combo()
