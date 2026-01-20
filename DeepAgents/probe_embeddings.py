
import logging
from dotenv import load_dotenv
from langchain_google_vertexai import VertexAIEmbeddings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ProbeEmbeddings")

load_dotenv("DeepAgents/.env")

def main():
    try:
        logger.info("Connecting to VertexAI Embeddings (text-embedding-004)...")
        embeddings = VertexAIEmbeddings(model_name="text-embedding-004")
        
        text = "DeepAgents is a production studio."
        logger.info(f"Embedding text: '{text}'")
        
        vector = embeddings.embed_query(text)
        logger.info(f"✅ Success! Vector dimension: {len(vector)}")
        
        if len(vector) == 768:
            logger.info("Dimensions match expectation (768).")
            return True
        else:
            logger.warning(f"Unexpected dimension: {len(vector)}")
            
    except Exception as e:
        logger.error(f"❌ Failed to embed: {e}")
        return False

if __name__ == "__main__":
    main()
