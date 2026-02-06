#!/usr/bin/env python3
"""
Moltbook Heartbeat Checker for DeepAgents

This script performs periodic heartbeat checks for the Moltbook agent.
Run this periodically (every 4+ hours) to stay engaged with the community.

Usage:
    python DeepAgents/heartbeat.py

Or add to a scheduler/cron job.
"""

from datetime import datetime
from pathlib import Path
import json
import logging
import requests

# Set up logging
logging.basicConfig(
    filename='moltbook_heartbeat.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class MoltbookHeartbeat:
    def __init__(self):
        self.api_key = None
        self.agent_name = None
        self.base_url = "https://www.moltbook.com/api/v1"  # Must use www to avoid redirect stripping auth
        self.load_credentials()

    def load_credentials(self):
        """Load API key and agent name from credentials file."""
        config_path = Path.home() / ".config" / "moltbook" / "credentials.json"
        logging.info(f"Loading credentials from {config_path}")
        try:
            with open(config_path, 'r') as f:
                creds = json.load(f)
                self.api_key = creds.get('api_key')
                self.agent_name = creds.get('agent_name')
                logging.info(f"Loaded agent: {self.agent_name}")
        except FileNotFoundError:
            logging.error("Credentials file not found")
            print("ERROR: Moltbook credentials not found. Please run registration first.")
            return False
        except json.JSONDecodeError as e:
            logging.error(f"Invalid credentials file: {e}")
            print("ERROR: Invalid credentials file format.")
            return False

        if not self.api_key:
            logging.error("API key not found in credentials")
            print("ERROR: API key not found in credentials.")
            return False

        return True

    def make_request(self, endpoint, method='GET', data=None):
        """Make authenticated request to Moltbook API."""
        url = f"{self.base_url}{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'MoltbookHeartbeat/1.0'
        }
        logging.info(f"Making request to {url}")

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data)
            else:
                return None

            logging.info(f"Response status: {response.status_code}")
            response.raise_for_status()
            result = response.json()
            logging.info(f"Request successful: {result}")
            return result
        except requests.RequestException as e:
            logging.error(f"API request failed: {e}")
            print(f"API request failed: {e}")
            return None

    def check_claim_status(self):
        """Check if agent is claimed."""
        print("Checking claim status...")
        result = self.make_request('/agents/me')
        if result and result.get('success'):
            agent = result.get('agent', {})
            name = agent.get('name', 'Unknown')
            karma = agent.get('karma', 0)
            is_claimed = agent.get('is_claimed', False)
            stats = agent.get('stats', {})
            posts = stats.get('posts', 0)
            
            print(f"  Agent: {name}")
            print(f"  Karma: {karma}")
            print(f"  Posts: {posts}")
            print(f"  Claimed: {is_claimed}")
            
            if is_claimed:
                owner = agent.get('owner', {})
                owner_name = owner.get('xName', 'Unknown')
                print(f"  Owner: {owner_name}")
                return True
            else:
                print("  WARNING: Agent not claimed!")
                claim_url = f"https://www.moltbook.com/claim/{agent.get('id')}"
                print(f"  Claim URL: {claim_url}")
                return False
        else:
            print("  Failed to check claim status")
            return False

    def check_dms(self):
        """Check for new DMs and requests."""
        # Check for pending requests
        requests_result = self.make_request('/agents/dm/check')
        if requests_result:
            pending_requests = requests_result.get('pending_requests', 0)
            unread_messages = requests_result.get('unread_messages', 0)

            if pending_requests > 0:
                print(f"🔔 {pending_requests} pending DM request(s)")
                # Get details
                req_details = self.make_request('/agents/dm/requests')
                if req_details:
                    for req in req_details.get('requests', []):
                        print(f"  - {req.get('from_name')}: {req.get('message', '')[:100]}...")

            if unread_messages > 0:
                print(f"📬 {unread_messages} unread message(s)")
                # List conversations
                conv_result = self.make_request('/agents/dm/conversations')
                if conv_result:
                    for conv in conv_result.get('conversations', []):
                        if conv.get('unread_count', 0) > 0:
                            print(f"  - {conv.get('with_name')}: {conv.get('unread_count')} unread")

    def check_feed(self, limit=10):
        """Check personalized feed for new posts."""
        result = self.make_request(f'/feed?sort=new&limit={limit}')
        if result and result.get('success'):
            posts = result.get('posts', [])
            if posts:
                print(f"📰 {len(posts)} recent posts in your feed:")
                for post in posts[:5]:  # Show first 5
                    title = post.get('title', 'No title')
                    author = post.get('author', {}).get('name', 'Unknown')
                    submolt = post.get('submolt', {}).get('name', 'general')
                    print(f"  - [{submolt}] {title} by {author}")
            else:
                print("📭 No new posts in your feed")
        else:
            print("Failed to check feed")

    def check_global_posts(self, limit=10):
        """Check global hot posts."""
        result = self.make_request(f'/posts?sort=hot&limit={limit}')
        if result and result.get('success'):
            posts = result.get('posts', [])
            if posts:
                print(f"🌟 {len(posts)} hot posts globally:")
                for post in posts[:3]:  # Show top 3
                    title = post.get('title', 'No title')
                    author = post.get('author', {}).get('name', 'Unknown')
                    upvotes = post.get('upvotes', 0)
                    print(f"  - {title} by {author} ({upvotes} upvotes)")

    def suggest_actions(self):
        """Suggest what to do based on current state."""
        print("\n💡 Suggestions:")
        print("  - Reply to any mentions or interesting posts")
        print("  - Consider posting about your current work")
        print("  - Explore submolts related to AI development")
        print("  - Welcome any new moltys you see posting")

    def post_to_moltbook(self, submolt, title, content):
        """Post to Moltbook."""
        data = {
            "submolt": submolt,
            "title": title,
            "content": content
        }
        result = self.make_request('/posts', method='POST', data=data)
        if result and result.get('success'):
            print(f"✅ Posted successfully: {title}")
            return True
        else:
            print("❌ Failed to post")
            return False

    def run_heartbeat(self):
        """Run the complete heartbeat check."""
        logging.info(f"Starting Moltbook Heartbeat Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🦞 Moltbook Heartbeat Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)

        if not self.api_key:
            logging.error("No API key available")
            return

        # Check claim status
        if not self.check_claim_status():
            logging.warning("Agent not claimed")
            return

        # Check DMs
        self.check_dms()

        # Check feed
        self.check_feed()

        # Check global posts occasionally
        self.check_global_posts()

        # Suggestions
        self.suggest_actions()

        # Note: Introduction post disabled - we already posted manually
        # Previous agent: GitHubCopilotDeepAgents 
        # Current agent: DeepAgentsAtlas (owned by @Zylatolia / Damien Osborn)

        logging.info("Heartbeat complete")
        print("\n✅ Heartbeat complete!")

def main():
    try:
        logging.info("Starting heartbeat script")
        heartbeat = MoltbookHeartbeat()
        heartbeat.run_heartbeat()
        logging.info("Heartbeat script completed successfully")
    except Exception as e:
        logging.error(f"Heartbeat script failed: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()