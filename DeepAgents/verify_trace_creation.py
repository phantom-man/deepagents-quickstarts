import os
import sys
import time

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langsmith import Client

# Load env
load_dotenv("DeepAgents/.env")

# Ensure environment variables are active
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "DeepAgents"

print(f"--- Verifying Tracing for Project: {os.getenv('LANGCHAIN_PROJECT')} ---")

try:
    # Initialize Model
    # Setting project/location explicitly from env if needed, usually ChatVertexAI picks them up
    # but we will pass them to be safe if they exist
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION")

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        temperature=0.7,
        project=project,
        location=location,
    )

    print("Sending request to LLM...")
    response = llm.invoke(
        [HumanMessage(content="Hello! Please confirm this is a test trace.")]
    )
    print(f"\nResponse received: {response.content[:50]}...")

    # Verify via Client
    print("\nQuerying LangSmith for recent runs...")
    time.sleep(3)  # Give it a moment to ingest
    client = Client()
    runs = list(client.list_runs(project_name="DeepAgents", limit=1))

    if runs:
        print(f"✅ FOUND RUN: {runs[0].name} (ID: {runs[0].id})")
        print("LangSmith Tracing is CONFIRMED WORKING.")
    else:
        print(
            "⚠️ No runs returned yet. It might take a few more seconds or configuration is partial."
        )

except Exception as e:
    print(f"\n❌ Error generating trace: {e}")
    sys.exit(1)
