"""
File Analyzer Service - Media File Metadata Extraction.

This service extracts metadata from uploaded files:
1. Audio files: duration, sample rate, channels
2. Video files: duration, resolution, frame rate
3. Image files: dimensions, format

Used for:
- Auto-configuring video segment counts based on audio duration
- Validating file constraints (min/max duration)
- Displaying file info to users
"""
import logging
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Tuple, Union

logger = logging.getLogger(__name__)


@dataclass
class AudioMetadata:
    """Metadata extracted from an audio file."""
    duration_seconds: float
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    format: Optional[str] = None
    bitrate: Optional[int] = None
    file_size_bytes: int = 0

    def __str__(self) -> str:
        mins = int(self.duration_seconds // 60)
        secs = int(self.duration_seconds % 60)
        return f"{mins}:{secs:02d} | {self.format or 'audio'}"

    @property
    def duration_formatted(self) -> str:
        """Format duration as MM:SS."""
        mins = int(self.duration_seconds // 60)
        secs = int(self.duration_seconds % 60)
        return f"{mins}:{secs:02d}"


@dataclass
class VideoMetadata:
    """Metadata extracted from a video file."""
    duration_seconds: float
    width: Optional[int] = None
    height: Optional[int] = None
    frame_rate: Optional[float] = None
    codec: Optional[str] = None
    file_size_bytes: int = 0
    has_audio: bool = False

    def __str__(self) -> str:
        mins = int(self.duration_seconds // 60)
        secs = int(self.duration_seconds % 60)
        res = f"{self.width}x{self.height}" if self.width and self.height else "unknown"
        return f"{mins}:{secs:02d} | {res}"

    @property
    def duration_formatted(self) -> str:
        """Format duration as MM:SS."""
        mins = int(self.duration_seconds // 60)
        secs = int(self.duration_seconds % 60)
        return f"{mins}:{secs:02d}"

    @property
    def resolution(self) -> str:
        """Format resolution as WxH."""
        if self.width and self.height:
            return f"{self.width}x{self.height}"
        return "unknown"


@dataclass
class ImageMetadata:
    """Metadata extracted from an image file."""
    width: int
    height: int
    format: Optional[str] = None
    mode: Optional[str] = None  # RGB, RGBA, etc.
    file_size_bytes: int = 0

    def __str__(self) -> str:
        return f"{self.width}x{self.height} | {self.format or 'image'}"

    @property
    def dimensions(self) -> str:
        """Format dimensions as WxH."""
        return f"{self.width}x{self.height}"


FileMetadata = Union[AudioMetadata, VideoMetadata, ImageMetadata]


class FileAnalyzer:
    """
    Analyzes uploaded files to extract metadata.

    Uses multiple backends in priority order:
    1. ffprobe (most reliable, requires ffmpeg)
    2. pydub (audio only, requires ffmpeg)
    3. cv2/OpenCV (video)
    4. PIL/Pillow (images)
    5. mutagen (audio metadata)
    """

    @staticmethod
    def analyze_audio(
        file_obj: Any,
        filename: Optional[str] = None
    ) -> Optional[AudioMetadata]:
        """
        Extract metadata from an audio file.

        Args:
            file_obj: File-like object with read() method, or file path string
            filename: Optional filename for format detection

        Returns:
            AudioMetadata or None if analysis fails
        """
        # Get filename from object or parameter
        if filename is None and hasattr(file_obj, 'name'):
            filename = file_obj.name

        # Determine file extension
        ext = Path(filename).suffix.lower() if filename else '.mp3'

        # Get file size
        file_size = 0
        if hasattr(file_obj, 'seek') and hasattr(file_obj, 'read'):
            file_obj.seek(0, 2)  # Seek to end
            file_size = file_obj.tell()
            file_obj.seek(0)  # Reset
        elif isinstance(file_obj, (str, Path)) and Path(file_obj).exists():
            file_size = Path(file_obj).stat().st_size

        # Try ffprobe first (most reliable)
        result = FileAnalyzer._analyze_audio_ffprobe(file_obj, ext)
        if result:
            result.file_size_bytes = file_size
            return result

        # Try pydub
        result = FileAnalyzer._analyze_audio_pydub(file_obj, ext)
        if result:
            result.file_size_bytes = file_size
            return result

        # Try mutagen
        result = FileAnalyzer._analyze_audio_mutagen(file_obj, ext)
        if result:
            result.file_size_bytes = file_size
            return result

        logger.warning(f"Could not analyze audio file: {filename}")
        return None

    @staticmethod
    def _analyze_audio_ffprobe(file_obj: Any, ext: str) -> Optional[AudioMetadata]:
        """Analyze audio using ffprobe."""
        try:
            import subprocess
            import json

            # Write to temp file if needed
            temp_path = None
            if hasattr(file_obj, 'read'):
                temp_path = tempfile.mktemp(suffix=ext)
                with open(temp_path, 'wb') as f:
                    file_obj.seek(0)
                    f.write(file_obj.read())
                    file_obj.seek(0)
                input_path = temp_path
            else:
                input_path = str(file_obj)

            try:
                result = subprocess.run(
                    [
                        'ffprobe', '-v', 'quiet',
                        '-print_format', 'json',
                        '-show_format', '-show_streams',
                        input_path
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result.returncode == 0:
                    data = json.loads(result.stdout)

                    duration = float(data.get('format', {}).get('duration', 0))

                    # Get audio stream info
                    audio_stream = None
                    for stream in data.get('streams', []):
                        if stream.get('codec_type') == 'audio':
                            audio_stream = stream
                            break

                    return AudioMetadata(
                        duration_seconds=duration,
                        sample_rate=int(audio_stream.get('sample_rate', 0)) if audio_stream else None,
                        channels=audio_stream.get('channels') if audio_stream else None,
                        format=ext.lstrip('.').upper(),
                        bitrate=int(data.get('format', {}).get('bit_rate', 0)) or None
                    )
            finally:
                if temp_path and os.path.exists(temp_path):
                    os.unlink(temp_path)

        except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
            logger.debug(f"ffprobe analysis failed: {e}")

        return None

    @staticmethod
    def _analyze_audio_pydub(file_obj: Any, ext: str) -> Optional[AudioMetadata]:
        """Analyze audio using pydub."""
        try:
            from pydub import AudioSegment  # type: ignore[import-not-found]

            # Load from file object or path
            if hasattr(file_obj, 'read'):
                file_obj.seek(0)
                audio = AudioSegment.from_file(file_obj, format=ext.lstrip('.'))
                file_obj.seek(0)
            else:
                audio = AudioSegment.from_file(str(file_obj))

            return AudioMetadata(
                duration_seconds=len(audio) / 1000.0,
                sample_rate=audio.frame_rate,
                channels=audio.channels,
                format=ext.lstrip('.').upper()
            )
        except Exception as e:
            logger.debug(f"pydub analysis failed: {e}")

        return None

    @staticmethod
    def _analyze_audio_mutagen(file_obj: Any, ext: str) -> Optional[AudioMetadata]:
        """Analyze audio using mutagen."""
        try:
            import mutagen  # type: ignore[import-not-found]

            # Mutagen needs a file path
            temp_path = None
            if hasattr(file_obj, 'read'):
                temp_path = tempfile.mktemp(suffix=ext)
                with open(temp_path, 'wb') as f:
                    file_obj.seek(0)
                    f.write(file_obj.read())
                    file_obj.seek(0)
                input_path = temp_path
            else:
                input_path = str(file_obj)

            try:
                audio = mutagen.File(input_path)
                if audio and audio.info:
                    return AudioMetadata(
                        duration_seconds=audio.info.length,
                        sample_rate=getattr(audio.info, 'sample_rate', None),
                        channels=getattr(audio.info, 'channels', None),
                        format=ext.lstrip('.').upper(),
                        bitrate=getattr(audio.info, 'bitrate', None)
                    )
            finally:
                if temp_path and os.path.exists(temp_path):
                    os.unlink(temp_path)

        except Exception as e:
            logger.debug(f"mutagen analysis failed: {e}")

        return None

    @staticmethod
    def analyze_video(
        file_obj: Any,
        filename: Optional[str] = None
    ) -> Optional[VideoMetadata]:
        """
        Extract metadata from a video file.

        Args:
            file_obj: File-like object or file path
            filename: Optional filename for format detection

        Returns:
            VideoMetadata or None if analysis fails
        """
        if filename is None and hasattr(file_obj, 'name'):
            filename = file_obj.name

        ext = Path(filename).suffix.lower() if filename else '.mp4'

        # Get file size
        file_size = 0
        if hasattr(file_obj, 'seek') and hasattr(file_obj, 'read'):
            file_obj.seek(0, 2)
            file_size = file_obj.tell()
            file_obj.seek(0)
        elif isinstance(file_obj, (str, Path)) and Path(file_obj).exists():
            file_size = Path(file_obj).stat().st_size

        # Try ffprobe first
        result = FileAnalyzer._analyze_video_ffprobe(file_obj, ext)
        if result:
            result.file_size_bytes = file_size
            return result

        # Try OpenCV
        result = FileAnalyzer._analyze_video_opencv(file_obj, ext)
        if result:
            result.file_size_bytes = file_size
            return result

        logger.warning(f"Could not analyze video file: {filename}")
        return None

    @staticmethod
    def _analyze_video_ffprobe(file_obj: Any, ext: str) -> Optional[VideoMetadata]:
        """Analyze video using ffprobe."""
        try:
            import subprocess
            import json

            temp_path = None
            if hasattr(file_obj, 'read'):
                temp_path = tempfile.mktemp(suffix=ext)
                with open(temp_path, 'wb') as f:
                    file_obj.seek(0)
                    f.write(file_obj.read())
                    file_obj.seek(0)
                input_path = temp_path
            else:
                input_path = str(file_obj)

            try:
                result = subprocess.run(
                    [
                        'ffprobe', '-v', 'quiet',
                        '-print_format', 'json',
                        '-show_format', '-show_streams',
                        input_path
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode == 0:
                    data = json.loads(result.stdout)

                    duration = float(data.get('format', {}).get('duration', 0))

                    # Find video stream
                    video_stream = None
                    has_audio = False
                    for stream in data.get('streams', []):
                        if stream.get('codec_type') == 'video':
                            video_stream = stream
                        elif stream.get('codec_type') == 'audio':
                            has_audio = True

                    # Parse frame rate (e.g., "30/1" or "29.97")
                    frame_rate = None
                    if video_stream:
                        r_frame_rate = video_stream.get('r_frame_rate', '0/1')
                        if '/' in r_frame_rate:
                            num, den = r_frame_rate.split('/')
                            if int(den) > 0:
                                frame_rate = float(num) / float(den)
                        else:
                            frame_rate = float(r_frame_rate)

                    return VideoMetadata(
                        duration_seconds=duration,
                        width=video_stream.get('width') if video_stream else None,
                        height=video_stream.get('height') if video_stream else None,
                        frame_rate=frame_rate,
                        codec=video_stream.get('codec_name') if video_stream else None,
                        has_audio=has_audio
                    )
            finally:
                if temp_path and os.path.exists(temp_path):
                    os.unlink(temp_path)

        except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
            logger.debug(f"ffprobe video analysis failed: {e}")

        return None

    @staticmethod
    def _analyze_video_opencv(file_obj: Any, ext: str) -> Optional[VideoMetadata]:
        """Analyze video using OpenCV."""
        try:
            import cv2  # type: ignore[import-not-found]

            temp_path = None
            if hasattr(file_obj, 'read'):
                temp_path = tempfile.mktemp(suffix=ext)
                with open(temp_path, 'wb') as f:
                    file_obj.seek(0)
                    f.write(file_obj.read())
                    file_obj.seek(0)
                input_path = temp_path
            else:
                input_path = str(file_obj)

            try:
                cap = cv2.VideoCapture(input_path)

                if cap.isOpened():
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

                    duration = frame_count / fps if fps > 0 else 0

                    cap.release()

                    return VideoMetadata(
                        duration_seconds=duration,
                        width=width,
                        height=height,
                        frame_rate=fps
                    )
            finally:
                if temp_path and os.path.exists(temp_path):
                    os.unlink(temp_path)

        except Exception as e:
            logger.debug(f"OpenCV video analysis failed: {e}")

        return None

    @staticmethod
    def analyze_image(
        file_obj: Any,
        filename: Optional[str] = None
    ) -> Optional[ImageMetadata]:
        """
        Extract metadata from an image file.

        Args:
            file_obj: File-like object or file path
            filename: Optional filename for format detection

        Returns:
            ImageMetadata or None if analysis fails
        """
        if filename is None and hasattr(file_obj, 'name'):
            filename = file_obj.name

        # Get file size
        file_size = 0
        if hasattr(file_obj, 'seek') and hasattr(file_obj, 'read'):
            file_obj.seek(0, 2)
            file_size = file_obj.tell()
            file_obj.seek(0)
        elif isinstance(file_obj, (str, Path)) and Path(file_obj).exists():
            file_size = Path(file_obj).stat().st_size

        try:
            from PIL import Image

            if hasattr(file_obj, 'read') and hasattr(file_obj, 'seek'):
                file_obj.seek(0)  # type: ignore[union-attr]
                img = Image.open(file_obj)
                file_obj.seek(0)  # type: ignore[union-attr]
            else:
                img = Image.open(str(file_obj))

            return ImageMetadata(
                width=img.width,
                height=img.height,
                format=img.format,
                mode=img.mode,
                file_size_bytes=file_size
            )
        except Exception as e:
            logger.warning(f"Could not analyze image: {e}")

        return None

    @staticmethod
    def analyze(
        file_obj: Any,
        filename: Optional[str] = None
    ) -> Optional[FileMetadata]:
        """
        Analyze any media file and return appropriate metadata.

        Auto-detects file type from extension.

        Args:
            file_obj: File-like object or file path
            filename: Optional filename for type detection

        Returns:
            AudioMetadata, VideoMetadata, or ImageMetadata
        """
        if filename is None and hasattr(file_obj, 'name'):
            filename = file_obj.name

        if not filename:
            logger.warning("Cannot analyze file without filename")
            return None

        ext = Path(filename).suffix.lower()

        # Audio extensions
        if ext in {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.aiff'}:
            return FileAnalyzer.analyze_audio(file_obj, filename)

        # Video extensions
        if ext in {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.wmv', '.flv', '.m4v'}:
            return FileAnalyzer.analyze_video(file_obj, filename)

        # Image extensions
        if ext in {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.svg'}:
            return FileAnalyzer.analyze_image(file_obj, filename)

        logger.warning(f"Unknown file type: {ext}")
        return None


def calculate_video_segments(
    audio_duration_seconds: float,
    target_segment_duration: float = 5.0,
    max_segments: int = 20,
    min_segments: int = 1
) -> Tuple[int, float]:
    """
    Calculate optimal number of video segments for an audio track.

    Args:
        audio_duration_seconds: Total audio duration
        target_segment_duration: Target duration per segment (default 5s)
        max_segments: Maximum allowed segments
        min_segments: Minimum allowed segments

    Returns:
        Tuple of (num_segments, actual_segment_duration)
    """
    if audio_duration_seconds <= 0:
        return min_segments, target_segment_duration

    # Calculate ideal segment count
    ideal_segments = int(audio_duration_seconds / target_segment_duration)

    # Clamp to bounds
    num_segments = max(min_segments, min(max_segments, ideal_segments))

    # Calculate actual segment duration
    actual_duration = audio_duration_seconds / num_segments

    return num_segments, actual_duration


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable form."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
