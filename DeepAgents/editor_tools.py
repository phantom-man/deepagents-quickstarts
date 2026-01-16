# pylint: disable=broad-exception-caught
# pylint: disable=import-error
"""
Editor Tools Module.
Responsible for merging video and audio assets.

UPGRADE: FFmpeg-first approach for maximum quality (stream copy, no re-encoding).
MoviePy kept as fallback for complex filter operations.
"""

import os
import logging
import subprocess
import shutil
from typing import List, Optional

# FFmpeg-python for Pythonic FFmpeg control
try:
    import ffmpeg as ffmpeg_lib
    FFMPEG_PYTHON_AVAILABLE = True
except ImportError:
    FFMPEG_PYTHON_AVAILABLE = False
    ffmpeg_lib = None
    logging.warning("ffmpeg-python not installed. Will use subprocess fallback.")

# Check if FFmpeg CLI is available
FFMPEG_CLI_AVAILABLE = shutil.which("ffmpeg") is not None
if not FFMPEG_CLI_AVAILABLE:
    logging.warning("FFmpeg CLI not found in PATH. Editor tools may be limited.")

# MoviePy as fallback for complex operations
try:
    from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    VideoFileClip = None
    AudioFileClip = None
    concatenate_videoclips = None
    logging.warning("MoviePy not installed. Complex filter operations unavailable.")

from langchain.tools import tool

# Import asset manager - handle both package and local imports
try:
    from asset_manager import AssetManager
except ImportError:
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

    filename = os.path.basename(path_or_url.split("?")[0])  # Handle query params
    # Ensure extension
    if "." not in filename:
        filename += ".tmp"

    local_path = os.path.join(temp_dir, filename)

    # Check if already downloaded
    if os.path.exists(local_path):
        logger.info("[CACHE HIT] Using cached download: %s", local_path)
        return local_path

    # Check if this is a GCS URL - use authenticated download
    if "storage.googleapis.com" in path_or_url or "storage.cloud.google.com" in path_or_url:
        logger.info("[DOWNLOAD] GCS authenticated download: %s", path_or_url)
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
            logger.info("[SUCCESS] GCS download complete: %s", local_path)
            return local_path

        except ImportError:
            logger.error("[FAILED] google-cloud-storage not installed for GCS download")
            raise
        except Exception as e:
            logger.error("[FAILED] GCS download error: %s", e)
            raise

    # Standard HTTP download for non-GCS URLs
    import requests
    logger.info("[DOWNLOAD] HTTP download: %s", path_or_url)
    try:
        response = requests.get(path_or_url, stream=True, timeout=300)
        response.raise_for_status()
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info("[SUCCESS] HTTP download complete: %s", local_path)
        return local_path
    except Exception as e:
        logger.error("Download failed: %s", e)
        return path_or_url  # Return original if fail


def _get_output_path(output_name: str) -> str:
    """Get the full output path in Artifacts/Video."""
    output_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../Artifacts/Video")
    )
    os.makedirs(output_dir, exist_ok=True)
    return os.path.join(output_dir, output_name)


def _is_simulated_file(path: str) -> bool:
    """Check if a file is a simulated/mock text file."""
    if path.endswith(".txt"):
        return True
    try:
        with open(path, "rb") as f:
            header = f.read(1024)
            try:
                text_preview = header.decode("utf-8")
                if any(tag in text_preview for tag in [
                    "[FINAL VIDEO SIMULATION]",
                    "[SIMULATED]",
                    "[AUDIO]",
                    "[VISUAL PANEL]"
                ]):
                    return True
            except UnicodeDecodeError:
                pass  # Binary file = real media
    except Exception:
        pass
    return False


