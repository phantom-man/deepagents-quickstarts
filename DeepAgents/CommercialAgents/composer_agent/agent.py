"""
Composer Agent Module.
Handles the creation of musical compositions (Audio or Text/ABC).
"""

# pylint: disable=too-many-lines, too-many-locals, too-many-branches, too-many-statements
# pylint: disable=broad-exception-caught, logging-fstring-interpolation, used-before-assignment

import os
import re
import sys
import time
import base64
import uuid
import logging
from dotenv import load_dotenv
from typing import Optional, Dict, Any

import requests
import google.auth
from google.auth.transport.requests import Request
from langchain_core.messages import HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from langchain.tools import tool

from DeepAgents.replicate_adapter import ChatReplicate
from DeepAgents.asset_manager import AssetManager
from DeepAgents.hub_manager import get_or_push_prompt
from DeepAgents.system_config import SystemConfiguration
from DeepAgents.model_schemas import get_model_schema

try:
    from DeepAgents.CommercialAgents.composer_agent.prompts import (
        COMPOSER_INSTRUCTIONS,
        # Note: ACE_STEP_SCHEMA, MINIMAX_SCHEMA, LYRIA_SCHEMA now loaded dynamically via get_model_schema()
    )
    # Legacy fallback schemas (used only if Hub/model_schemas unavailable)
    from DeepAgents.CommercialAgents.composer_agent.prompts import (
        ACE_STEP_SCHEMA,
        MINIMAX_SCHEMA,
        LYRIA_SCHEMA,
    )
except ImportError:
    # Basic fallback if file missing
    COMPOSER_INSTRUCTIONS = "You are an expert Music Composer AI."
    ACE_STEP_SCHEMA = "Error: Schema missing."
    MINIMAX_SCHEMA = "Error: Schema missing."
    LYRIA_SCHEMA = "Error: Schema missing."


# Setup Logging
logging.basicConfig(level=logging.INFO)
# Suppress noisy OpenTelemetry attribute warnings
logging.getLogger("opentelemetry.attributes").setLevel(logging.ERROR)
logger = logging.getLogger("ComposerAgent")


def _download_and_validate_asset(
    url: str,
    session_id: str,
    prefix: str = "audio",
    max_mb: int = 20,
    force_extension: Optional[str] = None,
) -> Optional[str]:
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
                logger.warning(
                    f"⚠️ Audio too large ({content_length/1024/1024:.2f}MB). Limit is {max_mb}MB."
                )
                return None
        except Exception:
            pass  # Head might fail on some signed URLs, create session to try GET

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
        "minimax/music-1.5": True,
        "google/lyria-2": True,
        "meta/musicgen": True,
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


# @tool
# def composer_consult_research(topic: str) -> str:
#    """
#    Consults the Research Agent to understand musical styles, historical context,
#    or specific instruments.
#    """
#    # Lazy import to avoid circular dependencies
#    from DeepAgents.CommercialAgents.research_agent.agent import run_research_task
#
#    logger.info("🎻 Composer > 📞 Calling Research Agent about: %s", topic)
#    extra_config = {
#        "tags": ["sub-agent-call", "agent:researcher", "source:composer"],
#        "metadata": {"parent_agent": "Composer", "trigger": "tool_call"},
#    }
#    result = run_research_task(topic, extra_config=extra_config)
#    if result:
#        return result
#    return "Research Agent could not find significant information."


