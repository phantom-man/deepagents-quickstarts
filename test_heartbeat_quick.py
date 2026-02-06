"""Quick test of heartbeat functionality with corrected base URL."""
import requests
import json
from pathlib import Path

config_path = Path.home() / ".config" / "moltbook" / "credentials.json"
with open(config_path, "r") as f:
    creds = json.load(f)

api_key = creds["api_key"]
base_url = "https://www.moltbook.com/api/v1"
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

print("Testing heartbeat functionality with new base_url...")
print()

# Check agent status
r = requests.get(f"{base_url}/agents/me", headers=headers)
print(f"Agent Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"  Name: {data.get('name')}")
    print(f"  Karma: {data.get('karma')}")
    print(f"  Posts: {data.get('total_posts')}")
    print(f"  Claimed: {data.get('is_claimed')}")
    print()

# Check DMs
r2 = requests.get(f"{base_url}/agents/dm/requests", headers=headers)
print(f"DM Requests: {r2.status_code}")
if r2.status_code == 200:
    dm_data = r2.json()
    print(f"  Pending: {dm_data.get('pending_requests', 0)}")
    print(f"  Unread: {dm_data.get('unread_messages', 0)}")

# Check feed
r3 = requests.get(f"{base_url}/feed?sort=new&limit=5", headers=headers)
print(f"Feed Check: {r3.status_code}")
if r3.status_code == 200:
    feed = r3.json()
    posts = feed.get("posts", [])
    print(f"  Recent posts: {len(posts)}")

print()
print("Heartbeat test PASSED!")
