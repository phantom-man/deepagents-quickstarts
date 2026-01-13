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
from langchain_core.messages import HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from DeepAgents.replicate_adapter import ChatReplicate
from langchain_anthropic import ChatAnthropic
from langchain.tools import tool

from DeepAgents.agent_factory import create_deep_agent
from DeepAgents.asset_manager import AssetManager
from DeepAgents.hub_manager import get_or_push_prompt

try:
    from DeepAgents.CommercialAgents.composer_agent.prompts import COMPOSER_INSTRUCTIONS
except ImportError:
    # Basic fallback if file missing
    COMPOSER_INSTRUCTIONS = "You are an expert Music Composer AI."

# Setup Logging
logging.basicConfig(level=logging.INFO)
# Suppress noisy OpenTelemetry attribute warnings
logging.getLogger("opentelemetry.attributes").setLevel(logging.ERROR)
logger = logging.getLogger("ComposerAgent")

def _download_and_validate_asset(url: str, session_id: str, prefix: str = "audio", max_mb: int = 20, force_extension: Optional[str] = None) -> Optional[str]:
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
        if force_extension:
            ext = force_extension.strip(".").lower()
        else:
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
    """
    Helper to generate lyrics and style using the LLM.
    Implements a Reflexion Loop to strictly enforce Minimax API constraints (Lyrics < 600 chars).
    """
    if not llm:
        return {"prompt": input_text}

    # RE-ENGINEERED PROMPT: Dynamic Schema Enshrinement for Minimax Music-1.5
    # Strict Sectional Budgets based on User's verified 576-char example.
    schema_compliant_prompt = (
        f'You are an expert Songwriter specialized in the Minimax Music-1.5 Schema.\n'
        f'The user wants a song about: "{input_text}".\n\n'
        "CRITICAL ARCHITECTURAL CONSTRAINTS (API WILL CRASH IF VIOLATED):\n"
        "1. TOTAL LENGTH: Must be UNDER 600 characters. (Ideal: ~550 chars).\n"
        "2. STRUCTURE: You must use EXACTLY these headers: [Verse], [Chorus], [Bridge], [Outro].\n"
        "3. SECTION BUDGETS (Strict Character Limits):\n"
        "   - [Verse]:  Max 140 chars (approx 4 lines)\n"
        "   - [Chorus]: Max 140 chars (approx 4 lines)\n"
        "   - [Bridge]: Max 140 chars (approx 4 lines)\n"
        "   - [Outro]:  Max 80 chars (approx 2 lines)\n"
        "4. DO NOT TRUNCATE by just cutting off text. You must RE-VISION the song to fit these limits natively.\n"
        "   If the story is long, condense it poetically. Do not write a novel.\n\n"
        "REQUIRED OUTPUT FORMAT (JSON-like Strictness):\n"
        "STYLE: <style description, max 200 chars>\n"
        "LYRICS:\n"
        "[Verse]\n"
        "In the hush of night, we find our space,\n"
        "Wrapped in moonlight’s gentle embrace.\n"
        "Your whisper’s soft, like a velvet song,\n"
        "In this tender moment, where we both belong.\n"
        "\n"
        "[Chorus]\n"
        "Just you and me, in this lazy jazz,\n"
        "Our souls entwined, nothing else we ask.\n"
        "In this serenade, we sway and sigh,\n"
        "Lost in this love, beneath the starry sky.\n"
        "\n"
        "[Bridge]\n"
        "Your voice, a lullaby, soothes my soul,\n"
        "In this night, together, we feel whole.\n"
        "Each moment shared, a timeless flight,\n"
        "In this gentle jazz, we find our light.\n"
        "\n"
        "[Outro]\n"
        "As dawn approaches, and stars fade away,\n"
        "In your arms, I wish to forever stay.\n"
        "(End of response. Do NOT add explanation or conversational text after Lyrics.)"
    )

    messages = [HumanMessage(content=schema_compliant_prompt)]
    last_valid_result = {}

    try:
        # from langchain_core.messages import AIMessage, HumanMessage  # REMOVED due to UnboundLocalError
        
        for attempt in range(1, 4): # Try up to 3 times
            response = llm.invoke(messages)
            content = response.content
            result = {}

            # Parse Output
            style_match = re.search(r"STYLE:\s*(.*)", content, re.IGNORECASE)
            result["prompt"] = style_match.group(1).strip() if style_match else input_text

            lyrics_match = re.search(r"LYRICS:\s*(.*)", content, re.IGNORECASE | re.DOTALL)
            lyrics = lyrics_match.group(1).strip() if lyrics_match else ""
            result["lyrics"] = lyrics

            # Validate Constraints
            constraint_errors = []
            if len(lyrics) > 550: # Safety buffer below 600
                constraint_errors.append(f"Lyrics are {len(lyrics)} chars (Max 550 allowable)")
            if len(result["prompt"]) > 290: # Safety buffer below 300
                constraint_errors.append(f"Style Prompt is {len(result['prompt'])} chars (Max 300 allowable)")

            if not constraint_errors and lyrics:
                logger.info(f"✅ Generated Valid Lyrics/Style (Attempt {attempt})")
                logger.info("Generated Style: %s", result.get("prompt"))
                return result

            # Reflexion: Add feedback to history for next turn
            logger.warning(f"⚠️ Constraint Violation (Attempt {attempt}): {', '.join(constraint_errors)}. Retrying...")
            messages.append(AIMessage(content=content))
            messages.append(HumanMessage(content=f"SYSTEM ERROR: The output violated strict API limits. \nErrors: {'; '.join(constraint_errors)}. \n\nPlease REWRITE the content to be significantly shorter. Keep the lyrics to just 4-6 lines maximum."))
            last_valid_result = result # Save just in case but don't return yet

        # Fallback if 3 attempts fail: Strict Truncation (The "Nuclear Option")
        logger.error("❌ Max retries reached. Applying forced truncation to fit schema.")
        final_lyrics = last_valid_result.get("lyrics", "")[:550]
        if "\n" in final_lyrics:
            final_lyrics = final_lyrics.rsplit("\n", 1)[0]
        last_valid_result["lyrics"] = final_lyrics
        last_valid_result["prompt"] = last_valid_result.get("prompt", input_text)[:290]
        
        return last_valid_result

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
    # Also check music-1.5 status (implied true if not checked explicitly but good to know)
    status_map["minimax/music-1.5"] = True # Assume true for now or add to check_service_status
    
    # --- 2. Strategy Selection & Fallback ---
    # Default selection logic
    target_model = model_name
    # if generic, pick based on intent
    if "/" not in target_model:
        lower_input = input_text.lower()
        if "voice" in lower_input or "speech" in lower_input:
            # STRICT POLICY: Use Minimax Speech, NEVER Bark
            target_model = "minimax/speech-01"
        elif "lyria" in target_model.lower() or "music" in target_model.lower():
            # [UPDATE] Default to Minimax 1.5 for basic music as it is superior
            target_model = "minimax/music-1.5"
        elif "minimax" in target_model.lower():
            target_model = "minimax/music-1.5"
        else:
            target_model = "minimax/music-1.5"

    logger.info(f"🎼 Initial Strategy: {target_model}")

    # Apply Service Status Fallbacks
    # Map music-01 requests to music-1.5 automatically
    if "music-01" in target_model:
        logger.info("ℹ️ Upgrading request from Music-01 to Music-1.5")
        target_model = "minimax/music-1.5"


    if "lyria" in target_model and status_map.get("google/lyria-2") is False:
        logger.warning("🚨 Lyria-2 is DOWN. Falling back to MusicGen.")
        target_model = "meta/musicgen"
    
    logger.info(f"✅ Final Strategy: {target_model}")

    # --- 3. Voice Generation (DEPRECATED: Bark) ---
    if "bark" in target_model or "suno-ai" in target_model:
        return "Error: Suno Bark is deprecated due to high latency. Use Minimax or XTTS-v2."

    # --- 4. Music Generation Pipeline ---
    
    # A. Generate Instrumental Base (if Minimax Music-01 still used, unlikely)
    instrumental_file_path = None
    
    # [PATCH] Music-1.5 does not need instrumental base.
    if "music-01" in target_model:
        # [PATCH] Disabled Lyria Base Gen due to WAV output incompatibility (Minimax needs MP3)
        logger.info("🎹 Step 1: Pre-generating Base Track skipped (No FFmpeg).")
        pass

    # B. Final Generation
    try:
        final_url = None
        current_model_used = target_model
        
        # Case: Minimax Music-1.5 (Preferred)
        if "music-1.5" in target_model:
            logger.info("🎤 Generating with Minimax Music-1.5 (Text-to-Music)...")
            lyric_data = _generate_lyrics_and_style(input_text, llm)
            lyrics_text = lyric_data.get("lyrics", input_text)
            style_prompt = lyric_data.get("prompt", input_text)
            
            # Schema: prompt (str), lyrics (str)
            # No files needed!
            payload = {
                "prompt": style_prompt,
                "lyrics": lyrics_text
            }
            logger.info(f"   Payload: {payload.keys()}")
            
            minimax_out = _safe_replicate_run("minimax/music-1.5", input_data=payload)
            final_url = str(minimax_out)

        # Case: Minimax Music-01 (Legacy)
        elif "music-01" in target_model:
            if not instrumental_file_path:
                logger.warning("Minimax base track missing. Continuing generation without instrumental base.")
            
            # Proceed with Minimax logic (using 'if True' to maintain indentation of existing block)
            if True:

                logger.info("🎤 Step 2: Adding Vocals with Minimax...")
                lyric_data = _generate_lyrics_and_style(input_text, llm)
                lyrics = lyric_data.get("lyrics", input_text)
                
                 # Voice Library Selection
                # Path: agent.py -> composer_agent -> CommercialAgents -> DeepAgents -> root -> data -> voices
                voice_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "voices")
                # [PATCH] Only load MP3s for Minimax compatibility (WAV causes code=400)
                available_voices = glob.glob(os.path.join(voice_dir, "*.mp3"))
                # available_voices = glob.glob(os.path.join(voice_dir, "*.wav")) + glob.glob(os.path.join(voice_dir, "*.mp3"))
                
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
                    "lyrics": lyrics
                }
                if instrumental_file_path:
                    payload["instrumental_file"] = open(instrumental_file_path, "rb")

                if selected_voice:
                     # FIX: Replicate Minimax Music-01 uses 'voice_file' NOT 'refer_voice'
                     logger.info(f"📂 Attaching voice_file: {selected_voice}")
                     payload["voice_file"] = open(selected_voice, "rb")

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
                
                # Retrieve used lyrics depending on the path taken
                used_lyrics_display = ""
                if "minimax" in current_model_used.lower():
                     # Try to recover the variable from local locals if possible, 
                     # but cleaner to have assigned it to a shared var. 
                     # Since we can't easily refactor the whole function safely in one go, 
                     # let's assume 'lyrics_text' or 'lyrics' variable is in scope from the blocks above.
                     # However, Python scoping leak in if-blocks is risky.
                     # Better: Let's assume the user wants transparency.
                     pass 

                return f"**Audio Generated ({current_model_used}):**\n- [Play Audio]({final_url})\n- Local: {final_path}\n\n**(Verified Lyrics Used)**:\n{locals().get('lyrics_text', locals().get('lyrics', 'N/A'))}"
            
        return "Generation failed: No URL returned."

    except Exception as e:
        # If E004 (Unavailable) or E003 (Access denied) or other Replicate API errors occur
        # we should try to fallback gracefully.
        error_msg = str(e)
        if "E004" in error_msg:  # Service Unavailable
             logger.warning("Minimax Service Unavailable (E004). ")
        elif "E006" in error_msg: # Invalid Input (often format)
             logger.warning("Minimax Invalid Input (E006). ")
        
        # Try one last Hail Mary fallback if we haven't tried Lyria yet as the primary engine 
        if "lyria" not in current_model_used:
             logger.info("↩️ Fallback: Attempting Lyria-2 instrumental as safety net.")
             try:
                 lyria_out = _safe_replicate_run("google/lyria-2", input_data={"prompt": input_text})
                 final_url = str(lyria_out)
                 if final_url:
                    fname = _generate_descriptive_filename(input_text, session_id)
                    local_path = _download_and_validate_asset(final_url, session_id, prefix="final_fallback")
                    if local_path:
                        final_path = os.path.join(os.path.dirname(local_path), fname)
                        os.rename(local_path, final_path)
                        logger.info(f"🎉 Fallback Asset Ready: {final_path}")
                        return f"**Audio Generated (Fallback Lyria):**\n- [Play Audio]({final_url})\n- Local: {final_path}\n*(Note: Primary model failed. Error: {str(e)})*"
             except Exception as ex:
                 logger.error(f"Fallback failed: {ex}")

        logger.error(f"Replicate Pipeline Failure: {e}")
        return f"Error: {e}"


