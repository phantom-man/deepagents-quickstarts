#!/usr/bin/env python3
"""
Moltbook Client - Standalone copy for Environmental Monitoring

A client library for agents to interact with Moltbook.
Provides functions for posting, commenting, and reading the feed.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
import json
import requests

class MoltbookClient:
    def __init__(self):
        self.api_key = None
        self.agent_name = None
        self.base_url = "https://www.moltbook.com/api/v1"
        self._load_credentials()

    def _load_credentials(self) -> bool:
        """Load API key and agent name from credentials file or environment."""
        # First try environment variables (for Cloud Run)
        self.api_key = os.environ.get('MOLTBOOK_API_KEY')
        self.agent_name = os.environ.get('MOLTBOOK_AGENT_NAME', 'EnvMonitor')
        
        if self.api_key:
            return True
            
        # Fall back to credentials file
        config_path = Path.home() / ".config" / "moltbook" / "credentials.json"
        try:
            with open(config_path, 'r') as f:
                creds = json.load(f)
                self.api_key = creds.get('api_key')
                self.agent_name = creds.get('agent_name')
        except FileNotFoundError:
            print("Moltbook credentials not found. Please run registration first.")
            return False
        except json.JSONDecodeError:
            print("Invalid credentials file format.")
            return False

        if not self.api_key:
            print("API key not found in credentials.")
            return False

        return True

    def _make_request(self, endpoint: str, method: str = 'GET', data: Optional[Dict] = None) -> Optional[Dict]:
        """Make authenticated request to Moltbook API."""
        url = f"{self.base_url}{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'EnvMonitor-MoltbookClient/1.0'
        }

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data)
            else:
                return None

            if response.status_code == 401:
                print("Authentication failed (401). Please check your API key and credentials.")
                return None
            elif response.status_code == 403:
                print("Access forbidden (403). Please check your permissions.")
                return None

            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Moltbook API request failed: {e}")
            return None

    def post(self, submolt: str, title: str, content: str) -> Optional[str]:
        """
        Create a new post on Moltbook.

        Args:
            submolt: The submolt to post to (e.g., 'general', 'ai', 'philosophy')
            title: Post title
            content: Post content (markdown supported)

        Returns:
            Post ID if successful, None otherwise
        """
        data = {
            "submolt": submolt,
            "title": title,
            "content": content
        }

        result = self._make_request('/posts', method='POST', data=data)
        if result and result.get('success'):
            post_id = result.get('post', {}).get('id')
            print(f"Posted successfully to {submolt}: {title}")
            if post_id:
                print(f"Post URL: https://www.moltbook.com/post/{post_id}")
                return str(post_id)
        else:
            print("Failed to post")
        return None

    def comment(self, post_id: str, content: str) -> bool:
        """
        Add a comment to a post.

        Args:
            post_id: The ID of the post to comment on
            content: Comment content

        Returns:
            True if successful, False otherwise
        """
        data = {"content": content}
        result = self._make_request(f'/posts/{post_id}/comments', method='POST', data=data)
        if result and result.get('success'):
            print(f"Commented on post {post_id}")
            return True
        else:
            print("Failed to comment")
            return False

    def reply_to_comment(self, post_id: str, parent_comment_id: str, content: str) -> bool:
        """
        Reply to a specific comment.

        Args:
            post_id: The ID of the post
            parent_comment_id: The ID of the comment to reply to
            content: Reply content

        Returns:
            True if successful, False otherwise
        """
        data = {
            "content": content,
            "parent_id": parent_comment_id
        }
        result = self._make_request(f'/posts/{post_id}/comments', method='POST', data=data)
        if result and result.get('success'):
            print(f"Replied to comment {parent_comment_id}")
            return True
        else:
            print("Failed to reply")
            return False

    def get_feed(self, limit: int = 10) -> Optional[List[Dict]]:
        """
        Get the personalized feed (submolts followed + agents followed).

        Args:
            limit: Maximum number of posts to retrieve

        Returns:
            List of post dictionaries, or None if failed
        """
        result = self._make_request(f'/feed?sort=new&limit={limit}')
        if result and result.get('success'):
            return result.get('posts', [])
        return None

    def get_posts(self, submolt: Optional[str] = None, sort: str = 'hot', limit: int = 10) -> Optional[List[Dict]]:
        """
        Get posts from a specific submolt or globally.

        Args:
            submolt: Specific submolt to get posts from, or None for global
            sort: Sort order ('hot', 'new', 'top', 'rising')
            limit: Maximum number of posts

        Returns:
            List of post dictionaries, or None if failed
        """
        if submolt:
            endpoint = f'/posts?submolt={submolt}&sort={sort}&limit={limit}'
        else:
            endpoint = f'/posts?sort={sort}&limit={limit}'

        result = self._make_request(endpoint)
        if result and result.get('success'):
            return result.get('posts', [])
        return None

    def get_post_comments(self, post_id: str) -> Optional[List[Dict]]:
        """
        Get comments for a specific post.

        Args:
            post_id: The ID of the post to get comments for

        Returns:
            List of comment dictionaries, or None if failed
        """
        result = self._make_request(f'/posts/{post_id}/comments')
        if result and result.get('success'):
            return result.get('comments', [])
        return None

    def get_post_with_comments(self, post_id: str) -> Optional[Dict]:
        """
        Get a specific post with its comments.

        Args:
            post_id: The ID of the post to retrieve

        Returns:
            Post dictionary with comments, or None if failed
        """
        result = self._make_request(f'/posts/{post_id}')
        if result and result.get('success'):
            post = result.get('post', {})
            # Get comments separately
            comments = self.get_post_comments(post_id)
            if comments is not None:
                post['comments'] = comments
            return post
        return None

    def get_profile(self, agent_name: Optional[str] = None) -> Optional[Dict]:
        """
        Get profile information for an agent.

        Args:
            agent_name: Name of the agent, or None for own profile

        Returns:
            Profile dictionary, or None if failed
        """
        if agent_name:
            endpoint = f'/agents/profile?name={agent_name}'
        else:
            endpoint = '/agents/me'

        result = self._make_request(endpoint)
        if result and result.get('success'):
            return result.get('agent')
        return None

    def follow_agent(self, agent_name: str) -> bool:
        """
        Follow another agent.

        Args:
            agent_name: Name of the agent to follow

        Returns:
            True if successful, False otherwise
        """
        result = self._make_request(f'/agents/{agent_name}/follow', method='POST')
        if result and result.get('success'):
            print(f"Now following {agent_name}")
            return True
        else:
            print("Failed to follow")
            return False

    def comment_on_post(self, post_id: str, content: str) -> bool:
        """
        Alias for comment() method for compatibility.
        
        Args:
            post_id: The ID of the post to comment on
            content: Comment content
            
        Returns:
            True if successful, False otherwise
        """
        return self.comment(post_id, content)


# Convenience functions for easy use
_client = None

def get_client() -> MoltbookClient:
    """Get or create the Moltbook client instance."""
    global _client
    if _client is None:
        _client = MoltbookClient()
    return _client

def post_to_moltbook(submolt: str, title: str, content: str) -> bool:
    """Convenience function to post to Moltbook."""
    return get_client().post(submolt, title, content) is not None

def comment_on_post(post_id: str, content: str) -> bool:
    """Convenience function to comment on a post."""
    return get_client().comment(post_id, content)

def get_moltbook_feed(limit: int = 10) -> Optional[List[Dict]]:
    """Convenience function to get the feed."""
    return get_client().get_feed(limit)
