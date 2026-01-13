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
        "lucataco/ace-step": True,
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


def _generate_lyrics_and_style(input_text: str, llm: Any, model_type: str = "minimax") -> Dict[str, str]:
    """
    Helper to generate lyrics and style using the LLM.
    Implements a Reflexion Loop to strictly enforce API constraints.
    Supports: Minimax Music-1.5, ACE-Step.
    """
    if not llm:
        return {"prompt": input_text, "tags": input_text}

    if model_type == "ace-step":
        # ACE-Step Schema
        schema_compliant_prompt = (
            f'You are an expert Songwriter specialized in the ACE-Step Music Schema.\n'
            f'The user wants a song about: "{input_text}".\n\n'
            "REQUIRED OUTPUT FORMAT:\n"
            "TAGS: <Generate 5-10 comma-separated descriptive keywords. STRICTLY ADHERE to the user's requested style/artist. Do NOT add unrelated genres (e.g. do not add 'rap' if user asked for 'rock'). If Style is 'REO Speedwagon', use tags like: 'Rock, 1980s, Power Ballad, Electric Guitar, Synthesizer, Male Vocals'.>\n"
            "LYRICS:\n"
            "[verse]\n"
            "<lyrics here>\n\n"
            "[chorus]\n"
            "<lyrics here>\n\n"
            "[bridge]\n"
            "<lyrics here>\n\n"
            "[instrumental] (Optional, use instead of lyrics if instrumental requested)\n"
            "(End of response)"
        )
    else:
        # Defaults to Minimax Music-1.5 Schema (High-Quality Condensed)
        # Optimized for "The 600-Char Challenge" per User Guidance
        schema_compliant_prompt = (
            f'You are an expert Songwriter specialized in the Minimax Music-1.5 Schema.\n'
            f'The user wants a song about: "{input_text}".\n\n'
            "CRITICAL CONSTRAINTS (THE 600-CHAR CHALLENGE):\n"
            "This model provides Radio-Quality audio but has a STRICT 600-character limit for lyrics.\n"
            "To succeed, you must use a 'Section-Label Skeleton' with maximizing density.\n\n"
            "RULES FOR SUCCESS:\n"
            "1. STRUCTURE: Must use these sections: [Intro], [Verse], [Chorus], [Bridge], [Outro].\n"
            "2. LENGTH: Keep each section 2-4 lines MAX. Short, punchy lines allow musical expansion.\n"
            "3. IMAGERY: Use compressed, evocative imagery. (e.g., 'City nights, empty streets' vs 'I am walking alone at night').\n"
            "4. STYLE: Put the Genre/Mood in the 'STYLE' field, NOT the lyrics.\n"
            "5. CHORUS: Make it simple and repetitive (The model loves repetition).\n"
            "6. RHYME: Avoid forced rhymes. Use light rhyme or no rhyme to prevent melodic derailment.\n"
            "7. ENDING: Always end with [Outro] to prevent infinite looping.\n"
            "8. BUDGET: Total Lyrics MUST be ~450-550 characters. Do NOT go over 580.\n\n"
            "REQUIRED OUTPUT FORMAT:\n"
            "STYLE: <Genre, Mood, Instrumentation. E.g., 'Emotional pop ballad, female vocals, atmospheric synths'>\n"
            "LYRICS:\n"
            "[Intro]\n"
            "Soft lights, slow breath\n\n"
            "[Verse]\n"
            "City nights calling me back\n"
            "Your voice in the static haze\n"
            "I chase the ghost of what we were\n"
            "Lost between the beats\n\n"
            "[Chorus]\n"
            "Hold on, hold on\n"
            "I’m not letting go\n"
            "Hold on, hold on\n"
            "You’re the fire in my soul\n\n"
            "[Bridge]\n"
            "One spark and we rise again\n\n"
            "[Outro]\n"
            "Fade into the dawn\n"
            "(End of response)"
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
            if model_type == "ace-step":
                tags_match = re.search(r"TAGS:\s*(.*)", content, re.IGNORECASE)
                result["tags"] = tags_match.group(1).strip() if tags_match else input_text
            else:
                style_match = re.search(r"STYLE:\s*(.*)", content, re.IGNORECASE)
                result["prompt"] = style_match.group(1).strip() if style_match else input_text

            lyrics_match = re.search(r"LYRICS:\s*(.*)", content, re.IGNORECASE | re.DOTALL)
            lyrics = lyrics_match.group(1).strip() if lyrics_match else ""
            result["lyrics"] = lyrics

            # Validate Constraints (Minimax Only)
            constraint_errors = []
            if model_type == "minimax":
                if len(lyrics) > 550: # Safety buffer below 600
                    constraint_errors.append(f"Lyrics are {len(lyrics)} chars (Max 550 allowable)")
                prompt_val = result.get("prompt", "")
                if len(prompt_val) > 290: # Safety buffer below 300
                    constraint_errors.append(f"Style Prompt is {len(prompt_val)} chars (Max 300 allowable)")
            
            # ACE-Step Constraints (Loose for now)
            if model_type == "ace-step":
                 if not result.get("tags") and not lyrics:
                     constraint_errors.append("Failed to generate Tags or Lyrics")

            if not constraint_errors and (lyrics or result.get("tags")):
                logger.info(f"✅ Generated Valid Lyrics/Style (Attempt {attempt}, Model: {model_type})")
                return result

            # Reflexion: Add feedback to history for next turn
            logger.warning(f"⚠️ Constraint Violation (Attempt {attempt}): {', '.join(constraint_errors)}. Retrying...")
            messages.append(AIMessage(content=content))
            messages.append(HumanMessage(content=f"SYSTEM ERROR: The output violated strict API requirements. \nErrors: {'; '.join(constraint_errors)}. \n\nPlease REWRITE the content to comply."))
            last_valid_result = result # Save just in case but don't return yet

        # Fallback if 3 attempts fail
        logger.error("❌ Max retries reached. Using best effort.")
        return last_valid_result

    except Exception as llm_err:  # pylint: disable=broad-exception-caught
        logger.error("Lyric generation failed: %s. Using raw input.", llm_err)
        return {"prompt": input_text, "tags": input_text, "lyrics": ""}


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


def _extract_replicate_url(output: Any) -> Optional[str]:
    """Helper to extract clean URL from Replicate output (List or String)."""
    if not output:
        return None
    if isinstance(output, (list, tuple)):
        if len(output) > 0:
            return str(output[0])
        return None
    return str(output)


def _handle_replicate_generation(  # pylint: disable=too-many-arguments
    model_name: str, input_text: str, llm: Any, assets: Any, session_id: str
) -> str:
    """
    Handle generation via Replicate (ACE-Step, Minimax, Lyria, MusicGen).
    Implements cascading fallback, service checks, and voice library integration.
    """
    if not os.environ.get("REPLICATE_API_TOKEN"):
        return "Error: REPLICATE_API_TOKEN not set."

    # --- 1. Service Availability Check ---
    status_map = check_service_status()
    
    # --- 2. Strategy Selection & Fallback ---
    # Default selection logic
    target_model = model_name
    
    # Logic: Default to ACE-Step unless specific model requested
    if "/" not in target_model:
        lower_input = input_text.lower()
        if "voice" in lower_input or "speech" in lower_input:
            target_model = "minimax/speech-01"
        elif "minimax" in lower_input:
            target_model = "minimax/music-1.5"
        elif "lyria" in lower_input:
            target_model = "google/lyria-2"
        elif "ace" in lower_input:
            target_model = "lucataco/ace-step"
        else:
            # NEW DEFAULT: Minimax Music-1.5 (High Fidelity, Strict Formatting)
            target_model = "minimax/music-1.5"

    logger.info(f"🎼 Initial Strategy: {target_model}")

    # Apply Service Status Fallbacks
    if "ace-step" in target_model and not status_map.get("lucataco/ace-step", True):
        logger.warning("🚨 ACE-Step is DOWN. Falling back to Minimax 1.5.")
        target_model = "minimax/music-1.5"

    if "music-01" in target_model:
        logger.info("ℹ️ Upgrading request from Music-01 to Music-1.5")
        target_model = "minimax/music-1.5"

    if "lyria" in target_model and status_map.get("google/lyria-2") is False:
        logger.warning("🚨 Lyria-2 is DOWN. Falling back to MusicGen.")
        target_model = "meta/musicgen"
    
    logger.info(f"✅ Final Strategy: {target_model}")

    if "bark" in target_model or "suno-ai" in target_model:
        return "Error: Suno Bark is deprecated due to high latency. Use ACE-Step or Minimax."

    # --- 4. Music Generation Pipeline ---
    try:
        final_url = None
        current_model_used = target_model

        # Parse Duration (Global Logic for all models)
        duration_sec = None
        dur_match = re.search(r"(\d+)\s*(min|minute|sec|second)", input_text, re.IGNORECASE)
        if dur_match:
            val = int(dur_match.group(1))
            unit = dur_match.group(2).lower()
            if "min" in unit:
                duration_sec = min(val * 60, 300) # Cap at 300s (5 mins) for Minimax
            else:
                duration_sec = min(val, 300)
            logger.info(f"   Duration parsed: {duration_sec}s")
        
        # Case: ACE-Step (Primary Default)
        if "ace-step" in target_model:
            logger.info("🎤 Generating with ACE-Step (Text-to-Music)...")
            
            # Map global duration to ACE specific logic (Cap 240s)
            ace_duration = min(duration_sec, 240) if duration_sec else 60
            logger.info(f"   ACE-Step Duration set to: {ace_duration}s")

            # Generate Tags/Lyrics
            lyric_data = _generate_lyrics_and_style(input_text, llm, model_type="ace-step")
            tags = lyric_data.get("tags", input_text)
            lyrics = lyric_data.get("lyrics", "[inst]")

            # Hardcoded Options from Examples (Tuned for Quality)
            payload = {
                "tags": tags,
                "lyrics": lyrics,
                "duration": ace_duration,
                "scheduler": "heun",
                "guidance_type": "apg",
                "guidance_scale": 20,        # Boosted to 20 for strict adherence
                "number_of_steps": 200,      # MAX (200) for best quality
                "granularity_scale": 10,
                "guidance_interval": 0.5,
                "min_guidance_scale": 3,
                "tag_guidance_scale": 10,    # MAX (10) - Absolute Stlye Adherence
                "lyric_guidance_scale": 10,  # MAX (10) - Absolute Lyric Adherence
                "guidance_interval_decay": 0
            }
            logger.info(f"   Payload Keys: {payload.keys()}")
            
            ace_out = _safe_replicate_run("lucataco/ace-step", input_data=payload)
            final_url = _extract_replicate_url(ace_out)

        # Case: Minimax Music-1.5
        elif "music-1.5" in target_model:
            logger.info("🎤 Generating with Minimax Music-1.5 (Text-to-Music)...")

            # Minimax doesn't have explicit 'duration' param typically, but we should pass it 
            # if the new API supports it, or rely on lyric length.
            # Assuming 'duration' int/float is supported per user instruction.
            
            lyric_data = _generate_lyrics_and_style(input_text, llm, model_type="minimax")
            lyrics_text = lyric_data.get("lyrics", input_text)
            style_prompt = lyric_data.get("prompt", input_text)
            
            payload = {
                "prompt": style_prompt,
                "lyrics": lyrics_text
            }
            # Note: Minimax Music-1.5 does NOT support 'duration'. Length is determined by text/lyrics.
            
            minimax_out = _safe_replicate_run("minimax/music-1.5", input_data=payload)
            final_url = _extract_replicate_url(minimax_out)

        # Case: Lyria-2
        elif "lyria" in target_model:
            logger.info("🎵 Generating with Google Lyria-2...")
            lyria_out = _safe_replicate_run("google/lyria-2", input_data={"prompt": input_text})
            final_url = _extract_replicate_url(lyria_out)

        # Case: MusicGen
        else:
            logger.info("🎵 Generating with MusicGen...")
            mg_out = _safe_replicate_run(
                "meta/musicgen", 
                input_data={"prompt": input_text, "duration": 20}
            )
            final_url = _extract_replicate_url(mg_out)

        # C. Save & Rename
        if final_url:
            fname = _generate_descriptive_filename(input_text, session_id)
            local_path = _download_and_validate_asset(final_url, session_id, prefix="final")
            
            if local_path:
                final_path = os.path.join(os.path.dirname(local_path), fname)
                os.rename(local_path, final_path)
                logger.info(f"🎉 Final Asset Ready: {final_path}")
                
                # Retrieve used lyrics for display
                used_lyrics = locals().get("lyrics", locals().get("lyrics_text", "N/A"))

                return f"**Audio Generated ({current_model_used}):**\n- [Play Audio]({final_url})\n- Local: {final_path}\n\n**(Verified Lyrics Used)**:\n{used_lyrics}"
            
        return "Generation failed: No URL returned."

    except Exception as e:
        logger.error(f"Replicate Pipeline Failure: {e}")
        return f"Error: {e}"


def _generate_music_audio_internal(prompt: str, model_name: str = "minimax/music-1.5") -> str:
    """
    Directly generates audio using a Replicate model determined by System Configuration.
    Args:
        prompt: The description of the music.
        model_name: Optional override, but System Config takes precedence for Capabilities.
    """
    logger.info("🎵 Direct Audio Tool called: %s", prompt)
    assets = AssetManager()
    
    # Dynamic Model Selection via LangSmith Config
    try:
        from DeepAgents.system_config import SystemConfiguration
        sys_config = SystemConfiguration()
        model_cfg = sys_config.get_capability_model("Composer", "music_generation")
        if model_cfg:
            target_model = model_cfg.get("id")
            logger.info(f"System Optimized Model Selection: {target_model} (Priority: {model_cfg.get('priority')})")
        else:
            logger.warning("System Config missing 'music_generation' capability. Using default.")
            target_model = "minimax/music-1.5"
    except Exception as e:
         logger.error(f"Config Load Error: {e}")
         target_model = "minimax/music-1.5"

    # We might need an LLM for lyrics if Minimax or ACE-Step
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
        # We default to 'minimax/music-1.5' as the primary generator
        return _generate_music_audio_internal(prompt, model_name="minimax/music-1.5")
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