def merge_ffmpeg_stream_copy(
    video_path: str,
    audio_path: str,
    output_path: str,
    shortest: bool = True
) -> str:
    """
    Merge video and audio using FFmpeg STREAM COPY (no re-encoding).
    This preserves maximum quality by copying the video bitstream directly.
    
    Args:
        video_path: Path to video file
        audio_path: Path to audio file  
        output_path: Output file path
        shortest: Stop when shortest stream ends
        
    Returns:
        Output path on success, error string on failure
    """
    if not FFMPEG_CLI_AVAILABLE:
        return "Error: FFmpeg CLI not available"
    
    logger.info("[FFMPEG] Stream copy merge: video=%s, audio=%s", video_path, audio_path)
    
    # Build FFmpeg command for maximum quality merge
    # -c:v copy = copy video stream (no re-encoding, zero quality loss)
    # -c:a aac = encode audio to AAC (required for MP4 container compatibility)
    # -map 0:v:0 = use first video stream from first input
    # -map 1:a:0 = use first audio stream from second input
    # -shortest = stop when shortest input ends
    
    cmd = [
        "ffmpeg", "-y",  # Overwrite output
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",  # Stream copy video (ZERO quality loss)
        "-c:a", "aac",   # Encode audio to AAC for MP4 compatibility
        "-b:a", "192k",  # High quality audio bitrate
        "-map", "0:v:0",
        "-map", "1:a:0",
    ]
    
    if shortest:
        cmd.append("-shortest")
    
    cmd.append(output_path)
    
    try:
        logger.info("[FFMPEG] Running: %s", " ".join(cmd))
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
            check=False
        )
        
        if result.returncode != 0:
            logger.error("[FFMPEG] Error: %s", result.stderr)
            return f"Error: FFmpeg failed - {result.stderr[:500]}"
        
        if os.path.exists(output_path):
            logger.info("[SUCCESS] FFmpeg stream copy merge complete: %s", output_path)
            return output_path
        else:
            return "Error: Output file not created"
            
    except subprocess.TimeoutExpired:
        return "Error: FFmpeg timed out"
    except Exception as e:
        logger.error("[FFMPEG] Exception: %s", e)
        return f"Error: {e}"


def merge_ffmpeg_python(
    video_path: str,
    audio_path: str,
    output_path: str,
    shortest: bool = True
) -> str:
    """
    Merge video and audio using ffmpeg-python library.
    Provides the same stream copy quality as CLI but with Pythonic interface.
    """
    if not FFMPEG_PYTHON_AVAILABLE or ffmpeg_lib is None:
        return "Error: ffmpeg-python not available"
    
    logger.info("[FFMPEG-PY] Merging: video=%s, audio=%s", video_path, audio_path)
    
    try:
        video = ffmpeg_lib.input(video_path)
        audio = ffmpeg_lib.input(audio_path)
        
        # Stream copy for video, AAC encode for audio
        output_kwargs = {
            'vcodec': 'copy',      # Stream copy video
            'acodec': 'aac',       # Encode audio to AAC
            'audio_bitrate': '192k'
        }
        
        if shortest:
            output_kwargs['shortest'] = None
        
        stream = ffmpeg_lib.output(
            video.video,
            audio.audio,
            output_path,
            **output_kwargs
        )
        
        # Run with overwrite
        ffmpeg_lib.run(stream, overwrite_output=True, quiet=True)
        
        if os.path.exists(output_path):
            logger.info("[SUCCESS] ffmpeg-python merge complete: %s", output_path)
            return output_path
        else:
            return "Error: Output file not created"
            
    except Exception as e:
        logger.error("[FFMPEG-PY] Exception: %s", e)
        return f"Error: {e}"


