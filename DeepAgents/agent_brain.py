import os
import time
import json
import logging
import lancedb
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from lancedb.pydantic import LanceModel, Vector
from lancedb.embeddings import get_registry
from sentence_transformers import SentenceTransformer

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AgentBrain")

# Force explicit embedding model for robustness
embedder = SentenceTransformer("all-MiniLM-L6-v2")
# Also need the registry model for Pydantic schema definition compatibility
registry_model = get_registry().get("sentence-transformers").create(name="all-MiniLM-L6-v2")

class MemoryItem(LanceModel):
    text: str = registry_model.SourceField()
    vector: Vector(384) = registry_model.VectorField() # type: ignore
    agent: str
    timestamp: float
    tags: str # JSON string

class AgentMemory:
    """
    The 'Hippocampus' of the Agent.
    Uses LanceDB (Embedded Vector Store) to store and retrieve semantic memories.
    """
    def __init__(self, db_path="data/lancedb"):
        # Ensure directory exists
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(base_dir, db_path)
        os.makedirs(self.db_path, exist_ok=True)
        
        # Connect to LanceDB
        logger.info(f"🧠 Connecting to Memory (LanceDB) at {self.db_path}...")
        self.db = lancedb.connect(self.db_path)
        
        self.table_name = "agent_memories"
        
        try:
            if self.table_name in self.db.table_names():
                self.table = self.db.open_table(self.table_name)
            else:
                self.table = self.db.create_table(self.table_name, schema=MemoryItem)
        except Exception as e:
            logger.error(f"Failed to initialize memory table: {e}")
            self.table = None

    def memorize(self, text, agent_role, tags=None):
        """Stores a new memory."""
        if tags is None:
            tags = []
            
        # Explicitly compute vector to ensure robustness
        vec = embedder.encode(text)
        
        item = MemoryItem(
            text=text,
            vector=vec,
            agent=agent_role,
            timestamp=time.time(),
            tags=json.dumps(tags)
        )
        
        try:
            if self.table is not None:
                self.table.add([item])
                logger.info(f"💾 Memory Stored: '{text[:50]}...'")
                return True
            else:
                logger.error("Memory table not initialized.")
                return False
        except Exception as e:
            logger.error(f"Failed to memorize: {e}")
            return False

    def recall(self, query, limit=3):
        """Retrieves relevant memories."""
        if self.table is None:
            return []
        
        try:
            # Explicitly embed the query
            query_vec = embedder.encode(query)
            # Search using vector
            results = self.table.search(query_vec).limit(limit).to_list()
            return results
        except Exception as e:
            logger.error(f"Failed to recall: {e}")
            return []


class AgentComms:
    """
    The 'Telepathy' of the Agent.
    Uses PostgreSQL to handle robust message passing and state.
    """
    def __init__(self, db_name="postgres", user="postgres", password="d1204l0723", host="localhost"):
        # Defaulting to 'postgres' db for initial check
        self.conn_params = {
            "dbname": db_name,
            "user": user,
            "password": password,
            "host": host
        }
        self.conn = None

    def connect(self):
        """Establish connection to the Nervous System (Postgres)."""
        try:
            self.conn = psycopg2.connect(
                dbname=self.conn_params['dbname'],
                user=self.conn_params['user'],
                password=self.conn_params['password'],
                host=self.conn_params['host']
            )
            self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            logger.info("📡 Connected to Nervous System (Postgres).")
            return True
        except psycopg2.OperationalError as e:
            logger.warning(f"⚠️ Could not connect to Postgres: {e}")
            # logger.warning("Please ensure PostgreSQL is installed and running.")
            return False

    def setup_tables(self):
        """Create the communication channels if they don't exist."""
        if not self.conn:
            return
            
        commands = [
            """
            CREATE TABLE IF NOT EXISTS agent_messages (
                id SERIAL PRIMARY KEY,
                sender TEXT NOT NULL,
                recipient TEXT NOT NULL,
                content TEXT NOT NULL,
                status TEXT DEFAULT 'unread',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]
        
        try:
            with self.conn.cursor() as cur:
                for cmd in commands:
                    cur.execute(cmd)
            logger.info("✅ Nervous System channels (Tables) configured.")
        except Exception as e:
            logger.error(f"Failed to setup tables: {e}")

    def send_message(self, sender, recipient, content):
        """Send a telepathic message."""
        if not self.conn:
            logger.error("Cannot send: Disconnected.")
            return

        sql = "INSERT INTO agent_messages (sender, recipient, content) VALUES (%s, %s, %s)"
        with self.conn.cursor() as cur:
            cur.execute(sql, (sender, recipient, content))
            # Optional: Postgres NOTIFY
            try:
                cur.execute(f"NOTIFY agent_channel, '{recipient}';")
            except:
                pass
        logger.info(f"📨 Sent from {sender} to {recipient}")

    def check_inbox(self, recipient):
        """Check for new messages."""
        if not self.conn:
            return []
            
        sql = "SELECT id, sender, content, created_at FROM agent_messages WHERE recipient = %s AND status = 'unread'"
        messages = []
        with self.conn.cursor() as cur:
            cur.execute(sql, (recipient,))
            rows = cur.fetchall()
            for r in rows:
                messages.append({"id": r[0], "sender": r[1], "content": r[2], "ts": r[3]})
                # Mark as read
                cur.execute("UPDATE agent_messages SET status = 'read' WHERE id = %s", (r[0],))
        
        return messages

# Test Block
if __name__ == "__main__":
    print("--- Initializing DeepAgents Brain ---")
    
    # 1. Test Memory (Works without Postgres)
    try:
        brain = AgentMemory()
        brain.memorize("The user prefers sci-fi themes over westerns.", "Director", ["preference", "style"])
        brain.memorize("Veo model 3.1 struggles with complex hand gestures.", "Cinematographer", ["bug", "restriction"])
    
        print("\n--- Testing Recall ---")
        query = "What should I avoid regarding hands?"
        thoughts = brain.recall(query)
        
        print(f"Query: '{query}'")
        for t in thoughts:
            # LanceDB return dictionaries
            txt = t.get('text', 'Unknown')
            dist = t.get('_distance', 0)
            print(f"💡 Recalled: {txt} (Distance: {dist})")
    except Exception as e:
        print(f"Memory Error: {e}")

    # 2. Test Comms (Will fail gracefully if no Postgres)
    print("\n--- Testing Nervous System (Comms) ---")
    comms = AgentComms() 
    if comms.connect():
        comms.setup_tables()
        comms.send_message("Director", "Cinematographer", "Prepare a shot list for the wasteland scene.")
        msgs = comms.check_inbox("Cinematographer")
        print(f"\n📬 Inbox: {msgs}")
    else:
        print("❌ Waiting for PostgreSQL Installation to enable Comms.")