def _generate_music_audio_internal(prompt: str, model_name: str = "minimax/music-01") -> str:
    """
    Directly generates audio using a Replicate model (MusicGen or Minimax).
    Args:
        prompt: The description of the music.
        model_name: "minimax/music-01" or "meta/musicgen..."
    """
    logger.info("🎵 Direct Audio Tool called: %s (%s)", prompt, model_name)
    assets = AssetManager()
    
    # Priority Cascade: Music-1.5 -> Lyria-2 -> MusicGen
    # If generic "music" requested, default to Music-1.5 as primary
    if "music-01" in model_name:
         target_model = "minimax/music-1.5" # 01 is deprecated/hard to use
    elif "music-1.5" in model_name:
         target_model = "minimax/music-1.5"
    elif "musicgen" in model_name:
         target_model = "meta/musicgen:b05b1dff1d8c6dc63d14b0cdb42135378dcb87f6373b0d3d341ede46e59e2b38"
    else:
         target_model = "minimax/music-1.5" # Default high quality

    # We might need an LLM for lyrics if Minimax
    # Using lazy import to avoid circular dependency or heavy init if unused
    llm_for_lyrics = None
    try:
        # Switch to Anthropic default for lyrics too
        llm_for_lyrics = ChatAnthropic(
            model_name="claude-3-haiku-20240307",
            temperature=0.7
        )
    except Exception as e:
        logger.warning("Could not init LLM for lyrics, continuing without: %s", e)
        try:
            # Fallback
            llm_for_lyrics = ChatReplicate(
                model="meta/meta-llama-3-70b-instruct", 
                model_kwargs={"temperature": 0.7, "max_length": 2048} 
            )
        except: pass

    return _handle_replicate_generation(
        model_name=target_model,
        input_text=prompt,
        llm=llm_for_lyrics,
        assets=assets,
        session_id="tool_direct"
    )


