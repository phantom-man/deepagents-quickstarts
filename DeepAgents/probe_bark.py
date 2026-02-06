import time

import replicate
from dotenv import load_dotenv

load_dotenv("DeepAgents/.env")


def test_bark():
    print("Testing Bark...")
    try:
        # Check model
        model = replicate.models.get("suno-ai/bark")
        version = model.latest_version
        if version is None:
            print("No version available for Bark")
            return
        print(f"Using Bark Version: {version.id}")

        start = time.time()
        output = replicate.run(
            f"suno-ai/bark:{version.id}",
            input={
                "prompt": "Hello, I am testing the generation speed.",
                "text_temp": 0.7,
            },
        )
        duration = time.time() - start
        print(f"Success in {duration:.2f}s: {output}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_bark()
