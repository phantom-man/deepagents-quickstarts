"""
Voice Library Generator.

This script pre-generates a comprehensive set of reference voice files using the
Replicate API (Suno AI Bark). These references are used by the Composer/Singer agents
to steer generation (Minimax/Lyria) without needing real-time voice synthesis every time.
"""

import os
import time
import logging
from pathlib import Path
from typing import Dict, Any
import requests
from dotenv import load_dotenv

# Optional Replicate import with error handling
try:
    import replicate
except ImportError:
    replicate = None

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Silence noisy libraries
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

logger = logging.getLogger("VoiceLibraryGen")

def _setup_environment() -> bool:
    """Loads environment variables and verifies API tokens."""
    # Resolve .env path relative to this script
    script_dir = Path(__file__).resolve().parent
    env_path = script_dir.parent / '.env'

    if env_path.exists():
        load_dotenv(env_path)
    else:
        # Fallback to local .env if script moved
        load_dotenv(script_dir / '.env')

    if not os.getenv("REPLICATE_API_TOKEN"):
        logger.error("❌ REPLICATE_API_TOKEN not found in environment.")
        return False

    return True

def _get_voice_definitions() -> Dict[str, str]:
    """Returns the dictionary of voice types and their generation prompts."""
    # Comprehensive list covering ranges (Soprano->Bass) and styles (Pop->Narrator)
    return {
        # --- Female Voices ---
        "female_soprano_classical": "WOMAN, SOPRANO, CLASSICAL, OPERA, HIGH PITCH, CLEAR VOCALS",
        "female_pop_bright": "WOMAN, POP, BRIGHT, UPBEAT, YOUTHFUL, ENERGY, HIGH QUALITY",
        "female_mezzo_jazz": "WOMAN, JAZZ, SMOKEY, MEZZO-SOPRANO, SOULFUL, BLUES, WARM",
        "female_rock_grit": "WOMAN, ROCK, POWERFUL, GRITTY, BELTING, INTENSE, LOUD",
        "female_alto_narrator": "WOMAN, ALTO, DEEP, CALM, NARRATION, AUDIOBOOK, TRUSTWORTHY",
        "female_whisper_ethereal": "WOMAN, WHISPER, ETHEREAL, AMBIENT, SOFT, BREATHY, MYSTERIOUS",

        # --- Male Voices ---
        "male_countertenor_pop": "MAN, COUNTERTENOR, HIGH PITCH, POP, FALSETTO, SMOOTH, RNB",
        "male_tenor_rock": "MAN, TENOR, ROCK, AGGRESSIVE, ENERGETIC, PUNCHY, GUITAR",
        "male_baritone_jazz": "MAN, BARITONE, JAZZ, CROONER, SMOOTH, VINTAGE, SWING",
        "male_bass_epic": "MAN, BASS, DEEP, EPIC, TRAILER, MOVIE, RESONANT, LOW",
        "male_narrator_clear": "MAN, NARRATOR, BROADCAST, NEWS, CLEAR, ARTICULATE, PROFESSIONAL",
        "male_rap_flow": "MAN, RAP, HIPHOP, RHYTHMIC, FLOW, LYRICAL, BEAT",

        # --- Experimental/Choir ---
        "choir_mixed_gospel": "CHOIR, GOSPEL, MIXED GROUP, HARMONY, UPLIFTING, SOUL",
        "voice_robot_future": "ROBOT, CYBORG, AUTOTUNE, FUTURISTIC, SCI-FI, SYNTHETIC"
    }

def _download_file(url: str, dest_path: Path):
    """Downloads content from URL to path."""
    try:
        # Set a reasonable timeout to prevent hanging
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logger.info("   ✅ Saved to %s", dest_path.name)

    except requests.exceptions.RequestException as e:
        logger.error("   ❌ Download failed: %s", e)
    except IOError as e:
        logger.error("   ❌ File IO error: %s", e)

def _retrieve_result_url(output: Any) -> str | None:
    """Extracts the audio URL from the prediction output."""
    url = None
    if isinstance(output, dict) and "audio_out" in output:
        url = output["audio_out"]
    elif isinstance(output, str):
        url = output
    return str(url) if url else None

def _process_prediction(name: str, pred: Any, output_dir: Path) -> bool:
    """Checks status of a prediction and handles completion. Returns True if done."""
    pred.reload()
    if pred.status == "succeeded":
        logger.info("✅ Job %s SUCCEEDED", name)
        url = _retrieve_result_url(pred.output)
        if url:
            file_path = output_dir / f"{name}.wav"
            _download_file(url, file_path)
        return True

    if pred.status == "failed":
        logger.error("❌ Job %s FAILED: %s", name, pred.error)
        return True

    if pred.status == "canceled":
        logger.warning("🚫 Job %s CANCELED", name)
        return True

    return False

def generate_voice_library():
    """Main execution loop for generating the library."""
    if not _setup_environment():
        return

    if not replicate:
        logger.error("❌ Replicate SDK is not installed. Run: pip install replicate")
        return

    # Define Output Directory: Artifacts/Audio/Voices
    script_dir = Path(__file__).resolve().parent
    output_dir = script_dir.parent / "Artifacts" / "Audio" / "Voices"

    # Ensure directory exists
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info("📂 Output Directory Verified: %s", output_dir)
    except OSError as e:
        logger.error("❌ Failed to create directory %s: %s", output_dir, e)
        return

    voices = _get_voice_definitions()
    logger.info("🚀 Starting PARALLEL generation for %d voice types...", len(voices))

    # Version object to use
    model = replicate.models.get("suno-ai/bark")
    # Pylance fix: Explicitly cast or assert valid version
    version = model.latest_version
    if not version:
        logger.error("❌ Could not determine latest version for suno-ai/bark")
        return

    # Store active predictions
    predictions = {}

    for name, prompt_desc in voices.items():
        file_path = output_dir / f"{name}.wav"
        if file_path.exists():
            logger.info("⏭️  Skipping %s (File exists)", name)
            continue

        logger.info("📨 Submitting job for %s...", name)

        text_prompt = (
            f"Hello, I am a generated reference voice for the {name.replace('_', ' ')} style. "
            "I am speaking clearly."
        )

        try:
            # Use predictions.create to run async
            pred = replicate.predictions.create(
                version=version,
                input={
                    "prompt": f"{prompt_desc}. {text_prompt}",
                    "text_temp": 0.7
                }
            )
            predictions[name] = pred
        # pylint: disable=broad-exception-caught
        except Exception as e:
            logger.error("❌ Failed to submit %s: %s", name, e)

    # Poll Results
    logger.info("⏳ Waiting for %d jobs to complete...", len(predictions))

    while predictions:
        done_list = []
        for name, pred in predictions.items():
            if _process_prediction(name, pred, output_dir):
                done_list.append(name)

        # Remove finished
        for name in done_list:
            del predictions[name]

        if predictions:
            time.sleep(5)  # Poll interval

    logger.info("🎉 All jobs processed.")

if __name__ == "__main__":
    generate_voice_library()
