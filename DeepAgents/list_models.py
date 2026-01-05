import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

print("Listing available models...")
try:
    for m in client.models.list():
        if m.supported_actions and "generateContent" in m.supported_actions:
            print(f"- {m.name}")
except Exception as e:
    print(f"Error: {e}")