@tool
def generate_music_tool(prompt: str) -> str:
    """
    Generates music/audio based on a text description.
    You MUST use this tool to actually create the audio file when the user asks for a song, melody, or composition.
    Input example: "A sad piano melody", "An upbeat rock song with lyrics about coding".
    Returns the path/link to the generated audio or an error message.
    """
    try:
        # Determine likely model based on prompt content (simple heuristic)
        # The agent.py logic already does this in _handle_replicate_generation
        # So we just pass the prompt.
        # We default to 'minimax/music-01' as the "high quality" default if not specified
        return _generate_music_audio_internal(prompt, model_name="minimax/music-01")
    except Exception as e:
        return f"Error generation music: {e}"


@tool
def browse_library_tool(filter_type: str = "all") -> str:
    """
    Browses the Asset Library to see what audio, video, or images have been generated.
    Args:
        filter_type: "audio", "video", "image", or "all".
    """
    assets = AssetManager()
    
    # If "all", pass None, else pass type
    a_type = None if filter_type == "all" else filter_type
    
    results = assets.list_assets(asset_type=a_type)
    if not results:
        return "Library is empty."
        
    output = "Current Asset Library:\n"
    for item in results[:10]: # Limit to 10 most recent
        output += f"- [{item.get('asset_type')}] {item.get('prompt', 'Unknown')} (File: {os.path.basename(item.get('path', ''))})\n"
        
    return output


