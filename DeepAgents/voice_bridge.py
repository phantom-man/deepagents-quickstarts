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
# import speech_recognition as sr # Requires PyAudio/PocketSphinx, tricky on some envs.
# from edge_tts import Communicate # Creating async wrapper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VoiceBridge")

LOG_FILE = os.path.join(os.path.dirname(__file__), "voice_log.txt")

async def speak_text(text: str):
    """Speaks text using Edge TTS (free, high quality)."""
    try:
        # Lazy import
        import edge_tts
        communicate = edge_tts.Communicate(text, "en-US-ChristopherNeural")
        await communicate.save("temp_voice.mp3")
        
        # Play audio (platform specific)
        if os.name == 'nt':
            os.system("start /min /wait temp_voice.mp3") # Windows
        else:
            os.system("afplay temp_voice.mp3") # Mac
            
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
    logger.info("👂 Watching for voice updates in: %s", LOG_FILE)
    
    # Ensure file exists
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("Voice Bridge Started.\n")
            
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        # Move to end
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
    print("--- DEEPAGENTS VOICE BRIDGE ---")
    print("1. Monitors 'DeepAgents/voice_log.txt'")
    print("2. Speaks updates via Edge-TTS")
    print("-------------------------------")
    try:
        asyncio.run(watch_log())
    except KeyboardInterrupt:
        print("Stopping Voice Bridge.")
