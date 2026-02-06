#!/usr/bin/env python3
from DeepAgents.moltbook_client import MoltbookClient

client = MoltbookClient()
if client._load_credentials():
    print("Credentials loaded successfully")
    post_id = client.post("ai", "Test Post", "This is a test post")
    if post_id:
        print(f"Posted with ID: {post_id}")
    else:
        print("Failed to post")
else:
    print("Credentials not loaded")