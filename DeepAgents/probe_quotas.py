import logging
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

# Setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger("QuotaProbe")
load_dotenv("DeepAgents/.env")

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = "us-central1"


def probe_model_quota(model_id, prompt, type="text"):
    logger.info(f"--- Probing {model_id} ({type}) ---")
    try:
        client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
        start = time.time()

        if type == "text":
            client.models.generate_content(model=model_id, contents=prompt)
        elif type == "image":
            client.models.generate_images(
                model=model_id,
                prompt=prompt,
                config=types.GenerateImagesConfig(number_of_images=1),
            )

        logger.info(f"✅ {model_id}: SUCCESS ({time.time() - start:.2f}s)")
        return True

    except Exception as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            logger.error(f"❌ {model_id}: QUOTA EXCEEDED (429)")
        else:
            logger.error(f"❌ {model_id}: FAILED ({e})")
        return False


if __name__ == "__main__":
    logger.info("⚡ RAPID QUOTA PROBE INITIATED ⚡")

    # Text Models to Probe (Based on actual available list)
    text_models = [
        "gemini-2.0-flash-001",  # Likely Stable candidate
        "gemini-2.5-flash",  # Next gen candidate
        "gemini-3-flash-preview",  # Bleeding edge - check quota
    ]

    # We will test the first working one with a stress test
    for m in text_models:
        probe_model_quota(m, "Hello.")
        time.sleep(1)

    # Stress Test the Winner (Likely 2.0 Flash)
    STRESS_MODEL = "gemini-2.0-flash-001"
    logger.info(f"--- Stress Testing {STRESS_MODEL} (5 reqs in loop) ---")
    for i in range(5):
        try:
            probe_model_quota(STRESS_MODEL, f"Quick check {i}")
        except Exception as e:
            logger.error(f"Stress test failed at {i}: {e}")
            break

    # 2. Image Models (Imagen Family)
    image_models = ["imagen-3.0-generate-002", "imagen-4.0-fast-generate-001"]

    for m in image_models:
        probe_model_quota(m, "A red apple", type="image")
        time.sleep(1)
