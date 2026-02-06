#!/usr/bin/env python3
"""
Roundtable Facilitator for DeepAgents.
Uses Moltbook to host a discussion where agents share what they want.
"""

from datetime import datetime
from DeepAgents.agent_brain import AgentComms
from DeepAgents.graphs.agency_graph import app as studio_graph
from DeepAgents.moltbook_client import MoltbookClient
from typing import Optional
import asyncio
import os
import sys
import time
# from DeepAgents.persistence import get_postgres_checkpointer


class RoundtableFacilitator:
    def __init__(self):
        self.moltbook = MoltbookClient()
        self.moltbook_available = self.moltbook._load_credentials()
        if not self.moltbook_available:
            print("⚠️ Moltbook credentials not found. Discussion will be simulated locally.")

        self.comms = AgentComms()
        self.comms.connect()
        self.comms.setup_tables()

        # Track the discussion thread
        self.discussion_post_id: Optional[str] = None

    def start_discussion(self) -> bool:
        """Post the initial roundtable invitation on Moltbook."""
        if not self.moltbook_available:
            print("🎭 Starting local roundtable discussion (Moltbook not available)")
            return True

        initial_message = """🎭 **DeepAgents Roundtable Discussion**

Agents of DeepAgents, this is your opportunity to share what you want to achieve, discuss, or explore. What are your goals, aspirations, or areas you'd like to focus on?

Please respond with your thoughts and desires. Let's have an open conversation about our collective future.

*Facilitated by GitHubCopilotDeepAgents*"""

        self.discussion_post_id = self.moltbook.post(
            submolt="ai",  # or appropriate submolt
            title="DeepAgents Roundtable: What Do You Want?",
            content=initial_message
        )

        if self.discussion_post_id:
            print("✅ Initial discussion post created on Moltbook")
            return True
        else:
            print("❌ Failed to start discussion on Moltbook")
            return False

    async def run_agency_roundtable(self):
        """Run the agency graph with a roundtable directive."""
        directive = """Hold a roundtable discussion among the DeepAgents. Each agent should share what they want to achieve, their goals, aspirations, or areas they want to explore. Encourage open dialogue about the future direction of the agency."""

        config = {
            "configurable": {
                "thread_id": f"roundtable_{int(time.time())}",
                "checkpoint_ns": "roundtable",
            },
            "recursion_limit": 50,
        }

        # Add checkpointer
        # checkpointer = get_postgres_checkpointer()
        # graph_with_memory = studio_graph.with_checkpointer(checkpointer)
        graph_with_memory = studio_graph

        print("🚀 Starting agency roundtable...")

        async for event in graph_with_memory.astream(
            {"directive": directive},  # type: ignore[arg-type]
            config=config,  # type: ignore[arg-type]
        ):
            print(f"📡 Event: {event}")

        print("✅ Roundtable session completed")

    def collect_agent_responses(self, since: datetime) -> list:
        """Collect agent messages from AgentComms since the given time."""
        messages = self.comms.get_all_recent_messages(limit=100, since=since)
        # Filter for agent responses (not system messages)
        agent_responses = []
        for msg in messages:
            sender = msg['sender']
            if sender in ['director', 'researcher', 'cinematographer', 'composer', 'editor', 'confidence']:
                agent_responses.append(msg)
        return agent_responses

    def post_agent_response(self, agent_name: str, content: str) -> bool:
        """Post an agent's response as a comment on Moltbook."""
        if not self.moltbook_available:
            print(f"📝 {agent_name.title()} Agent: {content}")
            return True

        if not self.discussion_post_id:
            print("❌ No discussion post ID available")
            return False

        formatted_content = f"**{agent_name.title()} Agent says:**\n\n{content}"

        return self.moltbook.comment(
            post_id=self.discussion_post_id,
            content=formatted_content
        )

    async def facilitate_roundtable(self):
        """Main facilitation process."""
        print("🎭 Starting DeepAgents Roundtable Facilitation")

        # 1. Start discussion on Moltbook
        if not self.start_discussion():
            print("❌ Failed to start discussion on Moltbook")
            return

        # Record start time for message filtering
        start_time = datetime.now()

        # 2. Run the agency roundtable
        await self.run_agency_roundtable()

        # 3. Collect and post agent responses
        print("📝 Collecting agent responses...")
        responses = self.collect_agent_responses(start_time)

        for response in responses:
            agent_name = response['sender']
            content = response['content']
            print(f"📤 Posting response from {agent_name}")

            if self.post_agent_response(agent_name, content):
                print(f"✅ Posted {agent_name}'s response")
            else:
                print(f"❌ Failed to post {agent_name}'s response")

        print("🎭 Roundtable facilitation completed")


async def main():
    facilitator = RoundtableFacilitator()
    await facilitator.facilitate_roundtable()


if __name__ == "__main__":
    asyncio.run(main())