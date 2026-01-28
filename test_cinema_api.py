"""Test cinematographer agent via LangGraph API."""

import json

import requests

# Test cinematographer graph via LangGraph API
url = "http://127.0.0.1:2024/runs/stream"

payload = {
    "assistant_id": "cinematographer",
    "input": {
        "messages": [
            {
                "role": "user",
                "content": "Generate a video of a majestic eagle soaring over mountain peaks at sunset",
            }
        ]
    },
    "stream_mode": ["messages", "values"],
    "config": {"configurable": {"thread_id": "veo_test_456"}},
}

print("Sending request to cinematographer agent...")
print(
    "Prompt: Generate a video of a majestic eagle soaring over mountain peaks at sunset"
)
print()

response = requests.post(url, json=payload, stream=True, timeout=300)
print(f"Response status: {response.status_code}")

# Stream response
for line in response.iter_lines():
    if line:
        decoded = line.decode("utf-8")
        if decoded.startswith("data:"):
            try:
                data = json.loads(decoded[5:].strip())
                if isinstance(data, dict):
                    # Print tool calls and results
                    if "messages" in data:
                        for msg in data.get("messages", []):
                            if isinstance(msg, dict):
                                if msg.get("type") == "tool":
                                    content = msg.get("content", "")
                                    print(f"TOOL RESULT: {content[:300]}...")
                                elif msg.get("type") == "ai" and msg.get("tool_calls"):
                                    for tc in msg.get("tool_calls", []):
                                        name = tc.get("name", "unknown")
                                        args = str(tc.get("args", {}))[:100]
                                        print(f"TOOL CALL: {name} - {args}")
            except json.JSONDecodeError:
                pass

print("\n--- Test complete ---")
