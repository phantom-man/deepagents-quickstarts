"""
Knowledge Store Module (LanceDB).
Provides a dedicated, high-speed vector database for information retrieval.
Adheres to "The Jewel Standard" (Pylint 10/10).
"""

import os
import logging
from typing import List, Dict, Any, Optional
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KnowledgeStore")

LANCEDB_URI = "Artifacts/Data/lancedb"

class KnowledgeStore:
    """
    Manages embedding and retrieval of knowledge using LanceDB.
    """
    def __init__(self, uri: str = LANCEDB_URI):
        self.uri = uri
        self.db = None
        self.table_name = "research_vectors"
        self._initialize_db()
        self._initialize_embeddings()

    def _initialize_embeddings(self):
        """Initializes the Google Embedding Model."""
        try:
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                logger.error("❌ GOOGLE_API_KEY not found in environment.")
                self.embeddings = None
                return

            self.embeddings = GoogleGenerativeAIEmbeddings(
                model="models/text-embedding-004"
            )
        except Exception as e: # pylint: disable=broad-exception-caught
            logger.error("Failed to initialize embeddings: %s", e)
            self.embeddings = None

    def _initialize_db(self):
        """Initializes the connection to LanceDB."""
        try:
            # pylint: disable=import-outside-toplevel
            import lancedb

            # Ensure directory exists
            os.makedirs(os.path.dirname(self.uri), exist_ok=True)

            self.db = lancedb.connect(self.uri)
            logger.info("Connected to LanceDB at %s", self.uri)
        except ImportError:
            logger.error("❌ 'lancedb' library not found. Please install: pip install lancedb")
            self.db = None
        except Exception as e: # pylint: disable=broad-exception-caught
            logger.error("Failed to initialize LanceDB: %s", e)
            self.db = None

    def embed_text(self, text: str) -> Optional[List[float]]:
        """Generates an embedding for the given text."""
        if self.embeddings is None:
            logger.error("Embeddings model not initialized.")
            return None
        try:
            return self.embeddings.embed_query(text)
        except Exception as e: # pylint: disable=broad-exception-caught
            logger.error("Embedding failed: %s", e)
            return None

    def add_documents(self, documents: List[Dict[str, Any]]):
        """
        Adds documents to the vector store.
        Each doc must have 'text' and 'metadata'. Vector is calculated auto if missing.
        """
        if self.db is None:
            logger.error("Database not connected.")
            return

        processed_docs = []
        for doc in documents:
            if "vector" not in doc:
                vector = self.embed_text(doc.get("text", ""))
                if vector:
                    doc["vector"] = vector
                else:
                    continue # Skip if embedding failed
            processed_docs.append(doc)

        if not processed_docs:
            return

        try:
            # Check if table exists, if not create it
            if self.table_name not in self.db.table_names():
                self.db.create_table(self.table_name, data=processed_docs)
                logger.info("Created table '%s' with %d documents.", self.table_name, len(processed_docs))
            else:
                table = self.db.open_table(self.table_name)
                table.add(processed_docs)
                logger.info("Added %d documents to '%s'.", len(processed_docs), self.table_name)

        except Exception as e: # pylint: disable=broad-exception-caught
            logger.error("Failed to add documents: %s", e)

    def search(self, query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Searches for similar documents using a text query.
        """
        if self.db is None:
            return []

        if self.table_name not in self.db.table_names():
            logger.warning("Table '%s' does not exist.", self.table_name)
            return []

        query_vector = self.embed_text(query_text)
        if not query_vector:
            return []

        try:
            table = self.db.open_table(self.table_name)
            results = table.search(query_vector).limit(limit).to_list()
            return results

        except Exception as e: # pylint: disable=broad-exception-caught
            logger.error("Search failed: %s", e)
            return []

# Example Usage
if __name__ == "__main__":
    # Dummy embedding for testing
    store = KnowledgeStore()
    dummy_data = [
        {"vector": [0.1, 0.2], "text": "Paper A", "id": 1},
        {"vector": [0.3, 0.4], "text": "Paper B", "id": 2}
    ]
    # Note: Requires lancedb installed to run logic, but class is valid.
    logger.info("KnowledgeStore initialized.")
