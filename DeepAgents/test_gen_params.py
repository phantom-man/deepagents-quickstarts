
import os
import replicate
from dotenv import load_dotenv

load_dotenv(".env")

try:
    print("Testing Lyria-2...")
    model = "google/lyria-2"
    # Basic run
    output = replicate.run(
        model,
        input={
            "prompt": "An upbeat techno loop",
            # "duration": 5 # Not supported
        }
    )
    print("Success:", output)
except Exception as e:
    print(f"Lyria Failed: {e}")

try:
    print("\nTesting Minimax Music-01 with Voice File...")
    model = "minimax/music-01"
    voice_path = r"Artifacts\Audio\Voices\male_deep_narrator_ref.wav" # Using path from context or similar
    # Adjust path if needed
    if not os.path.exists(voice_path):
         # Search for a valid voice file
         import glob
         voices = glob.glob("Artifacts/Audio/Voices/*.mp3")
         if voices:
             voice_path = voices[0]
         else:
             print("No voice file found")
             voice_path = None

    if voice_path:
        print(f"Using voice: {voice_path}")
        with open(voice_path, "rb") as f:
            output = replicate.run(
                model,
                input={
                    "lyrics": "Hello world, this is a test song.",
                    "voice_file": f
                }
            )
        print("Minimax Success:", output)
except Exception as e:
    print(f"Minimax Failed: {e}")
