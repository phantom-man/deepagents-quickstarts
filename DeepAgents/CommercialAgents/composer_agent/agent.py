import os
import replicate
from typing import List
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage
from langchain_google_vertexai import ChatVertexAI
from langchain_anthropic import ChatAnthropic

from DeepAgents.agent_brain import logger
from DeepAgents.asset_manager import AssetManager

def create_composer_agent(model_config=None, brain=None, session_id="default"):
    """
    Factory to create the Composer Agent runner.
    """
    if model_config is None:
        model_config = {"provider": "Replicate", "model": "meta/musicgen"}

    provider = model_config.get("provider", "Google")
    model_name = model_config.get("model", "gemini-1.5-pro")
    
    # Asset Manager
    assets = AssetManager()
    
    # Check for Replicate Token early
    if provider == "Replicate":
         if not os.environ.get("REPLICATE_API_TOKEN"):
             logger.warning("Replicate provider selected but REPLICATE_API_TOKEN is missing.")
             # Fallback to Google if token missing to avoid crash, or handle inside runner
             # We will allow it to proceed so the runner captures the specific error for the UI

    # 1. Initialize LLM (Used for Text Composition OR Prompt Engineering for MusicGen)
    llm = None
    if provider != "Replicate":
        try:
            if provider == "Google":
                llm = ChatVertexAI(model_name=model_name, temperature=0.7)
            elif provider == "Anthropic":
                llm = ChatAnthropic(
                    model_name=model_name, 
                    temperature=0.7,
                    timeout=None,
                    stop=None
                )
        except Exception as e:
            logger.error(f"Composer LLM Init Failed: {e}")
            return None

    # load ontology
    try:
        ontology_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../../Canon/Composer_Agent_Ontology.md"
        )
        if os.path.exists(ontology_path):
            with open(ontology_path, "r", encoding="utf-8") as f:
                ontology = f.read()
        else:
            ontology = "You are a Composer Agent. Create music."
    except Exception as e:
        ontology = "You are a Composer Agent."

    # 2. Define the Runner Function
    def run_agent(input_text, chat_history=None):
        logger.info(f"🎻 Composer receiving input: {input_text[:50]}...")
        
        # --- PATH A: REPLICATE (AUDIO) ---
        if provider == "Replicate":
             if not os.environ.get("REPLICATE_API_TOKEN"):
                 return "Error: REPLICATE_API_TOKEN environment variable not set. Please get a token from https://replicate.com/account/api-tokens"

             try:
                 # Default to MusicGen Large if model name isn't specific
                 # meta/musicgen:b05b1dff1d8c6dc63d14b0cdb42135378dcb87f6373b0d3d341ede46e59e2b38 (Large 3.3B)
                 model_id = "meta/musicgen:b05b1dff1d8c6dc63d14b0cdb42135378dcb87f6373b0d3d341ede46e59e2b38"
                 
                 output = replicate.run(
                    model_id,
                    input={
                        "prompt": input_text,
                        "model_version": "stereo-large",
                        "duration": 30
                    }
                 )
                 # Replicate MusicGen returns a URI string or bytes? Usually a URL.
                 if output:
                     # Save Asset
                     saved_path = assets.save_asset(
                         data=output,
                         asset_type="audio",
                         session_id=session_id,
                         prompt=input_text,
                         metadata={"provider": "Replicate", "model": model_id}
                     )
                     
                     if saved_path:
                         return f"**Audio Generated:**\n\n- [Play Audio]({output}) (Source)\n- Local: `{saved_path}`\n\n*(MusicGen via Replicate)*"
                     else:
                         return f"**Audio Generated:**\n\n{output}\n\n*(MusicGen via Replicate)*"
                 else:
                     return "Error: No output from Replicate."
             except Exception as e:
                 logger.error(f"Replicate Generation Error: {e}")
                 return f"Error generating audio: {e}"

        # --- PATH B: LLM (TEXT/ABC) ---
        
        # A. Memory Recall (Learning)
        context_str = ""
        if brain:
            # Search for similar scenes/music in memory
            memories = brain.recall(input_text, limit=2)
            if memories:
                context_str += "\n\n🧠 **Musical Memory Recall**:\n"
                for m in memories:
                    context_str += f"- Past Composition: {m['text'][:200]}...\n"

        # B. Construct Prompt
        messages: List[BaseMessage] = [
            SystemMessage(content=f"{ontology}\n\n{context_str}"),
        ]
        
        if chat_history:
            messages.extend(chat_history)
            
        messages.append(HumanMessage(content=input_text))

        # C. Generate
        try:
            if not llm:
                return "Error: LLM not initialized."
            response = llm.invoke(messages)
            result_text = response.content
            
            # D. Memory Storage (Learning)
            if brain and len(result_text) > 50:
                # Store the composition setup for future reference
                brain.memorize(
                    f"Composition Request: {input_text}\nResult: {result_text[:200]}", 
                    agent_role="Composer",
                    tags=["music", "composition"]
                )
                
            return result_text
            
        except Exception as e:
            logger.error(f"Composer Generation Error: {e}")
            return f"Error composing score: {e}"

    return run_agent
