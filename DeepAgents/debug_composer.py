from DeepAgents.CommercialAgents.composer_agent.agent import generate_music_audio
import logging

# Configure logging to show everything
logging.basicConfig(level=logging.DEBUG)

print("Testing Composer generation...")
try:
    # Use the same parameters the user asked for
    # "manually craft a song in the style of Oasis with the lyrics 'Hello World'"
    # generate_music_audio is a Tool, so we invoke it
    result = generate_music_audio.invoke({"prompt": "Song in the style of Oasis with lyrics 'Hello World'", "model_name": "minimax/music-01"})
    print("\nRESULT:")
    print(result)
except Exception as e:
    print("\nCRASHED:")
    print(e)