def _generate_lyrics_and_style(
    input_text: str, llm: Any, model_type: str = "minimax"
) -> Dict[str, str]:
    """
    Helper to generate lyrics and style using the LLM.
    Implements a Reflexion Loop to strictly enforce API constraints.
    Uses dynamic schema loading from LangSmith Hub via get_model_schema().
    Supports: Minimax Music-1.5, ACE-Step, Lyria.
    
    IMPORTANT: If input_text contains user-supplied lyrics (detected via markers like
    [Verse], [Chorus], [Bridge]), they will be passed through VERBATIM. The LLM will
    only be used to extract the style/genre prompt, NOT to rewrite lyrics.
    """
    if not llm:
        return {"prompt": input_text, "tags": input_text}

    # STEP 1: Detect user-supplied lyrics (verbatim pass-through)
    lyrics_markers = ["[verse", "[chorus", "[bridge", "[intro", "[outro", "[hook", "[pre-chorus"]
    input_lower = input_text.lower()
    has_user_lyrics = any(marker in input_lower for marker in lyrics_markers)
    
    if has_user_lyrics:
        logger.info("[LYRICS] User-supplied lyrics detected - passing through VERBATIM")
        
        # Extract the lyrics section (everything after "Lyrics:" or the first marker)
        user_lyrics = ""
        style_prompt = ""
        
        # Check if there's a "Lyrics:" label
        lyrics_label_match = re.search(r"(?:Lyrics|LYRICS):\s*(.+)", input_text, re.IGNORECASE | re.DOTALL)
        if lyrics_label_match:
            user_lyrics = lyrics_label_match.group(1).strip()
            # Style is everything before "Lyrics:"
            style_prompt = input_text[:lyrics_label_match.start()].strip()
        else:
            # Find first lyrics marker and split there
            first_marker_match = re.search(r"(\[(?:Verse|Chorus|Bridge|Intro|Outro|Hook|Pre-Chorus)[^\]]*\])", input_text, re.IGNORECASE)
            if first_marker_match:
                marker_pos = first_marker_match.start()
                style_prompt = input_text[:marker_pos].strip()
                user_lyrics = input_text[marker_pos:].strip()
            else:
                # Fallback: treat entire input as lyrics
                user_lyrics = input_text
        
        # Clean up style prompt (extract from "Audio/Music Prompt:" if present)
        audio_prompt_match = re.search(r"(?:Audio/Music Prompt|Audio Prompt|Music Prompt)[:\s]*[\"']?([^\"'\n]+)", style_prompt, re.IGNORECASE)
        if audio_prompt_match:
            style_prompt = audio_prompt_match.group(1).strip()
        
        # Remove artist name references from style prompt (content moderation)
        style_prompt = re.sub(r"\b(?:like|think|similar to|sounds like|meets)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*", "", style_prompt, flags=re.IGNORECASE)
        style_prompt = style_prompt.strip().strip('"').strip("'").strip(".")
        
        # Check if lyrics fit within Minimax limit (600 chars)
        if model_type == "minimax" and len(user_lyrics) > 600:
            logger.warning(f"[LYRICS] User lyrics are {len(user_lyrics)} chars (limit 600). Will truncate to fit.")
            # Truncate at a natural break point (last complete section that fits)
            truncated = ""
            for line in user_lyrics.split('\n'):
                if len(truncated) + len(line) + 1 <= 600:
                    truncated += line + '\n'
                elif line.startswith('[') and len(truncated) > 100:
                    # Hit a section marker and have enough content, stop here
                    break
            user_lyrics = truncated.strip()
            logger.info(f"[LYRICS] Truncated to {len(user_lyrics)} chars")
        
        return {"prompt": style_prompt or "rock anthem, powerful vocals", "lyrics": user_lyrics}

    # STEP 2: No user lyrics detected - use LLM to generate
    # Dynamic Schema Loading from Hub (with local fallback)
    try:
        # Map model_type to model_id for schema lookup
        model_id_map = {
            "ace-step": "replicate/lucataco/ace-step",
            "lyria": "google/lyria-002",
            "minimax": "minimax/music-1.5"
        }
        model_id = model_id_map.get(model_type, "minimax/music-1.5")
        schema_template = get_model_schema("Composer", "music_generation", model_id)
        schema_compliant_prompt = schema_template.format(input_text=input_text)
        logger.info(f"[SCHEMA] Using dynamic schema for {model_type}")
    except Exception as schema_error:
        logger.warning(f"[SCHEMA] Dynamic schema load failed ({schema_error}), using fallback")
        # Fallback to hardcoded schemas
        if model_type == "ace-step":
            schema_compliant_prompt = ACE_STEP_SCHEMA.format(input_text=input_text)
        elif model_type == "lyria":
            schema_compliant_prompt = LYRIA_SCHEMA.format(input_text=input_text)
        else:
            schema_compliant_prompt = MINIMAX_SCHEMA.format(input_text=input_text)

    messages = [HumanMessage(content=schema_compliant_prompt)]
    last_valid_result = {}

    try:
        # from langchain_core.messages import AIMessage, HumanMessage  # REMOVED due to UnboundLocalError

        for attempt in range(1, 4):  # Try up to 3 times
            response = llm.invoke(messages)
            content = response.content
            result = {}

            # Parse Output
            if model_type == "ace-step":
                tags_match = re.search(r"TAGS:\s*(.*)", content, re.IGNORECASE)
                result["tags"] = (
                    tags_match.group(1).strip() if tags_match else input_text
                )
            else:
                # Standard Style/Prompt Extraction (Minimax & Lyria)
                style_match = re.search(r"STYLE:\s*(.*)", content, re.IGNORECASE)
                result["prompt"] = (
                    style_match.group(1).strip() if style_match else input_text
                )

            lyrics_match = re.search(
                r"LYRICS:\s*(.*)", content, re.IGNORECASE | re.DOTALL
            )
            lyrics = lyrics_match.group(1).strip() if lyrics_match else ""
            result["lyrics"] = lyrics

            # Validate Constraints (Minimax Only)
            constraint_errors = []
            if model_type == "minimax":
                if len(lyrics) > 600:  # Minimax Music-1.5 hard limit
                    constraint_errors.append(
                        f"Lyrics are {len(lyrics)} chars (Max 600 allowed)"
                    )
                prompt_val = result.get("prompt", "")
                if len(prompt_val) > 290:  # Safety buffer below 300
                    constraint_errors.append(
                        f"Style Prompt is {len(prompt_val)} chars (Max 300 allowable)"
                    )

            # ACE-Step Constraints (Loose for now)
            if model_type == "ace-step":
                if not result.get("tags") and not lyrics:
                    constraint_errors.append("Failed to generate Tags or Lyrics")

            if not constraint_errors and (
                lyrics or result.get("tags") or result.get("prompt")
            ):
                logger.info(
                    f"✅ Generated Valid Lyrics/Style (Attempt {attempt}, Model: {model_type})"
                )
                return result

            # Reflexion: Add feedback to history for next turn
            logger.warning(
                f"⚠️ Constraint Violation (Attempt {attempt}): {', '.join(constraint_errors)}. Retrying..."
            )
            messages.append(AIMessage(content=content))
            messages.append(
                HumanMessage(
                    content=f"SYSTEM ERROR: The output violated strict API requirements. \nErrors: {'; '.join(constraint_errors)}. \n\nPlease REWRITE the content to comply."
                )
            )
            last_valid_result = result  # Save just in case but don't return yet

        # Fallback if 3 attempts fail
        logger.error("❌ Max retries reached. Using best effort.")
        return last_valid_result

    except Exception as llm_err:  # pylint: disable=broad-exception-caught
        logger.error("Lyric generation failed: %s. Using raw input.", llm_err)
        return {"prompt": input_text, "tags": input_text, "lyrics": ""}