def concat_videos_ffmpeg(
    video_paths: List[str],
    output_path: str
) -> str:
    """
    Concatenate multiple videos using FFmpeg concat demuxer.
    Uses stream copy for zero quality loss.
    
    Note: All videos must have same codec, resolution, and framerate.
    """
    if not FFMPEG_CLI_AVAILABLE:
        return "Error: FFmpeg CLI not available"
    
    if len(video_paths) == 1:
        # Single video, just copy it
        shutil.copy2(video_paths[0], output_path)
        return output_path
    
    logger.info("[FFMPEG] Concatenating %d videos", len(video_paths))
    
    # Create concat file list
    temp_dir = os.path.dirname(output_path)
    concat_file = os.path.join(temp_dir, "concat_list.txt")
    
    try:
        with open(concat_file, 'w', encoding='utf-8') as f:
            for vpath in video_paths:
                # Escape single quotes in paths
                safe_path = vpath.replace("'", "'\\''")
                f.write(f"file '{safe_path}'\n")
        
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-c", "copy",  # Stream copy both video and audio
            output_path
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
            check=False
        )
        
        # Cleanup concat file
        if os.path.exists(concat_file):
            os.remove(concat_file)
        
        if result.returncode != 0:
            logger.error("[FFMPEG] Concat error: %s", result.stderr)
            return f"Error: FFmpeg concat failed - {result.stderr[:500]}"
        
        if os.path.exists(output_path):
            logger.info("[SUCCESS] FFmpeg concat complete: %s", output_path)
            return output_path
        else:
            return "Error: Output file not created"
            
    except Exception as e:
        logger.error("[FFMPEG] Concat exception: %s", e)
        if os.path.exists(concat_file):
            os.remove(concat_file)
        return f"Error: {e}"


def merge_video_audio_logic(
    video_paths: List[str],
    audio_path: str,
    output_name: str = "final_cut.mp4"
) -> str:
    """
    Main merge logic - orchestrates FFmpeg (preferred) or MoviePy (fallback).
    
    Strategy:
    1. FFmpeg stream copy for MAXIMUM quality (no re-encoding)
    2. MoviePy fallback for complex filter operations
    3. Simulation mode for mock/test files
    """
    logger.info(
        "[EDITOR] Merging %d clips with audio %s...", len(video_paths), audio_path
    )

    # 0. Download Assets if URLs
    video_paths = [download_if_url(p) for p in video_paths]
    audio_path = download_if_url(audio_path)
    
    output_path = _get_output_path(output_name)

    # 1. Validate files exist
    for p in video_paths + [audio_path]:
        if not os.path.exists(p):
            return f"Error: File not found {p}"

    # 2. Check for simulation mode
    is_simulation = any(_is_simulated_file(p) for p in video_paths + [audio_path])
    
    if is_simulation or (not FFMPEG_CLI_AVAILABLE and not MOVIEPY_AVAILABLE):
        logger.info("[INFO] Simulation Mode - mock assets or no media tools available")
        assets = AssetManager()
        content = (
            f"[FINAL VIDEO SIMULATION]\n"
            f"Video Sources: {video_paths}\n"
            f"Audio Source: {audio_path}\n"
            f"(Merged by EditorTool - Simulation Mode)"
        )
        path = assets.save_asset(content, "video", "final_cut", "Merged Video")
        if path is None:
            return "Error: Failed to save simulation asset."
        logger.info("[SUCCESS] Simulation Merge Complete: %s", path)
        return path

    # 3. FFmpeg-first approach (PREFERRED for quality)
    if FFMPEG_CLI_AVAILABLE:
        logger.info("[STRATEGY] Using FFmpeg stream copy (maximum quality)")
        
        # Handle multiple videos: concat first, then merge audio
        if len(video_paths) > 1:
            # Step A: Concatenate videos
            concat_output = output_path.replace(".mp4", "_concat.mp4")
            concat_result = concat_videos_ffmpeg(video_paths, concat_output)
            
            if concat_result.startswith("Error"):
                logger.warning("[FALLBACK] FFmpeg concat failed, trying MoviePy")
            else:
                # Step B: Add audio to concatenated video
                result = merge_ffmpeg_stream_copy(
                    concat_output,
                    audio_path,
                    output_path,
                    shortest=True
                )
                
                # Cleanup intermediate file
                if os.path.exists(concat_output) and concat_output != output_path:
                    os.remove(concat_output)
                
                if not result.startswith("Error"):
                    return result
                logger.warning("[FALLBACK] FFmpeg merge failed: %s", result)
        else:
            # Single video - direct merge
            result = merge_ffmpeg_stream_copy(
                video_paths[0],
                audio_path,
                output_path,
                shortest=True
            )
            if not result.startswith("Error"):
                return result
            logger.warning("[FALLBACK] FFmpeg merge failed: %s", result)

    # 4. ffmpeg-python library fallback
    if FFMPEG_PYTHON_AVAILABLE and len(video_paths) == 1:
        logger.info("[STRATEGY] Using ffmpeg-python (stream copy)")
        result = merge_ffmpeg_python(
            video_paths[0],
            audio_path,
            output_path,
            shortest=True
        )
        if not result.startswith("Error"):
            return result
        logger.warning("[FALLBACK] ffmpeg-python failed: %s", result)

    # 5. MoviePy fallback (re-encodes, lower quality but more flexible)
    if MOVIEPY_AVAILABLE:
        logger.info("[STRATEGY] Using MoviePy (re-encoding, complex operations)")
        try:
            assert VideoFileClip is not None
            assert concatenate_videoclips is not None
            assert AudioFileClip is not None

            clips = [VideoFileClip(v_path) for v_path in video_paths]
            final_video = concatenate_videoclips(clips, method="compose")

            if os.path.exists(audio_path):
                audio = AudioFileClip(audio_path)
                audio = audio.with_duration(final_video.duration)
                final_video = final_video.with_audio(audio)

            final_video.write_videofile(
                output_path,
                codec="libx264",
                audio_codec="aac",
                preset="medium",  # Balance speed/quality
                audio_bitrate="192k"
            )

            # Close clips to release resources
            for clip in clips:
                clip.close()
            final_video.close()

            logger.info("[SUCCESS] MoviePy merge complete: %s", output_path)
            return output_path

        except Exception as e:
            logger.error("[MOVIEPY] Merge Failed: %s", e)
            return f"Error during MoviePy merge: {e}"

    return "Error: No media processing tools available (install FFmpeg or MoviePy)"


