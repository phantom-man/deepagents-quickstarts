import os
import time

import replicate
import requests
from dotenv import load_dotenv

# Load from DeepAgents folder
env_path = os.path.join(os.path.dirname(__file__), "DeepAgents", ".env")
load_dotenv(env_path)


def test_combo_fixed():
    print("🎵 Testing Lyria -> Minimax Pipeline (FIXED)...")

    # 1. Generate Instrumental (Lyria)
    print("1. Generating Base Track with Lyria-2...")
    try:
        lyria_output = replicate.run(
            "google/lyria-2:bb621623ee2772c96d300b2a303c9e444b482f6b0fafcc7424923e1429971120",
            input={
                "prompt": "A continuous 20 second synthwave loop, high energy.",
            },
        )
        print(f"✅ Lyria URL: {lyria_output}")
    except Exception as e:
        print(f"❌ Lyria Failed: {e}")
        return

    # Download with explicit extension
    lyria_filename = "combo_base_fixed.wav"
    with open(lyria_filename, "wb") as f:
        f.write(requests.get(str(lyria_output)).content)
    print(f"💾 Saved {lyria_filename}")

    # Wait for rate limit safety
    print("⏳ Sleeping 5s...")
    time.sleep(5)

    # 2. Add Vocals (Minimax)
    print("2. Adding Vocals with Minimax...")
    try:
        # Fetch latest version dynamically
        minimax_model = replicate.models.get("minimax/music-01")
        version = minimax_model.latest_version
        if version is None:
            print("❌ Could not get Minimax version")
            return

        # CORRECT PARAMETER: 'instrumental_file' not 'song_path'
        # Also passing empty lyrics to see if it generates just humming or requires lyrics?
        # Schema says lyrics default is "".

        minimax_output = replicate.run(
            f"minimax/music-01:{version.id}",
            input={
                "instrumental_file": open(
                    lyria_filename, "rb"
                ),  # explicit .wav file on disk
                "lyrics": "This is a test of the emergency broadcast system.",
                "model_name": "music_01",
            },
        )
        print(f"✅ Minimax Output: {minimax_output}")

    except Exception as e:
        print(f"❌ Minimax Failed: {e}")


if __name__ == "__main__":
    test_combo_fixed()