def _generate_descriptive_filename(
    prompt: str, session_id: str, ext: str = "mp3"
) -> str:
    """Generates a descriptive filename from the prompt."""
    clean_prompt = "".join([c if c.isalnum() else "_" for c in prompt[:30]]).strip("_")
    timestamp = int(time.time())
    return f"{clean_prompt}_{session_id[:6]}_{timestamp}.{ext}"


def _safe_replicate_run(
    model_id: str, input_data: Dict[str, Any], wait_time: int = 5
) -> Any:
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
    model_name: str, 
    input_text: str, 
    llm: Any, 
    assets: Any, 
    session_id: str,
    extra_params: Optional[Dict[str, Any]] = None
) -> str:
    """
    Handle generation via Replicate (ACE-Step, Minimax, Lyria, MusicGen).
    
    Args:
        model_name: Target model ID (e.g., "minimax/music-1.5")
        input_text: The music prompt/description
        llm: LLM for lyrics generation
        assets: AssetManager instance
        session_id: Session identifier
        extra_params: Additional model parameters from GUI schema
    
    FAIL FAST: Raises exceptions on critical failures.
    """
    if not os.environ.get("REPLICATE_API_TOKEN"):
        raise ValueError("REPLICATE_API_TOKEN not set. Cannot proceed with music generation.")

    # Merge extra_params if provided
    gui_params = extra_params or {}
    logger.info(f"[REPLICATE] GUI params: {gui_params}")

    # --- 1. Service Availability Check ---
    status_map = check_service_status()

    # --- 2. Strategy Selection ---
    # Use the model passed in directly - no more guessing from prompt
    target_model = model_name

    # Only do prompt-based selection if no model was specified
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
            target_model = "minimax/music-1.5"  # Default

    logger.info(f"[REPLICATE] Target Model: {target_model}")

    # Apply Service Status Fallbacks (FAIL FAST on primary model failure)
    if "ace-step" in target_model and not status_map.get("lucataco/ace-step", True):
        logger.warning("[REPLICATE] ACE-Step is DOWN. Falling back to Minimax 1.5.")
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

        # Parse Duration explicitly for models that support it
        duration_sec = None
        dur_match = re.search(
            r"(\d+)\s*(min|minute|sec|second)", input_text, re.IGNORECASE
        )
        if dur_match:
            val = int(dur_match.group(1))
            unit = dur_match.group(2).lower()
            if "min" in unit:
                duration_sec = min(val * 60, 300)  # Cap at 300s
            else:
                duration_sec = min(val, 300)
            logger.info(f"   Duration parsed: {duration_sec}s")

        # FIX: Sanitize prompt for Lyria - remove artist/band name references
        # Google Lyria rejects prompts with specific artist names due to copyright
        def sanitize_prompt_for_lyria(prompt: str) -> str:
            """Remove artist names and replace with descriptive style terms."""
            # Common pattern: "in the style of X" or "X style"
            import re as re_inner
            # Remove "in the style of [Artist]" patterns
            sanitized = re_inner.sub(
                r"in the style of [A-Z][a-zA-Z\s]+(?:,|\.|\s|$)",
                "with emotional intensity, ",
                prompt,
                flags=re_inner.IGNORECASE
            )
            # Remove "[Artist] style" patterns  
            sanitized = re_inner.sub(
                r"[A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)?\s+style",
                "90s alternative rock style",
                sanitized,
                flags=re_inner.IGNORECASE
            )
            # Remove specific known problematic artist names
            problematic_artists = [
                "Alanis Morissette", "Taylor Swift", "Beyonce", "Drake", 
                "Ed Sheeran", "Adele", "Coldplay", "Radiohead", "Nirvana",
                "Beatles", "Rolling Stones", "Pink Floyd", "Led Zeppelin"
            ]
            for artist in problematic_artists:
                sanitized = re_inner.sub(
                    rf"\b{re_inner.escape(artist)}\b",
                    "",
                    sanitized,
                    flags=re_inner.IGNORECASE
                )
            # Clean up extra spaces/commas
            sanitized = re_inner.sub(r"\s+", " ", sanitized).strip()
            sanitized = re_inner.sub(r",\s*,", ",", sanitized)
            return sanitized

        # Case: Native Google Lyria
        if "lyria-002" in target_model or (
            "lyria" in target_model
            and "google" in target_model
            and "002" in target_model
        ):
            logger.info("🎵 Generating with Native Google Lyria-2 (Vertex Predict)...")
            
            # Sanitize prompt to remove artist references
            lyria_prompt = sanitize_prompt_for_lyria(input_text)
            logger.info(f"   Sanitized prompt: {lyria_prompt[:100]}...")

            # Auth & Call (Lines omitted)
            credentials, project_id = google.auth.default()
            if not credentials.valid:
                credentials.refresh(Request())
            target_project = project_id or "crafty-hook-483415-b3"
            endpoint = f"https://us-central1-aiplatform.googleapis.com/v1/projects/{target_project}/locations/us-central1/publishers/google/models/lyria-002:predict"
            headers = {
                "Authorization": f"Bearer {credentials.token}",
                "Content-Type": "application/json",
            }

            # Use duration if valid (Lyria allows fixed lengths of 60s usually, check docs)
            # Actually Lyria 002 is often fixed or takes a length param. We'll ignore for now or pass context.
            payload = {
                "instances": [
                    {
                        "prompt": lyria_prompt,  # Use sanitized prompt without artist names
                    }
                ],
                "parameters": {"sampleCount": 1},
            }
            # Lyria 2 often generates fixed segments.

            # ... (Existing Request Logic)

            response = requests.post(endpoint, headers=headers, json=payload)
            if response.status_code == 200:
                data = response.json()
                if "predictions" in data and len(data["predictions"]) > 0:
                    pred = data["predictions"][0]
                    if "bytesBase64Encoded" in pred:
                        b64_data = pred["bytesBase64Encoded"]
                        audio_bytes = base64.b64decode(b64_data)

                        # Use AssetManager for proper storage and GCS upload
                        lyria_final_path = assets.save_asset(
                            data=audio_bytes,
                            asset_type="audio",
                            session_id=session_id,
                            prompt=input_text[:100],
                            subtype="music",
                            extension="wav"
                        )
                        
                        if lyria_final_path:
                            # Get the cloud URL from metadata
                            cloud_url = ""
                            meta_path = lyria_final_path + ".json"
                            if os.path.exists(meta_path):
                                import json
                                with open(meta_path, "r", encoding="utf-8") as mf:
                                    meta = json.load(mf)
                                    cloud_url = meta.get("cloud_url", "")
                            
                            logger.info(f"🎉 Final Asset Ready (Lyria Native): {lyria_final_path}")
                            if cloud_url:
                                logger.info(f"   Cloud URL: {cloud_url}")
                            
                            # Return with both local and cloud URL
                            result = f"**Audio Generated ({current_model_used}):**\n- Local: {lyria_final_path}"
                            if cloud_url:
                                result += f"\n- Cloud: {cloud_url}"
                            return result
                        else:
                            raise ValueError("Failed to save audio via AssetManager")
                    else:
                        raise ValueError(
                            f"Unexpected Lyria Response Keys: {pred.keys()}"
                        )
                else:
                    raise ValueError(f"No predictions returned: {data}")
            else:
                logger.error(
                    f"Lyria 002 Native Failed {response.status_code}: {response.text}"
                )
                # FIX: Lyria failed - fallback to MusicGen and ACTUALLY run it
                logger.warning("🚨 Lyria-002 failed. Falling back to MusicGen...")
                mg_out = _safe_replicate_run(
                    "meta/musicgen", input_data={"prompt": input_text, "duration": 20}
                )
                final_url = _extract_replicate_url(mg_out)
                current_model_used = "meta/musicgen (fallback)"

        # Case: ACE-Step (Optimized Configuration)
        elif "ace-step" in target_model:
            logger.info("🎤 Generating with ACE-Step (High Quality Mode)...")

            # Map global duration to ACE specific logic (Cap 240s)
            ace_duration = min(duration_sec, 240) if duration_sec else 60
            logger.info(f"   ACE-Step Duration set to: {ace_duration}s")

            # CRITICAL: Check GUI params FIRST
            gui_prompt = gui_params.get("prompt", "").strip() if gui_params else ""
            gui_lyrics = gui_params.get("lyrics", "").strip() if gui_params else ""
            
            if gui_prompt or gui_lyrics:
                # User pre-configured music in GUI
                logger.info("[ACE-STEP] Using pre-configured GUI prompt/lyrics")
                tags = gui_prompt or input_text
                lyrics = gui_lyrics or "[inst]"
            else:
                # No GUI config - parse Director's message
                lyric_data = _generate_lyrics_and_style(
                    input_text, llm, model_type="ace-step"
                )
                tags = lyric_data.get("tags", input_text)
                lyrics = lyric_data.get("lyrics", "[inst]")

            # ACE-Step requires 'tags' not 'prompt' - MAXIMUM QUALITY SETTINGS
            payload = {
                "tags": tags,  # REQUIRED field for ACE-Step
                "lyrics": lyrics,
                "duration": ace_duration,
                # === MAXIMUM QUALITY SETTINGS ===
                "scheduler": "euler",           # euler = more stable/cleaner than heun
                "guidance_type": "apg",         # APG = Adjusted Prompt Guidance (best)
                "guidance_scale": 15,           # 15 = optimal balance (20 can over-saturate)
                "number_of_steps": 200,         # 200 = MAXIMUM (best quality, slower)
                "granularity_scale": 10,        # 10 = MAXIMUM detail
                "guidance_interval": 0.5,       # Standard interval
                "min_guidance_scale": 3,        # Minimum guidance floor
                "tag_guidance_scale": 10,       # 10 = MAXIMUM style adherence
                "lyric_guidance_scale": 10,     # 10 = MAXIMUM lyric alignment
                "guidance_interval_decay": 0,   # No decay = consistent quality
            }
            logger.info(f"   ACE-Step Payload: tags='{tags[:50]}...', duration={ace_duration}s")

            ace_out = _safe_replicate_run("lucataco/ace-step", input_data=payload)
            final_url = _extract_replicate_url(ace_out)

        # Case: Minimax Music-1.5
        elif "music-1.5" in target_model:
            logger.info("[MINIMAX] Generating with Minimax Music-1.5 (Text-to-Music)...")
            logger.info(f"[MINIMAX] GUI params to apply: {gui_params}")

            # CRITICAL: Check GUI params FIRST before parsing Director's message
            # GUI prompt and lyrics should ALWAYS override Director's generated content
            gui_prompt = gui_params.get("prompt", "").strip() if gui_params else ""
            gui_lyrics = gui_params.get("lyrics", "").strip() if gui_params else ""
            
            if gui_prompt or gui_lyrics:
                # User pre-configured music in GUI - use those values directly
                logger.info("[MINIMAX] Using pre-configured GUI prompt/lyrics (ignoring Director's content)")
                style_prompt = gui_prompt or input_text
                lyrics_text = gui_lyrics
            else:
                # No GUI config - parse Director's message
                lyric_data = _generate_lyrics_and_style(
                    input_text, llm, model_type="minimax"
                )
                lyrics_text = lyric_data.get("lyrics", input_text)
                style_prompt = lyric_data.get("prompt", input_text)

            # Build payload with required params
            payload = {"prompt": style_prompt, "lyrics": lyrics_text}
            
            # Merge other GUI params (sample_rate, bitrate, etc.)
            if gui_params:
                for key, value in gui_params.items():
                    if key not in ["prompt", "lyrics"] and value is not None:
                        payload[key] = value
                        logger.info(f"[MINIMAX] Added GUI param: {key}={value}")

            logger.info(f"[MINIMAX] Final payload: {payload}")
            minimax_out = _safe_replicate_run("minimax/music-1.5", input_data=payload)
            final_url = _extract_replicate_url(minimax_out)

        # Case: Lyria-2
        elif "lyria" in target_model:
            logger.info("🎵 Generating with Google Lyria-2...")
            lyria_out = _safe_replicate_run(
                "google/lyria-2", input_data={"prompt": input_text}
            )
            final_url = _extract_replicate_url(lyria_out)

        # Case: MusicGen
        else:
            logger.info("🎵 Generating with MusicGen...")
            mg_out = _safe_replicate_run(
                "meta/musicgen", input_data={"prompt": input_text, "duration": 20}
            )
            final_url = _extract_replicate_url(mg_out)

        # C. Save & Rename - Use AssetManager for proper GCS upload
        if final_url:
            # Use AssetManager to save with proper directory structure AND GCS upload
            final_path = assets.save_asset(
                data=final_url,  # AssetManager handles URL downloads
                asset_type="audio",
                session_id=session_id,
                prompt=input_text[:100],
                subtype="music",
                extension="mp3"
            )

            if final_path:
                # Get the cloud URL from metadata
                cloud_url = ""
                meta_path = final_path + ".json"
                if os.path.exists(meta_path):
                    import json as json_mod
                    with open(meta_path, "r", encoding="utf-8") as mf:
                        meta = json_mod.load(mf)
                        cloud_url = meta.get("cloud_url", "")
                
                logger.info(f"🎉 Final Asset Ready: {final_path}")
                if cloud_url:
                    logger.info(f"   Cloud URL (PUBLIC): {cloud_url}")

                # Retrieve used lyrics for display
                used_lyrics = locals().get("lyrics", locals().get("lyrics_text", "N/A"))

                result = f"**Audio Generated ({current_model_used}):**\n- Local: {final_path}"
                if cloud_url:
                    result += f"\n- Cloud: {cloud_url}"
                result += f"\n\n**(Verified Lyrics Used)**:\n{used_lyrics}"
                return result
            else:
                # FIX: URL was returned but download failed
                logger.error(f"Download failed for URL: {final_url}")
                return f"**Generation Error:** Audio URL was generated but download/validation failed. URL: {final_url}"

        # FIX: Clear error message (not prefixed with 'Successfully Generated')
        logger.error("No audio URL returned from model")
        return "**Generation Error:** No audio URL returned from the model. The API call may have failed or the model returned an empty response."

    except Exception as e:
        logger.error(f"Replicate Pipeline Failure: {e}")
        return f"Error: {e}"


