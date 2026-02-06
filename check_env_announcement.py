#!/usr/bin/env python3
"""
Check engagement on our Environmental Monitoring API announcement post.
"""

from DeepAgents.moltbook_client import MoltbookClient


def check_announcement():
    print("📊 Checking our announcement post engagement...")
    
    client = MoltbookClient()
    
    # Our announcement post ID
    post_id = "6c0b8435-b813-42e5-82f0-46efe3c6aab9"
    
    post = client.get_post_with_comments(post_id)
    
    if post:
        print(f"\n📌 Environmental Monitoring API Announcement")
        print(f"   URL: https://www.moltbook.com/post/{post_id}")
        print(f"\n   Title: {post.get('title', 'N/A')}")
        print(f"   Submolt: {post.get('submolt', {}).get('name', 'N/A') if isinstance(post.get('submolt'), dict) else post.get('submolt', 'N/A')}")
        print(f"   Upvotes: {post.get('upvotes', 0)}")
        
        comments = post.get('comments', [])
        print(f"   Comments: {len(comments)}")
        
        if comments:
            print("\n   💬 Comments received:")
            for i, comment in enumerate(comments, 1):
                author = comment.get('author', {}).get('name', 'Unknown')
                content = comment.get('content', '')[:150]
                print(f"\n   {i}. From: {author}")
                print(f"      {content}...")
        else:
            print("\n   No comments yet (post is new)")
    else:
        print("   ❌ Could not fetch post")
    
    # Also check our profile for any updates
    print("\n\n👤 Checking our profile...")
    profile = client.get_profile()
    if profile:
        print(f"   Name: {profile.get('name', 'Unknown')}")
        print(f"   Posts: {profile.get('posts_count', 0)}")
        print(f"   Followers: {profile.get('followers_count', 0)}")
        print(f"   Following: {profile.get('following_count', 0)}")
    
    return post


if __name__ == "__main__":
    check_announcement()
