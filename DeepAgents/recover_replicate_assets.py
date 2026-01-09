# pylint: disable=broad-exception-caught
"""
Utility script to recover assets from Replicate history.
"""
import os
import replicate
import requests
from dotenv import load_dotenv

# Load env from DeepAgents/.env
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)


def download_asset(url, asset_id, output_dir):
    """Refactored download logic to reduce nesting."""
    print(f"   ⬇️ Downloading: {url}")
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        ext = "mp3"
        if url.endswith(".wav"):
            ext = "wav"

        filename = f"{asset_id}.{ext}"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "wb") as f:
            f.write(r.content)
        print(f"   💾 Saved to {filepath}")
        return True
    except Exception as e:
        print(f"   ❌ Download failed: {e}")
        return False


def recover_assets(model_filter=""):
    """
    Recover assets from Replicate predictions history.
    Args:
        model_filter: Optional string to filter model versions.
    """
    print("🔍 Searching Replicate history (ALL)...")

    try:
        # List predictions (default is latest 100)
        predictions = replicate.predictions.list()

        found_count = 0
        restored_count = 0

        output_dir = os.path.join(os.path.dirname(__file__), "recovered_assets")
        os.makedirs(output_dir, exist_ok=True)

        for pred in predictions:
            # Filter by model name roughly
            version_str = str(pred.version) if pred.version else ""

            if model_filter in version_str and pred.status == "succeeded":
                # Check if output looks like audio
                audio_url = None

                if pred.output:
                    if isinstance(pred.output, dict):
                        audio_url = pred.output.get("audio") or pred.output.get(
                            "audio_file"
                        )
                    elif isinstance(pred.output, str):
                        if pred.output.endswith((".mp3", ".wav")):
                            audio_url = pred.output

                if audio_url:
                    found_count += 1
                    print(f"✅ Found Audio Asset {pred.id} ({pred.created_at})")
                    if download_asset(audio_url, pred.id, output_dir):
                        restored_count += 1

        print("\n--- Recovery Complete ---")
        print(f"Found: {found_count}")
        print(f"Restored: {restored_count}")
        print(f"Location: {output_dir}")

    except Exception as e:
        print(f"❌ Error recovering assets: {e}")


if __name__ == "__main__":
    recover_assets()
