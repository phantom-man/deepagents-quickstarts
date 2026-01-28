import logging
import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Setup
logging.basicConfig(level=logging.ERROR)
load_dotenv("DeepAgents/.env")

# Candidates from User's List + Variants
candidates = [
    # Gemini 2.0 Family (Verified)
    "gemini-2.0-flash-001",
    # Gemini 1.5 Family (Quota: 4M TPM)
    "gemini-1.5-flash",
    "gemini-1.5-flash-001",
    "gemini-1.5-flash-002",
    "gemini-1.5-pro",
    "gemini-1.5-pro-002",
    # Gemini 2.0 Family (Quota: 5000 Concurrent?)
    "gemini-2.0-flash-live",  # Failed before, but user listed it
    "gemini-experimental",
    # MaaS Models (Quota: 30-600 RPM)
    # These often need specific publisher paths or endpoints
    "publishers/deepseek/models/deepseek-r1-0528-maas",
    "deepseek-r1-0528-maas",
    "publishers/meta/models/llama-3.3-70b-instruct-maas",
    "llama-3.3-70b-instruct-maas",
]


def probe_model(model_name):
    print(f"📡 Probing: {model_name:<40}", end="")
    try:
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            vertexai=True,
            temperature=0,
            max_retries=0,
            location="us-central1",
        )
        resp = llm.invoke("Hi")
        print(f"✅ SUCCESS. Response: {resp.content[:20]}...")
        return True
    except Exception as e:
        err_str = str(e)
        if "404" in err_str:
            print("❌ 404 Not Found")
        elif "429" in err_str:
            print("⚠️ 429 Quota Exceeded")
        else:
            print(f"❌ Error: {err_str[:50]}...")
        return False


print("--- Starting Quota Candidate Probe ---")
print(f"Project: {os.getenv('GOOGLE_CLOUD_PROJECT')}")
print("Location: us-central1")

successful = []
for model in candidates:
    if probe_model(model):
        successful.append(model)

print("\n🏆 Working Models:")
for m in successful:
    print(f" - {m}")
