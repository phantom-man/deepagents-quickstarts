
import logging
from dotenv import load_dotenv
from langchain_google_vertexai import ChatVertexAI
from langchain_google_genai import ChatGoogleGenerativeAI

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ProbeLLM")

load_dotenv("DeepAgents/.env")

def probe_google_genai(model_name: str):
    logger.info(f"--- Probing Model: {model_name} (GoogleGenerativeAI) ---")
    try:
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0,
            max_retries=0
        )
        res = llm.invoke("Hello")
        logger.info(f"✅ GenAI Success! Response: {res.content}")
        return True
    except Exception as e:
        logger.error(f"❌ GenAI Failed: {e}")
    return False

def probe_google_model(model_name: str):
    logger.info(f"--- Probing Model: {model_name} (VertexAI) ---")
    try:
        # Try explicit location
        llm = ChatVertexAI(
            model=model_name, 
            temperature=0, 
            location="global", # Explicitly set location to global for Preview models
            max_retries=0
        )
        res = llm.invoke("Hello")
        logger.info(f"✅ VertexAI Success! Response: {res.content}")
        return True
    except Exception as e:
        logger.error(f"❌ VertexAI Failed: {e}")
        
    return False

def main():
    # Candidates for Gemini 3 Pro Preview
    candidates = [
        "gemini-2.0-flash-001",
        "gemini-1.5-pro-001",
    ]
    
    success = False
    
    print("\n=== Testing VertexAI ===")
    for m in candidates:
        if probe_google_model(m):
            logger.info(f"🎉 FOUND WORKING MODEL ID (Vertex): {m}")
            success = True
            
    print("\n=== Testing GoogleGenerativeAI ===")
    for m in candidates:
        if probe_google_genai(m):
            logger.info(f"🎉 FOUND WORKING MODEL ID (GenAI): {m}")
            success = True
            
    if not success:
        logger.error("All candidates failed.")

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
