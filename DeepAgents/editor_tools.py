# pylint: disable=broad-exception-caught
# pylint: disable=import-error
"""
Editor Tools Module.
Responsible for merging video and audio assets using moviepy.
"""

import os
import logging
import uuid
from typing import List

try:
    from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips

    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    VideoFileClip = None
    AudioFileClip = None
    concatenate_videoclips = None
    logging.warning("MoviePy not installed. Editor tools will run in Simulation Mode.")

from langchain.tools import tool
from DeepAgents.asset_manager import AssetManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EditorTools")


@tool
def merge_video_audio(
    video_paths: List[str], audio_path: str, output_name: str = "final_cut.mp4"
) -> str:
    """
    Merges multiple video clips and an audio track into a single video file.
    Args:
        video_paths: List of absolute paths to video files.
        audio_path: Absolute path to the audio file.
        output_name: Name of the output file.
    Returns:
        Absolute path to the final video.
    """
    logger.info(
        "✂️ Editor > Merging %d clips with audio %s...", len(video_paths), audio_path
    )

    # 1. Validation (Simulated for safety if files are text mocks)
    real_files = True
    if not MOVIEPY_AVAILABLE:
        real_files = False

    for p in video_paths + [audio_path]:
        if not os.path.exists(p):
            return f"Error: File not found {p}"
        # Check if they are mock text files from simulation
        if p.endswith(".txt"):
            real_files = False
        # Robust check: peek at file content to see if it's a simulation text file masquerading as media
        try:
            with open(p, "rb") as f:
                header = f.read(1024)
                # Check for common text signatures or our specific [SIMULATED] tags
                # A real MP4/WAV is binary. If we find our text tag or mostly printable ascii, it's fake.
                try:
                    text_preview = header.decode("utf-8")
                    if (
                        "[FINAL VIDEO SIMULATION]" in text_preview
                        or "[SIMULATED]" in text_preview
                        or "[AUDIO]" in text_preview
                        or "[VISUAL PANEL]" in text_preview
                    ):
                        real_files = False
                except UnicodeDecodeError:
                    # If it's not valid utf-8, it's likely real binary media
                    pass
        except Exception:
            pass  # Ignore read errors, assume it might be real

    if not real_files:
        logging.info(
            "ℹ️ Simulation Mode triggered by missing MoviePy or detected mock assets."
        )
        # Mock Merge
        assets = AssetManager()
        content = f"[FINAL VIDEO SIMULATION]\nVideo Sources: {video_paths}\nAudio Source: {audio_path}\n(Merged by EditorTool)\n(Simulation Mode Active)"
        path = assets.save_asset(content, "video", "final_cut", "Merged Video")
        if path is None:
            return "Error: Failed to save simulation asset."
        logger.info("✅ Simulation Merge Complete: %s", path)
        return path

    try:
        # 2. MoviePy Logic
        # Assertions to satisfy static analysis (objects are not None if we reached here)
        assert VideoFileClip is not None
        assert concatenate_videoclips is not None
        assert AudioFileClip is not None

        clips = []
        for v_path in video_paths:
            clips.append(VideoFileClip(v_path))

        final_video = concatenate_videoclips(clips, method="compose")

        if os.path.exists(audio_path):
            audio = AudioFileClip(audio_path)
            # Loop audio if shorter, crop if longer, or just set it
            # For this simple tool, we set it and trim video to match or vice versa?
            # Let's trim audio to video length
            audio = audio.set_duration(final_video.duration)  # type: ignore
            final_video = final_video.set_audio(audio)  # type: ignore

        assets = AssetManager()
        # We need to save to a temp path first or direct to asset dir?
        # Let's output to a temp file then move or just return path
        output_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../generated_videos")
        )
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        final_path = os.path.join(output_dir, f"{uuid.uuid4()}_{output_name}")

        final_video.write_videofile(
            final_path, codec="libx264", audio_codec="aac", fps=24, logger=None
        )
        logger.info("✅ Render Complete: %s", final_path)
        return final_path

    except Exception as e:
        logger.error(
            "Merge failed with MoviePy: %s. Falling back to Simulation Merge.", e
        )
        # Fallback to Simulation Merge
        assets = AssetManager()
        content = f"[FINAL VIDEO SIMULATION - FALLBACK]\nReason: MoviePy Failure ({e})\nVideo Sources: {video_paths}\nAudio Source: {audio_path}\n"
        path = assets.save_asset(
            content, "video", "final_cut_fallback", "Merged Video (Fallback)"
        )
        if path is None:
            return "Error: Failed to save fallback asset."
        logger.info("✅ Fallback Simulation Merge Complete: %s", path)
        return path


@tool
def generate_storyboard_panel(description: str, filename: str) -> str:
    """
    Generates a visual asset (StoryBoard Panel) for the video.
    Returns the absolute path to the generated asset.
    """
    logger.info("🎨 Generative Artist > Creating panel: %s...", filename)
    assets = AssetManager()
    # Create a mock video file (text) or empty mp4 if moviepy was here
    # We use text file to simulate the asset for the 'Mock Merge' to handle
    content = f"[VISUAL PANEL]\nDescription: {description}\n(Generated by Lumiere/StoryBoard Tool)"
    path = assets.save_asset(content, "video", filename, description)
    if path is None:
        return f"Error: Failed to save asset {filename}"
    return path


# Expose tool
merge_tool = merge_video_audio
generate_visual_tool = generate_storyboard_panel
