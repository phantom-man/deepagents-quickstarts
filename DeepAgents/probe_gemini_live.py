
# Try both if installed
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None

try:
    from langchain_google_vertexai import ChatVertexAI
except ImportError:
    ChatVertexAI = None

from google.api_core.exceptions import ResourceExhausted, PermissionDenied, NotFound

# Setup
PROJECT_ID = "crafty-hook-483415-b3"
REGION = "us-central1"

def test_model(model_name, use_vertex=False):
    print(f"--- Testing Quota for {model_name} (Vertex={use_vertex}) ---")
    try:
        if use_vertex:
             if not ChatVertexAI:
                 print("Skipping Vertex (Not Installed)")
                 return
             llm = ChatVertexAI(
                model_name=model_name,
                project=PROJECT_ID,
                location=REGION,
                max_output_tokens=10
            )
        else:
            if not ChatGoogleGenerativeAI:
                 print("Skipping GenAI (Not Installed)")
                 return
            llm = ChatGoogleGenerativeAI(
                model=model_name,
                project=PROJECT_ID,
                location=REGION,
                max_output_tokens=10
            )
        response = llm.invoke("Hello")
        print(f"✅ Success! Response: {response.content}")
        return True
    except ResourceExhausted:
        print(f"❌ Quota Exceeded for {model_name}")
    except PermissionDenied:
         print(f"❌ Permission Denied for {model_name} (API not enabled?)")
    except NotFound:
         print(f"❌ Not Found for {model_name}")
    except Exception as e:
        print(f"⚠️ Error testing {model_name}: {e}")
    return False

if __name__ == "__main__":
    print(f"Project: {PROJECT_ID}")
    
    # Target from user request
    test_model("gemini-2.0-flash-live", use_vertex=True)
    test_model("gemini-2.0-flash-exp", use_vertex=True)
    
    # Try non-vertex as well
    test_model("gemini-2.0-flash-live", use_vertex=False)
