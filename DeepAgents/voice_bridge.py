# pylint: disable=broad-exception-caught
# pylint: disable=import-outside-toplevel
"""
Voice Bridge (Log Watcher).
Watches 'DeepAgents/voice_log.txt' for new lines and speaks them using Edge-TTS.
Also listens for 'Hey Copilot' to trigger interruptions (Conceptual Implementation).
"""
import os
import sys
import time
import asyncio
import logging
import subprocess
import threading

# Add Repo Root to Path to ensure 'DeepAgents' package resolves
# Current: DeepAgents/voice_bridge.py -> Parent: DeepAgents -> Root: ../
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Replicate Import
try:
    import replicate
    REPLICATE_AVAILABLE = True
except ImportError:
    REPLICATE_AVAILABLE = False

try:
    import static_ffmpeg # type: ignore
    static_ffmpeg.add_paths()
except ImportError:
    pass

# Handle local vs package imports
try:
    from DeepAgents.atlas_db import add_command, init_db
except ImportError:
    try:
         # Fallback for side-by-side
        from atlas_db import add_command, init_db
    except ImportError as e:
        logging.error(f"Failed to import atlas_db: {e}")
        sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VoiceBridge")

LOG_FILE = os.path.join(os.path.dirname(__file__), "voice_log.txt")

def input_loop():
    """Runs in a separate thread to capture user input."""
    init_db()
    print("🎤 Voice Bridge Interactive Mode Active.")
    print("   Type a message and press ENTER to inject it into the running Agent (Atlas).")
    print("   (Type 'exit' to quit voice bridge)")
    
    while True:
        try:
            user_input = input(">> ")
            if user_input.lower() in ["exit", "quit"]:
                logger.info("Exiting Input Loop...")
                os._exit(0) # Force exit main process
                
            if user_input.strip():
                add_command(user_input)
                logger.info("💉 Injected User Command (Atlas DB): %s", user_input)
                
        except (EOFError, KeyboardInterrupt):
            break

async def speak_text(text: str):
    """
    Speaks text using primary cloud provider (Replicate) or fallback (EdgeTTS).
    
    User Request: Minimax/Speech-02-Turbo.
    Status: Not publicly available on Replicate. 
    Substitution: lucataco/xtts-v2 (Fast, High Quality).
    """
    
    # 1. Try Replicate (XTTS-v2 as Minimax Proxy)
    if REPLICATE_AVAILABLE and os.getenv("REPLICATE_API_TOKEN"):
        try:
            logger.info("🗣️ Replicate Speaking: %s", text[:50])
            
            # Locate local voice file
            # Path: Artifacts/Audio/Voices/male_deep_narrator_ref.wav relative to root
            voice_path = os.path.join(os.path.dirname(__file__), "..", "Artifacts", "Audio", "Voices", "male_deep_narrator_ref.wav")
            
            if os.path.exists(voice_path):
                speaker_input = open(voice_path, "rb")
            else:
                # Fallback to URL if local file missing
                logger.warning(f"Voice file not found at {voice_path}. Using fallback URL.")
                speaker_input = "https://replicate.delivery/pbxt/Jt79w0xsT6GCR01c0fK8/male.wav"

            # Using XTTS-v2 which is faster/better than Bark
            output = replicate.run(
                "lucataco/xtts-v2:684bc3855b37866c0c65add2ff39c78f3dea3f4ff103a436465326e0f438d55e",
                input={
                    "text": text,
                    "speaker": speaker_input,
                    "language": "en",
                    "cleanup_voice": True,
                    "temperature": 0.75
                }
            )
            
            # Output is a URL
            audio_url = output

            
            # Streaming play via ffplay
            if audio_url:
                 subprocess.run(
                    ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(audio_url)],
                    check=True
                 )
                 return # Success
                 
        except Exception as e:
            logger.warning(f"Replicate TTS Failed ({e}). Falling back to EdgeTTS.")

    # 2. Fallback to Edge TTS
    try:
        # Lazy import
        import edge_tts # type: ignore
        communicate = edge_tts.Communicate(text, "en-US-ChristopherNeural")
        await communicate.save("temp_voice.mp3")
        
        # Play audio (headless via ffplay)
        # -nodisp: No graphical window
        # -autoexit: Close after playing
        # -loglevel quiet: Don't spam console
        try:
            subprocess.run(
                ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", "temp_voice.mp3"],
                check=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to current method if ffplay fails
            if os.name == 'nt':
                os.system("start /min /wait temp_voice.mp3")
            else:
                os.system("afplay temp_voice.mp3")
            
        logger.info("🗣️ Spoke: %s", text)
        time.sleep(1) # Debounce
        
        if os.path.exists("temp_voice.mp3"):
            os.remove("temp_voice.mp3")
            
    except ImportError:
        logger.error("❌ edge-tts not installed. Run: pip install edge-tts")
        print(f"FAILED TO SPEAK: {text}")
    except Exception as e:
        logger.error("TTS Error: %s", e)

async def watch_log():
    """Watches the log file for new lines."""
    # CLEAR LOG ON STARTUP (User Requirement)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("") # Wipe it clean
    logger.info("🧹 Wiped previous voice logs.")
    logger.info("👂 Watching for voice updates in: %s", LOG_FILE)
            
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        # Move to end (in case anything was written in the microsecond between wipe and read)
        f.seek(0, os.SEEK_END)
        
        while True:
            line = f.readline()
            if line:
                clean_line = line.strip()
                if clean_line:
                    await speak_text(clean_line)
            else:
                await asyncio.sleep(1)

if __name__ == "__main__":
    print("--- DEEPAGENTS VOICE BRIDGE (SPEAKER ONLY) ---")
    print("1. Monitors 'DeepAgents/voice_log.txt'")
    print("2. Speaks updates via Edge-TTS")
    print("----------------------------------------------")
    
    # NOTE: Input is now handled via DeepAgents/run_atlas.py in the main console.
    # We no longer need the input thread here.
    
    try:
        asyncio.run(watch_log())
    except KeyboardInterrupt:
        print("Stopping Voice Bridge.")
