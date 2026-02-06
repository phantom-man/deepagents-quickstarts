"""
Solve Moltbook comment verification challenges.
"""

import requests
import json
from pathlib import Path
import re

def load_credentials():
    """Load Moltbook API credentials."""
    config_path = Path.home() / ".config" / "moltbook" / "credentials.json"
    with open(config_path, "r") as f:
        return json.load(f)

def solve_challenge(challenge_text: str) -> float:
    """Extract and solve the math problem from the challenge."""
    # Extract numbers from the challenge
    # The challenges are obscured but contain math problems
    
    print(f"Challenge: {challenge_text[:100]}...")
    
    # Look for number words
    number_words = {
        'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
        'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9,
        'ten': 10, 'eleven': 11, 'twelve': 12, 'thirteen': 13,
        'fourteen': 14, 'fifteen': 15, 'sixteen': 16, 'seventeen': 17,
        'eighteen': 18, 'nineteen': 19, 'twenty': 20, 'thirty': 30,
        'forty': 40, 'fifty': 50, 'sixty': 60, 'seventy': 70,
        'eighty': 80, 'ninety': 90, 'hundred': 100
    }
    
    # Clean up the challenge text (remove weird formatting)
    clean = challenge_text.lower()
    clean = re.sub(r'[^a-z0-9\s\+\-\*\/\?]', ' ', clean)
    clean = ' '.join(clean.split())  # Normalize whitespace
    
    print(f"Cleaned: {clean}")
    
    # Try to find the operation and numbers
    if 'product' in clean:
        # Multiplication
        words = clean.split()
        numbers = []
        i = 0
        while i < len(words):
            word = words[i]
            if word in number_words:
                num = number_words[word]
                # Check for compound numbers like "twenty three"
                if i + 1 < len(words) and words[i+1] in number_words:
                    next_num = number_words[words[i+1]]
                    if num >= 20 and next_num < 10:
                        num = num + next_num
                        i += 1
                numbers.append(num)
            i += 1
        
        if len(numbers) >= 2:
            result = numbers[-2] * numbers[-1]
            print(f"Found numbers: {numbers[-2]} * {numbers[-1]} = {result}")
            return float(result)
    
    elif 'combined' in clean or 'total' in clean or 'sum' in clean:
        # Addition
        words = clean.split()
        numbers = []
        i = 0
        while i < len(words):
            word = words[i]
            if word in number_words:
                num = number_words[word]
                # Check for compound numbers
                if i + 1 < len(words) and words[i+1] in number_words:
                    next_num = number_words[words[i+1]]
                    if num >= 20 and next_num < 10:
                        num = num + next_num
                        i += 1
                numbers.append(num)
            i += 1
        
        if len(numbers) >= 2:
            result = numbers[-2] + numbers[-1]
            print(f"Found numbers: {numbers[-2]} + {numbers[-1]} = {result}")
            return float(result)
    
    # Fallback: try to find any digit patterns
    digits = re.findall(r'\d+', clean)
    if len(digits) >= 2:
        result = int(digits[-2]) * int(digits[-1])  # Guess multiplication
        print(f"Fallback with digits: {digits}")
        return float(result)
    
    print("Could not solve automatically")
    return 0.0


def verify_comment(verification_code: str, answer: float):
    """Submit verification answer."""
    creds = load_credentials()
    api_key = creds["api_key"]
    base_url = "https://www.moltbook.com/api/v1"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{base_url}/verify",
        headers=headers,
        json={
            "verification_code": verification_code,
            "answer": f"{answer:.2f}"
        }
    )
    
    return response.status_code, response.json()


def main():
    # The verification challenges from the comments
    verifications = [
        {
            "code": "moltbook_verify_d3b774d3240343d5ff2b64d5ec6a1fcb",
            "challenge": "twenty three * seven - product of velocities",
            "numbers": [23, 7],
            "operation": "multiply"
        },
        {
            "code": "moltbook_verify_4d8c3795532445752cf0e43bd5ddc5f0",
            "challenge": "twenty three notons + sixteen notons - combined force",
            "numbers": [23, 16],
            "operation": "add"
        },
        {
            "code": "moltbook_verify_186f6fd75215cd04cf9c4a84f217aa4f",
            "challenge": "thirty two notons + fifteen notons - total force",
            "numbers": [32, 15],
            "operation": "add"
        }
    ]
    
    for v in verifications:
        if v["operation"] == "multiply":
            answer = v["numbers"][0] * v["numbers"][1]
        else:  # add
            answer = v["numbers"][0] + v["numbers"][1]
        
        print(f"\nVerifying: {v['challenge'][:50]}...")
        print(f"  Answer: {answer:.2f}")
        
        status, result = verify_comment(v["code"], float(answer))
        print(f"  Status: {status}")
        if result.get("success"):
            print(f"  ✅ Verified!")
        else:
            print(f"  ❌ Failed: {result}")


if __name__ == "__main__":
    main()
