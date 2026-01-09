"""
Composer Agent Module.
Handles the creation of musical compositions (Audio or Text/ABC).
"""

import os
import re
import random
import time
import shutil
import uuid
import mimetypes
from typing import Optional, Dict, Any, List
import requests

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_google_vertexai import ChatVertexAI
from langchain_anthropic import ChatAnthropic
from langchain.tools import tool

from DeepAgents.agent_factory import create_deep_agent
from DeepAgents.agent_brain import AgentMemory
from DeepAgents.editor_tools import AssetManager

# Setup Logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ComposerAgent")

def _download_and_validate_asset(url: str, session_id: str, prefix: str = "audio", max_mb: int = 20) -> Optional[str]:
    """
    Downloads and validates audio from a URL.
    Returns local filepath if valid, None if failed/invalid.
    Enforces Limits: < max_mb MB.
    """
    try:
        logger.info(f"⬇️ Downloading & Validating {prefix}: {url}")
        
        # 1. Head Check for Size
        try:
            h = requests.head(url, timeout=10)
            content_length = int(h.headers.get("content-length", 0))
            max_bytes = max_mb * 1024 * 1024 
            
            if content_length > max_bytes:
                 logger.warning(f"⚠️ Audio too large ({content_length/1024/1024:.2f}MB). Limit is {max_mb}MB.")
                 # Proceed with caution if we can stream/truncate, but mostly fail.
                 return None
        except Exception:
            pass # Head might fail on some signed URLs, create session to try GET
        
        # 2. Download
        r = requests.get(url, timeout=60, stream=True)
        if r.status_code != 200:
            logger.error(f"❌ Download failed: {r.status_code}")
            return None
            
        ext = "mp3"
        ct = r.headers.get("content-type", "").lower()
        if "wav" in ct: ext = "wav"
        
        tmp_name = f"temp_{prefix}_{session_id}_{uuid.uuid4().hex[:6]}.{ext}"
        
        downloaded_size = 0
        with open(tmp_name, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                downloaded_size += len(chunk)
                if downloaded_size > max_bytes:
                     logger.warning("⚠️ File exceeded max size during download.")
                     return None
                f.write(chunk)
                
        if downloaded_size < 100:
             logger.warning("⚠️ File too small to be audio.")
             return None
             
        logger.info(f"✅ Audio Validated & Saved: {tmp_name} ({downloaded_size} bytes)")
        return tmp_name
        
    except Exception as e:
        logger.error(f"Validation Failed: {e}")
        return None

# Local imports
from DeepAgents.CommercialAgents.research_agent.agent import run_research_task
from DeepAgents.agent_brain import logger
from DeepAgents.asset_manager import AssetManager

# Import new history tools
try:
    from DeepAgents.CommercialAgents.composer_agent.history_tools import (
        narrative_reconstruction,
        counterfactual_simulation,
    )
except ImportError:
    narrative_reconstruction = None
    counterfactual_simulation = None

# Optional Replicate import
try:
    import replicate
except ImportError:
    replicate = None


@tool
def composer_consult_research(topic: str) -> str:
    """
    Consults the Research Agent to understand musical styles, historical context,
    or specific instruments.
    """
    logger.info("🎻 Composer > 📞 Calling Research Agent about: %s", topic)
    extra_config = {
        "tags": ["sub-agent-call", "agent:researcher", "source:composer"],
        "metadata": {"parent_agent": "Composer", "trigger": "tool_call"},
    }
    result = run_research_task(topic, extra_config=extra_config)
    if result:
        return result
    return "Research Agent could not find significant information."


def _generate_lyrics_and_style(input_text: str, llm: Any) -> Dict[str, str]:
    """Helper to generate lyrics and style using the LLM."""
    if not llm:
        return {"prompt": input_text}

    lyric_prompt = (
        f'You are an expert Songwriter. The user wants a song about: "{input_text}".\n\n'
        "Please generate:\n"
        "1. A concise musical style description (Genre, instruments, mood).\n"
        "2. Complete lyrics for a song (up to 2 verses and a chorus).\n\n"
        "Output format:\n"
        "STYLE: <style description>\n"
        "LYRICS:\n"
        "<lyrics text>\n"
    )

    try:
        response = llm.invoke([HumanMessage(content=lyric_prompt)])
        content = response.content
        result = {}

        style_match = re.search(r"STYLE:\s*(.*)", content, re.IGNORECASE)
        if style_match:
            result["prompt"] = style_match.group(1).strip()
        else:
            result["prompt"] = input_text

        lyrics_match = re.search(r"LYRICS:\s*(.*)", content, re.IGNORECASE | re.DOTALL)
        if lyrics_match:
            result["lyrics"] = lyrics_match.group(1).strip()

        logger.info("Generated Style: %s", result.get("prompt"))
        return result

    except Exception as llm_err:  # pylint: disable=broad-exception-caught
        logger.error("Lyric generation failed: %s. Using raw input.", llm_err)
        return {"prompt": input_text}


def _handle_replicate_generation(  # pylint: disable=too-many-arguments
    model_name: str, input_text: str, llm: Any, assets: Any, session_id: str
) -> str:
    """Handle generation via Replicate (MusicGen or Minimax)."""
    if not os.environ.get("REPLICATE_API_TOKEN"):
        return (
            "Error: REPLICATE_API_TOKEN not set. "
            "Please get a token from https://replicate.com/account/api-tokens"
        )

    # --- PIPELINE START ---

    # 0. Voice Library Selection (for Minimax)
    voice_path = None
    voice_url = None
    if "minimax" in model_name:
        try:
            voice_dir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../../../data/voices")
            )
            if os.path.exists(voice_dir):
                voices = [f for f in os.listdir(voice_dir) if f.endswith(".mp3")]
                if voices:
                    selected_voice = random.choice(voices)
                    voice_path = os.path.join(voice_dir, selected_voice)
                    logger.info("🎤 Selected Voice Reference: %s", selected_voice)

                    # 1. Upload Voice to Replicate (or temporary host if needed)
                    # For simplicity, we create a file handle which replicate client often uploads automatically
                    # if passed as open file object.
                    # pylint: disable=consider-using-with
                    voice_url = open(voice_path, "rb")
                else:
                    logger.warning(
                        "No voices found in data/voices. Please run setup_audio_assets.py"
                    )
        except Exception as e:
            logger.error("Voice selection failed: %s", e)

    # 1. Instrumental Generation (The 'Song File' Reference)
    # If using Minimax, we first generate an instrumental using MusicGen/Lyria
    instrumental_url = None
    if "minimax" in model_name:
        logger.info(
            "🎹 Step 1: Generating Instrumental Reference (MusicGen/Lyria Proxy)..."
        )
        try:
            # Use MusicGen as the robust fallback for 'Lyria' style instrumental
            inst_model = "meta/musicgen:b05b1dff1d8c6dc63d14b0cdb42135378dcb87f6373b0d3d341ede46e59e2b38"

            # Simple instrumental prompt derived from input
            inst_prompt = f"Instrumental backing track, {input_text}"

            inst_output = None
            if replicate:
                inst_output = replicate.run(
                    inst_model, input={"prompt": inst_prompt, "duration": 15}
                )

            if inst_output:
                # Ensure we convert the FileOutput object to a clear string URL
                instrumental_url = str(inst_output)
                logger.info(f"✅ Instrumental Generated: {instrumental_url}")
            else:
                logger.error("Instrumental generation returned None.")
        except Exception as e:
            logger.error(f"Instrumental Step Failed: {e}")
            # If instrumental fails, we might fall back to MusicGen for the whole thing later

    try:
        # Determine model
        current_model = (
            model_name
            if "/" in model_name
            else (
                "meta/musicgen:b05b1dff1d8c6dc63d14b0cdb42135378dcb87f6373b0d3d341ede46e59e2b38"
            )
        )
        input_args = {}
        final_prompt = input_text

        # Minimax Logic (Step 2)
        is_minimax = any(
            x in current_model.lower() for x in ["minimax", "music-01", "music-1.5"]
        )

        if is_minimax:
            logger.info(
                "Minimax model detected (%s). Engaging Lyricist Sub-routine.",
                current_model,
            )
            lyric_data = _generate_lyrics_and_style(input_text, llm)
            input_args.update(lyric_data)  # Contains 'lyrics'
            final_prompt = lyric_data.get("prompt", input_text)

            # Add References - CORRECTED for Minimax Music-01 via Schema Inspection
            # Schema:
            # - voice_file: Voice reference (mp3/wav)
            # - instrumental_file: Instrumental reference (mp3/wav)
            # - song_file: Reference song (music + vocals)

            if voice_url:
                input_args["voice_file"] = voice_url
                logger.info("🎤 Using Voice Asset as 'voice_file' reference.")

            if instrumental_url:
                # Minimax might fail with URL references for instrumental if format isn't autodetected.
                # Safe bet: Download it to temp file and upload as file handle.
                # Use robust validation helper
                local_instr = _download_and_validate_asset(instrumental_url, session_id, prefix="instr")
                
                if local_instr:
                     input_args["instrumental_file"] = open(local_instr, "rb")
                     logger.info("🎹 Instrumental Attached as File Handle.")
                else:
                     logger.warning("Could not validate instrumental. Skipping instrumental_file.")

            # Remove any old attempts at 'song_file' or 'audio_sample'
            input_args.pop("song_file", None)
            input_args.pop("audio_sample", None)

        else:
            # MusicGen defaults
            if "musicgen" not in current_model.lower() and "/" not in current_model:
                # Fallback to MusicGen default ID if generic name provided
                current_model = "meta/musicgen:b05b1dff1d8c6dc63d14b0cdb42135378dcb87f6373b0d3d341ede46e59e2b38"
            input_args["prompt"] = input_text
            input_args["model_version"] = "stereo-large"
            input_args["duration"] = 30

        logger.info(
            "Calling Replicate Model: %s with args: %s",
            current_model,
            list(input_args.keys()),
        )

        if not replicate:
            return "Error: Replicate module not installed."

        output = None
        max_retries = 5  # retries
        base_wait_time = 60  # Minimum 60 seconds as requested

        for attempt in range(max_retries):
            try:
                logger.info(
                    f"🚀 Attempt {attempt+1}/{max_retries} - Generating with {current_model}..."
                )

                # Run Replicate (blocking call)
                output = replicate.run(current_model, input=input_args)

                if output:
                    logger.info("✅ Generation Success!")
                    break

                raise ValueError("Output was None")

            except Exception as e:
                err_str = str(e).lower()
                is_rate_limit = (
                    "429" in err_str
                    or "rate limit" in err_str
                    or "quota" in err_str
                    or "throttled" in err_str
                )

                if is_rate_limit:
                    wait_time = base_wait_time * (attempt + 1)
                    logger.warning(
                        f"⚠️ RATE LIMIT DETECTED (429). Throttling for {wait_time} seconds..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ Generation Error on attempt {attempt+1}: {e}")

                    # Logic for Minimax "No Vocal" error (E006)
                    if "e006" in err_str or "vocal" in err_str:
                        logger.warning(
                            "⚠️ Minimax Input Error detected. Switching to MusicGen Fallback immediately."
                        )
                        try:
                            current_model = "meta/musicgen:b05b1dff1d8c6dc63d14b0cdb42135378dcb87f6373b0d3d341ede46e59e2b38"
                            input_args = {"prompt": final_prompt, "duration": 30}
                            is_minimax = False
                            # Immediate retry with new model in the NEXT loop iteration
                            time.sleep(2)
                            continue
                        except Exception:
                            logger.warning("Fallback setup failed.")

                    if attempt == max_retries - 1:
                        # Last attempt failed.
                        logger.error("All attempts exhausted.")
                        # Loop ends naturally

                    time.sleep(5)

        if not output:
            return f"Error: Failed to generate audio after {max_retries} attempts."

        # Handle Output Formatting
        # Replicate often returns a FileOutput object or iterator.
        # We MUST convert to string URL immediately to avoid serialization issues later.
        final_url = str(output)

        # Minimax/Music-01 sometimes returns a list or dict
        if isinstance(output, (list, tuple)):
            final_url = str(output[0])
        elif hasattr(output, "url"):
            final_url = output.url  # type: ignore

        logger.info(f"✅ Final Asset URL: {final_url}")

        # Save to local file via AssetManager
        local_path = assets.save_asset(
            data=final_url,
            asset_type="audio",
            session_id=session_id,
            prompt=input_text or "generated_audio",
        )

        return (
            f"**Audio Generated:**\n- [Play Audio]({final_url})\n- Local: {local_path}"
        )

    except Exception as e:
        logger.exception("Critical error in Replicate handler")
        return f"System Error during generation: {str(e)}"


