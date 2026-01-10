# pylint: disable=broad-exception-caught
# pylint: disable=import-error
# pylint: disable=no-name-in-module
"""
Confidence Audit Agent Module.
Responsible for reviewing content for accuracy, safety, and brand alignment.
Uses Research Agent as a tool.
"""

import sys
import os
import uuid
import logging
from typing import cast

from dotenv import load_dotenv
from langchain_core.runnables.config import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool
from deepagents import create_deep_agent

from DeepAgents.CommercialAgents.confidence_agent.prompts import CONFIDENCE_INSTRUCTIONS
from DeepAgents.agent_brain import AgentMemory
# Import Research Agent to use as a tool function
try:
    from DeepAgents.CommercialAgents.research_agent.agent import run_research_task
except ImportError:
    # Fallback to absolute import if possible or mock
    # Should work if PYTHONPATH is set
    from DeepAgents.CommercialAgents.research_agent.agent import run_research_task

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@tool
def consult_research_agent(topic: str) -> str:
    """Consults the Research Agent to gather evidence, fact-check claims,
    or retrieve detailed information about a specific topic.
    Use this to verify statements found in the content you are auditing.
    """
    print(f"\n⚖️ Confidence Agent > 📞 Calling Research Agent to verify: {topic}")
    result = run_research_task(topic)
    if result:
        return result
    return "Research Agent found no conclusive evidence."

def create_confidence_agent(model_name="gemini-3-pro-preview"):
    """Creates and returns the Confidence Agent."""

    # Initialize the model
    # Strict Rule: Global location for experimental models
    location = "global" if "exp" in model_name or "preview" in model_name else "us-central1"

    try:
        model = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.0,
            location=location,
            max_retries=1
        )
    except Exception as e:
         logger.error("Failed to initialize Primary Model (%s): %s. Switching to fallback.", model_name, e)
         model = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.1,
            location="us-central1"
        )

    # Create the Deep Agent
    agent = create_deep_agent(
        model=model,
        tools=[consult_research_agent],
        system_prompt=CONFIDENCE_INSTRUCTIONS,
    )

    return agent

def _extract_final_answer(event: dict) -> str:
    """Extracts the final answer from a LangGraph event stream."""
    extracted_report = ""
    for key in event:
        val = event[key]
        msgs = []
        if isinstance(val, dict) and "messages" in val:
            msgs = val["messages"]
            if hasattr(msgs, "value"):
                msgs = msgs.value
        elif hasattr(val, "messages"):
            msgs = getattr(val, "messages")

        if msgs and isinstance(msgs, list):
            msg = msgs[-1]
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    print(f"👉 Tool Call: {tc['name']} ({tc['args']})")
            if hasattr(msg, "content") and msg.content:
                extracted_report = msg.content
    return extracted_report

def run_confidence_audit(content_to_audit: str):
    """Executes a confidence audit with memory and research integration."""
    memory = AgentMemory()

    print("\n⚖️ Confidence Audit Task: Auditing content...")

    # 1. BRAIN CHECK: Have we audited similar content or established rules?
    print("🧠 Checking Memory for Audit Rules/History...")
    context_str = ""
    try:
        past_audits = memory.recall("audit rules for commercial content", limit=2)
        if past_audits:
            print("💡 Found past audit insights!")
            for res in past_audits:
                if hasattr(res, "text"):
                    context_str += f"- {res.text[:300]}...\n"
                    print(f"   Context: {res.text[:100]}...")
    except Exception as e:
        logger.warning("Memory Warning: %s", e)

    # 2. CREATE AGENT
    agent = create_confidence_agent()

    # 3. RUN AGENT
    # We augment the prompt with memory context
    initial_msg = (f"Audit the following content for accuracy, safety, and brand alignment. "
                   f"Content: '{content_to_audit}'")
    if context_str:
        initial_msg += f"\n\nCONSIDER PAST AUDIT INSIGHTS:\n{context_str}"

    config = {"configurable": {"thread_id": f"confidence_{uuid.uuid4()}"}}
    print("🚀 Starting Audit Stream...")

    final_report = ""

    inputs = {"messages": [("user", initial_msg)]}

    try:
        run_config = cast(RunnableConfig, config)
        for event in agent.stream(inputs, config=run_config):
            snippet = _extract_final_answer(event)
            if snippet:
                final_report = snippet
    except Exception as e:
        logger.error("Agent Loop Error: %s", e)
        return None

    # 4. MEMORIZE
    if final_report:
        print("\n🛡️ --- AUDIT REPORT ---")
        print(final_report)
        print("-----------------------")

        # --- ARGUS UPGRADE: Fact-Checking Dashboard ---
        try:
            print("\n📊 Generating Argus Fact Dashboard...")
            dash_llm = ChatGoogleGenerativeAI(
                model="gemini-3-pro-preview", 
                temperature=0,
                project=os.getenv("GOOGLE_CLOUD_PROJECT"),
                location="global"
            )
            dash_prompt = (
                "Convert the following audit report into a high-visibility Markdown Dashboard.\n"
                "Format: A Table with columns [Claim | Verification Status | Confidence | Notes].\n\n"
                f"REPORT:\n{final_report}"
            )
            dashboard = dash_llm.invoke(dash_prompt).content
            print(f"\n{dashboard}\n")
        except Exception as e:
            logger.warning("Dashboard generation failed: %s", e)
        # ----------------------------------------------

        print("\n🧠 Memorizing Audit Decision...")
        memory.memorize(
            f"Audit Report on content '{content_to_audit[:50]}...': {final_report}",
            "ConfidenceAgent",
            tags=["audit_report"]
        )
        print("✅ Audit stored in Long-Term Memory.")
        return final_report

    print("❌ No final report produced.")
    return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        USER_INPUT = sys.argv[1]
        run_confidence_audit(USER_INPUT)
    else:
        print("Please provide content to audit as an argument.")
