
import replicate
from dotenv import load_dotenv

load_dotenv("DeepAgents/.env")

def test_xtts():
    print("Testing XTTS...")
    try:
        # Generic XTTS
        model = "lucataco/xtts-v2:684bc3855b37866c9c65add2ff39c78f3dea3f4ff30305807d637e5b3950b719"
        output = replicate.run(
            model,
            input={
                "text": "Hello, this is a test of the emergency broadcast system.",
                "speaker": "Ana Florence" # Trying a common preset
            }
        )
        print(f"Success: {output}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_xtts()
