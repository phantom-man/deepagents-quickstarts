import logging

from dotenv import load_dotenv
from langchain.tools import tool
from langchain_google_vertexai import ChatVertexAI

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@tool
def simple_tool(input_str: str) -> str:
    """A simple tool to test binding."""
    return f"Processed: {input_str}"


def test_binding():
    print("--- Testing ChatVertexAI Tool Binding ---")
    try:
        model = ChatVertexAI(
            model="gemini-2.0-flash-001",
            temperature=0,
            location="us-central1",  # or global, check what works
        )

        print(f"Model initialized: {model.model_name}")

        # Test 1: Simple Invocation
        print("Invoking simple prompt...")
        res = model.invoke("Hello")
        print(f"Response: {res.content}")

        # Test 2: Binding
        print("Binding tool...")
        model_with_tools = model.bind_tools([simple_tool])

        # Test 3: Invocation with Tools
        print("Invoking with tool request...")
        res_tool = model_with_tools.invoke("Use the simple tool to process 'test'")
        print(f"Tool Call Response: {res_tool.tool_calls}")

        print("✅ SUCCESS: Tool binding and invocation worked!")

    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_binding()
