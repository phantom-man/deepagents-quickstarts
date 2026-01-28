import sys

import replicate
from dotenv import load_dotenv

load_dotenv("DeepAgents/.env")

# Model from agent.py
model = "minimax/music-01"

print(f"DEBUG: Testing {model}...")

# Test 1: Full inputs (Prompt + Lyrics)
inputs_full = {
    "prompt": "Orchestral epic music, 80s synthwave style.",
    "lyrics": "This is a test song / We are checking the API / Minimax please work",
}

try:
    print("\nAttempt 1: Prompt + Lyrics")
    output = replicate.run(model, input=inputs_full)
    print("SUCCESS:", output)
    sys.exit(0)
except Exception as e:
    print("FAILED:", e)

# Test 2: Prompt Only
inputs_prompt = {"prompt": "Orchestral epic music, 80s synthwave style."}

try:
    print("\nAttempt 2: Prompt Only")
    output = replicate.run(model, input=inputs_prompt)
    print("SUCCESS:", output)
    sys.exit(0)
except Exception as e:
    print("FAILED:", e)
