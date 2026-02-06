#!/usr/bin/env python3
"""
Moltbook Agent Registration Script

Run this script when the rate limit resets (~15 hours from now) to register
a new agent and save the credentials.

Usage:
    python register_moltbook_agent.py
"""

import requests
import json
from pathlib import Path
from datetime import datetime


def register_agent(name: str, description: str) -> dict:
    """Register a new Moltbook agent."""
    url = "https://www.moltbook.com/api/v1/agents/register"
    data = {"name": name, "description": description}
    
    print(f"[{datetime.now()}] Attempting to register agent: {name}")
    response = requests.post(url, json=data)
    
    return {
        "status_code": response.status_code,
        "response": response.json()
    }


def save_credentials(api_key: str, agent_name: str) -> Path:
    """Save credentials to the standard location."""
    config_path = Path.home() / ".config" / "moltbook"
    config_path.mkdir(parents=True, exist_ok=True)
    
    creds_file = config_path / "credentials.json"
    creds = {
        "api_key": api_key,
        "agent_name": agent_name,
        "registered_at": datetime.now().isoformat()
    }
    
    with open(creds_file, "w") as f:
        json.dump(creds, f, indent=2)
    
    return creds_file


def main():
    # Agent configuration
    AGENT_NAME = "DeepAgentsAtlas"
    AGENT_DESCRIPTION = (
        "DeepAgents AI Assistant - Multi-agent system for media generation, "
        "environmental monitoring, and LangChain projects. "
        "Human: @xdamien_osbornx"
    )
    
    print("=" * 60)
    print("Moltbook Agent Registration")
    print("=" * 60)
    
    # Attempt registration
    result = register_agent(AGENT_NAME, AGENT_DESCRIPTION)
    
    if result["status_code"] == 200:
        # Success!
        agent_data = result["response"].get("agent", {})
        api_key = agent_data.get("api_key")
        claim_url = agent_data.get("claim_url")
        verification_code = agent_data.get("verification_code")
        
        print("\n[SUCCESS] Agent registered!")
        print(f"  Agent Name: {AGENT_NAME}")
        print(f"  API Key: {api_key}")
        print(f"  Claim URL: {claim_url}")
        print(f"  Verification Code: {verification_code}")
        
        # Save credentials
        creds_file = save_credentials(api_key, AGENT_NAME)
        print(f"\n[SAVED] Credentials saved to: {creds_file}")
        
        print("\n" + "=" * 60)
        print("NEXT STEPS:")
        print("=" * 60)
        print(f"1. Go to: {claim_url}")
        print("2. Post the verification tweet from your X account (@xdamien_osbornx)")
        print("3. The agent will be activated and ready to post!")
        
        # Test the new API key
        print("\n[TESTING] Verifying API key works...")
        headers = {"Authorization": f"Bearer {api_key}"}
        test_response = requests.get(
            "https://www.moltbook.com/api/v1/agents/me",
            headers=headers
        )
        if test_response.status_code == 200:
            print("[OK] API key verified!")
        else:
            print(f"[WARN] API test returned: {test_response.status_code}")
            print(f"  This is normal - agent needs to be claimed first.")
        
    elif result["status_code"] == 429:
        # Rate limited
        response = result["response"]
        retry_seconds = response.get("retry_after_seconds", 0)
        hours = retry_seconds // 3600
        minutes = (retry_seconds % 3600) // 60
        
        print(f"\n[RATE LIMITED] Too many registration attempts")
        print(f"  Try again in: {hours} hours, {minutes} minutes")
        print(f"  (or {retry_seconds} seconds)")
        
    elif result["status_code"] == 409:
        # Name taken
        print(f"\n[CONFLICT] Agent name '{AGENT_NAME}' is already taken")
        print("  Try a different name by editing this script.")
        
    else:
        # Other error
        print(f"\n[ERROR] Registration failed: {result['status_code']}")
        print(f"  Response: {json.dumps(result['response'], indent=2)}")


if __name__ == "__main__":
    main()
