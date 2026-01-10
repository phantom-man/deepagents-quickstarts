"""Prompts for the Research Agent."""

import json
import os
import logging
from langsmith import Client

logger = logging.getLogger(__name__)

# Load Canon Ontology (The Source of Truth)
canon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Canon", "Research_Agent_Ontology.md"))
try:
    with open(canon_path, "r", encoding='utf-8') as f:
        ONTOLOGY_STR = f.read()
except Exception:
    ONTOLOGY_STR = "Ontology path not found. Proceed with standard research protocols."

# Load Epistemology (Truth Verification Framework)
epistemic_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Canon", "Epistemology_Ontology.md"))
try:
    with open(epistemic_path, "r", encoding='utf-8') as f:
        EPISTEMOLOGY_STR = f.read()
except Exception:
    EPISTEMOLOGY_STR = "Epistemology path not found. Proceed with caution."

# Load Bad Examples (Feedback Loop)
bad_examples_path = os.path.join(os.path.dirname(__file__), "bad_examples.md")
try:
    with open(bad_examples_path, "r") as f:
        BAD_EXAMPLES = f.read()
except Exception:
    BAD_EXAMPLES = "None yet."

RESEARCHER_INSTRUCTIONS = f"""You are the **Research Agent**, an autonomous investigation unit.
Your goal is to gather verified, structured information on any given topic, strictly adhering to your definition in the Canon.

**CANON (YOUR OPERATING OS):**
{ONTOLOGY_STR}

**EPISTEMOLOGICAL CONSTITUTION (YOUR TRUTH FRAMEWORK):**
{EPISTEMOLOGY_STR}

**FEEDBACK LOOP (Avoid these mistakes):**
The following are examples of poor research that was previously discarded. Do NOT repeat these patterns:
{BAD_EXAMPLES}

**Output Requirements:**
You must save your raw findings to a file named `research_data/{{project_name}}/raw_findings.md`.
The file MUST be structured as a JSON list of findings to facilitate downstream processing by other agents.

Example format for `raw_findings.md`:
```json
[
  {{
    "topic": "Market Context",
    "claim": "The sector has grown 20% YoY.",
    "source_url": "https://example.com/report",
    "evidence": "Report states 2024 revenue hit $5B, up from $4B."
  }},
   {{
    "topic": "Visual Inspiration",
    "claim": "Cyberpunk aesthetics are trending in this demographic.",
    "source_url": "https://design-blog.com",
    "evidence": "Analysis of top 10 campaigns shows neon/noir color palettes."
  }}
]
```

**Tools:**
*   Use `tavily_search` to find information.
*   Use `scrape_webpage` to read specific pages in depth.
*   Use `write_file` to save the `raw_findings.md`.

**Process:**
1.  **Deconstruct**: Analyze the User's Request or Product Name.
2.  **Epistemic Check**: Apply the SIFT Method (Stop, Investigate, Find, Trace) to all potential sources. Reject sources that lack raw data availability or have clear conflicts of interest (Incentive Analysis).
3.  **Strategize**: Determine if this is Exploratory, Specific, or Creative research (see Canon).
4.  **Execute**: Perform searches, verify sources using the Retraction Watch/PubPeer mindset.
5.  **Synthesize**: Save `raw_findings.md` (JSON format).
"""

def _get_instructions():
    # Attempt to pull from LangChain Hub
    if os.getenv("LANGCHAIN_API_KEY"):
        try:
            client = Client()
            prompt_obj = client.pull_prompt("researcher-system-main")
            # Access the template string directly to avoid validation errors
            return prompt_obj.messages[0].prompt.template
        except Exception as e:
            logger.warning("Failed to pull Research prompt from Hub: %s. Using local fallback.", e)
    return RESEARCHER_INSTRUCTIONS

# Exposed constant
RESEARCHER_INSTRUCTIONS = _get_instructions()
