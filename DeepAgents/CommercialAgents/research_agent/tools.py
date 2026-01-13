import os
import urllib.request
import urllib.error
from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.tools.arxiv.tool import ArxivQueryRun

# Initialize Tavily Search or Mock
try:
    if not os.environ.get("TAVILY_API_KEY"):
        raise ValueError("TAVILY_API_KEY Missing")
    tavily_search = TavilySearchResults(max_results=5)
except Exception:
    # Define a mock tool if Tavily is unavailable
    @tool
    def tavily_search(query: str) -> str:
        """Mock Search Tool (Tavily not configured). Returns simulated results."""
        return f"Simulated Search Results for: {query}\n1. [Wiki] Lord of the Rings is an epic high-fantasy novel by J.R.R. Tolkien.\n2. [Summary] The Hero's Journey (Monomyth) involves a hero going on an adventure, winning a victory, and coming home changed."

# Initialize Arxiv Search
arxiv_search = ArxivQueryRun()

@tool
def scrape_webpage(url: str) -> str:
    """
    Scrapes the content of a webpage.
    Args:
        url: The URL to scrape.
    """
    try:
        # Basic scrape with header to avoid 403s
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read().decode('utf-8')[:8000] # Limit context window usage
    except Exception as e:
        return f"Error scraping {url}: {e}"

@tool
def save_research_file(filename: str, content: str) -> str:
    """
    Saves research findings to a file.
    Args:
        filename: Relative path (e.g., 'rome/fall.md') or name.
        content: The text content to save.
    """
    try:
        # Enforce absolute path relative to data/research
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        target_dir = os.path.join(root_dir, "data", "research")
        
        # Sanitize filename (remove leading slashes to avoid absolute override)
        clean_name = filename.lstrip("/\\")
        
        full_path = os.path.join(target_dir, clean_name)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        return f"File successfully saved to: {full_path}"
    except Exception as e:
        return f"Error saving file: {e}"

@tool
def submit_finding_for_review(finding_text: str) -> str:
    """
    Submits a research finding to the Confidence Agent (Editor) for validation.
    The finding MUST be verified.
    Returns: JSON string with {status: ACCEPTED/REJECTED, score: float, critique: str}
    """
    try:
        # Lazy import to avoid circular dependency
        from DeepAgents.CommercialAgents.confidence_agent.agent import create_confidence_agent
        from langchain_core.messages import HumanMessage
        
        # Initialize Confidence Agent (Ephemeral)
        # Using default config (Anthropic)
        auditor = create_confidence_agent()
        
        prompt = f"VERIFICATION REQUEST:\n\n{finding_text}"
        
        result = auditor.invoke({"messages": [HumanMessage(content=prompt)]})
        
        # Parse the JSON response just to log it (return full string to Research Agent)
        result_content = result["messages"][-1].content
        return str(result_content)

    except Exception as e:
        return f'{{"status": "ERROR", "score": 0.0, "critique": "Validation System Error: {e}"}}'

# Expose
__all__ = ["tavily_search", "arxiv_search", "scrape_webpage", "save_research_file", "submit_finding_for_review"]
