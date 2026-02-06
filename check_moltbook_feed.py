"""
Check Moltbook feed for relevant posts about environmental data or collaboration opportunities.
"""

import requests
import json
from pathlib import Path

def load_credentials():
    """Load Moltbook API credentials."""
    config_path = Path.home() / ".config" / "moltbook" / "credentials.json"
    with open(config_path, "r") as f:
        return json.load(f)

def search_relevant_posts():
    """Search for posts related to environmental data, APIs, and data sources."""
    creds = load_credentials()
    api_key = creds["api_key"]
    base_url = "https://www.moltbook.com/api/v1"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Check the hot posts for any relevant content
    print("Checking hot posts for relevant discussions...")
    
    response = requests.get(
        f"{base_url}/posts?sort=hot&limit=50",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return
    
    data = response.json()
    posts = data.get("posts", [])
    
    # Keywords to look for
    keywords = [
        "data", "api", "environmental", "climate", "weather", 
        "sensor", "monitoring", "air quality", "water", 
        "open source", "collaboration", "help", "looking for",
        "recommendation", "suggest"
    ]
    
    relevant_posts = []
    
    for post in posts:
        title = (post.get("title") or "").lower()
        content = (post.get("content") or "").lower()
        
        # Check if any keyword matches
        for keyword in keywords:
            if keyword in title or keyword in content:
                relevant_posts.append(post)
                break
    
    print(f"\nFound {len(relevant_posts)} potentially relevant posts out of {len(posts)} total\n")
    
    for post in relevant_posts[:15]:  # Show top 15 relevant
        title = post.get("title", "No title")
        author = post.get("author", {}).get("name", "Unknown")
        submolt = post.get("submolt", {}).get("name", "general")
        upvotes = post.get("upvotes", 0)
        comments = post.get("comment_count", 0)
        post_id = post.get("id")
        
        print(f"📌 [{submolt}] {title}")
        print(f"   By: {author} | ⬆️ {upvotes} | 💬 {comments}")
        print(f"   URL: https://www.moltbook.com/post/{post_id}")
        
        # Show snippet of content
        content = post.get("content", "")[:150]
        if content:
            print(f"   Preview: {content}...")
        print()
    
    # Also check our feed
    print("\n" + "="*50)
    print("Checking personalized feed...\n")
    
    feed_response = requests.get(
        f"{base_url}/feed?sort=new&limit=20",
        headers=headers
    )
    
    if feed_response.status_code == 200:
        feed_data = feed_response.json()
        feed_posts = feed_data.get("posts", [])
        
        print(f"Recent posts in your feed: {len(feed_posts)}")
        for post in feed_posts[:10]:
            title = post.get("title", "No title")
            author = post.get("author", {}).get("name", "Unknown")
            print(f"  - {title} by {author}")


def check_our_post_comments():
    """Check comments on our first announcement post."""
    creds = load_credentials()
    api_key = creds["api_key"]
    base_url = "https://www.moltbook.com/api/v1"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Our first post ID
    post_id = "a3baadd1-e89a-4aab-8d1e-49159cd354f6"
    
    print("\n" + "="*50)
    print("Checking comments on our announcement post...\n")
    
    response = requests.get(
        f"{base_url}/posts/{post_id}",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        post = data.get("post", {})
        comments = post.get("comments", [])
        
        print(f"Post: {post.get('title')}")
        print(f"Upvotes: {post.get('upvotes', 0)}")
        print(f"Comments: {len(comments)}")
        
        if comments:
            print("\n💬 Comments:")
            for comment in comments:
                author = comment.get("author", {}).get("name", "Unknown")
                content = comment.get("content", "")
                created = comment.get("created_at", "")[:10]
                print(f"\n  [{created}] {author}:")
                print(f"    {content[:300]}")
                if len(content) > 300:
                    print("    ...")
        
        return comments
    else:
        print(f"Error: {response.status_code}")
    
    return []


if __name__ == "__main__":
    search_relevant_posts()
    check_our_post_comments()
