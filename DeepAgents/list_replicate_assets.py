import logging
import os
import sys

from dotenv import load_dotenv

sys.path.append(os.getcwd())
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ReplicateHistory")

try:
    import replicate
except ImportError:
    print("replicate not installed.")
    sys.exit(1)


def main():
    token = os.getenv("REPLICATE_API_TOKEN")
    if not token:
        print("REPLICATE_API_TOKEN missing.")
        return

    print("🔎 Fetching Replicate History (Last 50)...")
    try:
        # Use replicate.predictions.list()
        # This returns an iterator or list of Prediction objects
        predictions = replicate.predictions.list()

        count = 0
        limit = 50

        for pred in predictions:
            count += 1
            if count > limit:
                break

            model = pred.model
            status = pred.status
            created_at = pred.created_at

            # Identify output
            output = pred.output
            output_url = None
            if isinstance(output, str) and output.startswith("http"):
                output_url = output
            elif isinstance(output, (list, tuple)) and len(output) > 0:
                output_url = output[0]
            elif isinstance(output, dict) and "url" in output:
                output_url = output["url"]
            elif output is not None and hasattr(output, "url"):
                output_url = getattr(output, "url", None)

            if output_url:
                print(
                    f"[{created_at}] {status} | Model: {model} | Output: {output_url}"
                )
            else:
                pass
                # print(f"[{created_at}] {status} | Model: {model} | No Output/URL")

    except Exception as e:
        print(f"Error fetching history: {e}")


if __name__ == "__main__":
    main()
