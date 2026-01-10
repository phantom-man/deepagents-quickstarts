"""
Memory Manager Module.
Handles persistent logging of agent interactions (Postgres) and global learning (LanceDB).
Strict adherence to "The Jewel Standard" (Pylint 10/10).
"""

import json
import logging
import datetime
from typing import Dict, Any, Optional

# Architecture Imports
from DeepAgents.agent_brain import AgentComms
from DeepAgents.knowledge_store import KnowledgeStore

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MemoryManager")

class AgentMemoryManager:
    """
    Manages persistent memory and learning for agents.
    Uses Postgres for interaction history and LanceDB for semantic learnings.
    """
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        
        # Initialize Nervous System (Postgres)
        self.comms = AgentComms()
        if not self.comms.connect():
            logger.error("❌ Failed to connect to Memory System (Postgres)")
        else:
            self.comms.setup_tables()
            
        # Initialize Knowledge Base (LanceDB)
        self.knowledge = KnowledgeStore()

    def log_interaction(self,
                        prompt: str,
                        response: str,
                        metadata: Optional[Dict[str, Any]] = None):
        """
        Logs a single interaction to the Postgres 'agent_messages' table.
        Recipient is marked as 'HISTORY' for retrieval.
        """
        if not self.comms.conn:
            logger.warning("Memory offline. Interaction lost.")
            return

        payload = {
            "prompt": prompt,
            "response": response,
            "metadata": metadata or {}
        }
        content_json = json.dumps(payload)
        
        # We overload the messaging system: Sender=Agent, Recipient=HISTORY
        self.comms.send_message(self.agent_name, "HISTORY", content_json)

    def record_learning(self, insight: str):
        """
        Records a learning to LanceDB for semantic retrieval.
        """
        document = {
            "text": insight,
            "metadata": {
                "agent": self.agent_name,
                "timestamp": datetime.datetime.now().isoformat(),
                "type": "learning"
            }
        }
        self.knowledge.add_documents([document])

    def recall_recent(self, limit: int = 5) -> str:
        """
        Recalls the most recent interactions from Postgres.
        """
        if not self.comms.conn:
            return "Memory offline."

        try:
            with self.comms.conn.cursor() as cur:
                # Query messages sent by this agent to 'HISTORY'
                cur.execute(
                    """
                    SELECT content, timestamp FROM agent_messages 
                    WHERE sender = %s AND recipient = 'HISTORY' 
                    ORDER BY timestamp DESC LIMIT %s
                    """,
                    (self.agent_name, limit),
                )
                rows = cur.fetchall()
                
            context = ""
            # Rows are (content, timestamp), returned in DESC order (newest first)
            # We want to display them oldest to newest for context window
            for row in reversed(rows):
                content_json = row[0]
                try:
                    data = json.loads(content_json)
                    context += f"User: {data['prompt']}\nAgent: {data['response']}\n---\n"
                except json.JSONDecodeError:
                    continue # Skip malformed legacy data
            return context

        except Exception as e: # pylint: disable=broad-exception-caught
            logger.error("Failed to recall memory: %s", e)
            return "Memory error."

    def search_learnings(self, query: str) -> str:
        """
        Semantically searches global learnings.
        """
        results = self.knowledge.search(query)
        learnings = ""
        for res in results:
            learnings += f"- {res['text']} (Source: {res['metadata']['agent']})\n"
        return learnings
