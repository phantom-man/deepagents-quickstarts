"""
Meeting Rendering Module.
This module synthesizes audio from a transcript and merges it into a single file.
"""

import os
import json
import logging
import subprocess
import static_ffmpeg  # type: ignore # Import static_ffmpeg to ensure binary availability
from google.cloud import texttospeech
from pydub import AudioSegment # type: ignore
from dotenv import load_dotenv

# Ensure ffmpeg paths are added
static_ffmpeg.add_paths()

load_dotenv("DeepAgents/.env")

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RenderMeeting")

TRANSCRIPT_FILE = "DeepAgents/round_table_1_transcript.json"
OUTPUT_DIR = "DeepAgents/generated_videos"
FINAL_AUDIO_FILE = "DeepAgents/generated_videos/round_table_1_full.wav"

def check_ffmpeg():
    """Checks if ffmpeg is available."""
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False

def synthesize_text(text: str, voice_name: str, output_path: str):
    """Synthesizes text to audio using Google Cloud TTS."""
    client = texttospeech.TextToSpeechClient()

    # Parse voice name e.g. "en-US-Studio-M"
    lang_code = "-".join(voice_name.split("-")[:2]) # "en-US"

    input_text = texttospeech.SynthesisInput(text=text)

    # Note: Studio voices and Neural2 require specific configuration
    voice = texttospeech.VoiceSelectionParams(
        language_code=lang_code,
        name=voice_name
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16, # WAV
        speaking_rate=1.0
    )

    try:
        response = client.synthesize_speech(
            input=input_text, voice=voice, audio_config=audio_config
        )
        with open(output_path, "wb") as out:
            out.write(response.audio_content)
        logger.info("Generated: %s", output_path)
        return True
    # pylint: disable=broad-exception-caught
    except Exception as e:
        logger.error("Failed to synthesize '%s...': %s", text[:20], e)
        return False

def merge_audio(audio_segments, output_path):
    """Merges audio segments into a single file."""
    if not check_ffmpeg():
        logger.warning("⚠️ FFmpeg not found! Cannot merge.")
        logger.info("Individual .wav files are available in the output directory.")
        return

    logger.info("Merging audio segments...")
    try:
        combined = AudioSegment.empty()
        for seg_path in audio_segments:
            segment = AudioSegment.from_wav(seg_path)
            combined += segment
            combined += AudioSegment.silent(duration=500)

        combined.export(output_path, format="wav")
        logger.info("✅ Full meeting audio saved to: %s", output_path)
    # pylint: disable=broad-exception-caught
    except Exception as e:
        logger.error("Failed to merge audio: %s", e)

def render_meeting(transcript_path: str = TRANSCRIPT_FILE, output_path: str = FINAL_AUDIO_FILE):
    """Main rendering function."""
    if not os.path.exists(transcript_path):
        logger.error("Transcript file not found: %s", transcript_path)
        return

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript = json.load(f)

    audio_segments = []

    logger.info("🎙️ Starting Synthesis...")

    for i, turn in enumerate(transcript):
        speaker = turn.get("speaker", "Unknown")
        text = turn.get("text", "")
        voice = turn.get("voice_choice") or turn.get("choice")

        if not voice:
             # Fallback default if still None
            voice = "en-US-Neural2-A"

        if not voice or not text:
            logger.warning("Skipping turn %d: Missing voice or text.", i)
            continue

        filename = f"segment_{i:03d}_{speaker}_{voice}.wav"
        filepath = os.path.join(OUTPUT_DIR, filename)

        # Synthesize
        if synthesize_text(text, voice, filepath):
            audio_segments.append(filepath)
        else:
            logger.warning("Skipping failed segment %d", i)

    logger.info("✅ Synthesis complete. Generated %d segments.", len(audio_segments))

    merge_audio(audio_segments, output_path)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Render meeting transcript to audio.")
    parser.add_argument("--input", default=TRANSCRIPT_FILE, help="Path to input transcript JSON")
    parser.add_argument("--output", default=FINAL_AUDIO_FILE, help="Path to output WAV file")

    args = parser.parse_args()

    render_meeting(args.input, args.output)
