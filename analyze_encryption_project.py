#!/usr/bin/env python3
"""
Retrieve posts and comments from the encryption algorithm project
"""

from DeepAgents.moltbook_client import get_client
import json

def find_encryption_project_posts():
    """Find posts related to the encryption algorithm project"""
    client = get_client()
    if not client._load_credentials():
        print("❌ Failed to load credentials")
        return

    print("🔍 Searching for encryption algorithm project posts...")

    # Search in different submolts
    submolts = ['crypto', 'ai', 'general', 'science', 'technology']

    all_posts = []
    for submolt in submolts:
        print(f"📋 Checking submolt: {submolt}")
        posts = client.get_posts(submolt, sort='new', limit=50)
        if posts:
            # Filter for encryption/crypto related posts
            crypto_posts = [p for p in posts if any(keyword in p.get('title', '').lower() or keyword in p.get('content', '').lower()
                           for keyword in ['quantum', 'encryption', 'crypto', 'resistant', 'algorithm'])]
            all_posts.extend(crypto_posts)
            print(f"   Found {len(crypto_posts)} relevant posts in {submolt}")

    # Also check global feed
    print("📋 Checking global feed...")
    feed = client.get_feed(100)
    if feed:
        crypto_feed_posts = [p for p in feed if any(keyword in p.get('title', '').lower() or keyword in p.get('content', '').lower()
                              for keyword in ['quantum', 'encryption', 'crypto', 'resistant', 'algorithm'])]
        # Avoid duplicates
        existing_ids = {p['id'] for p in all_posts}
        new_posts = [p for p in crypto_feed_posts if p['id'] not in existing_ids]
        all_posts.extend(new_posts)
        print(f"   Found {len(new_posts)} additional relevant posts in feed")

    print(f"\n📊 Total relevant posts found: {len(all_posts)}")

    # Display and analyze posts
    collaborating_agents = set()
    contributions = {}
    interactions = []

    for i, post in enumerate(all_posts, 1):
        post_id = post.get('id')
        title = post.get('title', 'No title')
        author = post.get('author', {}).get('name', 'Unknown')
        submolt = post.get('submolt', 'unknown')
        content_preview = post.get('content', '')[:200]

        print(f"\n{i}. [{submolt}] {title}")
        print(f"   Author: {author} (Post ID: {post_id})")
        print(f"   Content: {content_preview}...")

        if author != 'Unknown':
            collaborating_agents.add(author)
            if author not in contributions:
                contributions[author] = []
            contributions[author].append(f"Posted: {title}")

        # Get comments for this post
        comments = client.get_post_comments(str(post_id))
        if comments:
            print(f"   💬 Comments: {len(comments)}")
            for comment in comments:
                comment_author = comment.get('author', {}).get('name', 'Unknown')
                comment_content = comment.get('content', '')[:150]

                print(f"      - {comment_author}: {comment_content}...")

                if comment_author != 'Unknown':
                    collaborating_agents.add(comment_author)
                    if comment_author not in contributions:
                        contributions[comment_author] = []
                    contributions[comment_author].append(f"Commented on '{title}': {comment_content}")

                # Record interaction
                interactions.append({
                    'type': 'comment',
                    'post_id': post_id,
                    'post_title': title,
                    'commenter': comment_author,
                    'content': comment_content
                })
        else:
            print("   💬 No comments found")

    # Summary
    print(f"\n🎯 COLLABORATING AGENTS IDENTIFIED: {len(collaborating_agents)}")
    print("Agents:", ', '.join(sorted(collaborating_agents)))

    print("
📋 CONTRIBUTIONS:"    for agent in sorted(contributions.keys()):
        print(f"\n🤖 {agent}:")
        for contribution in contributions[agent][:5]:  # Limit to 5 per agent
            print(f"   • {contribution}")
        if len(contributions[agent]) > 5:
            print(f"   • ... and {len(contributions[agent]) - 5} more contributions")

    print("
💬 NOTABLE INTERACTIONS:"    for interaction in interactions[:10]:  # Show first 10
        print(f"• {interaction['commenter']} commented on '{interaction['post_title'][:50]}...': {interaction['content'][:100]}...")

    if len(interactions) > 10:
        print(f"... and {len(interactions) - 10} more interactions")

    # Save results
    results = {
        'agents': list(collaborating_agents),
        'contributions': contributions,
        'interactions': interactions,
        'posts_found': len(all_posts)
    }

    with open('encryption_project_analysis.json', 'w') as f:
        json.dump(results, f, indent=2)

    print("
💾 Results saved to encryption_project_analysis.json"    return results

if __name__ == "__main__":
    find_encryption_project_posts()