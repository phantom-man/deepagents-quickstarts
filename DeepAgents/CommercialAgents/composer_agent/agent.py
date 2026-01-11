"""
Composer Agent Module.
Handles the creation of musical compositions (Audio or Text/ABC).
"""

import os
import re
import random
import time
import uuid
import logging
import glob
from typing import Optional, Dict, Any, List
import requests

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatReplicate
from langchain_anthropic import ChatAnthropic
from langchain.tools import tool

from DeepAgents.agent_factory import create_deep_agent
from DeepAgents.asset_manager import AssetManager

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ComposerAgent")

def _download_and_validate_asset(url: str, session_id: str, prefix: str = "audio", max_mb: int = 20) -> Optional[str]:
    """
    Downloads and validates audio from a URL.
    Returns local filepath if valid, None if failed/invalid.
    Enforces Limits: < max_mb MB.
    Enforces Extension: .mp3 or .wav
    """
    try:
        # If url is already a local file path or file object, handle gracefully
        if not isinstance(url, str):
            return None
        if os.path.exists(url):
            return url

        logger.info(f"⬇️ Downloading & Validating {prefix}: {url}")
        
        # 1. Head Check for Size
        try:
            h = requests.head(url, timeout=10)
            content_length = int(h.headers.get("content-length", 0))
            max_bytes = max_mb * 1024 * 1024 
            
            if content_length > max_bytes:
                logger.warning(f"⚠️ Audio too large ({content_length/1024/1024:.2f}MB). Limit is {max_mb}MB.")
                return None
        except Exception:
            pass # Head might fail on some signed URLs, create session to try GET

        # 2. Download
        r = requests.get(url, timeout=60, stream=True)
        if r.status_code != 200:
            logger.error(f"❌ Download failed: {r.status_code}")
            return None

        # Fix Extension Logic: Prioritize Content-Type, fallback to URL, default to .mp3
        ct = r.headers.get("content-type", "").lower()
        if "wav" in ct:
            ext = "wav"
        elif "mpeg" in ct or "mp3" in ct:
            ext = "mp3"
        else:
            # Fallback to URL extension if valid
            if url.lower().endswith(".wav"):
                ext = "wav"
            elif url.lower().endswith(".mp3"):
                ext = "mp3"
            else:
                # Force .mp3 if unknown, as ffmpeg/libraries usually handle mime sniffing
                # but Replicate NEEDS the extension in the filename.
                ext = "mp3"

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


def check_service_status() -> Dict[str, bool]:
    """
    Checks if critical Replicate models are available.
    Returns: Dict of model_slug -> is_available
    """
    status_map = {
        "minimax/music-01": True,
        "google/lyria-2": True,
        "meta/musicgen": True
    }
    
    if not replicate:
        logger.warning("Replicate SDK not installed. Assuming all DOWN.")
        return {k: False for k in status_map}

    # A simple way to "check" without burning money is checking model existence
    # We can't easily check for "E003" without running, but we can verify version resolution works.
    logger.info("📡 Checking Replicate Service Status...")
    for model in status_map.keys():
        try:
            m = replicate.models.get(model)
            # Accessing latest version usually confirms API connectivity & Existence
            v = m.latest_version 
        except Exception as e:
            logger.warning(f"⚠️ Service {model} seems DOWN or Unreachable: {e}")
            status_map[model] = False
            
    return status_map


@tool
def composer_consult_research(topic: str) -> str:
    """
    Consults the Research Agent to understand musical styles, historical context,
    or specific instruments.
    """
    # Lazy import to avoid circular dependencies
    from DeepAgents.CommercialAgents.research_agent.agent import run_research_task
    
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


def _generate_descriptive_filename(prompt: str, session_id: str, ext: str = "mp3") -> str:
    """Generates a descriptive filename from the prompt."""
    clean_prompt = "".join([c if c.isalnum() else "_" for c in prompt[:30]]).strip("_")
    timestamp = int(time.time())
    return f"{clean_prompt}_{session_id[:6]}_{timestamp}.{ext}"


def _safe_replicate_run(model_id: str, input_data: Dict[str, Any], wait_time: int = 5) -> Any:
    """Runs Replicate prediction with rate limit hygiene."""
    logger.info(f"⏳ Waiting {wait_time}s to avoid Rate Limits...")
    time.sleep(wait_time)
    
    if ":" not in model_id and "/" in model_id:
        try:
            model = replicate.models.get(model_id)
            version = model.latest_version
            model_id = f"{model_id}:{version.id}"
            logger.info(f"   Resolved latest version: {version.id}")
        except Exception as e:
            logger.warning(f"Could not resolve version for {model_id}: {e}")

    return replicate.run(model_id, input=input_data)


