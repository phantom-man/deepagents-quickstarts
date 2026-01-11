"""
Agent Brain Module.
Handles the 'Hippocampus' (Memory) and 'Telepathy' (Communication)
systems for the Agent Swarm.
"""

import os
import time
import json
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

import lancedb
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from lancedb.pydantic import LanceModel, Vector
# from lancedb.embeddings import get_registry

# from sentence_transformers import SentenceTransformer
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Load env vars
load_dotenv()

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AgentBrain")

# Force explicit embedding model for robustness (Switched to Google per user request)
# Note: Google text-embedding-004 is 768 dim.
EMBEDDER = GoogleGenerativeAIEmbeddings(
    model="models/text-embedding-004",
    project=os.getenv("GOOGLE_CLOUD_PROJECT"),
    location=os.getenv("GOOGLE_CLOUD_LOCATION")
)
# EMBEDDER = SentenceTransformer("all-MiniLM-L6-v2")

# Also need the registry model for Pydantic schema definition compatibility
# LanceDB registry for VertexAI might not be standard, so we might need to rely on manual embedding
# or custom registry if available. For now, we will handle embedding manually in add_memory
# and use Vector(768) in schema.


class MemoryItem(LanceModel):
    """Schema for a single memory item in LanceDB."""

    text: str  # = REGISTRY_MODEL.SourceField()
    vector: Vector(768)  # = REGISTRY_MODEL.VectorField() # type: ignore
    agent: str
    timestamp: float
    tags: str  # JSON string


class AgentMemory:
    """
    The 'Hippocampus' of the Agent.
    Uses LanceDB (Embedded Vector Store) to store and retrieve semantic memories.
    """

    def __init__(self, db_path: str = "../data/lancedb"):
        # Ensure directory exists
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.abspath(os.path.join(base_dir, db_path))
        os.makedirs(self.db_path, exist_ok=True)

        # Connect to LanceDB
        logger.info("🧠 Connecting to Memory (LanceDB) at %s...", self.db_path)
        self.db = lancedb.connect(self.db_path)

        self.table_name = "agent_memories"

        try:
            if self.table_name in self.db.table_names():
                self.table = self.db.open_table(self.table_name)
            else:
                self.table = self.db.create_table(self.table_name, schema=MemoryItem)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to initialize memory table: %s", e)
            self.table = None

    def memorize(
        self, text: str, agent_role: str, tags: Optional[List[str]] = None
    ) -> bool:
        """Stores a new memory."""
        if tags is None:
            tags = []

        # Explicitly compute vector to ensure robustness
        # vec = EMBEDDER.encode(text) # SentenceTransformers syntax
        vec = EMBEDDER.embed_query(text)  # VertexAIEmbeddings syntax

        item = MemoryItem(
            text=text,
            vector=vec,
            agent=agent_role,
            timestamp=time.time(),
            tags=json.dumps(tags),
        )

        try:
            if self.table is not None:
                self.table.add([item])
                logger.info("💾 Memory Stored: '%s...'", text[:50])
                return True
            logger.error("Memory table not initialized.")
            return False
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to memorize: %s", e)
            return False

    def recall(self, query: str, limit: int = 3) -> List[Any]:
        """Retrieves relevant memories."""
        if self.table is None:
            return []

        try:
            # Explicitly embed the query
            query_vec = EMBEDDER.embed_query(query)
            # Search using vector
            results = self.table.search(query_vec).limit(limit).to_list()
            return results
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to recall: %s", e)
            return []


