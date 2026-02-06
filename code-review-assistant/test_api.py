#!/usr/bin/env python3
"""
Test script for the Code Review Assistant
"""

import requests
import json

def test_code_review():
    # Sample code to analyze
    test_code = """
def fibonacci(n):
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fibonacci(n-1) + fibonacci(n-2)

# Test the function
print(fibonacci(10))
"""

    # API request
    url = "http://localhost:8000/api/review"
    payload = {
        "code": test_code,
        "language": "python",
        "context": "Recursive Fibonacci implementation"
    }

    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            print("✅ Code Review Results:")
            print(f"Summary: {result['summary']}")
            print(f"Score: {result['score']}/100")
            print("\nComments:")
            for comment in result['comments']:
                print(f"  Line {comment['line']}: [{comment['type']}] {comment['message']} ({comment['severity']})")
        else:
            print(f"❌ API Error: {response.status_code}")
            print(response.text)
    except requests.RequestException as e:
        print(f"❌ Request failed: {e}")
        print("Note: Make sure the server is running with: python backend/main.py")

if __name__ == "__main__":
    test_code_review()</content>
<parameter name="filePath">c:\Users\User\source\repos\deepagents-quickstarts\code-review-assistant\test_api.py