def create_composer_agent(
    model_config: Optional[Dict[str, Any]] = None,
    brain: Any = None,
    session_id: str = "default",
):
    """
    Factory to create the Composer Agent runner.
    """
    if model_config is None:
        # Default to Anthropic Haiku for the Brain, music gen is separate
        model_config = {"provider": "Anthropic", "model": "claude-3-haiku-20240307"}

    provider = model_config.get("provider", "Anthropic")
    model_name = model_config.get("model", "claude-3-haiku-20240307")

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
        # Determine Brain Provider (Separate from Music Gen Model)
        # Default to Anthropic if not specified for Brain
        brain_provider = "Anthropic" 
        brain_model = "claude-3-haiku-20240307"
        
        # Override if config explicitly asks for Replicate Brain (unlikely for now)
        # But we respect global "provider" if it matches a known LLM provider
        if provider in ["Google", "Anthropic"]:
             brain_provider = provider
             # Map models? Or just use default per provider
             if provider == "Google": brain_model = "gemini-1.5-flash"
        
        logger.info(f"🎻 Orpheus > Initializing Brain with {brain_provider}/{brain_model}...")

        if brain_provider == "Anthropic":
            try:
                llm = ChatAnthropic(
                    model_name=brain_model, 
                    temperature=0.7
                )
            except Exception as e:
                logger.warning(f"Anthropic Brain Init Failed: {e}")
                # Fallback to Replicate Llama 3
                brain_provider = "Replicate"
                brain_model = "meta/meta-llama-3-8b-instruct"

        if brain_provider == "Replicate":
            try:
                # Requires REPLICATE_API_TOKEN in env
                from DeepAgents.replicate_adapter import ChatReplicate
                llm = ChatReplicate(
                    model=brain_model,
                    model_kwargs={"temperature": 0.5, "max_length": 2048, "top_p": 1}
                )
            except Exception as e:
                logger.warning(f"Replicate Init Failed: {e}. Falling back to Google.")
                brain_provider = "Google"

        if brain_provider == "Google":
            try:
                target_model = "gemini-1.5-flash"
                llm = ChatGoogleGenerativeAI(
                    model=target_model,
                    temperature=0.5,
                    project=os.getenv("GOOGLE_CLOUD_PROJECT"),
                    location="us-central1" # Flash is reliable here
                )
            except Exception:
                pass


        if not llm:
             raise ValueError("No LLM could be initialized")

    except Exception as e:
        logger.error(f"Brain Init Failed: {e}")
        # Final Dummy Fallback
        return lambda *args, **kwargs: f"Error: Agent Brain Died. {e}"

    # 3. Initialize Agent
    # Fix: Restored valid 'browse_library_tool'
    
    # 🔗 HUB INTEGRATION: Pull System Prompt
    hub_prompt = get_or_push_prompt("composer-system-prompt", COMPOSER_INSTRUCTIONS)
    
    # We replace 'compose_tool' (which was recursive) with 'generate_music_tool' (which wraps the logic)
    agent = create_deep_agent(
        model=llm,
        tools=[generate_music_tool, browse_library_tool], 
        system_prompt=hub_prompt,
    )
    
    return agent


def run_composer_task(request_description: str) -> str:
    """
    Synchronous entry point for the Director to consult the Composer.
    Creates an ephemeral agent, runs the task, and returns the result string.
    """
    logger.info(f"🎻 Composer Consulted: {request_description}")
    try:
        # Create a fresh agent instance
        agent = create_composer_agent()
        
        # Format input (Standard LangGraph)
        inputs = {"messages": [HumanMessage(content=request_description)]}
        
        # Run
        result = agent.invoke(inputs)
        
        # Parse Result
        if isinstance(result, dict) and "messages" in result:
             # Get the AI's final response
             final_response = result["messages"][-1].content
             return str(final_response)
        
        return str(result)

    except Exception as e:
        logger.error(f"Composer Task Failed: {e}")
        return f"Composer failed to process request. Error: {e}"


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(run_composer_task(sys.argv[1]))
    else:
        print("Composer Agent ready. Pass a prompt to test.")