class AgentConfig:
    """
    Manages persistent configuration for Agents (Providers, Models).
    Stores data in a local JSON file (acting as a simple database).
    """

    def __init__(self, config_path: str = "../data/agent_config.json"):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.abspath(os.path.join(base_dir, config_path))
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Loads configuration from disk."""
        if not os.path.exists(self.config_path):
            return self._default_config()
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to load config: %s", e)
            return self._default_config()

    def _default_config(self) -> Dict[str, Any]:
        """Returns default configuration."""
        return {
            "Director": {"provider": "Replicate", "model": "meta/meta-llama-3-70b-instruct"},
            "Researcher": {"provider": "Replicate", "model": "meta/meta-llama-3-70b-instruct"},
            "Confidence": {"provider": "Replicate", "model": "meta/meta-llama-3-70b-instruct"},
            "Cinematographer": {
                "provider": "Replicate",
                "model": "meta/meta-llama-3-70b-instruct",
                "image_provider": "Replicate",
                "image_model": "black-forest-labs/flux-1.1-pro",
                "video_provider": "Replicate",
                "video_model": "zeroscope/v2-xl",
            },
            "Composer": {"provider": "Replicate", "model": "meta/musicgen"},
        }

    def save_config(self) -> None:
        """Persists configuration to disk."""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
            logger.info("⚙️ Configuration saved.")
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to save config: %s", e)

    def get_agent_config(self, agent_role: str) -> Dict[str, Any]:
        """Returns config for specific agent."""
        return self.config.get(
            agent_role, {"provider": "Replicate", "model": "meta/meta-llama-3-70b-instruct"}
        )

    def set_agent_config(
        self, agent_role: str, provider: str, model: str, **kwargs
    ) -> None:
        """Updates config for specific agent."""
        # Start with existing or new dict
        cfg = self.config.get(agent_role, {})
        # Update basics
        cfg["provider"] = provider
        cfg["model"] = model
        # Update extras (like image_provider)
        for k, v in kwargs.items():
            cfg[k] = v

        self.config[agent_role] = cfg
        self.save_config()


class AgentComms:
    """
    The 'Telepathy' of the Agent.
    Uses PostgreSQL to handle robust message passing and state.
    """

    def __init__(
        self,
        db_name: str = None,
        user: str = None,
        password: str = None,
        host: str = None,
    ):
        # Load from env or use defaults
        self.conn_params = {
            "dbname": db_name or os.getenv("POSTGRES_DB", "postgres"),
            "user": user or os.getenv("POSTGRES_USER", "postgres"),
            "password": password or os.getenv("POSTGRES_PASSWORD", "d1204l0723"),
            "host": host or os.getenv("POSTGRES_HOST", "localhost"),
        }
        self.conn = None

    def connect(self) -> bool:
        """Establish connection to the Nervous System (Postgres)."""
        try:
            self.conn = psycopg2.connect(
                dbname=self.conn_params["dbname"],
                user=self.conn_params["user"],
                password=self.conn_params["password"],
                host=self.conn_params["host"],
            )
            self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            logger.info("📡 Connected to Nervous System (Postgres).")
            return True
        except psycopg2.OperationalError as e:
            logger.warning("⚠️ Could not connect to Postgres: %s", e)
            # logger.warning("Please ensure PostgreSQL is installed and running.")
            return False

    def setup_tables(self) -> None:
        """Create the communication channels if they don't exist."""
        if not self.conn:
            return

        commands = [
            """
            CREATE TABLE IF NOT EXISTS agent_messages (
                id SERIAL PRIMARY KEY,
                sender VARCHAR(50),
                recipient VARCHAR(50),
                content TEXT,
                status VARCHAR(20) DEFAULT 'unread',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_recipient_status 
            ON agent_messages(recipient, status);
            """,
        ]
        try:
            with self.conn.cursor() as cur:
                for command in commands:
                    cur.execute(command)
            logger.info("✅ Nervous System channels (tables) verified.")
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to setup tables: %s", e)

    def send_message(self, sender: str, recipient: str, content: str) -> None:
        """Sends a telepathic message."""
        if not self.conn:
            logger.warning("Comms offline. Cannot send message.")
            return

        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO agent_messages (sender, recipient, content) VALUES (%s, %s, %s)",
                    (sender, recipient, content),
                )
            logger.info("📨 Message Sent: %s -> %s", sender, recipient)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to send message: %s", e)

    def receive_messages(
        self, recipient: str, mark_read: bool = True
    ) -> List[Dict[str, Any]]:
        """Checks for incoming thoughts."""
        if not self.conn:
            return []

        messages = []
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "SELECT id, sender, content, timestamp FROM agent_messages "
                    "WHERE recipient = %s AND status = 'unread' ORDER BY timestamp ASC",
                    (recipient,),
                )
                rows = cur.fetchall()

                for row in rows:
                    messages.append(
                        {
                            "id": row[0],
                            "sender": row[1],
                            "content": row[2],
                            "timestamp": row[3],
                        }
                    )
                    if mark_read:
                        # Mark as read immediately
                        # In a real system, you might wait until processed
                        cur.execute(
                            "UPDATE agent_messages SET status = 'read' WHERE id = %s",
                            (row[0],),
                        )
            if messages:
                logger.info("📬 Received %d messages for %s.", len(messages), recipient)
            return messages
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to receive messages: %s", e)
            return []


if __name__ == "__main__":
    # Test Brain
    try:
        mem = AgentMemory()
        mem.memorize("Test memory", "System", ["test"])
        RECALLED = mem.recall("Test")
        print(f"Recalled: {RECALLED}")

        brain_comms = AgentComms()
        if brain_comms.connect():
            brain_comms.setup_tables()
    except Exception as err:  # pylint: disable=broad-exception-caught
        print(f"Detailed check failed: {err}")
