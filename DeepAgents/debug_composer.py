import logging

# Note: generate_music_audio may not exist as a direct import
# This is a debug script that may need updating
try:
    from DeepAgents.CommercialAgents.composer_agent.agent import create_composer_agent
    HAS_COMPOSER = True
except ImportError:
    HAS_COMPOSER = False

# Configure logging to show everything
logging.basicConfig(level=logging.DEBUG)

print("Testing Composer generation...")
if not HAS_COMPOSER:
    print("Composer agent not available - create_composer_agent not found")
else:
    try:
        # Use the same parameters the user asked for
        # "manually craft a song in the style of Oasis with the lyrics 'Hello World'"
        composer = create_composer_agent()
        print("Composer agent created successfully")
        print("\nRESULT:")
        print("Agent ready for invocation")
    except Exception as e:
        print("\nCRASHED:")
        print(e)
