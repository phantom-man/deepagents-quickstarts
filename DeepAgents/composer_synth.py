"""
Meta AudioCraft (MusicGen) Wrapper.
Generates music from text descriptions using the MusicGen model.
Adheres to "The Jewel Standard" (Pylint 10/10).
"""

import argparse
import logging
import sys
from langsmith import traceable

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ComposerSynth")

@traceable(run_type="tool", name="MusicGen Generation")
def generate_music(prompt: str, duration: int = 15, output_path: str = "output.wav"):
    """
    Generates music using Meta's MusicGen model.
    Note: Requires 'audiocraft' and 'torch' installed.
    
    Args:
        prompt (str): Text description of the music.
        duration (int): Duration in seconds.
        output_path (str): File path to save the .wav file.
    """
    try:
        # pylint: disable=import-outside-toplevel
        from audiocraft.models import MusicGen # type: ignore
        from audiocraft.data.audio import audio_write # type: ignore
    except ImportError:
        logger.error("❌ 'audiocraft' library not found.")
        logger.info("Please install: pip install git+https://github.com/facebookresearch/audiocraft.git") # pylint: disable=line-too-long
        sys.exit(1)

    logger.info("🎵 initializing MusicGen (small)... this may take a moment.")
    try:
        model = MusicGen.get_pretrained('facebook/musicgen-small')
        model.set_generation_params(duration=duration)

        logger.info("Generating: '%s' (%ds)", prompt, duration)
        wav = model.generate([prompt])  # generates 3 samples.

        # AudioWrite expects a tensor, here we just take the first one
        # Removing '.wav' extension if present because audio_write adds it
        save_path = output_path
        if save_path.endswith(".wav"):
            save_path = save_path[:-4]

        audio_write(save_path, wav[0].cpu(), model.sample_rate, strategy="loudness")
        logger.info("✅ Saved to: %s.wav", save_path)

    except Exception as e: # pylint: disable=broad-exception-caught
        logger.error("Failed to generate music: %s", e)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate music with Meta AudioCraft.")
    parser.add_argument("prompt", help="Text description of the music.")
    parser.add_argument("--duration", type=int, default=15, help="Duration in seconds.")
    parser.add_argument("--output", default="generated_music.wav", help="Output filename.")

    args = parser.parse_args()

    generate_music(args.prompt, args.duration, args.output)
