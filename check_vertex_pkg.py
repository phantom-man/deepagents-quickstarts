try:
    from langchain_google_vertexai import ChatVertexAI

    print("ChatVertexAI is available")
except ImportError:
    print("ChatVertexAI is NOT available")

try:
    from langchain_google_genai import ChatGoogleGenerativeAI

    print("ChatGoogleGenerativeAI is available")
except ImportError:
    print("ChatGoogleGenerativeAI is NOT available")
