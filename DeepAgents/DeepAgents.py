import os
from dotenv import load_dotenv
from langchain_tavily import TavilySearch 
from google import genai

# Load environment variables from .env file
load_dotenv()

# Verify keys are loaded (printing partial keys for security)
tavily_key = os.getenv("TAVILY_API_KEY")
google_key = os.getenv("GOOGLE_API_KEY")

# Optional: LangChain Tracing
if os.getenv("LANGCHAIN_TRACING_V2") == "true":
    print("LangChain Tracing is enabled.")

print(f"Tavily Key Loaded: {'Yes (' + tavily_key[:5] + '...)' if tavily_key else 'No'}")
print(f"Google Key Loaded: {'Yes (' + google_key[:5] + '...)' if google_key else 'No'}")

if not tavily_key or not google_key:
    print("Skipping execution: Missing API keys.")
    exit(0)

try:
    # Initialize the Tavily Search Tool
    tool = TavilySearch(
        api_key=tavily_key,
        max_results=5,
        search_depth="advanced",
        include_answer=True,
        include_raw_content=True
    )

    # Initialize Google Gemini Client
    client = genai.Client(api_key=google_key)

    print("\n--- Running Search ---")
    query = "What happened in the latest AI news?"
    results = tool.invoke({"query": query})

    # Print raw search results
    if 'results' in results:
        for result in results['results']:
            print(f"Source: {result.get('url', 'Unknown')}")
    
        # Integrate: Use Gemini to process the search results
        print("\n--- Generating Summary with Gemini ---")
        context = "\n\n".join([f"Source: {r.get('url')}\nContent: {r.get('content')}" for r in results['results']])
        prompt = f"Based on the following search results, provide a concise summary of the latest AI news:\n\n{context}"

        response = client.models.generate_content(
            model="gemini-2.0-flash-exp", 
            contents=prompt
        )
        print(response.text)
    else:
        print("No results found from Tavily.")

except Exception as e:
    print(f"An error occurred: {e}")
