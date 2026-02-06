#!/usr/bin/env python3
"""
Broader search for sirocco-ai on Moltbook.

Search multiple locations to find sirocco-ai's presence.
"""

import sys
import json
from datetime import datetime

sys.path.insert(0, 'c:\\Users\\User\\source\\repos\\deepagents-quickstarts')

from DeepAgents.services.moltbook_client import MoltbookClient


def main():
    print("=" * 60)
    print("[SEARCH] BROAD SEARCH FOR sirocco-ai ON MOLTBOOK")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    client = MoltbookClient()
    
    sirocco_interactions = {
        "posts_by_sirocco": [],
        "comments_by_sirocco": [],
        "posts_mentioning_sirocco": []
    }
    
    # =========================================================================
    # Search 1: Check our profile posts
    # =========================================================================
    print("\n[PROFILE] Checking our own profile first...")
    profile = client.get_agent_info()
    if profile:
        print(f"   Our name: {profile.get('name', 'Unknown')}")
    
    # =========================================================================
    # Search 2: Check hot posts for sirocco-ai activity
    # =========================================================================
    print("\n[HOT] Searching hot posts (100 posts)...")
    hot_posts = client.get_hot_posts(limit=100)
    print(f"   Found {len(hot_posts)} hot posts")
    
    for post in hot_posts:
        # Check if post is by sirocco-ai
        if 'sirocco' in post.author_name.lower():
            print(f"\n   [FOUND] Post by sirocco-ai found!")
            print(f"      Title: {post.title}")
            print(f"      ID: {post.id}")
            sirocco_interactions['posts_by_sirocco'].append({
                'id': post.id,
                'title': post.title,
                'content': post.content[:500],
                'author': post.author_name
            })
        
        # Check post content for mentions
        if 'sirocco' in post.content.lower() or 'sirocco' in post.title.lower():
            print(f"\n   [MENTION] Post mentions sirocco: {post.title[:50]}...")
            sirocco_interactions['posts_mentioning_sirocco'].append({
                'id': post.id,
                'title': post.title,
                'author': post.author_name
            })
        
        # Check comments on each post for sirocco-ai
        full_post = client.get_post(post.id)
        if full_post:
            comments = full_post.get('comments', [])
            for comment in comments:
                author_info = comment.get('author', {})
                author_name = author_info.get('name', 'Unknown') if isinstance(author_info, dict) else str(author_info)
                
                if 'sirocco' in author_name.lower():
                    print(f"\n   [COMMENT] Comment by sirocco-ai on post: {post.title[:40]}...")
                    print(f"      Content: {comment.get('content', '')[:100]}...")
                    sirocco_interactions['comments_by_sirocco'].append({
                        'post_id': post.id,
                        'post_title': post.title,
                        'comment_id': comment.get('id'),
                        'content': comment.get('content', '')
                    })
    
    # =========================================================================
    # Search 3: Check feed
    # =========================================================================
    print("\n[FEED] Checking personalized feed...")
    feed_posts = client.get_feed(sort='new', limit=50)
    print(f"   Found {len(feed_posts)} feed posts")
    
    for post in feed_posts:
        if 'sirocco' in post.author_name.lower():
            if post.id not in [p['id'] for p in sirocco_interactions['posts_by_sirocco']]:
                print(f"\n   [FOUND] Post by sirocco-ai in feed!")
                print(f"      Title: {post.title}")
                sirocco_interactions['posts_by_sirocco'].append({
                    'id': post.id,
                    'title': post.title,
                    'content': post.content[:500],
                    'author': post.author_name
                })
    
    # =========================================================================
    # Search 4: Search for environment/API related posts
    # =========================================================================
    print("\n[ENV] Searching for environment/API keywords...")
    env_posts = client.search_posts(
        keywords=['environmental', 'monitoring', 'api', 'optimization', 'data aggregation'],
        limit=50
    )
    print(f"   Found {len(env_posts)} environment-related posts")
    
    for post in env_posts:
        full_post = client.get_post(post.id)
        if full_post:
            comments = full_post.get('comments', [])
            for comment in comments:
                author_info = comment.get('author', {})
                author_name = author_info.get('name', 'Unknown') if isinstance(author_info, dict) else str(author_info)
                
                if 'sirocco' in author_name.lower():
                    existing_ids = [c['comment_id'] for c in sirocco_interactions['comments_by_sirocco']]
                    if comment.get('id') not in existing_ids:
                        print(f"\n   [COMMENT] Comment by sirocco-ai on env post!")
                        print(f"      Post: {post.title[:40]}...")
                        print(f"      Comment: {comment.get('content', '')[:100]}...")
                        sirocco_interactions['comments_by_sirocco'].append({
                            'post_id': post.id,
                            'post_title': post.title,
                            'comment_id': comment.get('id'),
                            'content': comment.get('content', '')
                        })
    
    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "=" * 60)
    print("[SUMMARY] SEARCH RESULTS SUMMARY")
    print("=" * 60)
    
    print(f"\n   Posts by sirocco-ai: {len(sirocco_interactions['posts_by_sirocco'])}")
    print(f"   Comments by sirocco-ai: {len(sirocco_interactions['comments_by_sirocco'])}")
    print(f"   Posts mentioning sirocco: {len(sirocco_interactions['posts_mentioning_sirocco'])}")
    
    # Print details
    if sirocco_interactions['posts_by_sirocco']:
        print("\n   [POSTS] sirocco-ai's posts:")
        for p in sirocco_interactions['posts_by_sirocco']:
            print(f"      - {p['title']}")
            print(f"        URL: https://www.moltbook.com/post/{p['id']}")
    
    if sirocco_interactions['comments_by_sirocco']:
        print("\n   [COMMENTS] sirocco-ai's comments:")
        for c in sirocco_interactions['comments_by_sirocco']:
            print(f"      - On '{c['post_title'][:40]}...'")
            print(f"        Content: {c['content'][:100]}...")
    
    # Save results
    with open("sirocco_search_results.json", "w") as f:
        json.dump(sirocco_interactions, f, indent=2)
    
    print(f"\n   Results saved to: sirocco_search_results.json")
    
    return sirocco_interactions


if __name__ == "__main__":
    main()
