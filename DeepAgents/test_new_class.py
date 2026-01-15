
import os
from dotenv import load_dotenv
load_dotenv("DeepAgents/.env")

# Try to use ChatGoogleGenerativeAI with Vertex Credentials
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    print("Imported ChatGoogleGenerativeAI")
    
    # Attempt 1: Pass project/location (Old Vertex Style) to see if it accepts them
    # OR maybe it detects ADC?
    
    print("Attempting to init ChatGoogleGenerativeAI with Vertex params...")
    
    # NOTE: langchain-google-genai usually uses GOOGLE_API_KEY. 
    # But if ChatVertexAI is deprecated in favor of this, this MUST support Vertex.
    # Maybe we just don't pass api_key and pass project?
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-001",
        google_api_key=None, # Explicitly None to force ADC?
        # project=os.getenv("GOOGLE_CLOUD_PROJECT"), # Is this supported?
        # location="us-central1"
    )
    
    # We might need to handle auth differently. 
    # Let's see if it works with ADC automatically if key is missing.
    
    print("Invoking...")
    res = llm.invoke("Hi")
    print(f"Result: {res.content}")
    
except Exception as e:
    print(f"Error: {e}")
    
    # Check if there is specific info in the exception about Auth
