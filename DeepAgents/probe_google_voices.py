from dotenv import load_dotenv
from google.cloud import texttospeech

load_dotenv("DeepAgents/.env")


def list_voices():
    try:
        client = texttospeech.TextToSpeechClient()
        response = client.list_voices()

        print(f"Total Voices Available: {len(response.voices)}")

        # Categorize
        gemini = []
        journey = []
        neural2 = []
        wavenet = []
        studio = []

        for voice in response.voices:
            name = voice.name
            if "gemini" in name.lower():
                gemini.append(voice)
            elif "journey" in name.lower():
                journey.append(voice)
            elif "neural2" in name.lower():
                neural2.append(voice)
            elif "wavenet" in name.lower():
                wavenet.append(voice)
            elif "studio" in name.lower():
                studio.append(voice)

        print("\n--- Summary ---")
        print(f"Gemini Voices: {len(gemini)}")
        print(f"Journey Voices: {len(journey)}")
        print(f"Neural2 Voices: {len(neural2)}")
        print(f"Studio Voices: {len(studio)}")
        print(f"WaveNet Voices: {len(wavenet)}")

        print("\n--- Sample of Journey/Gemini/Studio (Likely High Quality) ---")
        for v in journey + gemini + studio[:5]:
            print(
                f"Name: {v.name}, Gender: {v.ssml_gender.name}, Lang: {v.language_codes[0]}"
            )

    except Exception as e:
        print(f"Error listing voices: {e}")


if __name__ == "__main__":
    list_voices()
