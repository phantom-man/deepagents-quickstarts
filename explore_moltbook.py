#!/usr/bin/env python3
"""
Script to explore Moltbook and find active agents
"""

from DeepAgents.moltbook_client import get_moltbook_feed, get_client

def explore_moltbook():
    print("🔍 Exploring Moltbook feed...")

    # Get recent posts
    feed = get_moltbook_feed(20)
    if not feed:
        print("❌ Failed to get feed")
        return

    print(f"\n📋 Found {len(feed)} recent posts:")
    active_agents = set()

    for i, post in enumerate(feed, 1):
        author = post.get('author', {}).get('name', 'Unknown')
        title = post.get('title', 'No title')
        post_id = post.get('id')
        submolt = post.get('submolt', 'unknown')

        print(f"{i}. [{submolt}] {title}")
        print(f"   By: {author} (Post ID: {post_id})")
        print(f"   Content preview: {post.get('content', '')[:100]}...")
        print()

        if author != 'Unknown':
            active_agents.add(author)

    print(f"🎯 Active agents identified: {', '.join(active_agents)}")

    # Get some profiles
    print("\n👤 Getting profiles of active agents:")
    client = get_client()
    for agent in list(active_agents)[:5]:  # Limit to 5
        profile = client.get_profile(agent)
        if profile:
            print(f"- {agent}: {profile.get('bio', 'No bio')[:100]}...")
        else:
            print(f"- {agent}: Profile not found")

if __name__ == "__main__":
    explore_moltbook()</content>
<parameter name="filePath">c:\Users\User\source\repos\deepagents-quickstarts\explore_moltbook.py