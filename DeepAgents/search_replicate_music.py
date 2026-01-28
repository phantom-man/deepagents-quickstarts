import os

import replicate
from dotenv import load_dotenv

# Load Env
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

import sys

print("X" * 50)
print("STARTING REPLICATE SEARCH")
print("X" * 50)
sys.stdout.flush()

search_terms = [
    "music",
    "song",
    "minimax",
    "suno",
    "udio",
    "riffusion",
    "stable audio",
    "ace-step",
]

print("Searching Replicate for music models with lyrics/vocal support...")

seen_models = set()

for term in search_terms:
    print(f"\n--- Searching for '{term}' ---")
    try:
        results = replicate.models.search(term)
        for model in results:
            if model.owner + "/" + model.name in seen_models:
                continue
            seen_models.add(model.owner + "/" + model.name)

            # Filter for music/audio related (though search term helps)
            desc = (model.description or "").lower()
            name = model.name.lower()

            # Check for lyric/vocal keywords in description
            has_lyrics_mention = any(
                w in desc for w in ["lyric", "vocal", "sing", "voice", "speech"]
            )

            # Get schema to be sure
            try:
                if model.latest_version:
                    schema = model.latest_version.openapi_schema
                    inputs = (
                        schema.get("components", {})
                        .get("schemas", {})
                        .get("Input", {})
                        .get("properties", {})
                    )

                    # Check for lyrics input
                    has_lyrics_input = (
                        "lyrics" in inputs or "text" in inputs or "vocals" in inputs
                    )

                    # Check duration
                    duration_info = inputs.get("duration", {})
                    max_duration = duration_info.get("maximum", "Unknown")
                    default_duration = duration_info.get("default", "Unknown")

                    # If strictly searching for lyrics support
                    if has_lyrics_mention or has_lyrics_input:
                        print(f"\nModel: {model.owner}/{model.name}")
                        print(f"  Description: {model.description}")
                        print(
                            f"  URL: https://replicate.com/{model.owner}/{model.name}"
                        )
                        print(
                            f"  Lyrics Input Found: {has_lyrics_input} (Keys: {list(inputs.keys())})"
                        )
                        print(
                            f"  Duration: Max={max_duration}, Default={default_duration}"
                        )
                        # print(f"  Run Count: {model.run_count}") # run_count might not be available on object
            except Exception:
                # print(f"  Could not fetch version details for {model.name}: {e}")
                pass

    except Exception as e:
        print(f"Error searching for {term}: {e}")
