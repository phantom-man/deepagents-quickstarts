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



def download_if_url(path_or_url: str) -> str:
    """Downloads a file if it is a URL, otherwise returns the path.
    Supports both regular HTTP URLs and Google Cloud Storage URLs (authenticated).
    """
    if not path_or_url.startswith("http"):
        return path_or_url
    
    temp_dir = os.path.join(os.path.dirname(__file__), "../Artifacts/Temp")
    os.makedirs(temp_dir, exist_ok=True)
    
    filename = os.path.basename(path_or_url.split("?")[0]) # Handle query params
    # Ensure extension
    if "." not in filename:
        filename += ".tmp"
        
    local_path = os.path.join(temp_dir, filename)
    
    # Check if already downloaded
    if os.path.exists(local_path):
        return local_path
    
    # Check if this is a GCS URL - use authenticated download
    if "storage.googleapis.com" in path_or_url or "storage.cloud.google.com" in path_or_url:
        logger.info(f"[DOWNLOAD] GCS authenticated download: {path_or_url}")
        try:
            from google.cloud import storage
            from urllib.parse import urlparse
            
            # Parse the GCS URL to extract bucket and blob
            parsed = urlparse(path_or_url)
            
            # Format: storage.googleapis.com/bucket-name/path/to/file
            # OR: storage.cloud.google.com/bucket-name/path/to/file
            path_parts = parsed.path.lstrip("/").split("/", 1)
            if len(path_parts) < 2:
                raise ValueError(f"Invalid GCS URL format: {path_or_url}")
            
            bucket_name = path_parts[0]
            blob_name = path_parts[1]
            
            client = storage.Client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            
            blob.download_to_filename(local_path)
            logger.info(f"[SUCCESS] GCS download complete: {local_path}")
            return local_path
            
        except ImportError:
            logger.error("[FAILED] google-cloud-storage not installed for GCS download")
            raise
        except Exception as e:
            logger.error(f"[FAILED] GCS download error: {e}")
            raise
    
    # Standard HTTP download for non-GCS URLs
    import requests
    logger.info(f"[DOWNLOAD] HTTP download: {path_or_url}")
    try:
        response = requests.get(path_or_url, stream=True)
        response.raise_for_status()
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192): 
                f.write(chunk)
        return local_path
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return path_or_url # Return original if fail, logic will catch non-existence later

def merge_video_audio_logic(
    video_paths: List[str], audio_path: str, output_name: str = "final_cut.mp4"
) -> str:
    """
    Logic for merging video and audio.
    """
    logger.info(
        "[EDITOR] Merging %d clips with audio %s...", len(video_paths), audio_path
    )

    # 0. Download Assets if URLs
    video_paths = [download_if_url(p) for p in video_paths]
    audio_path = download_if_url(audio_path)

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
            "[INFO] Simulation Mode triggered by missing MoviePy or detected mock assets."
        )
        # Mock Merge
        assets = AssetManager()
        content = f"[FINAL VIDEO SIMULATION]\nVideo Sources: {video_paths}\nAudio Source: {audio_path}\n(Merged by EditorTool)\n(Simulation Mode Active)"
        path = assets.save_asset(content, "video", "final_cut", "Merged Video")
        if path is None:
            return "Error: Failed to save simulation asset."
        logger.info("[SUCCESS] Simulation Merge Complete: %s", path)
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
            os.path.join(os.path.dirname(__file__), "../Artifacts/Video")
        )
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        final_path = os.path.join(output_dir, output_name)
        final_video.write_videofile(final_path, codec="libx264", audio_codec="aac")
        
        return final_path
        
    except Exception as e:
        logger.error("Merge Failed: %s", e)
        return f"Error during merge: {e}"


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
    return merge_video_audio_logic(video_paths, audio_path, output_name)


@tool
def generate_storyboard_panel(description: str, filename: str) -> str:
    """
    Generates a visual asset (StoryBoard Panel) for the video.
    Returns the absolute path to the generated asset.
    """
    logger.info("[ARTIST] Creating panel: %s...", filename)
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