def _handle_replicate_generation(  # pylint: disable=too-many-arguments
    model_name: str, input_text: str, llm: Any, assets: Any, session_id: str
) -> str:
    """
    Handle generation via Replicate (Lyria, Minimax, MusicGen, Bark).
    Implements cascading fallback, service checks, and voice library integration.
    """
    if not os.environ.get("REPLICATE_API_TOKEN"):
        return "Error: REPLICATE_API_TOKEN not set."

    # --- 1. Service Availability Check ---
    status_map = check_service_status()
    
    # --- 2. Strategy Selection & Fallback ---
    # Default selection logic
    target_model = model_name
    # if generic, pick based on intent
    if "/" not in target_model:
        lower_input = input_text.lower()
        if "voice" in lower_input or "speech" in lower_input:
            target_model = "suno-ai/bark"
        elif "lyria" in target_model.lower() or "music" in target_model.lower():
            target_model = "google/lyria-2"
        elif "minimax" in target_model.lower():
            target_model = "minimax/music-01"
        else:
            target_model = "google/lyria-2"

    logger.info(f"🎼 Initial Strategy: {target_model}")

    # Apply Service Status Fallbacks
    if "minimax" in target_model and status_map.get("minimax/music-01") is False:
        logger.warning("🚨 Minimax Music-01 is DOWN. Falling back to Lyria-2.")
        target_model = "google/lyria-2"

    if "lyria" in target_model and status_map.get("google/lyria-2") is False:
        logger.warning("🚨 Lyria-2 is DOWN. Falling back to MusicGen.")
        target_model = "meta/musicgen"
    
    logger.info(f"✅ Final Strategy: {target_model}")

    # --- 3. Voice Generation (Bark) - Only if explicitly requested separate from Minimax ---
    if ("bark" in target_model or "suno-ai" in target_model) and "minimax" not in target_model:
        try:
            logger.info(f"🗣️ Generating Voice with {target_model}...")
            output = _safe_replicate_run(
                "suno-ai/bark",
                input_data={"prompt": input_text, "text_temp": 0.7}
            )
            if output:
                # Bark can return dict or AudioOut object
                url = output["audio_out"] if isinstance(output, dict) else str(output)
                fname = _generate_descriptive_filename(f"voice_{input_text}", session_id, "wav")
                local_path = _download_and_validate_asset(url, session_id, prefix="voice")
                if local_path:
                    final_path = os.path.join(os.path.dirname(local_path), fname)
                    os.rename(local_path, final_path)
                    return f"**Voice Generated:**\n- [Play]({url})\n- Local: {final_path}"
        except Exception as e:
            logger.error(f"Voice Gen Failed: {e}")
            return f"Voice Generation Error: {e}"

    # --- 4. Music Generation Pipeline ---
    
    # A. Generate Instrumental Base (if Minimax needs it >15s)
    instrumental_file_path = None
    
    if "minimax" in target_model:
        logger.info("🎹 Step 1: Pre-generating Base Track for Minimax...")
        try:
            # Prefer MusicGen for Minimax Base because of Codec/Format consistency
            base_model = "meta/musicgen"
            base_prompt = f"Instrumental backing track, {input_text}"
            
            logger.info("   Using MusicGen for base track to ensure valid WAV format...")
            mg_out = _safe_replicate_run(
                base_model, 
                input_data={"prompt": base_prompt, "duration": 20}
            )
            
            if mg_out:
                temp_base = _download_and_validate_asset(str(mg_out), session_id, prefix="base_mg")
                if temp_base:
                    instrumental_file_path = temp_base
                    
        except Exception as e:
            logger.error(f"Base Track Gen Failed: {e}")

    # B. Final Generation
    try:
        final_url = None
        current_model_used = target_model
        
        # Case: Minimax
        if "minimax" in target_model:
            if not instrumental_file_path:
                logger.warning("Minimax requires base track >15s. Fallback to MusicGen.")
                target_model = "meta/musicgen" # Switch strategy
            else:
                logger.info("🎤 Step 2: Adding Vocals with Minimax...")
                lyric_data = _generate_lyrics_and_style(input_text, llm)
                lyrics = lyric_data.get("lyrics", input_text)
                
                 # Voice Library Selection
                voice_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "voices")
                available_voices = glob.glob(os.path.join(voice_dir, "*.wav"))
                
                selected_voice = None
                if available_voices:
                    # Basic matching
                    search_text = input_text.lower() + " " + lyrics.lower()
                    
                    # Priority: Match specific keywords
                    filtered = []
                    if "female" in search_text:
                        filtered = [v for v in available_voices if "female" in os.path.basename(v)]
                    elif "male" in search_text:
                        filtered = [v for v in available_voices if "male" in os.path.basename(v)]
                    
                    # Secondary: Style
                    if not filtered:
                        filtered = available_voices # Reset
                        
                    final_candidates = []
                    for v in filtered:
                        fname = os.path.basename(v).lower()
                        if any(style in search_text for style in ["rock", "pop", "jazz", "narrator", "ethereal"]):
                             if any(s in fname for s in ["rock", "pop", "jazz", "narrator", "ethereal"] if s in search_text):
                                 final_candidates.append(v)
                    
                    if not final_candidates:
                        final_candidates = filtered
                    
                    if final_candidates:
                        selected_voice = random.choice(final_candidates)
                        logger.info(f"🎙️ Selected Voice Reference: {os.path.basename(selected_voice)}")

                payload = {
                    "instrumental_file": open(instrumental_file_path, "rb"),
                    "lyrics": lyrics,
                    "model_name": "music_01"
                }
                if selected_voice:
                    payload["refer_voice"] = open(selected_voice, "rb")

                minimax_out = _safe_replicate_run("minimax/music-01", input_data=payload)
                final_url = str(minimax_out)

        # Case: Lyria-2 (Fallback or Primary)
        if "lyria" in target_model and not final_url: # Check not final_url in case above switch logic ran
            logger.info("🎵 Generating with Google Lyria-2...")
            lyria_out = _safe_replicate_run("google/lyria-2", input_data={"prompt": input_text})
            final_url = str(lyria_out)
            current_model_used = "google/lyria-2"

        # Case: MusicGen (Fallback or Explicit)
        if not final_url: 
            logger.info("🎵 Generating with MusicGen...")
            mg_out = _safe_replicate_run(
                "meta/musicgen", 
                input_data={"prompt": input_text, "duration": 20}
            )
            final_url = str(mg_out)
            current_model_used = "meta/musicgen"

        # C. Save & Rename
        if final_url:
            fname = _generate_descriptive_filename(input_text, session_id)
            local_path = _download_and_validate_asset(final_url, session_id, prefix="final")
            
            if local_path:
                final_path = os.path.join(os.path.dirname(local_path), fname)
                os.rename(local_path, final_path)
                logger.info(f"🎉 Final Asset Ready: {final_path}")
                return f"**Audio Generated ({current_model_used}):**\n- [Play Audio]({final_url})\n- Local: {final_path}"
            
        return "Generation failed: No URL returned."

    except Exception as e:
        logger.error(f"Replicate Pipeline Failure: {e}")
        return f"Error: {e}"