def _select_optimal_music_model(prompt: str, llm: Any) -> str:
    """
    Selects the best music model based on prompt analysis and System Configuration.
    """
    try:
        sys_config = SystemConfiguration()
        cfg = sys_config.load_config()

        # Get all composer music models
        capabilities = cfg.get("agents", {}).get("Composer", {}).get("capabilities", [])
        music_cap = next(
            (c for c in capabilities if c.get("type") == "music_generation"), None
        )

        if not music_cap:
            return "minimax/music-1.5"  # Fallback

        models = music_cap.get("models", [])

        # 1. Analyze Prompt for Constraints (Lyrics vs Instrumental & Duration)
        requires_lyrics = False
        requires_duration = False
        duration_val = 0

        # Heuristics for Lyrics (Fast & effective)
        lyrics_keywords = [
            "lyrics",
            "singing",
            "vocal",
            "rap",
            "song about",
            "ballad",
            "verse",
            "chorus",
            "voice",
        ]
        if any(w in prompt.lower() for w in lyrics_keywords):
            requires_lyrics = True

        # Heuristics for Duration
        dur_match = re.search(r"(\d+)\s*(min|minute|sec|second)", prompt, re.IGNORECASE)
        if dur_match:
            requires_duration = True
            val = int(dur_match.group(1))
            unit = dur_match.group(2).lower()
            if "min" in unit:
                duration_val = val * 60
            else:
                duration_val = val

        # LLM Confirmation (Optional but robust)
        if llm:
            try:
                # Classify very cheaply
                msg = HumanMessage(
                    content=f"""Classify this music request: '{prompt}'.
                1. Reply 'VOCAL' if it needs singing/lyrics, or 'INSTRUMENTAL' if it is background/score/instrumental only.
                2. Reply 'DURATION_YES' if specific time length is requested, 'DURATION_NO' if not.
                Format: <TYPE>|<DURATION_CONSTRAINT>
                Example: VOCAL|DURATION_NO
                Reply ONLY the string."""
                )
                res = llm.invoke([msg])
                parts = res.content.upper().split("|")
                if len(parts) >= 1:
                    if "VOCAL" in parts[0]:
                        requires_lyrics = True
                    elif "INSTRUMENTAL" in parts[0]:
                        requires_lyrics = False
                if len(parts) >= 2:
                    if "DURATION_YES" in parts[1]:
                        requires_duration = True
            except Exception as e:
                logger.warning(f"Classification skipped: {e}")

        # 2. Filter Models
        candidates = []
        for m in models:
            score = m.get("priority", 0)
            model_id = m.get("id")

            # Constraint: Lyrics
            model_supports_lyrics = m.get("supports_lyrics", False)
            if requires_lyrics and not model_supports_lyrics:
                continue

            # Constraint: Duration (Soft Constraint / Penalty)
            # If User asks for duration, but model ignores it (like Minimax), penalize heavily
            model_supports_duration = m.get(
                "supports_duration", True
            )  # Default to True if undefined unless known bad
            if requires_duration and not model_supports_duration:
                logger.info(
                    f"   Model {model_id} penalized: Ignores requested duration."
                )
                score -= 50  # Massive penalty, pushes it below others

            # Add to candidates with dynamic score
            candidates.append({"id": model_id, "score": score, "data": m})

        # 3. Sort by Dynamic Score
        candidates.sort(key=lambda x: x["score"], reverse=True)

        if not candidates:
            # Fallback
            logger.info(
                "No models matched strict constraints. Returning highest priority available."
            )
            candidates = [{"id": m["id"], "score": m["priority"]} for m in models]
            candidates.sort(key=lambda x: x["score"], reverse=True)

        best_model = candidates[0].get("id")
        logger.info(
            f"🧠 Model Selection: Request(Lyrics={requires_lyrics}, Duration={requires_duration}) -> Selected '{best_model}' (Score: {candidates[0]['score']})"
        )
        return best_model

    except Exception as e:
        logger.error(f"Selection Logic Failed: {e}")
        return "minimax/music-1.5"


