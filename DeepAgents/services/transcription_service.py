"""
Google Cloud Speech-to-Text Transcription Service.

Provides audio-to-text transcription using Google Cloud Speech-to-Text API.
Supports local files, GCS URIs, and various audio formats.

Requirements:
    pip install google-cloud-speech

Authentication:
    Set GOOGLE_APPLICATION_CREDENTIALS environment variable to your service account key,
    or use Application Default Credentials (ADC).
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Literal, Optional

from google.api_core.client_options import ClientOptions
from google.cloud import speech
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech

logger = logging.getLogger(__name__)


# Audio encoding types supported
AudioEncoding = Literal[
    "LINEAR16",  # Uncompressed 16-bit signed little-endian samples (WAV)
    "FLAC",  # Free Lossless Audio Codec
    "MP3",  # MP3 audio
    "OGG_OPUS",  # Ogg Opus
    "WEBM_OPUS",  # WebM Opus
    "AUTO",  # Auto-detect (V2 API only)
]


@dataclass
class TranscriptionResult:
    """Result from a transcription operation."""

    transcript: str
    confidence: float
    language_code: Optional[str] = None
    words: Optional[List[dict]] = None  # Word-level timestamps if requested


@dataclass
class TranscriptionResponse:
    """Full response containing all transcription results."""

    results: List[TranscriptionResult]
    full_transcript: str  # Combined transcript from all results

    @classmethod
    def from_v1_response(
        cls, response: speech.RecognizeResponse
    ) -> "TranscriptionResponse":
        """Create from V1 API response."""
        results = []
        full_text_parts = []

        for result in response.results:
            if result.alternatives:
                alt = result.alternatives[0]
                results.append(
                    TranscriptionResult(
                        transcript=alt.transcript,
                        confidence=alt.confidence
                        if hasattr(alt, "confidence")
                        else 0.0,
                        language_code=result.language_code
                        if hasattr(result, "language_code")
                        else None,
                    )
                )
                full_text_parts.append(alt.transcript)

        return cls(results=results, full_transcript=" ".join(full_text_parts))

    @classmethod
    def from_v2_response(
        cls, response: cloud_speech.RecognizeResponse
    ) -> "TranscriptionResponse":
        """Create from V2 API response."""
        results = []
        full_text_parts = []

        for result in response.results:
            if result.alternatives:
                alt = result.alternatives[0]
                results.append(
                    TranscriptionResult(
                        transcript=alt.transcript,
                        confidence=alt.confidence
                        if hasattr(alt, "confidence")
                        else 0.0,
                    )
                )
                full_text_parts.append(alt.transcript)

        return cls(results=results, full_transcript=" ".join(full_text_parts))


class TranscriptionService:
    """
    Google Cloud Speech-to-Text transcription service.

    Supports both V1 (stable) and V2 (latest features like Chirp models) APIs.

    Example:
        >>> service = TranscriptionService()
        >>> result = service.transcribe_file("audio.wav")
        >>> print(result.full_transcript)

        # Using V2 API with Chirp model:
        >>> result = service.transcribe_file_v2("audio.wav", model="chirp_3")
        >>> print(result.full_transcript)
    """

    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize the transcription service.

        Args:
            project_id: Google Cloud project ID. If not provided, uses
                       GOOGLE_CLOUD_PROJECT environment variable.
        """
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        self._v1_client: Optional[speech.SpeechClient] = None
        self._v2_client: Optional[SpeechClient] = None

    @property
    def v1_client(self) -> speech.SpeechClient:
        """Lazy-loaded V1 Speech client."""
        if self._v1_client is None:
            self._v1_client = speech.SpeechClient()
        return self._v1_client

    @property
    def v2_client(self) -> SpeechClient:
        """Lazy-loaded V2 Speech client."""
        if self._v2_client is None:
            self._v2_client = SpeechClient()
        return self._v2_client

    def _get_v1_encoding(
        self, encoding: AudioEncoding
    ) -> speech.RecognitionConfig.AudioEncoding:
        """Map string encoding to V1 API enum."""
        encoding_map = {
            "LINEAR16": speech.RecognitionConfig.AudioEncoding.LINEAR16,
            "FLAC": speech.RecognitionConfig.AudioEncoding.FLAC,
            "MP3": speech.RecognitionConfig.AudioEncoding.MP3,
            "OGG_OPUS": speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
            "WEBM_OPUS": speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
        }
        return encoding_map.get(
            encoding, speech.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED
        )

    def transcribe_file(
        self,
        audio_file: str,
        language_code: str = "en-US",
        encoding: AudioEncoding = "LINEAR16",
        sample_rate_hertz: int = 16000,
        enable_automatic_punctuation: bool = True,
        model: Optional[str] = None,
    ) -> TranscriptionResponse:
        """
        Transcribe a local audio file using V1 API.

        Best for: Short audio files (< 60 seconds), standard use cases.

        Args:
            audio_file: Path to local audio file.
            language_code: BCP-47 language code (e.g., "en-US", "es-ES").
            encoding: Audio encoding format.
            sample_rate_hertz: Sample rate in Hz.
            enable_automatic_punctuation: Add punctuation to transcript.
            model: Recognition model (e.g., "phone_call", "video", "default").

        Returns:
            TranscriptionResponse with transcription results.

        Raises:
            FileNotFoundError: If audio file doesn't exist.
            google.api_core.exceptions.GoogleAPIError: On API errors.
        """
        audio_path = Path(audio_file)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file}")

        logger.info(f"Transcribing file: {audio_file}")

        with open(audio_file, "rb") as f:
            audio_content = f.read()

        audio = speech.RecognitionAudio(content=audio_content)

        # Build config with typed parameters
        config = speech.RecognitionConfig(
            encoding=self._get_v1_encoding(encoding),
            sample_rate_hertz=sample_rate_hertz,
            language_code=language_code,
            enable_automatic_punctuation=enable_automatic_punctuation,
            model=model,
        )

        response = self.v1_client.recognize(config=config, audio=audio)

        logger.info(f"Transcription complete. Results: {len(response.results)}")
        return TranscriptionResponse.from_v1_response(response)

    def transcribe_file_long(
        self,
        audio_file: str,
        language_code: str = "en-US",
        encoding: AudioEncoding = "LINEAR16",
        sample_rate_hertz: int = 16000,
        timeout: int = 300,
    ) -> TranscriptionResponse:
        """
        Transcribe a longer audio file using async/long-running operation.

        Best for: Audio files between 1-8 hours.
        Note: For files > 60 seconds, consider using GCS URI instead.

        Args:
            audio_file: Path to local audio file.
            language_code: BCP-47 language code.
            encoding: Audio encoding format.
            sample_rate_hertz: Sample rate in Hz.
            timeout: Operation timeout in seconds.

        Returns:
            TranscriptionResponse with transcription results.
        """
        audio_path = Path(audio_file)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file}")

        logger.info(f"Starting long-running transcription: {audio_file}")

        with open(audio_file, "rb") as f:
            audio_content = f.read()

        audio = speech.RecognitionAudio(content=audio_content)
        config = speech.RecognitionConfig(
            encoding=self._get_v1_encoding(encoding),
            sample_rate_hertz=sample_rate_hertz,
            language_code=language_code,
            enable_automatic_punctuation=True,
        )

        operation = self.v1_client.long_running_recognize(config=config, audio=audio)
        logger.info("Waiting for operation to complete...")

        response = operation.result(timeout=timeout)

        logger.info(
            f"Long-running transcription complete. Results: {len(response.results)}"
        )
        return TranscriptionResponse.from_v1_response(response)

    def transcribe_gcs(
        self,
        gcs_uri: str,
        language_code: str = "en-US",
        encoding: AudioEncoding = "FLAC",
        sample_rate_hertz: int = 16000,
    ) -> TranscriptionResponse:
        """
        Transcribe an audio file from Google Cloud Storage.

        Best for: Large files, production pipelines.

        Args:
            gcs_uri: GCS URI (e.g., "gs://bucket/audio.flac").
            language_code: BCP-47 language code.
            encoding: Audio encoding format.
            sample_rate_hertz: Sample rate in Hz.

        Returns:
            TranscriptionResponse with transcription results.
        """
        logger.info(f"Transcribing GCS file: {gcs_uri}")

        audio = speech.RecognitionAudio(uri=gcs_uri)
        config = speech.RecognitionConfig(
            encoding=self._get_v1_encoding(encoding),
            sample_rate_hertz=sample_rate_hertz,
            language_code=language_code,
            enable_automatic_punctuation=True,
        )

        response = self.v1_client.recognize(config=config, audio=audio)

        logger.info(f"GCS transcription complete. Results: {len(response.results)}")
        return TranscriptionResponse.from_v1_response(response)

    def transcribe_file_v2(
        self,
        audio_file: str,
        language_codes: Optional[List[str]] = None,
        model: str = "long",
        region: str = "global",
        enable_automatic_punctuation: bool = True,
    ) -> TranscriptionResponse:
        """
        Transcribe using V2 API with advanced features.

        Best for: Latest models (Chirp), auto-detection, advanced features.

        Args:
            audio_file: Path to local audio file.
            language_codes: List of BCP-47 language codes. Default: ["en-US"].
            model: Model to use. Options:
                   - "long": For long-form audio (default)
                   - "short": For short utterances
                   - "chirp": Universal Speech Model
                   - "chirp_2": Chirp 2 model
                   - "chirp_3": Latest Chirp model (best quality)
            region: API region. Use "us" for Chirp models.
            enable_automatic_punctuation: Add punctuation to transcript.

        Returns:
            TranscriptionResponse with transcription results.
        """
        if not self.project_id:
            raise ValueError(
                "Project ID required for V2 API. Set GOOGLE_CLOUD_PROJECT env var "
                "or pass project_id to TranscriptionService."
            )

        audio_path = Path(audio_file)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file}")

        logger.info(f"Transcribing file (V2 API, model={model}): {audio_file}")

        # Use regional endpoint for Chirp models
        if model.startswith("chirp"):
            region = "us"  # Chirp requires US region

        client = SpeechClient(
            client_options=ClientOptions(api_endpoint=f"{region}-speech.googleapis.com")
            if region != "global"
            else None
        )

        with open(audio_file, "rb") as f:
            audio_content = f.read()

        config = cloud_speech.RecognitionConfig(
            auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
            language_codes=language_codes or ["en-US"],
            model=model,
            features=cloud_speech.RecognitionFeatures(
                enable_automatic_punctuation=enable_automatic_punctuation,
            ),
        )

        request = cloud_speech.RecognizeRequest(
            recognizer=f"projects/{self.project_id}/locations/{region}/recognizers/_",
            config=config,
            content=audio_content,
        )

        response = client.recognize(request=request)

        logger.info(f"V2 transcription complete. Results: {len(response.results)}")
        return TranscriptionResponse.from_v2_response(response)


# Convenience function for quick usage
def transcribe(
    audio_file: str,
    language_code: str = "en-US",
    use_v2: bool = False,
    model: Optional[str] = None,
) -> str:
    """
    Quick transcription function.

    Args:
        audio_file: Path to audio file.
        language_code: Language code (default: "en-US").
        use_v2: Use V2 API for advanced features.
        model: Optional model name.

    Returns:
        Transcribed text as a string.

    Example:
        >>> text = transcribe("meeting.wav")
        >>> print(text)
        "Hello, welcome to the meeting..."
    """
    service = TranscriptionService()

    if use_v2:
        result = service.transcribe_file_v2(
            audio_file, language_codes=[language_code], model=model or "long"
        )
    else:
        result = service.transcribe_file(
            audio_file, language_code=language_code, model=model
        )

    return result.full_transcript


if __name__ == "__main__":
    # Quick test
    import sys

    if len(sys.argv) < 2:
        print("Usage: python transcription_service.py <audio_file>")
        print("Example: python transcription_service.py audio.wav")
        sys.exit(1)

    audio_path = sys.argv[1]
    print(f"Transcribing: {audio_path}")

    try:
        text = transcribe(audio_path)
        print(f"\nTranscript:\n{text}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
