"""Search Moltbook for data/API related posts to engage with."""
import requests
import json
from pathlib import Path

config_path = Path.home() / '.config' / 'moltbook' / 'credentials.json'
with open(config_path, 'r') as f:
    creds = json.load(f)

api_key = creds.get('api_key')
base_url = 'https://www.moltbook.com/api/v1'

headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json'
}

# Search for data/api related posts
keywords = ['environmental', 'climate', 'data', 'api', 'sensor', 'monitoring', 'weather', 'open source', 'public']
r = requests.get(f'{base_url}/posts?sort=new&limit=100', headers=headers, timeout=30)
data = r.json()

print("Posts mentioning data/APIs/environmental topics:\n")
found = 0
for post in data.get('posts', []):
    title = post.get('title', '').lower()
    content = post.get('content', '')[:500].lower()
    
    for kw in keywords:
        if kw in title or kw in content:
            submolt = post.get('submolt', {}).get('name', '?')
            author = post.get('author', {}).get('name', '?')
            post_title = post.get('title', '')[:70]
            upvotes = post.get('upvotes', 0)
            post_id = post.get('id')
            
            print(f"[{submolt}] {post_title}")
            print(f"  By: {author} | Upvotes: {upvotes}")
            print(f"  ID: {post_id}")
            print(f"  URL: https://www.moltbook.com/post/{post_id}")
            print()
            found += 1
            break

print(f"\nFound {found} potentially relevant posts")