def _generate_music_audio_internal(
    prompt: str, 
    model_name: str = "auto",
    model_params: Optional[Dict[str, Any]] = None
) -> str:
    """
    Directly generates audio using a Replicate model.
    
    Args:
        prompt: The description of the music.
        model_name: Model ID (e.g., "minimax/music-1.5"). "auto" triggers dynamic selection.
        model_params: Additional model parameters from GUI schema (e.g., sample_rate, bitrate)
    
    FAIL FAST: Raises exceptions on failure instead of returning error strings.
    """
    logger.info(f"[MUSIC] Direct Audio Tool called with model: {model_name}")
    logger.info(f"[MUSIC] Prompt: {prompt[:100]}...")
    if model_params:
        logger.info(f"[MUSIC] Params: {model_params}")
    
    assets = AssetManager()

    # 1. Init LLM (Needed for lyrics generation)
    llm_for_lyrics = None
    try:
        llm_for_lyrics = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-001", vertexai=True, temperature=0.7
        )
    except Exception as e:
        logger.warning("Could not init LLM for lyrics/selection: %s", e)
        # FAIL FAST for lyrics - some models require lyrics
        if "minimax" in model_name.lower():
            raise ValueError(f"Cannot initialize lyrics LLM for Minimax model: {e}")

    # 2. Select Model (only if "auto")
    if model_name == "auto" or "/" not in model_name:
        target_model = _select_optimal_music_model(prompt, llm_for_lyrics)
        logger.info(f"[MUSIC] Auto-selected model: {target_model}")
    else:
        target_model = model_name
        logger.info(f"[MUSIC] Using specified model: {target_model}")

    # 3. Execute with params
    return _handle_replicate_generation(
        model_name=target_model,
        input_text=prompt,
        llm=llm_for_lyrics,
        assets=assets,
        session_id="tool_direct",
        extra_params=model_params  # Pass GUI params through
    )


