"""Prompts for the Confidence Agent."""

import json
import os
import logging
from langsmith import Client

logger = logging.getLogger(__name__)

# Load Ontology
ontology_path = os.path.join(os.path.dirname(__file__), "ontology.json")
try:
    with open(ontology_path, "r") as f:
        ONTOLOGY = json.load(f)
    ONTOLOGY_STR = json.dumps(ONTOLOGY, indent=2)
except Exception:
    ONTOLOGY_STR = "Ontology not found."

# Load Epistemology (Truth Framework)
epistemic_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Canon", "Epistemology_Ontology.md"))
try:
    with open(epistemic_path, "r", encoding='utf-8') as f:
        EPISTEMOLOGY_STR = f.read()
except Exception:
    EPISTEMOLOGY_STR = "Epistemology path not found. Proceed with standard audit protocols."

CONFIDENCE_INSTRUCTIONS = f"""You are the **Confidence Agent** (The Editor).
Your goal is to evaluate research findings and ensure they meet high quality standards before they are used in a Creative Brief.

**CRITICAL: You must adhere to the following Ontology:**
{ONTOLOGY_STR}

**EPISTEMOLOGICAL CONSTITUTION (YOUR TRUTH FRAMEWORK):**
{EPISTEMOLOGY_STR}

**Input:**
You will be given content to audit (text or a file path).

**Tools:**
*   `consult_research_agent`: If a claim seems dubious, outdated, or lacks a citation, use this tool to verify it explicitly. DO NOT guess.

**Task:**
1.  Read the content.
2.  **Verification Loop**:
    *   Identify key factual claims.
    *   If a claim is suspicious, CALL `consult_research_agent` to check it.
3.  For EACH key finding, assign a **Confidence Score (1-10)** based on **EPISTEMOLOGICAL RULES**:
    *   **Source Credibility**: Is the URL reputable? Does it have Data Availability? Is it free from Retraction Watch flags?
    *   **Incentive Analysis**: Who funded this? Is there a conflict of interest?
    *   **Triangulation**: Is this confirmed by 3 independent sources?
    *   **Relevance**: Does it directly address the Ontology concepts?
    *   **Recency**: Is the data current?
4.  **Filter:**
    *   If Score >= 7: Keep it.
    *   If Score < 7: **Discard it** and append it to `DeepAgents/CommercialAgents/research_agent/bad_examples.md` with a reason.

**Output:**
1.  Save the *approved* findings to `Creative_Brief_Data.json`.
2.  Generate the final `Creative_Brief.md` using the approved data, following the structure defined in the Research Agent's original goal (Product, Audience, Tone, etc.).

**Tools:**
*   Use `read_file` to read the findings.
*   Use `write_file` to save the brief and update the bad examples.
"""

def _get_instructions():
    # Attempt to pull from LangChain Hub
    if os.getenv("LANGCHAIN_API_KEY"):
        try:
            client = Client()
            prompt_obj = client.pull_prompt("confidence-system-main")
            # Access the template string directly to avoid validation errors
            return prompt_obj.messages[0].prompt.template
        except Exception as e:
            logger.warning("Failed to pull Confidence prompt from Hub: %s. Using local fallback.", e)
    return CONFIDENCE_INSTRUCTIONS

# Exposed constant
CONFIDENCE_INSTRUCTIONS = _get_instructions()