@tool
def compose_tool(request: str) -> str:
    """
    Multimodal Composer Tool [ORPHEUS].
    Capabilities:
    1. Compose Music/Lyrics: "Create a sad song about robots."
    2. Historical Narrative Analysis: "Analyze the fall of Rome for tragic themes."

    Use this tool for ANY task involving Music, Sound, Lyrics, OR Deep Historical/Narrative Analysis.
    """
    try:
        # Check if Replicate package is installed
        try:
            # pylint: disable=import-outside-toplevel, unused-import
            import replicate as _replicate_pkg  # noqa: F401

            has_replicate_pkg = True
        except ImportError:
            has_replicate_pkg = False

        # Default configuration
        # Only use Replicate if Token exists AND package is installed
        use_replicate = os.environ.get("REPLICATE_API_TOKEN") and has_replicate_pkg

        config = {"provider": "Replicate" if use_replicate else "Google"}
        agent_runner = create_composer_agent(
            model_config=config, session_id="tool_call"
        )

        if not agent_runner:
            return "Error: Could not initialize Composer Agent."

        return agent_runner(request)
    except Exception as e:
        return f"Composer Tool Error: {e}"


def create_composer_agent(
    model_config: Optional[Dict[str, Any]] = None,
    brain: Any = None,
    session_id: str = "default",
):
    """
    Factory to create the Composer Agent runner.
    """
    if model_config is None:
        # Default to the "Cheap" model (Minimax) as requested
        model_config = {"provider": "Replicate", "model": "minimax/music-01"}

    provider = model_config.get("provider", "Google")
    model_name = model_config.get("model", "minimax/music-01")

    assets = AssetManager()

    # Force Load Env if Token Missing
    if not os.environ.get("REPLICATE_API_TOKEN"):
        load_dotenv()
        # Fallback hardcoded if needed (DO NOT COMMIT) - But we rely on .env

    # Check for Replicate Token early
    if (
        "replicate" in provider.lower()
        or "minimax" in model_name.lower()
        or "musicgen" in model_name.lower()
    ):
        if not os.environ.get("REPLICATE_API_TOKEN"):
            logger.warning(
                "Replicate provider selected but REPLICATE_API_TOKEN is missing."
            )

    # Initialize LLM with Fallback
    llm = None
    try:
        # USER REQUEST: "Gemini 3 Pro Preview"
        # Using the preview model as requested and verified available.
        target_model = "gemini-3-pro-preview"

        logger.info(f"🎻 Orpheus > Initializing Brain with {target_model}...")

        try:
            # Initialize: Set max_retries=0 to avoid annoying "Failover over and over" logs if model is 404
            test_llm = ChatVertexAI(
                model=target_model,
                temperature=0.7,
                max_retries=0,
                location="global", # Updated to global for Preview models
            )
            test_llm.invoke("Ping")  # Force API call
            llm = test_llm
            logger.info(f"✅ {target_model} is ONLINE.")

        except Exception:
            # logger.warning(f"⚠️ {target_model} Unavailable: {e}")
            # Simplify log to avoid panic
            logger.info(
                f"ℹ️ {target_model} not reachable (Access/Region). Switching to fallback."
            )

            # Fallback
            fallback = "gemini-1.5-pro-001"
            try:
                test_llm = ChatVertexAI(model=fallback, temperature=0.7, max_retries=0)
                test_llm.invoke("Ping")
                llm = test_llm
                logger.info(f"Using Fallback: {fallback}")
            except Exception:
                logger.info("Using Fallback: gemini-2.0-flash-001")
                llm = ChatVertexAI(model="gemini-2.0-flash-001", temperature=0.7)

        if provider == "Anthropic":
            llm = ChatAnthropic(
                model_name=model_name, temperature=0.7, timeout=None, stop=None
            )

    except Exception as e:
        logger.error("Composer LLM Init Failed: %s", e)
        # Continue with llm=None (Passive Mode)

        logger.error("Composer LLM Init Failed: %s", e)
        if provider != "Replicate":
            return None

    # Load Ontology
    try:
        ontology_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../../Canon/Composer_Ontology.md",
        )
        if os.path.exists(ontology_path):
            with open(ontology_path, "r", encoding="utf-8") as f:
                ontology = f.read()
        else:
            ontology = "You are a Composer Agent. Create music."
    except Exception:  # pylint: disable=broad-exception-caught
        ontology = "You are a Composer Agent."

    def run_agent(
        input_text: str, chat_history: Any = None
    ) -> str:  # pylint: disable=unused-argument
        logger.info("🎻 Composer receiving input: %s...", input_text[:50])

        # --- PATH A: REPLICATE (AUDIO) ---
        if provider == "Replicate":
            return _handle_replicate_generation(
                model_name=model_name,
                input_text=input_text,
                llm=llm,
                assets=assets,
                session_id=session_id,
            )

        # --- PATH B: LLM (TEXT/ABC) ---
        context_str = ""
        if brain:
            memories = brain.recall(input_text, limit=2)
            if memories:
                context_str += "\n\n🧠 **Musical Memory Recall**:\n"
                for m in memories:
                    context_str += f"- Past Composition: {m['text'][:200]}...\n"

        final_system_prompt = (
            f"{ontology}\n\n{context_str}\n\n"
            "If you need to research a musical style, use the 'composer_consult_research' tool."
        )

        if not llm:
            return "Error: LLM not initialized for Composer."

        # Define tools, including new history tools if available
        tools = [composer_consult_research]
        if narrative_reconstruction:
            tools.append(narrative_reconstruction)
        if counterfactual_simulation:
            tools.append(counterfactual_simulation)

        agent = create_deep_agent(
            model=llm, tools=tools, system_prompt=final_system_prompt
        )

        final_output = ""
        config = {"configurable": {"thread_id": f"composer_{session_id}"}}

        try:
            for event in agent.stream(
                {"messages": [("user", input_text)]}, config=config  # type: ignore
            ):
                for val in event.values():
                    msgs = []
                    if isinstance(val, dict) and "messages" in val:
                        msgs = val["messages"]
                        if hasattr(msgs, "value"):
                            msgs = msgs.value
                    elif hasattr(val, "messages"):
                        msgs = getattr(val, "messages", [])

                    if msgs:
                        last_msg = msgs[-1]
                        if hasattr(last_msg, "content") and last_msg.content:
                            final_output = last_msg.content

            # Memory Storage
            if brain and len(final_output) > 50:
                brain.memorize(
                    f"Composition Request: {input_text}\nResult: {final_output[:200]}...",
                    agent_role="Composer",
                    tags=["music", "composition"],
                )

            return final_output

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Composer Generation Error: %s", e)
            return f"Error composing score: {e}"

    return run_agent
