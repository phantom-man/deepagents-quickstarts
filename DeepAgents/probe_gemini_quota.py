
import os
import google.auth
from langchain_google_genai import ChatGoogleGenerativeAI
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable, PermissionDenied

# Setup
PROJECT_ID = "crafty-hook-483415-b3"
REGION = "us-central1"

def test_model(model_name):
    print(f"--- Testing Quota for {model_name} ---")
    try:
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            project=PROJECT_ID,
            location=REGION,
            max_output_tokens=10
        )
        response = llm.invoke("Hello, are you operational?")
        print(f"✅ Success! Response: {response.content}")
        return True
    except ResourceExhausted:
        print(f"❌ Quota Exceeded for {model_name}")
    except PermissionDenied:
         print(f"❌ Permission Denied for {model_name} (API not enabled?)")
    except Exception as e:
        print(f"⚠️ Error testing {model_name}: {e}")
    return False

if __name__ == "__main__":
    print(f"Project: {PROJECT_ID}")
    test_model("gemini-1.5-pro-002")
    test_model("gemini-1.5-flash-002")