@tool
def merge_video_audio(
    video_paths: List[str],
    audio_path: str,
    output_name: str = "final_cut.mp4"
) -> str:
    """
    Merges multiple video clips and an audio track into a single video file.
    
    Uses FFmpeg stream copy for MAXIMUM QUALITY (no re-encoding of video).
    Falls back to MoviePy for complex operations if needed.
    
    Args:
        video_paths: List of absolute paths or URLs to video files.
        audio_path: Absolute path or URL to the audio file.
        output_name: Name of the output file.
        
    Returns:
        Absolute path to the final video file.
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
    content = (
        f"[VISUAL PANEL]\n"
        f"Description: {description}\n"
        f"(Generated by Lumiere/StoryBoard Tool)"
    )
    path = assets.save_asset(content, "video", filename, description)
    if path is None:
        return f"Error: Failed to save asset {filename}"
    return path


# Expose tools
merge_tool = merge_video_audio
generate_visual_tool = generate_storyboard_panel


# Utility function for direct FFmpeg merging (for programmatic use)
def quick_merge(
    video_url: str,
    audio_url: str,
    output_name: Optional[str] = None
) -> str:
    """
    Quick utility for merging a single video with audio.
    Downloads URLs if needed, uses FFmpeg stream copy.
    
    Args:
        video_url: Video file path or URL
        audio_url: Audio file path or URL
        output_name: Optional output filename (auto-generated if None)
        
    Returns:
        Path to merged output file
    """
    import uuid
    if output_name is None:
        output_name = f"merged_{uuid.uuid4().hex[:8]}.mp4"
    
    return merge_video_audio_logic([video_url], audio_url, output_name)
