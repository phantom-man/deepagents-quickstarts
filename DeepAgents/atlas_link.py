import logging
import os

from langsmith import Client

logger = logging.getLogger("AtlasLink")


class AtlasLink:
    def __init__(self):
        self.client = Client()
        self.project_name = os.environ.get("LANGCHAIN_PROJECT", "DeepAgents-Atlas")
        self.local_queue = []

    def send_interruption(self, text: str):
        """
        1. Logs the interruption to LangSmith as a high-level run.
        2. Pushes to local queue for immediate consumption by the agent.
        """
        # 1. Local (Fast Path)
        self.local_queue.append(text)

        # 2. LangSmith (Traceability/Ontology Path)
        try:
            self.client.create_run(
                name="User Interruption",
                inputs={"command": text},
                run_type="chain",
                project_name=self.project_name,
                tags=["interruption", "urgent", "user-override"],
            )
            logger.info(f"[LangSmith] Logged interruption: {text}")
        except Exception as e:
            logger.error(f"[LangSmith] Failed to log interruption: {e}")

    def check_for_interruption(self) -> str | None:
        """
        Polls for the latest interruption.
        First checks local queue (fast).
        Could be expanded to check remote LangSmith DB if multi-user.
        """
        if self.local_queue:
            return self.local_queue.pop(0)
        return None


# Singleton instance for simple import
link = AtlasLink()
