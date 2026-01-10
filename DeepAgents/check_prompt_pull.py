
import os
from dotenv import load_dotenv
from langsmith import Client

load_dotenv("DeepAgents/.env")

try:
    client = Client()
    prompt = client.pull_prompt("deep-agents-director-system")
    print(f"Type: {type(prompt)}")
    # content = prompt.format_messages({})[0].content # This is what I want to verify
    msgs = prompt.invoke({}).to_messages()
    print(f"Messages: {msgs}")
    print(f"Content: {msgs[0].content[:50]}...")
except Exception as e:
    print(f"Error: {e}")
