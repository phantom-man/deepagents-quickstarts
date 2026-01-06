import os
import urllib.request
import urllib.error
from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults

# Initialize Tavily Search
tavily_search = TavilySearchResults(max_results=5)

@tool
def scrape_webpage(url: str) -> str:
    """
    Fetches the content of a webpage using a custom User-Agent to avoid blocking.
    Useful for reading product pages, articles, or blog posts in depth.
    """
    print(f"Scraping {url}...")
    try:
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        )
        with urllib.request.urlopen(req) as response:
            content = response.read().decode('utf-8')
            # Basic HTML cleanup could go here, but returning raw text is often fine for LLMs
            # or we could use BeautifulSoup if we wanted to be fancy, but let's keep it simple and robust.
            return content[:50000] # Limit content to avoid context overflow

    except urllib.error.HTTPError as e:
        return f"Error: HTTP {e.code} - {e.reason}"
    except urllib.error.URLError as e:
        return f"Error: URL Error - {e.reason}"
    except Exception as e:
        return f"Error: {str(e)}"
