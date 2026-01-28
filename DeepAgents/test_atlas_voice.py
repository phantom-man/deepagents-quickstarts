import os
import time

VOICE_LOG_PATH = os.path.join(os.path.dirname(__file__), "voice_log.txt")


def speak(text):
    print(f"Writing to log: {text}")
    with open(VOICE_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{text}\n")


if __name__ == "__main__":
    print("--- ATLAS AUDIO TEST ---")
    print(f"Target: {VOICE_LOG_PATH}")

    messages = [
        "System Check Initiated.",
        "Atlas Voice Bridge is verified.",
        "I am ready to operate.",
    ]

    for msg in messages:
        speak(msg)
        time.sleep(3)  # Give time to speak
