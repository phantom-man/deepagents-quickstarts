# pylint: disable=broad-exception-caught
# pylint: disable=invalid-name
"""
Cinematographer Agent (VeoAgent).
Responsible for generating video and storyboard assets using Google Vertex AI (Veo + Imagen).
NOTE: Veo usage is currently DISABLED due to cost constraints ($0.75/s). Defers to SVD.
"""

import os
import sys
import time
import argparse
import uuid
import logging
from dotenv import load_dotenv

# from google import genai # Disabled for now to prevent accidental usage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

try:
    from agent_brain import AgentMemory, AgentComms
except ImportError:
    from DeepAgents.agent_brain import AgentMemory, AgentComms

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Cinematographer")

# Initialize Brain Components
print("🎥 Connecting to Nervous System...")
try:
    memory = AgentMemory()
    comms = AgentComms(password="d1204l0723")
    if not comms.connect():
        print("❌ Failed to connect to Nervous System (Postgres)")
        sys.exit(1)
except Exception as e:
    print(f"❌ Brain Connection Failed: {e}")
    sys.exit(1)


def load_canonical_ontology(role_name):
    """Loads the ontology file to refresh agent context."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "Canon", f"{role_name}_Ontology.md")
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            print(f"✅ {role_name} Ontology Refreshed ({len(content)} chars)")
            return content
    except FileNotFoundError:
        print(f"⚠️ Warning: Ontology for {role_name} not found at {path}")
        return ""


# Refresh Context
cinematographer_canon = load_canonical_ontology("Cinematographer")


def refine_prompt_with_thinking(raw_prompt):
    """Uses a Reasoning Model to refine the prompt based on the Cinematographer Ontology."""
    print("🧠 Cinematographer is thinking... (Refining Prompt)")

    # Switched to VertexAI/ADC and accessible model (Gemini 3 Pro)
    llm = ChatGoogleGenerativeAI(
        model="gemini-3-pro-preview",
        temperature=0.7,
        project=os.getenv("GOOGLE_CLOUD_PROJECT"),
        location=os.getenv("GOOGLE_CLOUD_LOCATION")
    )

    system_prompt = f"""You are the **Cinematographer Agent**.
    Your goal is to translate a raw concept into a perfect prompt for the Google Veo Video Generation Model.

    **YOUR BRAIN (ONTOLOGY):**
    {cinematographer_canon}
    
    **TASK:**
    1. Analyze the user's request: "{raw_prompt}"
    2. Consult your Ontology regarding Lighting, Composition, Camera Movement, and Atmosphere.
    3. Output ONLY the optimized prompt for Veo. Do not include explanations.
    """

    response = llm.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=raw_prompt)]
    )
    # Ensure content is string to avoid type errors
    content = response.content
    if isinstance(content, list):
        content = " ".join([str(x) for x in content])
    optimized_prompt = str(content).strip()
    print(f"✨ Optimized Prompt: {optimized_prompt}")
    return optimized_prompt


# Initialize Google Gen AI Client for Vertex AI
# Uses Application Default Credentials (ADC) from gcloud auth
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = "us-central1"  # Veo is available in us-central1

if not PROJECT_ID:
    print("Error: GOOGLE_CLOUD_PROJECT not found in .env")
    sys.exit(1)

print(f"Initializing Vertex AI Client for project: {PROJECT_ID}")
# client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION) # Disabled
client = None

def generate_video(model_name, prompt, output_file="output_video.mp4"):
    """Generates a video using the specified model."""
    print(f"\n--- Generating Video with {model_name} ---")

    if model_name == "veo":
        logger.error("❌ Veo generation is currently DISABLED due to cost constraints.")
        logger.info("Please use Stable Video Diffusion (SVD) instead.")
        return None

    print(f"Prompt: {prompt}")
    print("Waiting for generation (this may take a minute)...")

    try:
        # Generate content
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config={"response_mime_type": "video/mp4"},
        )

        # Check if we got a valid response
        # The structure of response might vary depending on the model/backend
        if (
            response.candidates
            and response.candidates[0].content
            and response.candidates[0].content.parts
        ):
            part = response.candidates[0].content.parts[0]

            if part.inline_data and part.inline_data.data:
                with open(output_file, "wb") as f:
                    f.write(part.inline_data.data)
                print(f"✅ Video saved to {output_file}")
                return True

            # Sometimes the video is a URI if it's large or on Vertex
            print(f"⚠️ Response received. Part: {part}")
        else:
            print("⚠️ Response received but no content parts found.")

    except Exception as e:
        print(f"❌ Error generating video: {e}")
        return False
    return False


def generate_storyboard(prompt, output_file):
    """Generates a storyboard image using Imagen 3."""
    print("\n--- Generating Storyboard with imagen-3.0-generate-001 ---")
    print(f"Prompt: {prompt}")

    try:
        response = client.models.generate_images(
            model="imagen-3.0-generate-001",
            prompt=prompt,
            config={"aspect_ratio": "16:9"},
        )

        if response.generated_images:
            gen_img = response.generated_images[0]
            # Handle different SDK versions for Image object

            # 1. Try Google GenAI SDK v1 pattern (img.image.image_bytes)
            if hasattr(gen_img, "image") and gen_img.image is not None:
                img_obj = gen_img.image
                if hasattr(img_obj, "image_bytes"):
                    with open(output_file, "wb") as f:
                        f.write(img_obj.image_bytes)  # type: ignore
                    print(f"✅ Storyboard saved to {output_file}")
                    return True
                if hasattr(img_obj, "save"):
                    img_obj.save(output_file)  # type: ignore
                    print(f"✅ Storyboard saved to {output_file}")
                    return True

            # 2. Try direct image_bytes (older or alternative SDK)
            if hasattr(gen_img, "image_bytes"):
                with open(output_file, "wb") as f:
                    f.write(gen_img.image_bytes)  # type: ignore
                print(f"✅ Storyboard saved to {output_file}")
                return True

            print(f"⚠️ Image object structure unknown: {dir(gen_img)}")
            return False

        print("⚠️ No images returned.")

    except Exception as e:
        print(f"❌ Storyboard Generation Failed: {e}")
        return False
    return False


def run_cinematographer_loop(mode="full"):
    """Main loop for the Cinematographer Agent."""
    print(f"\n🎥 --- CINEMATOGRAPHER AGENT STANDING BY (Mode: {mode.upper()}) ---")
    print("Waiting for orders from Director...")

    # Ensure assets directory exists
    assets_dir = os.path.join(os.path.dirname(__file__), "../Artifacts/Audio")
    os.makedirs(assets_dir, exist_ok=True)

    while True:
        # Check for messages
        try:
            # Replaced check_inbox with receive_messages
            messages = comms.receive_messages(recipient="Cinematographer")
        except Exception as e:
            print(f"Connection error: {e}, retrying...")
            time.sleep(5)
            continue

        if messages:
            for msg in messages:
                print(f"\n📩 Message Received from {msg['sender']}:")
                print(f"📄 Content: {msg['content'][:100]}...")

                # 1. Refine the prompt
                refined_prompt = refine_prompt_with_thinking(msg["content"])

                # Unique ID for this job
                job_id = str(uuid.uuid4())[:8]
                report_lines = []

                # 2. Generate Storyboard (Always if mode is storyboard or full)
                if mode in ["storyboard", "full"]:
                    sb_filename = f"storyboard_{job_id}.png"
                    sb_path = os.path.join(assets_dir, sb_filename)
                    if generate_storyboard(refined_prompt, sb_path):
                        report_lines.append(f"Storyboard created: {sb_filename}")
                        # Store in Memory
                        memory.memorize(
                            f"Created Storyboard for '{msg['content']}'",
                            "Cinematographer",
                            tags=["asset", "storyboard", sb_path],
                        )
                    else:
                        report_lines.append("Storyboard generation failed.")

                # 3. Generate Video (Only if mode is full)
                if mode == "full":
                    vid_filename = f"video_{job_id}.mp4"
                    vid_path = os.path.join(assets_dir, vid_filename)
                    if generate_video("veo-2.0-generate-001", refined_prompt, vid_path):
                        report_lines.append(f"Video created: {vid_filename}")
                        # Store in Memory
                        memory.memorize(
                            f"Created Video for '{msg['content']}'",
                            "Cinematographer",
                            tags=["asset", "video", vid_path],
                        )
                    else:
                        report_lines.append("Video generation failed.")
                elif mode == "storyboard":
                    report_lines.append(
                        "Video generation skipped (Mode: Storyboard Only)."
                    )

                # 4. Report back
                final_report = " | ".join(report_lines)
                comms.send_message(
                    sender="Cinematographer", recipient="Director", content=final_report
                )
                print(f"✅ Report sent to Director: {final_report}")

        else:
            time.sleep(5)  # Poll every 5 seconds


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cinematographer Agent")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["storyboard", "full"],
        default="storyboard",
        help="Operation mode: 'storyboard' (images only) or 'full' (images + video)",
    )
    args_parsed = parser.parse_args()

    run_cinematographer_loop(mode=args_parsed.mode)
