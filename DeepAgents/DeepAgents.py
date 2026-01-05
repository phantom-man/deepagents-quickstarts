#import os
#from dotenv import load_dotenv
#from langchain_tavily import TavilySearch 
#from google import genai

# Load environment variables from .env file
#load_dotenv()

# Verify keys are loaded (printing partial keys for security)
#tavily_key = os.getenv("TAVILY_API_KEY")
#google_key = os.getenv("GOOGLE_API_KEY")

#print(f"Tavily Key Loaded: {'Yes (' + tavily_key[:5] + '...)' if tavily_key else 'No'}")
#print(f"Google Key Loaded: {'Yes (' + google_key[:5] + '...)' if google_key else 'No'}")

# Initialize the Tavily Search Tool
#tool = TavilySearch(
#    api_key=tavily_key,
 #   max_results=5,
  #  search_depth="advanced",
   # include_answer=True,
    #include_raw_content=True
#)

# Initialize Google Gemini Client
#client = genai.Client(api_key=google_key)

#print("\n--- Running Search ---")
#query = "What happened in the latest AI news?"
#results = tool.invoke({"query": query})

# Print raw search results
#for result in results['results']:
#    print(f"Source: {result['url']}")
    # print(f"Content: {result['content']}\n") # Optional: print raw content

# Integrate: Use Gemini to process the search results
#print("\n--- Generating Summary with Gemini ---")
#context = "\n\n".join([f"Source: {r['url']}\nContent: {r['content']}" for r in results['results']])
#prompt = f"Based on the following search results, provide a concise summary of the latest AI news:\n\n{context}"

#response = client.models.generate_content(
    #model="gemini-2.0-flash-exp", # Reverting to the original model as others also have limits
    #contents=prompt
#)
#print(response.text)
