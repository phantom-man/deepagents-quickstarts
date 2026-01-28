import os

from dotenv import load_dotenv
from google import genai

load_dotenv()
project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
location = "us-central1"

print(f"Listing available models in project {project_id} ({location})...")
client = genai.Client(vertexai=True, project=project_id, location=location)

print("Listing available models...")
try:
    print("--- START MODEL LIST ---")
    # Pager object, iterate to get models
    for m in client.models.list():
        # Print name and display name if available
        print(f"- {m.name} ({m.display_name})")
    print("--- END MODEL LIST ---")
except Exception as e:
    print(f"Error: {e}")
