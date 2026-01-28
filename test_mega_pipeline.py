import os
import time

import replicate
import requests
from dotenv import load_dotenv

# Load from DeepAgents folder
env_path = os.path.join(os.path.dirname(__file__), "DeepAgents", ".env")
load_dotenv(env_path)


def test_mega_pipeline():
    print("🚀 Starting Mega Pipeline Test...")

    # 1. Voice Generation (Bark)
    print("\n🗣️ 1. Generating Voice (Bark) - Target >15s...")
    long_prompt = (
        "Hello, I am speaking for a very long time to ensure this file is over fifteen seconds long. "
        "I will keep talking about the weather, the blue sky, the fluffy clouds, and the infinite vastness of space. "
        "Hopefully this is enough audio to satisfy the Minimax requirement of fifteen seconds. "
        "Just to be sure, I will add one more sentence here."
    )
    try:
        voice_output = replicate.run(
            "suno-ai/bark:b76242b40d67c76ab6742e987628a2a9ac019e11d56ab96c4e91ce03b79b2787",
            input={"prompt": long_prompt, "text_temp": 0.7},
        )
        # Bark returns dict or object depending on version
        if isinstance(voice_output, dict):
            voice_url = voice_output["audio_out"]
        else:
            voice_url = str(voice_output)

        print(f"✅ Voice URL: {voice_url}")

        # Download
        voice_file = "test_voice.wav"
        with open(voice_file, "wb") as f:
            f.write(requests.get(voice_url).content)
        print(f"💾 Saved {voice_file}")

    except Exception as e:
        print(f"❌ Voice Gen Failed: {e}")
        return

    time.sleep(2)

    # 2. Music Generation (MusicGen - More robust format)
    print("\n🎹 2. Generating Music (MusicGen)...")
    try:
        # Using MusicGen because Lyria output format (codec) might be incompatible with Minimax
        # and we lack ffmpeg to convert.
        lyria_output = replicate.run(
            "meta/musicgen:b05b1dff1d8c6dc63d14b0cdb42135378dcb87f6373b0d3d341ede46e59e2b38",
            input={
                "prompt": "A continuous 20 second synthwave loop, high energy.",
                "duration": 20,
            },
        )
        print(f"✅ MusicGen URL: {lyria_output}")

        lyria_file = "test_music.wav"
        with open(lyria_file, "wb") as f:
            f.write(requests.get(str(lyria_output)).content)
        print(f"💾 Saved {lyria_file}")

    except Exception as e:
        print(f"❌ MusicGen Failed: {e}")
        return

    time.sleep(5)

    # 3. Combination (Minimax)
    print("\n🎤 3. Combining with Minimax...")
    try:
        minimax_model = replicate.models.get("minimax/music-01")
        version = minimax_model.latest_version
        if version is None:
            print("❌ Could not get Minimax version")
            return

        minimax_output = replicate.run(
            f"minimax/music-01:{version.id}",
            input={
                "instrumental_file": open(lyria_file, "rb"),
                "voice_file": open(voice_file, "rb"),
                "lyrics": "Neon lights in the city night, we are driving fast.",
                "model_name": "music_01",
            },
        )
        print(f"✅ Minimax Output: {minimax_output}")

        final_file = "test_final.mp3"
        with open(final_file, "wb") as f:
            f.write(requests.get(str(minimax_output)).content)
        print(f"🎉 Saved {final_file}")

    except Exception as e:
        print(f"❌ Minimax Failed: {e}")


if __name__ == "__main__":
    test_mega_pipeline()
