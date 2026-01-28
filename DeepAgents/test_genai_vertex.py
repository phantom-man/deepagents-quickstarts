import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv("DeepAgents/.env")

print("Testing ChatGoogleGenerativeAI with vertexai=True...")

try:
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-001",
        vertexai=True,
        project=os.getenv("GOOGLE_CLOUD_PROJECT"),
        location="us-central1",
    )

    print("Invoking...")
    res = llm.invoke("Hi")
    print(f"Result: {res.content}")
    print("✅ SUCCESS: ChatGoogleGenerativeAI works with Vertex AI mode.")

except Exception as e:
    print(f"❌ ERROR: {e}")
