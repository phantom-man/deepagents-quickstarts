
import os
import sys
from dotenv import load_dotenv

# Load Env
load_dotenv("DeepAgents/.env")

project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
location = "us-central1" # User specified region

print(f"🔍 Probing using google-genai SDK...")
print(f"   Project: {project_id}")
print(f"   Location: {location}")

try:
    from google import genai
    from google.genai import types
    
    print("✅ google.genai SDK imported successfully.")
    
    client = genai.Client(
        vertexai=True,
        project=project_id,
        location=location
    )
    
    models_to_test = [
        "gemini-2.0-flash",
        "gemini-2.0-flash-001",
        "gemini-2.0-pro-exp-02-05", 
        "gemini-2.0-flash-lite-preview-02-05" 
    ]
    
    for model in models_to_test:
        print(f"\n🧪 Testing Model: {model}")
        try:
            response = client.models.generate_content(
                model=model,
                contents="Ping"
            )
            print(f"   ✅ SUCCESS! Response: {response.text}")
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            
except ImportError:
    print("❌ google-genai SDK not found.")
except Exception as e:
    print(f"❌ Critical Error: {e}")