@tool
def generate_music_audio(prompt: str, model_name: str = "minimax/music-01") -> str:
    """
    Directly generates audio using a Replicate model (MusicGen or Minimax).
    Args:
        prompt: The description of the music.
        model_name: "minimax/music-01" or "meta/musicgen..."
    """
    logger.info("🎵 Direct Audio Tool called: %s (%s)", prompt, model_name)
    assets = AssetManager()
    
    # Priority Cascade: Lyria-2 -> Minimax -> MusicGen
    # If generic "music" requested, default to Lyria-2 as primary
    if "music-01" in model_name:
         target_model = "minimax/music-01"
    elif "musicgen" in model_name:
         target_model = "meta/musicgen:b05b1dff1d8c6dc63d14b0cdb42135378dcb87f6373b0d3d341ede46e59e2b38"
    target_model = "meta/musicgen:b05b1dff1d8c6dc63d14b0cdb42135378dcb87f6373b0d3d341ede46e59e2b38"

    # We might need an LLM for lyrics if Minimax
    # Using lazy import to avoid circular dependency or heavy init if unused
    llm_for_lyrics = None
    try:
        # Simple default configuration for the lyrics helper: Replicate Llama 3
        llm_for_lyrics = ChatReplicate(
            model="meta/meta-llama-3-70b-instruct", 
            model_kwargs={"temperature": 0.7, "max_length": 2048} 
        )
    except Exception as e:
        logger.warning("Could not init LLM for lyrics, continuing without: %s", e)

    return _handle_replicate_generation(
        model_name=target_model,
        input_text=prompt,
        llm=llm_for_lyrics,
        assets=assets,
        session_id="tool_direct"
    )


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
        # USER REQUEST: "Switch defaults to Replicate Llama 3 for testing"
        target_model = "meta/meta-llama-3-8b-instruct"

        logger.info(f"🎻 Orpheus > Initializing Brain with {target_model}...")
        
        try:
             # Requires REPLICATE_API_TOKEN in env
            from langchain_community.chat_models import ChatReplicate
            llm = ChatReplicate(
                model=target_model,
                model_kwargs={"temperature": 0.5, "max_length": 2048, "top_p": 1}
            )
        except Exception as e:
            logger.warning(f"Replicate Init Failed: {e}. Falling back to Google.")
            # Fallback Logic
            target_model = "gemini-1.5-flash"
            llm = ChatGoogleGenerativeAI(
                model=target_model,
                temperature=0.5,
                project=os.getenv("GOOGLE_CLOUD_PROJECT"),
                location="us-central1" # Flash is reliable here
            )

        if not llm:
             raise ValueError("No LLM could be initialized")

    except Exception as e:
        logger.error(f"Brain Init Failed: {e}")
        # Final Dummy Fallback
        return lambda *args, **kwargs: f"Error: Agent Brain Died. {e}"

    # 3. Initialize Agent
    agent = create_deep_agent(
        model=llm,
        tools=[compose_tool, browse_library_tool], 
        system_prompt=COMPOSER_INSTRUCTIONS,
    )

    return agent

