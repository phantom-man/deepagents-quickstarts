import os
import logging
from gtts import gTTS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AssetGenerator")

# Target Directory
VOICE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../Artifacts/Audio/Voices"))
os.makedirs(VOICE_DIR, exist_ok=True)

# Generate 5 Distinct "Vocal" References
SAMPLES = [
    {"name": "female_en_us.mp3", "text": "This is a reference voice for a female pop singer. Soaring high notes.", "lang": "en", "tld": "us"},
    {"name": "male_en_uk.mp3", "text": "This is a reference voice for a male british rock singer. Deep and raspy.", "lang": "en", "tld": "co.uk"},
    {"name": "female_fr.mp3", "text": "Ceci est une voix de référence pour une chanteuse de jazz doux.", "lang": "fr", "tld": "fr"},
    {"name": "male_es.mp3", "text": "Esta es una voz de referencia para un cantante latino apasionado.", "lang": "es", "tld": "es"},
    {"name": "female_ja.mp3", "text": "これは女性のポップシンガーの参考音声です。", "lang": "ja", "tld": "co.jp"},
]

def generate_voice(data):
    path = os.path.join(VOICE_DIR, data["name"])
    if os.path.exists(path):
        logger.info(f"✅ Exists: {data['name']}")
        return
        
    logger.info(f"🎤 Generating: {data['name']}...")
    try:
        tts = gTTS(text=data["text"], lang=data["lang"], tld=data.get("tld", "com"))
        tts.save(path)
        logger.info(f"✅ Saved: {path}")
    except Exception as e:
         logger.error(f"❌ Failed {data['name']}: {e}")

def main():
    print(f"--- Generating Voice Assets to {VOICE_DIR} ---")
    for s in SAMPLES:
        generate_voice(s)
    print("--- Asset Generation Complete ---")

if __name__ == "__main__":
    main()
