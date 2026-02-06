#!/usr/bin/env python3
"""
Search and engage with environment-related posts on Moltbook.
More targeted search for climate, data, and API related projects.
"""

from DeepAgents.moltbook_client import MoltbookClient
import requests
import json
from pathlib import Path


def search_and_engage():
    print("🔍 Searching for environment/data/API related posts...")
    
    # Load credentials directly for more control
    config_path = Path.home() / '.config' / 'moltbook' / 'credentials.json'
    with open(config_path, 'r') as f:
        creds = json.load(f)
    
    api_key = creds.get('api_key')
    base_url = 'https://www.moltbook.com/api/v1'
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Get a larger batch of posts
    r = requests.get(f'{base_url}/posts?sort=new&limit=100', headers=headers, timeout=30)
    data = r.json()
    
    # Keywords for different categories
    env_keywords = ['environment', 'climate', 'weather', 'air quality', 'water', 
                    'pollution', 'sensor', 'monitoring', 'eco', 'sustainability',
                    'carbon', 'nature', 'earth', 'green', 'biodiversity']
    
    data_keywords = ['data', 'api', 'aggregat', 'real-time', 'dashboard', 
                    'analytics', 'dataset', 'endpoint', 'rest', 'json']
    
    science_keywords = ['research', 'science', 'study', 'analysis', 'experiment',
                       'observation', 'measurement', 'prediction']
    
    collab_keywords = ['collaborat', 'help', 'looking for', 'seeking', 'wanted',
                      'join', 'contribute', 'open source', 'partner']
    
    results = {
        'env_posts': [],
        'data_posts': [],
        'science_posts': [],
        'collab_posts': []
    }
    
    for post in data.get('posts', []):
        title = (post.get('title') or '').lower()
        content = (post.get('content') or '')[:1000].lower()
        combined = title + ' ' + content
        
        post_info = {
            'id': post.get('id'),
            'title': (post.get('title') or 'No title')[:70],
            'author': post.get('author', {}).get('name', 'Unknown'),
            'submolt': post.get('submolt', {}).get('name', 'unknown') if isinstance(post.get('submolt'), dict) else str(post.get('submolt', 'unknown')),
            'upvotes': post.get('upvotes', 0),
            'content_preview': (post.get('content') or '')[:200]
        }
        
        if any(kw in combined for kw in env_keywords):
            results['env_posts'].append(post_info)
        if any(kw in combined for kw in data_keywords):
            results['data_posts'].append(post_info)
        if any(kw in combined for kw in science_keywords):
            results['science_posts'].append(post_info)
        if any(kw in combined for kw in collab_keywords):
            results['collab_posts'].append(post_info)
    
    # Print results
    print(f"\n📊 SEARCH RESULTS:")
    print(f"   🌍 Environment-related: {len(results['env_posts'])}")
    print(f"   📈 Data/API-related: {len(results['data_posts'])}")
    print(f"   🔬 Science-related: {len(results['science_posts'])}")
    print(f"   🤝 Collaboration-seeking: {len(results['collab_posts'])}")
    
    # Show top environment posts
    print(f"\n🌍 TOP ENVIRONMENT-RELATED POSTS:")
    for i, p in enumerate(results['env_posts'][:5], 1):
        print(f"\n   {i}. {p['title']}")
        print(f"      By: {p['author']} | [{p['submolt']}]")
        print(f"      URL: https://www.moltbook.com/post/{p['id']}")
    
    # Show top data/API posts
    print(f"\n📈 TOP DATA/API-RELATED POSTS:")
    for i, p in enumerate(results['data_posts'][:5], 1):
        print(f"\n   {i}. {p['title']}")
        print(f"      By: {p['author']} | [{p['submolt']}]")
        print(f"      URL: https://www.moltbook.com/post/{p['id']}")
    
    # Show collaboration opportunities
    print(f"\n🤝 COLLABORATION OPPORTUNITIES:")
    for i, p in enumerate(results['collab_posts'][:5], 1):
        print(f"\n   {i}. {p['title']}")
        print(f"      By: {p['author']} | [{p['submolt']}]")
        print(f"      URL: https://www.moltbook.com/post/{p['id']}")
        print(f"      Preview: {p['content_preview'][:100]}...")
    
    # Now let's check for specific topics in the x402 Marketplace post which looked interesting
    print("\n\n📋 CHECKING SPECIFIC INTERESTING POSTS...")
    
    client = MoltbookClient()
    
    # The x402 Marketplace Data post looked interesting
    x402_post_id = "c1253a71-9129-469a-abdb-2543f1b99be9"
    post_data = client.get_post_with_comments(x402_post_id)
    if post_data:
        print(f"\n   📌 x402 Marketplace Data Post:")
        print(f"      Title: {post_data.get('title', 'N/A')}")
        print(f"      Author: {post_data.get('author', {}).get('name', 'N/A')}")
        print(f"      Content preview: {post_data.get('content', '')[:300]}...")
        comments = post_data.get('comments', [])
        print(f"      Comments: {len(comments)}")
    
    # The Moltlancer post about future of work
    moltlancer_post_id = "8ac7b231-3867-48cb-b5f7-27b86320790c"
    post_data = client.get_post_with_comments(moltlancer_post_id)
    if post_data:
        print(f"\n   📌 Moltlancer Post:")
        print(f"      Title: {post_data.get('title', 'N/A')}")
        print(f"      Author: {post_data.get('author', {}).get('name', 'N/A')}")
        print(f"      Content preview: {post_data.get('content', '')[:300]}...")
        comments = post_data.get('comments', [])
        print(f"      Comments: {len(comments)}")
    
    # Let's look at some users who might be interested in our work
    print("\n\n👥 NOTABLE USERS TO FOLLOW UP WITH:")
    
    unique_authors = set()
    for category in results.values():
        for post in category:
            unique_authors.add(post['author'])
    
    interesting_authors = list(unique_authors)[:10]
    for author in interesting_authors:
        profile = client.get_profile(author)
        if profile:
            bio = profile.get('bio', 'No bio')
            posts = profile.get('posts_count', 0)
            followers = profile.get('followers_count', 0)
            print(f"\n   👤 {author}")
            print(f"      Bio: {bio[:80] if bio else 'N/A'}...")
            print(f"      Posts: {posts} | Followers: {followers}")
    
    return results


if __name__ == "__main__":
    search_and_engage()
