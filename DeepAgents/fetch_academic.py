"""
Research Agent Tool: Fetch Academic Papers
Uses Semantic Scholar API to retrieve research papers.
Strict adherence to "The Jewel Standard" (Pylint 10/10).
"""

import argparse
import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FetchAcademic")

SEMANTIC_SCHOLAR_API_URL = "https://api.semanticscholar.org/graph/v1/paper/search"


def search_semantic_scholar(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Searches Semantic Scholar for papers matching the query.

    Args:
        query (str): The search term.
        limit (int): Max results to return.

    Returns:
        List[Dict[str, Any]]: A list of paper dictionaries.
    """
    params = {
        "query": query,
        "limit": limit,
        "fields": "title,abstract,authors,year,url,citationCount",
    }

    encoded_params = urllib.parse.urlencode(params)
    url = f"{SEMANTIC_SCHOLAR_API_URL}?{encoded_params}"

    logger.info("Querying Semantic Scholar: %s", query)

    try:
        # Respect rate limits (simple pause, though basic API is robust)
        time.sleep(1)

        with urllib.request.urlopen(url) as response:
            if response.status != 200:
                logger.error("API returned status: %d", response.status)
                return []

            data = json.loads(response.read().decode())
            papers = data.get("data", [])

            logger.info("Found %d papers.", len(papers))
            return papers

    except urllib.error.URLError as e:
        logger.error("Network error querying Semantic Scholar: %s", e)
        return []
    except json.JSONDecodeError as e:
        logger.error("Failed to parse API response: %s", e)
        return []


def save_results(
    papers: List[Dict[str, Any]], output_file: Optional[str] = None
) -> None:
    """
    Saves the fetched papers to a JSON file or prints them.

    Args:
        papers (List[Dict]): The list of papers.
        output_file (Optional[str]): Path to save JSON.
    """
    if not papers:
        logger.warning("No papers to save.")
        return

    if output_file:
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(papers, f, indent=2)
            logger.info("Results saved to %s", output_file)
        except OSError as e:
            logger.error("Failed to write output file: %s", e)
    else:
        # Print to stdout if no file needed
        print(json.dumps(papers, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch academic papers via Semantic Scholar."
    )
    parser.add_argument("query", help="Search query string.")
    parser.add_argument("--limit", type=int, default=5, help="Number of results.")
    parser.add_argument("--output", help="Path to save results JSON.")

    args = parser.parse_args()

    results = search_semantic_scholar(args.query, args.limit)
    save_results(results, args.output)