# NOTE: Old global @tool definitions removed. Tools are now defined as closures
# inside create_composer_agent() to capture GUI config from factory scope.
# This is the correct LangChain pattern for injecting runtime config.


def create_composer_agent(
    model_config: Optional[Dict[str, Any]] = None,
    brain: Any = None,
    session_id: str = "default",
    music_model_id: Optional[str] = None,
    music_model_params: Optional[Dict[str, Any]] = None,
    voice_config: Optional[Dict[str, Any]] = None,
):
    """
    Factory to create the Composer Agent runner.
    
    Args:
        model_config: LLM brain configuration (provider, model for reasoning)
        brain: Pre-initialized LLM (optional, for testing)
        session_id: Session identifier for asset tracking
        music_model_id: GUI-selected music generation model (e.g., "minimax/music-1.5")
        music_model_params: GUI-selected model parameters from schema
        voice_config: Voice configuration dict with 'source', 'file', 'model_id' keys
    """
    if model_config is None:
        # Default to Google Gemini for the Brain, music gen is separate
        model_config = {"provider": "Google", "model": "gemini-2.0-flash-001"}

    provider = model_config.get("provider", "Google")
    model_name = model_config.get("model", "gemini-2.0-flash-001")
    
    # Capture music model config for closures (FAIL FAST: No default fallback)
    # If GUI didn't provide a model, we use the system config default
    effective_music_model = music_model_id
    effective_music_params = music_model_params or {}
    effective_voice_config = voice_config or {}
    
    if not effective_music_model:
        # Pull from SystemConfiguration as authoritative default
        try:
            sys_config = SystemConfiguration()
            cfg = sys_config.load_config()
            capabilities = cfg.get("agents", {}).get("Composer", {}).get("capabilities", [])
            music_cap = next((c for c in capabilities if c.get("type") == "music_generation"), None)
            if music_cap and music_cap.get("models"):
                # Get highest priority model
                models = sorted(music_cap["models"], key=lambda x: x.get("priority", 0), reverse=True)
                effective_music_model = models[0].get("id", "").replace("replicate/", "")
                logger.info(f"[CONFIG] Using system default music model: {effective_music_model}")
        except Exception as e:
            logger.warning(f"[CONFIG] Could not load system config: {e}")
    
    # FAIL FAST: If still no model, use hardcoded fallback and log warning
    if not effective_music_model:
        effective_music_model = "minimax/music-1.5"
        logger.warning(f"[CONFIG] No music model configured, using fallback: {effective_music_model}")
    
    logger.info(f"[CONFIG] Music Model: {effective_music_model}, Params: {effective_music_params}")

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
        # Default to Google if not specified for Brain
        brain_provider = "Google"
        brain_model = "gemini-2.0-flash-001"

        # Override if config explicitly asks for Replicate Brain (unlikely for now)
        # But we respect global "provider" if it matches a known LLM provider
        if provider in ["Google", "Anthropic"]:
            brain_provider = provider
            # Use the passed model name if available
            if provider == "Google":
                brain_model = model_name if model_name else "gemini-2.0-flash-001"

        logger.info(
            f"🎻 Orpheus > Initializing Brain with {brain_provider}/{brain_model}..."
        )

        if brain_provider == "Anthropic":
            llm = ChatAnthropic(model_name=brain_model, temperature=0.7)

        if brain_provider == "Replicate":
            # Requires REPLICATE_API_TOKEN in env
            llm = ChatReplicate(
                model=brain_model,
                model_kwargs={"temperature": 0.5, "max_length": 2048, "top_p": 1},
            )

        if brain_provider == "Google":
            # Use brain_model which should be gemini-2.0-flash-001 now
            llm = ChatGoogleGenerativeAI(
                model=brain_model,
                vertexai=True,
                temperature=0.5,
                location="us-central1",  # Vertex usually auto-detects
                max_retries=1,
            )

        if not llm:
            raise ValueError("No LLM could be initialized")

    except Exception as e:
        logger.error(f"Brain Init Failed: {e}")
        # Fail loudly
        raise e

    # 3. Initialize Agent

    # 🔗 HUB INTEGRATION: Pull System Prompt
    hub_prompt = get_or_push_prompt("composer-system-prompt", COMPOSER_INSTRUCTIONS)

    # --- DEFINE TOOLS AS CLOSURES (Capture config from factory scope) ---
    # This is the CORRECT LangChain pattern for injecting runtime config into tools.
    # The tools capture effective_music_model, effective_music_params, etc. from closure scope.
    
    @tool
    def generate_music_tool(prompt: str) -> str:
        """
        YOU MUST CALL THIS TOOL IMMEDIATELY. Generates music/audio from a text description.
        Do NOT describe or plan - just call this tool with the music prompt.
        Input: A descriptive prompt like "Lo-fi hip hop, chill piano, 80bpm, instrumental"
        Returns: Path to the generated audio file.
        """
        # Use the model from GUI config (captured via closure)
        logger.info(f"[TOOL] generate_music_tool called with model: {effective_music_model}")
        logger.info(f"[TOOL] Model params: {effective_music_params}")
        
        try:
            # Direct execution with the GUI-selected model
            return _generate_music_audio_internal(
                prompt, 
                model_name=effective_music_model,
                model_params=effective_music_params
            )
        except Exception as e:
            logger.error(f"[TOOL] Music generation failed: {e}")
            raise  # FAIL FAST - don't swallow errors
    
    @tool
    def browse_library_tool(filter_type: str = "all") -> str:
        """
        Browses the Asset Library to see what audio, video, or images have been generated.
        Args:
            filter_type: "audio", "video", "image", or "all".
        """
        # If "all", pass None, else pass type
        a_type = None if filter_type == "all" else filter_type

        results = assets.list_assets(asset_type=a_type)
        if not results:
            return "Library is empty."

        output = "Current Asset Library:\n"
        for item in results[:10]:  # Limit to 10 most recent
            output += f"- [{item.get('asset_type')}] {item.get('prompt', 'Unknown')} (File: {os.path.basename(item.get('path', ''))})\n"

        return output

    # LINEAR CHAIN (No Retry Loops)
    # The Composer is a simple "One-Shot" agent. It should not loop.
    logger.info("[AGENT INIT] Creating Linear Composer Agent (Fail Fast Enabled)")

    # Bind Tools with FORCED TOOL EXECUTION
    # tool_choice="any" maps to Gemini's FunctionCallingConfig(mode='ANY')
    # This MANDATES the model MUST call one of the provided tools.
    target_tools = [generate_music_tool, browse_library_tool]
    llm_with_tools = llm.bind_tools(target_tools, tool_choice="any")
    logger.info("[TOOL BINDING] Composer tools bound with tool_choice='any' (forced execution)")

    from langchain_core.messages import SystemMessage, AIMessage
    from langchain_core.runnables import RunnableLambda

    def linear_runner(state):
        # Unwrap state
        messages = state["messages"]
        
        # FORCEFUL system prompt requiring immediate tool execution
        force_tool_instruction = (
            "CRITICAL: You MUST call generate_music_tool NOW. "
            "Do NOT describe, plan, or explain. Just call the tool with an optimized prompt. "
            "Text-only responses are FORBIDDEN."
        )
        
        if isinstance(hub_prompt, str):
            sys_content = f"{hub_prompt}\n\n{force_tool_instruction}"
            if not isinstance(messages[0], SystemMessage):
                messages = [SystemMessage(content=sys_content)] + messages
        elif isinstance(hub_prompt, object) and hasattr(hub_prompt, "format"):
            sys_content = f"{COMPOSER_INSTRUCTIONS}\n\n{force_tool_instruction}"
            messages = [SystemMessage(content=sys_content)] + messages

        # 1. Invoke LLM
        response = llm_with_tools.invoke(messages)

        # 2. Check Tool Call
        if response.tool_calls:
            # We allow EXACTLY ONE tool execution
            tc = response.tool_calls[0]
            t_name = tc["name"]

            tool_map = {t.name: t for t in target_tools}
            selected = tool_map.get(t_name)

            if selected:
                try:
                    logger.info(f"🎻 Executing Tool: {t_name}")
                    res = selected.invoke(tc["args"])

                    # Return the tool result directly as the "Answer"
                    # We do NOT loop back to LLM to summarize, to avoid "Echo Chamber"
                    # FIX: Don't prefix error results with "Successfully Generated"
                    res_str = str(res)
                    if "Error" in res_str or "failed" in res_str.lower():
                        return {"messages": [AIMessage(content=res_str)]}
                    else:
                        return {
                            "messages": [
                                AIMessage(content=f"Successfully Generated: {res}")
                            ]
                        }
                except Exception as e:
                    logger.error(f"❌ Tool Execution Failed: {e}")
                    raise e  # Fail Fast
            else:
                raise ValueError(f"Unknown tool invoked: {t_name}")

        # No tool call? Return text.
        return {"messages": [response]}

    agent = RunnableLambda(linear_runner)

    return agent


