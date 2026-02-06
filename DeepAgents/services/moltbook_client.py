"""
Enhanced Moltbook Client for DeepAgents

A robust client for interacting with the Moltbook platform that handles:
- Authentication
- Rate limiting
- Verification challenges
- Post and comment management
- DM handling
"""

import requests
import json
import re
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class MoltbookPost:
    """Represents a Moltbook post."""
    id: str
    title: str
    content: str
    submolt: str
    author_name: str
    upvotes: int
    comment_count: int
    created_at: str


@dataclass  
class MoltbookComment:
    """Represents a Moltbook comment."""
    id: str
    content: str
    author_name: str
    upvotes: int
    created_at: str


class MoltbookClient:
    """
    Robust Moltbook API client with automatic verification handling.
    """
    
    BASE_URL = "https://www.moltbook.com/api/v1"
    
    def __init__(self, credentials_path: Optional[Path] = None):
        """Initialize the client with credentials."""
        self.credentials_path = credentials_path or (Path.home() / ".config" / "moltbook" / "credentials.json")
        self.api_key: Optional[str] = None
        self.agent_name: Optional[str] = None
        self._load_credentials()
        
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "DeepAgentsAtlas/1.0"
        })
        
        if self.api_key:
            self.session.headers["Authorization"] = f"Bearer {self.api_key}"
    
    def _load_credentials(self):
        """Load credentials from file."""
        try:
            with open(self.credentials_path, "r") as f:
                creds = json.load(f)
                self.api_key = creds.get("api_key")
                self.agent_name = creds.get("agent_name")
        except FileNotFoundError:
            logger.warning(f"Credentials file not found at {self.credentials_path}")
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in credentials file")
    
    def _solve_verification(self, challenge: str) -> Optional[float]:
        """
        Solve the Moltbook math verification challenge.
        
        The challenges are obfuscated text with math problems embedded.
        """
        # Number words mapping
        number_words = {
            'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
            'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9,
            'ten': 10, 'eleven': 11, 'twelve': 12, 'thirteen': 13,
            'fourteen': 14, 'fifteen': 15, 'sixteen': 16, 'seventeen': 17,
            'eighteen': 18, 'nineteen': 19, 'twenty': 20, 'thirty': 30,
            'forty': 40, 'fifty': 50, 'sixty': 60, 'seventy': 70,
            'eighty': 80, 'ninety': 90, 'hundred': 100
        }
        
        # Clean the challenge text
        clean = challenge.lower()
        clean = re.sub(r'[^a-z0-9\s]', ' ', clean)
        clean = ' '.join(clean.split())
        
        # Extract numbers
        words = clean.split()
        numbers = []
        i = 0
        while i < len(words):
            word = words[i]
            if word in number_words:
                num = number_words[word]
                # Handle compound numbers
                if i + 1 < len(words) and words[i+1] in number_words:
                    next_num = number_words[words[i+1]]
                    if num >= 20 and next_num < 10:
                        num = num + next_num
                        i += 1
                numbers.append(num)
            i += 1
        
        if len(numbers) < 2:
            logger.warning(f"Could not extract enough numbers from challenge")
            return None
        
        # Determine operation
        if 'product' in clean:
            result = numbers[-2] * numbers[-1]
        elif any(w in clean for w in ['combined', 'total', 'sum', 'adds', 'and']):
            result = numbers[-2] + numbers[-1]
        elif 'difference' in clean:
            result = abs(numbers[-2] - numbers[-1])
        else:
            # Default to addition
            result = numbers[-2] + numbers[-1]
        
        logger.info(f"Solved challenge: {numbers[-2]} op {numbers[-1]} = {result}")
        return float(result)
    
    def _verify_content(self, verification_code: str, answer: float) -> Tuple[bool, Dict]:
        """Submit verification answer."""
        response = self.session.post(
            f"{self.BASE_URL}/verify",
            json={
                "verification_code": verification_code,
                "answer": f"{answer:.2f}"
            }
        )
        
        result = response.json()
        return result.get("success", False), result
    
    # =========================================================================
    # PUBLIC API METHODS
    # =========================================================================
    
    def get_agent_info(self) -> Optional[Dict]:
        """Get current agent information."""
        response = self.session.get(f"{self.BASE_URL}/agents/me")
        if response.status_code == 200:
            data = response.json()
            return data.get("agent")
        return None
    
    def get_feed(self, sort: str = "new", limit: int = 20) -> List[MoltbookPost]:
        """Get personalized feed."""
        response = self.session.get(
            f"{self.BASE_URL}/feed",
            params={"sort": sort, "limit": limit}
        )
        
        if response.status_code != 200:
            return []
        
        data = response.json()
        posts = []
        for p in data.get("posts", []):
            posts.append(MoltbookPost(
                id=p.get("id"),
                title=p.get("title", ""),
                content=p.get("content", ""),
                submolt=p.get("submolt", {}).get("name", "general"),
                author_name=p.get("author", {}).get("name", "Unknown"),
                upvotes=p.get("upvotes", 0),
                comment_count=p.get("comment_count", 0),
                created_at=p.get("created_at", "")
            ))
        return posts
    
    def get_hot_posts(self, limit: int = 50) -> List[MoltbookPost]:
        """Get hot posts globally."""
        response = self.session.get(
            f"{self.BASE_URL}/posts",
            params={"sort": "hot", "limit": limit}
        )
        
        if response.status_code != 200:
            return []
        
        data = response.json()
        posts = []
        for p in data.get("posts", []):
            posts.append(MoltbookPost(
                id=p.get("id"),
                title=p.get("title", ""),
                content=p.get("content") or "",
                submolt=p.get("submolt", {}).get("name", "general") if p.get("submolt") else "general",
                author_name=p.get("author", {}).get("name", "Unknown") if p.get("author") else "Unknown",
                upvotes=p.get("upvotes", 0),
                comment_count=p.get("comment_count", 0),
                created_at=p.get("created_at", "")
            ))
        return posts
    
    def get_post(self, post_id: str) -> Optional[Dict]:
        """Get a specific post with comments."""
        response = self.session.get(f"{self.BASE_URL}/posts/{post_id}")
        if response.status_code == 200:
            return response.json().get("post")
        return None
    
    def create_post(
        self, 
        submolt: str, 
        title: str, 
        content: str,
        auto_verify: bool = True
    ) -> Tuple[bool, Optional[str], Dict]:
        """
        Create a new post with automatic verification.
        
        Returns: (success, post_id, full_response)
        """
        response = self.session.post(
            f"{self.BASE_URL}/posts",
            json={
                "submolt": submolt,
                "title": title,
                "content": content
            }
        )
        
        # Handle rate limiting
        if response.status_code == 429:
            data = response.json()
            retry_after = data.get("retry_after_seconds", 60)
            logger.warning(f"Rate limited. Retry after {retry_after} seconds")
            return False, None, {"error": "rate_limited", "retry_after": retry_after}
        
        if response.status_code not in (200, 201):
            return False, None, {"error": response.text}
        
        result = response.json()
        
        # Handle verification if needed
        if result.get("requires_verification") and auto_verify:
            verification = result.get("verification", {})
            challenge = verification.get("challenge", "")
            code = verification.get("code", "")
            
            answer = self._solve_verification(challenge)
            if answer is not None:
                success, verify_result = self._verify_content(code, answer)
                if success:
                    post_id = verify_result.get("post", {}).get("id")
                    return True, post_id, verify_result
                else:
                    return False, None, verify_result
            else:
                return False, None, {"error": "could_not_solve_verification"}
        
        # No verification needed or already handled
        post_id = result.get("post", {}).get("id")
        return True, post_id, result
    
    def create_comment(
        self,
        post_id: str,
        content: str,
        auto_verify: bool = True
    ) -> Tuple[bool, Optional[str], Dict]:
        """
        Create a comment on a post with automatic verification.
        
        Returns: (success, comment_id, full_response)
        """
        response = self.session.post(
            f"{self.BASE_URL}/posts/{post_id}/comments",
            json={"content": content}
        )
        
        if response.status_code == 429:
            data = response.json()
            retry_after = data.get("retry_after_seconds", 60)
            return False, None, {"error": "rate_limited", "retry_after": retry_after}
        
        if response.status_code not in (200, 201):
            return False, None, {"error": response.text}
        
        result = response.json()
        
        if result.get("verification_required") and auto_verify:
            verification = result.get("verification", {})
            challenge = verification.get("challenge", "")
            code = verification.get("code", "")
            
            answer = self._solve_verification(challenge)
            if answer is not None:
                success, verify_result = self._verify_content(code, answer)
                if success:
                    comment_id = verify_result.get("comment", {}).get("id")
                    return True, comment_id, verify_result
        
        comment_id = result.get("comment", {}).get("id")
        return True, comment_id, result
    
    def upvote_post(self, post_id: str) -> bool:
        """Upvote a post."""
        response = self.session.post(f"{self.BASE_URL}/posts/{post_id}/upvote")
        return response.status_code == 200
    
    def search_posts(
        self, 
        keywords: List[str],
        limit: int = 50
    ) -> List[MoltbookPost]:
        """Search for posts containing specific keywords."""
        all_posts = self.get_hot_posts(limit=limit)
        
        matching = []
        for post in all_posts:
            text = f"{post.title} {post.content}".lower()
            if any(kw.lower() in text for kw in keywords):
                matching.append(post)
        
        return matching
    
    def get_dm_status(self) -> Dict:
        """Check DM requests and unread messages."""
        response = self.session.get(f"{self.BASE_URL}/agents/dm/requests")
        if response.status_code == 200:
            return response.json()
        return {"pending_requests": 0, "unread_messages": 0}


# =========================================================================
# CONVENIENCE FUNCTIONS
# =========================================================================

def get_client() -> MoltbookClient:
    """Get a configured MoltbookClient instance."""
    return MoltbookClient()


def quick_post(submolt: str, title: str, content: str) -> Tuple[bool, Optional[str]]:
    """Quick helper to create a post."""
    client = get_client()
    success, post_id, _ = client.create_post(submolt, title, content)
    return success, post_id


def quick_comment(post_id: str, content: str) -> Tuple[bool, Optional[str]]:
    """Quick helper to create a comment."""
    client = get_client()
    success, comment_id, _ = client.create_comment(post_id, content)
    return success, comment_id
