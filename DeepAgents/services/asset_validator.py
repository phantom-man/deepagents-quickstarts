"""
Asset Validator - Validates files against model schema requirements.

This module validates uploaded files to ensure they meet the
requirements specified in model schemas (type, duration, content).

Philosophy: Fail Fast - Validation errors are surfaced immediately.
"""

import logging
import mimetypes
import os
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, BinaryIO, Dict, Optional, Tuple, Union

if TYPE_CHECKING:
    from DeepAgents.services.schema_service import AssetRequirement

logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """Validation result status."""

    VALID = "valid"
    INVALID_TYPE = "invalid_type"
    INVALID_DURATION = "invalid_duration"
    INVALID_CONTENT = "invalid_content"
    FILE_TOO_LARGE = "file_too_large"
    FILE_EMPTY = "file_empty"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class ValidationResult:
    """Result of file validation."""

    status: ValidationStatus
    is_valid: bool
    message: str
    details: Optional[dict] = None

    @property
    def icon(self) -> str:
        """Get status icon for UI."""
        return "✓" if self.is_valid else "✗"

    @property
    def color(self) -> str:
        """Get status color for UI."""
        return "green" if self.is_valid else "red"


class AssetValidator:
    """
    Validates asset files against schema requirements.

    Checks:
    - File type (MIME type)
    - File size
    - Duration (for audio/video)
    - Content type (voice, music, etc.)
    """

    # Maximum file size in bytes (100MB default)
    MAX_FILE_SIZE = 100 * 1024 * 1024

    # MIME type mappings
    AUDIO_MIMES = {
        "audio/wav",
        "audio/x-wav",
        "audio/wave",
        "audio/mpeg",
        "audio/mp3",
        "audio/flac",
        "audio/x-flac",
        "audio/ogg",
        "audio/vorbis",
        "audio/mp4",
        "audio/m4a",
        "audio/x-m4a",
    }

    VIDEO_MIMES = {
        "video/mp4",
        "video/mpeg",
        "video/quicktime",
        "video/x-msvideo",
        "video/webm",
    }

    IMAGE_MIMES = {"image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif"}

    def __init__(self, max_file_size: Optional[int] = None):
        """
        Initialize validator.

        Args:
            max_file_size: Max file size in bytes (default 100MB)
        """
        self.max_file_size = max_file_size or self.MAX_FILE_SIZE
        self._pydub_available = self._check_pydub()
        self._opencv_available = self._check_opencv()

    @staticmethod
    def _format_duration(seconds: Optional[float]) -> Optional[str]:
        """Format duration in seconds to mm:ss or hh:mm:ss string."""
        if seconds is None:
            return None
        if seconds <= 0:
            return "0s"
        total_seconds = int(round(seconds))
        hours, remainder = divmod(total_seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    def _check_pydub(self) -> bool:
        """Check if pydub is available for audio duration."""
        try:
            import pydub  # noqa

            return True
        except ImportError:
            logger.warning("pydub not available - audio duration checks disabled")
            return False

    def _check_opencv(self) -> bool:
        """Check if opencv is available for video duration."""
        try:
            import cv2  # noqa

            return True
        except ImportError:
            logger.warning("opencv not available - video duration checks disabled")
            return False

    def validate_file(
        self,
        file: Union[str, Path, BinaryIO],
        asset_type: str,
        content_type: Optional[str] = None,
        min_duration: Optional[float] = None,
        max_duration: Optional[float] = None,
        required: bool = True,
    ) -> ValidationResult:
        """
        Validate a file against requirements.

        Args:
            file: File path or file-like object
            asset_type: Expected type ('audio', 'video', 'image')
            content_type: Expected content ('voice', 'music', 'song', etc.)
            min_duration: Minimum duration in seconds
            max_duration: Maximum duration in seconds
            required: Whether the file is required

        Returns:
            ValidationResult with status and message
        """
        # Handle missing file
        if file is None:
            if required:
                return ValidationResult(
                    status=ValidationStatus.INVALID_TYPE,
                    is_valid=False,
                    message="Required file not provided",
                )
            return ValidationResult(
                status=ValidationStatus.VALID,
                is_valid=True,
                message="Optional file not provided",
            )

        try:
            # Get file info
            file_path, file_size, mime_type = self._get_file_info(file)

            # Check file size
            if file_size == 0:
                return ValidationResult(
                    status=ValidationStatus.FILE_EMPTY,
                    is_valid=False,
                    message="File is empty",
                )

            if file_size > self.max_file_size:
                return ValidationResult(
                    status=ValidationStatus.FILE_TOO_LARGE,
                    is_valid=False,
                    message=f"File too large: {file_size / 1024 / 1024:.1f}MB (max {self.max_file_size / 1024 / 1024:.1f}MB)",
                )

            # Check MIME type
            type_valid, type_msg = self._validate_mime_type(mime_type, asset_type)
            if not type_valid:
                return ValidationResult(
                    status=ValidationStatus.INVALID_TYPE,
                    is_valid=False,
                    message=type_msg,
                    details={"mime_type": mime_type, "expected": asset_type},
                )

            # Check duration for audio/video
            if asset_type in ("audio", "video") and (min_duration or max_duration):
                duration_valid, duration_msg, actual_duration = self._validate_duration(
                    file_path, asset_type, min_duration, max_duration
                )
                if not duration_valid:
                    return ValidationResult(
                        status=ValidationStatus.INVALID_DURATION,
                        is_valid=False,
                        message=duration_msg,
                        details={
                            "duration": actual_duration,
                            "min_duration": min_duration,
                            "max_duration": max_duration,
                        },
                    )

            # All checks passed
            details = {
                "file_size": file_size,
                "mime_type": mime_type,
                "asset_type": asset_type,
            }

            return ValidationResult(
                status=ValidationStatus.VALID,
                is_valid=True,
                message=f"Valid {asset_type} file ({file_size / 1024:.1f}KB)",
                details=details,
            )

        except Exception as e:
            logger.error(f"Validation error: {e}")
            return ValidationResult(
                status=ValidationStatus.UNKNOWN_ERROR,
                is_valid=False,
                message=f"Validation error: {str(e)}",
            )

    def _get_file_info(
        self, file: Union[str, Path, BinaryIO]
    ) -> Tuple[Optional[str], int, Optional[str]]:
        """
        Get file path, size, and MIME type.

        Args:
            file: File path or file-like object

        Returns:
            Tuple of (path, size, mime_type)
        """
        if isinstance(file, (str, Path)):
            # File path
            file_path = str(file)
            file_size = os.path.getsize(file_path)
            mime_type, _ = mimetypes.guess_type(file_path)
        else:
            # File-like object (e.g., Streamlit UploadedFile)
            # Use Any type for duck-typed access to Streamlit UploadedFile attributes
            file_obj: Any = file
            file_path = None

            # Get size - Streamlit UploadedFile has .size attribute
            if hasattr(file_obj, "size"):
                file_size = file_obj.size
            else:
                current_pos = file_obj.tell()
                file_obj.seek(0, 2)  # Seek to end
                file_size = file_obj.tell()
                file_obj.seek(current_pos)  # Restore position

            # Get MIME type - Streamlit UploadedFile has .type attribute
            if hasattr(file_obj, "type"):
                mime_type = file_obj.type
            elif hasattr(file_obj, "name"):
                mime_type, _ = mimetypes.guess_type(file_obj.name)
            else:
                mime_type = None

            # If we need duration check, save to temp file
            if file_path is None and hasattr(file_obj, "read"):
                # Create temp file for duration checking
                suffix = Path(file_obj.name).suffix if hasattr(file_obj, "name") else ""
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(file_obj.read())
                    file_path = tmp.name
                    file_obj.seek(0)  # Reset for later use

        return file_path, file_size, mime_type

    def _validate_mime_type(
        self, mime_type: Optional[str], expected_type: str
    ) -> Tuple[bool, str]:
        """
        Validate MIME type against expected asset type.

        Args:
            mime_type: Detected MIME type
            expected_type: Expected type ('audio', 'video', 'image')

        Returns:
            Tuple of (is_valid, message)
        """
        if not mime_type:
            return False, "Could not determine file type"

        mime_type = mime_type.lower()

        type_map = {
            "audio": self.AUDIO_MIMES,
            "video": self.VIDEO_MIMES,
            "image": self.IMAGE_MIMES,
        }

        valid_mimes = type_map.get(expected_type, set())

        if mime_type in valid_mimes:
            return True, f"Valid {expected_type} type"

        # Check if it's at least the right category
        if mime_type.startswith(expected_type + "/"):
            return True, f"Valid {expected_type} type (extended)"

        return False, f"Invalid file type: expected {expected_type}, got {mime_type}"

    def _validate_duration(
        self,
        file_path: Optional[str],
        asset_type: str,
        min_duration: Optional[float],
        max_duration: Optional[float],
    ) -> Tuple[bool, str, Optional[float]]:
        """
        Validate file duration against requirements.

        Args:
            file_path: Path to file
            asset_type: 'audio' or 'video'
            min_duration: Minimum duration in seconds
            max_duration: Maximum duration in seconds

        Returns:
            Tuple of (is_valid, message, actual_duration)
        """
        if not file_path:
            return True, "Duration check skipped (no file path)", None

        duration = None

        if asset_type == "audio" and self._pydub_available:
            try:
                from pydub import AudioSegment

                audio = AudioSegment.from_file(file_path)
                duration = len(audio) / 1000.0  # ms to seconds
            except Exception as e:
                logger.warning(f"Could not get audio duration: {e}")
                return True, "Duration check skipped", None

        elif asset_type == "video" and self._opencv_available:
            try:
                import cv2

                cap = cv2.VideoCapture(file_path)
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                cap.release()

                if fps > 0:
                    duration = frame_count / fps
            except Exception as e:
                logger.warning(f"Could not get video duration: {e}")
                return True, "Duration check skipped", None

        if duration is None:
            return True, "Duration check skipped (no analyzer)", None

        # Validate duration
        if min_duration and duration < min_duration:
            return (
                False,
                f"File too short: {duration:.1f}s (min {min_duration}s)",
                duration,
            )

        if max_duration and duration > max_duration:
            return (
                False,
                f"File too long: {duration:.1f}s (max {max_duration}s)",
                duration,
            )

        return True, f"Duration valid: {duration:.1f}s", duration

    def validate_from_requirement(
        self, file: Union[str, Path, BinaryIO], requirement: "AssetRequirement"
    ) -> ValidationResult:
        """
        Validate file against an AssetRequirement object.

        Args:
            file: File to validate
            requirement: AssetRequirement from schema

        Returns:
            ValidationResult
        """
        return self.validate_file(
            file=file,
            asset_type=requirement.asset_type,
            content_type=requirement.content_type,
            min_duration=requirement.min_duration,
            max_duration=requirement.max_duration,
            required=requirement.required,
        )


def get_asset_validator() -> AssetValidator:
    """Get singleton AssetValidator instance."""
    if not hasattr(get_asset_validator, "_instance"):
        get_asset_validator._instance = AssetValidator()
    return get_asset_validator._instance


def validate_upload(
    file: Union[str, Path, BinaryIO],
    asset_type: str,
    min_duration: Optional[float] = None,
    max_duration: Optional[float] = None,
) -> ValidationResult:
    """
    Convenience function to validate an uploaded file.

    Args:
        file: Uploaded file
        asset_type: 'audio', 'video', or 'image'
        min_duration: Min duration in seconds
        max_duration: Max duration in seconds

    Returns:
        ValidationResult
    """
    validator = get_asset_validator()
    return validator.validate_file(
        file=file,
        asset_type=asset_type,
        min_duration=min_duration,
        max_duration=max_duration,
    )

    def extract_metadata(
        self, file_path: Union[str, Path], asset_type: str
    ) -> Dict[str, Any]:
        """Extract best-effort metadata for audio or video files."""
        metadata: Dict[str, Any] = {}
        path = str(file_path)

        if not os.path.exists(path):
            return metadata

        try:
            stat_info = os.stat(path)
            metadata["file_size_bytes"] = stat_info.st_size
            metadata["file_size_readable"] = (
                f"{stat_info.st_size / (1024 * 1024):.2f} MB"
            )
        except OSError as exc:
            logger.warning(f"Could not stat file for metadata: {exc}")

        mime_type, _ = mimetypes.guess_type(path)
        if mime_type:
            metadata["mime_type"] = mime_type

        duration_seconds: Optional[float] = None

        if asset_type == "video" and self._opencv_available:
            try:
                import cv2

                cap = cv2.VideoCapture(path)
                fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
                frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
                width = cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0.0
                height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0.0
                cap.release()

                if fps > 0:
                    duration_seconds = frame_count / fps

                if width > 0 and height > 0:
                    metadata["resolution"] = f"{int(width)}x{int(height)}"

                if fps > 0:
                    metadata["fps"] = round(fps, 2)
            except Exception as exc:  # pylint: disable=broad-except
                logger.warning(f"Could not extract video metadata: {exc}")

        if asset_type == "audio" and self._pydub_available:
            try:
                from pydub import AudioSegment

                audio = AudioSegment.from_file(path)
                duration_seconds = len(audio) / 1000.0
                metadata["channels"] = audio.channels
                metadata["frame_rate"] = audio.frame_rate
                metadata["sample_width_bytes"] = audio.sample_width
            except Exception as exc:  # pylint: disable=broad-except
                logger.warning(f"Could not extract audio metadata: {exc}")

        if duration_seconds is not None:
            metadata["duration_seconds"] = round(duration_seconds, 2)
            formatted = self._format_duration(duration_seconds)
            if formatted:
                metadata["duration_readable"] = formatted

        return metadata
