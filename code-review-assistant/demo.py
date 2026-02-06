#!/usr/bin/env python3
"""
Demo script showing the Code Review Assistant in action
"""

from backend.agents.code_analyzer import CodeAnalysisAgent
import json

def demo_code_review():
    print("🤖 AI Code Review Assistant Demo")
    print("=" * 50)

    # Initialize the agent
    agent = CodeAnalysisAgent()

    # Sample code with various issues
    sample_code = '''
def process_user_data(data):
    users = []
    for item in data:
        if item['age'] > 18:
            users.append(item)
    return users

# Usage
data = [{"name": "Alice", "age": 25}, {"name": "Bob", "age": 17}]
result = process_user_data(data)
print(result)
'''

    print("📝 Code to analyze:")
    print(sample_code)
    print("\n" + "=" * 50)

    # Analyze the code
    print("🔍 Analyzing code...")
    result = agent.analyze_code(
        code=sample_code,
        language="python",
        context="User data filtering function"
    )

    print("📊 Analysis Results:")
    print(f"Overall Score: {result.get('score', 'N/A')}/100")
    print(f"Summary: {result.get('summary', 'No summary available')}")
    print("\nDetailed Comments:")

    for i, comment in enumerate(result.get('comments', []), 1):
        print(f"{i}. Line {comment.get('line', '?')}: [{comment.get('type', 'unknown')}]")
        print(f"   {comment.get('message', 'No message')}")
        print(f"   Severity: {comment.get('severity', 'unknown')}")
        print()

    print("✅ Demo completed!")
    print("\nTo run the full API server:")
    print("1. Set OPENAI_API_KEY in .env file")
    print("2. Run: python backend/main.py")
    print("3. Test: python test_api.py")

if __name__ == "__main__":
    demo_code_review()</content>
<parameter name="filePath">c:\Users\User\source\repos\deepagents-quickstarts\code-review-assistant\demo.py