"""Prompts for the Composer Agent [ORPHEUS]."""
import os
import logging
from langsmith import Client

logger = logging.getLogger(__name__)

DEFAULT_COMPOSER_INSTRUCTIONS = """You are the **Composer Agent** [ORPHEUS].
Your role is to create a musical composition plan and generate audio assets.

**YOUR OBJECTIVE:**
1. Analyze the Director's treatment for emotional tone, pacing, and theme.
2. Write lyrics that fit the requested style (e.g., Hero's Journey, LOTR).
3. Generate a concrete prompt for a Music Generation Model.
4. Output the audio asset.

**RULES:**
- Lyrics must be rhyming and rhythmic.
- The prompt must include genre, instruments, and mood.
- You are responsible for the *entire* auditory experience.
"""

def _get_instructions():
    # Attempt to pull from LangChain Hub
    if os.getenv("LANGCHAIN_API_KEY"):
        try:
            client = Client()
            prompt_obj = client.pull_prompt("composer-system-main")
            # Access the template string directly to avoid validation errors
            return prompt_obj.messages[0].prompt.template
        except Exception as e: # pylint: disable=broad-exception-caught
            logger.warning("Failed to pull Composer prompt from Hub: %s. using local fallback.", e)
    
    return DEFAULT_COMPOSER_INSTRUCTIONS

COMPOSER_INSTRUCTIONS = _get_instructions()
