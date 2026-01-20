
import os
import time
from dotenv import load_dotenv

# Load Environment
load_dotenv("DeepAgents/.env")

project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
location = "us-central1"
model_id = "gemini-2.0-flash-001"

# 10 Random Questions
questions = [
    "What is the airspeed velocity of an unladen swallow?",
    "Explain quantum entanglement to a 5-year-old.",
    "Write a haiku about a crashing server.",
    "Who won the World Series in 1982?",
    "What are the three laws of robotics?",
    "Convert 100 degrees Celsius to Fahrenheit.",
    "What is the capital of Assyria?",
    "Why is the sky blue?",
    "Write a Python function to reverse a string.",
    "What comes after a million?"
]

print(f"🧪 Starting Load Test for {model_id}...")
print("   SDK: google.genai (Modern)")
print(f"   Questions: {len(questions)}")
print("   Rate: 1 request / 5 seconds\n")

try:
    from google import genai
    
    client = genai.Client(
        vertexai=True,
        project=project_id,
        location=location
    )
    
    success_count = 0
    
    for i, q in enumerate(questions, 1):
        print(f"[{i}/{len(questions)}] Asking: {q}")
        start_time = time.time()
        
        try:
            response = client.models.generate_content(
                model=model_id,
                contents=q
            )
            elapsed = time.time() - start_time
            print(f"   ✅ Answered in {elapsed:.2f}s: {response.text[:50]}...")
            success_count += 1
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            
        if i < len(questions):
            print("   ⏳ Waiting 5s...")
            time.sleep(5)
            
    print(f"\n✅ Test Complete. Success: {success_count}/{len(questions)}")

except ImportError:
    print("❌ Critical: google-genai SDK not installed.")
except Exception as e:
    print(f"❌ Critical Error: {e}")
