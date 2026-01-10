# pylint: disable=broad-exception-caught
# pylint: disable=import-outside-toplevel
"""
Voice Bridge (Log Watcher).
Watches 'DeepAgents/voice_log.txt' for new lines and speaks them using Edge-TTS.
Also listens for 'Hey Copilot' to trigger interruptions (Conceptual Implementation).
"""
import os
import time
import asyncio
import logging
import subprocess

try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
except ImportError:
    pass

import sys
import threading

# Add current dir to path to import atlas_db
sys.path.append(os.path.dirname(__file__))
try:
    from atlas_db import add_command, init_db
except ImportError:
    # Fallback if running from root
    from DeepAgents.atlas_db import add_command, init_db

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
    """Speaks text using Edge TTS (free, high quality)."""
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
