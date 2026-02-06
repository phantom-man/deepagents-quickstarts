import json
import logging
import os
import urllib.error
import urllib.request
from typing import Optional

from langchain_community.tools.arxiv.tool import ArxivQueryRun
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import BaseTool, tool

from DeepAgents.agent_brain import AgentMemory

logger = logging.getLogger(__name__)

# Initialize Tavily Search or Mock
tavily_search_tool: Optional[BaseTool] = None
try:
    if not os.environ.get("TAVILY_API_KEY"):
        # Not required if we are using Google Grounding
        # raise ValueError("TAVILY_API_KEY Missing")
        # Just warn and set to Mock
        logger.warning("TAVILY_API_KEY missing. Tavily search disabled.")
        tavily_search_tool = None
    else:
        # Check for new package
        try:
            from langchain_tavily import TavilySearchResults  # type: ignore[import-not-found]
        except ImportError:
            # Fallback to community
            from langchain_community.tools.tavily_search import TavilySearchResults

        tavily_search_tool = TavilySearchResults(max_results=5)
except Exception:
    tavily_search_tool = None

# DEPRECATED: Tavily is deprecated for Google Agents. Use Native Google Search Grounding instead.
# Removed tavily_search tool.

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
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read().decode("utf-8")[:8000]  # Limit context window usage
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
        root_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )
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
        from langchain_core.messages import HumanMessage

        from DeepAgents.CommercialAgents.confidence_agent.agent import (
            create_confidence_agent,
        )

        # Initialize Confidence Agent (Ephemeral)
        # Using default config (Anthropic)
        auditor = create_confidence_agent()

        prompt = f"VERIFICATION REQUEST:\n\n{finding_text}"

        result = auditor.invoke({"messages": [HumanMessage(content=prompt)]})

        # Parse the JSON response
        result_content = result["messages"][-1].content

        # --- FEEDBACK LOOP LEARNING ---
        try:
            # Clean possible markdown block ```json ... ```
            cleaned_json = (
                result_content.replace("```json", "").replace("```", "").strip()
            )
            data = json.loads(cleaned_json)

            score = float(data.get("score", 0.0))

            # 1. Negative Reinforcement (Score < 0.7)
            if score < 0.7:
                # Store in LanceDB as a "Lesson Learned"
                mem = AgentMemory()
                mem.memorize(
                    f"[REJECTED MISTAKE] Finding: {finding_text}\nCritique: {data.get('critique', 'N/A')}",
                    "ResearchAgent",
                    tags=["rejected_finding", "mistake"],
                )
                logger.info("❌ Finding Rejected and Logged to Memory (LanceDB).")

                # Check for legacy file and warn
                bad_ex_path = os.path.join(os.path.dirname(__file__), "bad_examples.md")
                if os.path.exists(bad_ex_path):
                    logger.warning(
                        "Legacy 'bad_examples.md' exists but system now uses Vector Memory."
                    )

            # 2. Positive Reinforcement (Score >= 0.8)
            elif score >= 0.8:
                # Save to LanceDB
                mem = AgentMemory()
                mem.memorize(
                    f"VERIFIED FACT ({score}): {finding_text}",
                    "ResearchAgent",
                    tags=["verified_fact", "research_finding"],
                )
                logger.info("✅ Finding Approved and Memorized.")

        except json.JSONDecodeError:
            logger.warning("Could not parse Confidence Agent JSON for feedback loop.")
        except Exception as e:
            logger.error(f"Feedback Loop Error: {e}")
        # -----------------------------

        return str(result_content)

    except Exception as e:
        return f'{{"status": "ERROR", "score": 0.0, "critique": "Validation System Error: {e}"}}'


# Expose
__all__ = [
    "arxiv_search",
    "scrape_webpage",
    "save_research_file",
    "submit_finding_for_review",
]