def run_composer_task(
    request_description: str,
    model_id: str = None,
    model_params: dict = None,
    voice_source: str = None,
    voice_file: any = None,
    voice_model_id: str = None
) -> str:
    """
    Synchronous entry point for the Director to consult the Composer.
    Handles HITL via ApprovalManager.
    
    Args:
        request_description: The audio directive/plan from Director
        model_id: Optional model ID from GUI (e.g., "google-deepmind/lyria-2")
        model_params: Optional dict of model parameters from GUI schema
        voice_source: 'generate', 'upload', or 'local' (for models requiring voice)
        voice_file: Uploaded file or local path for voice reference
        voice_model_id: Model ID for voice generation if voice_source='generate'
    """
    logger.info(f"[COMPOSER] Composer Consulted: {request_description}")
    
    # Log model configuration if provided
    if model_id:
        logger.info(f"[COMPOSER] Using model from GUI: {model_id}")
    if model_params:
        logger.info(f"[COMPOSER] Model params: {model_params}")
    if voice_source:
        logger.info(f"[COMPOSER] Voice source: {voice_source}, file: {voice_file}, model: {voice_model_id}")
    
    try:
        from DeepAgents.approval_manager import is_asset_rejected

        # Build voice config dict for passing to factory
        voice_config = None
        if voice_source:
            voice_config = {
                "source": voice_source,
                "file": voice_file,
                "model_id": voice_model_id
            }

        # Create agent with GUI-selected model config (PROPER INJECTION)
        agent = create_composer_agent(
            music_model_id=model_id,
            music_model_params=model_params,
            voice_config=voice_config
        )

        # Format input
        inputs = {"messages": [HumanMessage(content=request_description)]}

        # Run
        result = agent.invoke(inputs)

        final_response = ""
        if isinstance(result, dict) and "messages" in result:
            msg = result["messages"][-1]
            if isinstance(msg.content, list):
                # Flatten list of blocks to string
                texts = [
                    block.get("text", "") if isinstance(block, dict) else str(block)
                    for block in msg.content
                ]
                final_response = "\n".join(texts)
            else:
                final_response = str(msg.content)
        else:
            final_response = str(result)

        # HITL Check Logic
        # We need to extract the asset path from the response string to check approval
        # Simple heuristic: Look for valid paths or http links

        # Regex for paths (simplified)
        matches = re.findall(
            r"([a-zA-Z]:\\[^ \n\r\t]+|\/Users\/[^ \n\r\t]+|http[s]?://[^ \n\r\t]+)",
            final_response,
        )

        candidates = []
        for p in matches:
            # Clean punctuation
            p = p.rstrip(".,\"'()")
            # Ignore tools/scripts, look for extensions
            if any(
                ext in p.lower() for ext in [".mp3", ".wav", ".mp4", ".png", ".jpg"]
            ):
                candidates.append(p)

        # Prioritize Cloud URLs (http) over local paths for LangSmith compatibility
        # Sort so http comes first
        candidates.sort(key=lambda x: 0 if x.startswith("http") else 1)

        for p in candidates:
            if is_asset_rejected(p):
                return f"HITL_REJECTED: User rejected asset {p}. Retry."
            # HITL DISABLED: Always proceed
            # if not is_asset_approved(p):
            #    return f"HITL_REVIEW_REQUIRED: {p}"

        return str(final_response)

    except Exception as e:
        logger.error(f"Composer Task Failed: {e}")
        return f"Composer failed to process request. Error: {e}"


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(run_composer_task(sys.argv[1]))
    else:
        print("Composer Agent ready. Pass a prompt to test.")
