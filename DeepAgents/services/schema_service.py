"""
Schema Service - Multi-Provider Schema Fetching and Parsing.

This service provides zero-touch dynamic UI generation by:
1. Fetching schemas from multiple providers (Replicate, Vertex AI, Google GenAI)
2. Parsing them into UI-friendly control definitions
3. Caching schemas to avoid repeated API calls
4. Detecting asset requirements (voice files, music files, etc.)

Architecture: Strategy Pattern with provider-specific handlers.
Philosophy: Fail Fast - If schema fetch fails, raise immediately.
"""

import hashlib
import json
import logging
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

import requests

# Lazy import to avoid circular dependency
if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class ControlType(Enum):
    """UI Control types derived from OpenAPI schema types."""

    TEXT = "text"  # string without format
    TEXT_AREA = "textarea"  # string with multiline hint
    NUMBER = "number"  # integer or number
    SLIDER = "slider"  # number with min/max
    CHECKBOX = "checkbox"  # boolean
    SELECT = "select"  # enum values
    FILE = "file"  # format: uri, file input
    AUDIO_FILE = "audio"  # file with audio/* content type
    VIDEO_FILE = "video"  # file with video/* content type
    IMAGE_FILE = "image"  # file with image/* content type
    HIDDEN = "hidden"  # internal params to hide


@dataclass
class ControlDefinition:
    """Definition for a single UI control derived from schema."""

    name: str
    control_type: ControlType
    label: str
    description: str = ""
    required: bool = False
    default: Any = None
    # For numeric controls
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    step: Optional[float] = None
    # For select controls
    options: List[Any] = field(default_factory=list)
    # For file controls
    accepted_types: List[str] = field(default_factory=list)
    max_duration: Optional[float] = None  # seconds
    min_duration: Optional[float] = None  # seconds
    # Order in UI
    order: int = 0


@dataclass
class AssetRequirement:
    """Describes a required asset input for a model."""

    param_name: str
    asset_type: str  # 'audio', 'video', 'image'
    description: str
    required: bool = True
    # Constraints from schema
    accepted_formats: List[str] = field(default_factory=list)
    min_duration: Optional[float] = None
    max_duration: Optional[float] = None
    # Content hints
    content_type: Optional[str] = None  # 'voice', 'music', 'instrumental', etc.


@dataclass
class ModelSchema:
    """Parsed schema for a model with UI controls and asset requirements."""

    model_id: str
    name: str
    description: str
    controls: List[ControlDefinition] = field(default_factory=list)
    asset_requirements: List[AssetRequirement] = field(default_factory=list)
    output_type: str = "unknown"  # 'audio', 'video', 'image', 'text'
    # Raw schema for reference
    raw_schema: Dict[str, Any] = field(default_factory=dict)
    # Cache metadata
    fetched_at: float = 0
    version_id: Optional[str] = None
    # Provider info
    provider: str = "replicate"


# =============================================================================
# PROVIDER HANDLERS - Strategy Pattern for Multi-Provider Schema Fetching
# =============================================================================


class SchemaProvider(ABC):
    """Abstract base class for provider-specific schema handlers."""

    @abstractmethod
    def can_handle(self, model_id: str, provider: Optional[str] = None) -> bool:
        """Check if this handler can process the given model."""
        pass

    @abstractmethod
    def fetch_schema(self, model_id: str) -> Dict[str, Any]:
        """Fetch raw schema data from the provider API."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the provider name."""
        pass


class ReplicateSchemaProvider(SchemaProvider):
    """Handler for Replicate-hosted models."""

    # Override defaults for specific models with optimal quality settings
    SCHEMA_DEFAULT_OVERRIDES: Dict[str, Dict[str, Any]] = {
        "lucataco/ace-step": {
            # MAXIMUM QUALITY SETTINGS for ACE-Step music generation
            "scheduler": "euler",  # euler = more stable/cleaner than heun
            "guidance_type": "apg",  # APG = Adjusted Prompt Guidance (best)
            "guidance_scale": 15,  # 15 = optimal balance (20 can over-saturate)
            "number_of_steps": 200,  # 200 = MAXIMUM (best quality, slower)
            "granularity_scale": 10,  # 10 = MAXIMUM detail
            "guidance_interval": 0.5,  # Standard interval
            "min_guidance_scale": 3,  # Minimum guidance floor
            "tag_guidance_scale": 10,  # 10 = MAXIMUM style adherence
            "lyric_guidance_scale": 10,  # 10 = MAXIMUM lyric alignment
            "guidance_interval_decay": 0,  # No decay = consistent quality
            "duration": 60,  # Default 60s song length
        }
    }

    def __init__(self, api_token: str):
        self.api_token = api_token

    def get_provider_name(self) -> str:
        return "replicate"

    def can_handle(self, model_id: str, provider: Optional[str] = None) -> bool:
        """Replicate models have owner/name format and provider is replicate or None."""
        if provider and provider != "replicate":
            return False
        # Check format: owner/name (with possible version)
        if (
            "/" in model_id
            and not model_id.startswith("veo-")
            and not model_id.startswith("imagen-")
        ):
            return True
        return False

    def fetch_schema(self, model_id: str) -> Dict[str, Any]:
        """Fetch schema from Replicate API and apply default overrides."""
        url = f"https://api.replicate.com/v1/models/{model_id}"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code != 200:
            raise ValueError(
                f"Replicate API error for {model_id}: "
                f"HTTP {response.status_code} - {response.text}"
            )

        schema_data = response.json()

        # Apply default overrides if available for this model
        overrides = self.SCHEMA_DEFAULT_OVERRIDES.get(model_id, {})
        if overrides:
            self._apply_default_overrides(schema_data, overrides)
            logger.info(f"Applied quality default overrides for {model_id}")

        return schema_data

    def _apply_default_overrides(
        self, schema_data: Dict[str, Any], overrides: Dict[str, Any]
    ) -> None:
        """Apply default value overrides to schema properties."""
        try:
            props = (
                schema_data.get("latest_version", {})
                .get("openapi_schema", {})
                .get("components", {})
                .get("schemas", {})
                .get("Input", {})
                .get("properties", {})
            )

            for param_name, default_value in overrides.items():
                if param_name in props:
                    props[param_name]["default"] = default_value
                    logger.debug(f"Override: {param_name} default -> {default_value}")
        except Exception as e:
            logger.warning(f"Failed to apply schema overrides: {e}")


class VertexAISchemaProvider(SchemaProvider):
    """Handler for Google Vertex AI models (Veo, Imagen, etc.)."""

    # Pre-defined schemas for Vertex AI models (no public OpenAPI endpoint)
    VERTEX_SCHEMAS: Dict[str, Dict[str, Any]] = {
        "veo-3.1-fast-generate-001": {
            "name": "Veo 3.1 Fast",
            "description": "Google Vertex AI fast video generation. 720p/1080p output.",
            "openapi_schema": {
                "components": {
                    "schemas": {
                        "Input": {
                            "type": "object",
                            "required": ["prompt"],
                            "properties": {
                                "prompt": {
                                    "type": "string",
                                    "title": "Prompt",
                                    "description": "Text description of the video to generate.",
                                    "x-order": 0,
                                },
                                "negative_prompt": {
                                    "type": "string",
                                    "title": "Negative Prompt",
                                    "description": "What to avoid in the video.",
                                    "x-order": 1,
                                },
                                "aspect_ratio": {
                                    "type": "string",
                                    "title": "Aspect Ratio",
                                    "description": "Output aspect ratio.",
                                    "enum": ["16:9", "9:16", "1:1"],
                                    "default": "16:9",
                                    "x-order": 2,
                                },
                                "duration_seconds": {
                                    "type": "integer",
                                    "title": "Duration (seconds)",
                                    "description": "Video duration in seconds (5-8).",
                                    "minimum": 5,
                                    "maximum": 8,
                                    "default": 5,
                                    "x-order": 3,
                                },
                                "resolution": {
                                    "type": "string",
                                    "title": "Resolution",
                                    "description": "Output resolution.",
                                    "enum": ["720p", "1080p"],
                                    "default": "720p",
                                    "x-order": 4,
                                },
                                "enhance_prompt": {
                                    "type": "boolean",
                                    "title": "Enhance Prompt",
                                    "description": "Use AI to enhance the prompt.",
                                    "default": True,
                                    "x-order": 5,
                                },
                            },
                        },
                        "Output": {"type": "string", "format": "uri"},
                    }
                }
            },
        },
        "veo-3.1-generate-001": {
            "name": "Veo 3.1",
            "description": "Google Vertex AI premium video generation. Supports 4K output.",
            "openapi_schema": {
                "components": {
                    "schemas": {
                        "Input": {
                            "type": "object",
                            "required": ["prompt"],
                            "properties": {
                                "prompt": {
                                    "type": "string",
                                    "title": "Prompt",
                                    "description": "Text description of the video to generate.",
                                    "x-order": 0,
                                },
                                "negative_prompt": {
                                    "type": "string",
                                    "title": "Negative Prompt",
                                    "description": "What to avoid in the video.",
                                    "x-order": 1,
                                },
                                "aspect_ratio": {
                                    "type": "string",
                                    "title": "Aspect Ratio",
                                    "description": "Output aspect ratio.",
                                    "enum": ["16:9", "9:16", "1:1", "4:3", "3:4"],
                                    "default": "16:9",
                                    "x-order": 2,
                                },
                                "duration_seconds": {
                                    "type": "integer",
                                    "title": "Duration (seconds)",
                                    "description": "Video duration in seconds (5-8).",
                                    "minimum": 5,
                                    "maximum": 8,
                                    "default": 5,
                                    "x-order": 3,
                                },
                                "resolution": {
                                    "type": "string",
                                    "title": "Resolution",
                                    "description": "Output resolution.",
                                    "enum": ["720p", "1080p", "4k"],
                                    "default": "1080p",
                                    "x-order": 4,
                                },
                                "enhance_prompt": {
                                    "type": "boolean",
                                    "title": "Enhance Prompt",
                                    "description": "Use AI to enhance the prompt.",
                                    "default": True,
                                    "x-order": 5,
                                },
                                "generate_audio": {
                                    "type": "boolean",
                                    "title": "Generate Audio",
                                    "description": "Generate synchronized audio track.",
                                    "default": False,
                                    "x-order": 6,
                                },
                            },
                        },
                        "Output": {"type": "string", "format": "uri"},
                    }
                }
            },
        },
        "en-US-Studio-O": {
            "name": "Google Cloud TTS Studio O",
            "description": "Premium female voice from Google Cloud Text-to-Speech. Natural intonation and expression.",
            "openapi_schema": {
                "components": {
                    "schemas": {
                        "Input": {
                            "type": "object",
                            "required": ["text"],
                            "properties": {
                                "text": {
                                    "type": "string",
                                    "title": "Text",
                                    "description": "The text to convert to speech (max 5000 characters).",
                                    "x-order": 0,
                                },
                                "speaking_rate": {
                                    "type": "number",
                                    "title": "Speaking Rate",
                                    "description": "Speed of speech (0.25-4.0). 1.0 is normal.",
                                    "minimum": 0.25,
                                    "maximum": 4.0,
                                    "default": 1.0,
                                    "x-order": 1,
                                },
                                "pitch": {
                                    "type": "number",
                                    "title": "Pitch",
                                    "description": "Voice pitch adjustment (-20 to 20 semitones).",
                                    "minimum": -20.0,
                                    "maximum": 20.0,
                                    "default": 0.0,
                                    "x-order": 2,
                                },
                                "audio_encoding": {
                                    "type": "string",
                                    "title": "Audio Encoding",
                                    "description": "Output audio format.",
                                    "enum": [
                                        "MP3",
                                        "LINEAR16",
                                        "OGG_OPUS",
                                        "MULAW",
                                        "ALAW",
                                    ],
                                    "default": "MP3",
                                    "x-order": 3,
                                },
                            },
                        },
                        "Output": {"type": "string", "format": "uri"},
                    }
                }
            },
        },
        "en-US-Studio-M": {
            "name": "Google Cloud TTS Studio M",
            "description": "Premium male voice from Google Cloud Text-to-Speech. Natural intonation and expression.",
            "openapi_schema": {
                "components": {
                    "schemas": {
                        "Input": {
                            "type": "object",
                            "required": ["text"],
                            "properties": {
                                "text": {
                                    "type": "string",
                                    "title": "Text",
                                    "description": "The text to convert to speech (max 5000 characters).",
                                    "x-order": 0,
                                },
                                "speaking_rate": {
                                    "type": "number",
                                    "title": "Speaking Rate",
                                    "description": "Speed of speech (0.25-4.0). 1.0 is normal.",
                                    "minimum": 0.25,
                                    "maximum": 4.0,
                                    "default": 1.0,
                                    "x-order": 1,
                                },
                                "pitch": {
                                    "type": "number",
                                    "title": "Pitch",
                                    "description": "Voice pitch adjustment (-20 to 20 semitones).",
                                    "minimum": -20.0,
                                    "maximum": 20.0,
                                    "default": 0.0,
                                    "x-order": 2,
                                },
                                "audio_encoding": {
                                    "type": "string",
                                    "title": "Audio Encoding",
                                    "description": "Output audio format.",
                                    "enum": [
                                        "MP3",
                                        "LINEAR16",
                                        "OGG_OPUS",
                                        "MULAW",
                                        "ALAW",
                                    ],
                                    "default": "MP3",
                                    "x-order": 3,
                                },
                            },
                        },
                        "Output": {"type": "string", "format": "uri"},
                    }
                }
            },
        },
        "imagen-3.0-generate-002": {
            "name": "Imagen 3",
            "description": "Google's Imagen 3 for high-quality image generation.",
            "openapi_schema": {
                "components": {
                    "schemas": {
                        "Input": {
                            "type": "object",
                            "required": ["prompt"],
                            "properties": {
                                "prompt": {
                                    "type": "string",
                                    "title": "Prompt",
                                    "description": "Text description of the image to generate.",
                                    "x-order": 0,
                                },
                                "negative_prompt": {
                                    "type": "string",
                                    "title": "Negative Prompt",
                                    "description": "What to avoid in the image.",
                                    "x-order": 1,
                                },
                                "aspect_ratio": {
                                    "type": "string",
                                    "title": "Aspect Ratio",
                                    "description": "Output aspect ratio.",
                                    "enum": ["1:1", "16:9", "9:16", "4:3", "3:4"],
                                    "default": "1:1",
                                    "x-order": 2,
                                },
                                "number_of_images": {
                                    "type": "integer",
                                    "title": "Number of Images",
                                    "description": "How many images to generate (1-4).",
                                    "minimum": 1,
                                    "maximum": 4,
                                    "default": 1,
                                    "x-order": 3,
                                },
                                "safety_filter_level": {
                                    "type": "string",
                                    "title": "Safety Filter",
                                    "description": "Content safety filtering level.",
                                    "enum": [
                                        "block_none",
                                        "block_few",
                                        "block_some",
                                        "block_most",
                                    ],
                                    "default": "block_some",
                                    "x-order": 4,
                                },
                                "person_generation": {
                                    "type": "string",
                                    "title": "Person Generation",
                                    "description": "How to handle people in images.",
                                    "enum": ["dont_allow", "allow_adult", "allow_all"],
                                    "default": "allow_adult",
                                    "x-order": 5,
                                },
                            },
                        },
                        "Output": {
                            "type": "array",
                            "items": {"type": "string", "format": "uri"},
                        },
                    }
                }
            },
        },
    }

    def get_provider_name(self) -> str:
        return "vertex-ai"

    def can_handle(self, model_id: str, provider: Optional[str] = None) -> bool:
        """Check if this is a Vertex AI model."""
        if provider == "vertex-ai":
            return True
        # Check for known Vertex AI model patterns
        if model_id.startswith("veo-") or model_id.startswith("imagen-"):
            return True
        # Handle google/voice-name format for Cloud TTS
        model_name = model_id.split("/")[-1] if "/" in model_id else model_id
        return model_name in self.VERTEX_SCHEMAS

    def fetch_schema(self, model_id: str) -> Dict[str, Any]:
        """Return pre-defined schema for Vertex AI models."""
        # Handle google/voice-name format for Cloud TTS
        model_name = model_id.split("/")[-1] if "/" in model_id else model_id

        if model_name in self.VERTEX_SCHEMAS:
            schema_data = self.VERTEX_SCHEMAS[model_name].copy()
            schema_data["latest_version"] = {"id": model_id}
            return schema_data

        # For unknown Vertex AI models, return a minimal schema
        logger.warning(
            f"No pre-defined schema for Vertex AI model: {model_id}, using minimal schema"
        )
        return {
            "name": model_id,
            "description": f"Google Vertex AI model: {model_id}",
            "latest_version": {"id": model_id},
            "openapi_schema": {
                "components": {
                    "schemas": {
                        "Input": {
                            "type": "object",
                            "required": ["prompt"],
                            "properties": {
                                "prompt": {
                                    "type": "string",
                                    "title": "Prompt",
                                    "description": "Input prompt for the model.",
                                    "x-order": 0,
                                }
                            },
                        },
                        "Output": {"type": "string", "format": "uri"},
                    }
                }
            },
        }


class GoogleGenAISchemaProvider(SchemaProvider):
    """Handler for Google GenAI models (Lyria, etc.)."""

    # Pre-defined schemas for Google GenAI models
    GENAI_SCHEMAS: Dict[str, Dict[str, Any]] = {
        "lyria-2": {
            "name": "Lyria-2",
            "description": "Google's Lyria 2 music generation. Creates 48kHz stereo instrumental tracks.",
            "openapi_schema": {
                "components": {
                    "schemas": {
                        "Input": {
                            "type": "object",
                            "required": ["prompt"],
                            "properties": {
                                "prompt": {
                                    "type": "string",
                                    "title": "Prompt",
                                    "description": "Describe the music: genre, mood, instruments, tempo (e.g., 'upbeat electronic dance music with synths, 120 BPM').",
                                    "x-order": 0,
                                },
                                "negative_prompt": {
                                    "type": "string",
                                    "title": "Negative Prompt",
                                    "description": "What to avoid in the music (e.g., 'vocals, lyrics, distortion').",
                                    "x-order": 1,
                                },
                                "duration_seconds": {
                                    "type": "integer",
                                    "title": "Duration (seconds)",
                                    "description": "Length of generated music (max 30 seconds).",
                                    "minimum": 5,
                                    "maximum": 30,
                                    "default": 15,
                                    "x-order": 2,
                                },
                                "temperature": {
                                    "type": "number",
                                    "title": "Temperature",
                                    "description": "Creativity level (0.0-1.0). Higher = more experimental.",
                                    "minimum": 0.0,
                                    "maximum": 1.0,
                                    "default": 0.7,
                                    "x-order": 3,
                                },
                            },
                        },
                        "Output": {"type": "string", "format": "uri"},
                    }
                }
            },
        },
        "musicfx": {
            "name": "MusicFX",
            "description": "Google's MusicFX for AI-generated music loops and tracks.",
            "openapi_schema": {
                "components": {
                    "schemas": {
                        "Input": {
                            "type": "object",
                            "required": ["prompt"],
                            "properties": {
                                "prompt": {
                                    "type": "string",
                                    "title": "Prompt",
                                    "description": "Describe the music style and mood.",
                                    "x-order": 0,
                                },
                                "duration_seconds": {
                                    "type": "integer",
                                    "title": "Duration (seconds)",
                                    "description": "Length of generated music.",
                                    "minimum": 5,
                                    "maximum": 60,
                                    "default": 15,
                                    "x-order": 1,
                                },
                            },
                        },
                        "Output": {"type": "string", "format": "uri"},
                    }
                }
            },
        },
        "gemini-2.5-flash-lite-tts": {
            "name": "Gemini 2.5 Flash Lite TTS",
            "description": "Google's Gemini 2.5 Flash Lite for fast, natural text-to-speech. Supports multiple languages and voices.",
            "openapi_schema": {
                "components": {
                    "schemas": {
                        "Input": {
                            "type": "object",
                            "required": ["text"],
                            "properties": {
                                "text": {
                                    "type": "string",
                                    "title": "Text",
                                    "description": "The text to convert to speech.",
                                    "x-order": 0,
                                },
                                "voice": {
                                    "type": "string",
                                    "title": "Voice",
                                    "description": "Voice preset to use.",
                                    "enum": [
                                        "Zephyr",
                                        "Puck",
                                        "Charon",
                                        "Kore",
                                        "Fenrir",
                                        "Leda",
                                        "Orus",
                                        "Aoede",
                                    ],
                                    "default": "Zephyr",
                                    "x-order": 1,
                                },
                                "language_code": {
                                    "type": "string",
                                    "title": "Language",
                                    "description": "Language code (e.g., en-US, es-ES, fr-FR, de-DE, ja-JP).",
                                    "default": "en-US",
                                    "x-order": 2,
                                },
                                "speaking_rate": {
                                    "type": "number",
                                    "title": "Speaking Rate",
                                    "description": "Speed of speech (0.5-2.0). 1.0 is normal.",
                                    "minimum": 0.5,
                                    "maximum": 2.0,
                                    "default": 1.0,
                                    "x-order": 3,
                                },
                                "pitch": {
                                    "type": "number",
                                    "title": "Pitch",
                                    "description": "Voice pitch adjustment (-10 to 10 semitones).",
                                    "minimum": -10.0,
                                    "maximum": 10.0,
                                    "default": 0.0,
                                    "x-order": 4,
                                },
                            },
                        },
                        "Output": {"type": "string", "format": "uri"},
                    }
                }
            },
        },
    }

    def get_provider_name(self) -> str:
        return "google-genai"

    def can_handle(self, model_id: str, provider: Optional[str] = None) -> bool:
        """Check if this is a Google GenAI model."""
        if provider == "google-genai":
            return True
        # Check for known GenAI models
        model_name = model_id.split("/")[-1] if "/" in model_id else model_id
        return model_name in self.GENAI_SCHEMAS

    def fetch_schema(self, model_id: str) -> Dict[str, Any]:
        """Return pre-defined schema for Google GenAI models."""
        # Extract model name (handle google/lyria-2 format)
        model_name = model_id.split("/")[-1] if "/" in model_id else model_id

        if model_name in self.GENAI_SCHEMAS:
            schema_data = self.GENAI_SCHEMAS[model_name].copy()
            schema_data["latest_version"] = {"id": model_id}
            return schema_data

        logger.warning(f"No pre-defined schema for Google GenAI model: {model_id}")
        return {
            "name": model_id,
            "description": f"Google GenAI model: {model_id}",
            "latest_version": {"id": model_id},
            "openapi_schema": {
                "components": {
                    "schemas": {
                        "Input": {
                            "type": "object",
                            "required": ["prompt"],
                            "properties": {
                                "prompt": {
                                    "type": "string",
                                    "title": "Prompt",
                                    "description": "Input prompt for the model.",
                                    "x-order": 0,
                                }
                            },
                        },
                        "Output": {"type": "string", "format": "uri"},
                    }
                }
            },
        }


class SchemaService:
    """
    Multi-Provider Schema Service.

    Fetches and parses model schemas from multiple providers:
    - Replicate: Uses Replicate API for OpenAPI schemas
    - Vertex AI: Uses pre-defined schemas for Google Cloud models
    - Google GenAI: Uses pre-defined schemas for Google AI models

    Architecture: Strategy Pattern with provider-specific handlers.
    """

    # Parameters to hide from UI (internal/advanced)
    HIDDEN_PARAMS = {
        "seed",
        "num_outputs",
        "disable_safety_checker",
        "output_format",
        "output_quality",
        "webhook",
        "webhook_events_filter",
    }

    # Keywords that indicate file inputs
    FILE_KEYWORDS = {
        "file",
        "audio",
        "image",
        "video",
        "voice",
        "music",
        "reference",
        "input_",
    }

    # Keywords that indicate audio content types
    AUDIO_CONTENT_KEYWORDS = {
        "voice": "voice",
        "vocal": "voice",
        "speech": "voice",
        "music": "music",
        "song": "music",
        "melody": "melody",
        "instrumental": "instrumental",
        "reference_audio": "voice",  # Usually voice reference
    }

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize multi-provider schema service.

        Args:
            cache_dir: Directory for caching schemas. Defaults to DeepAgents/.cache/schemas/
        """
        # API tokens
        self.replicate_token = os.environ.get("REPLICATE_API_TOKEN")

        # Setup cache directory
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path(__file__).parent.parent / ".cache" / "schemas"

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._schema_cache: Dict[str, ModelSchema] = {}

        # Initialize provider handlers (order matters - more specific first)
        self._providers: List[SchemaProvider] = []

        # Vertex AI handler (no API token needed - uses pre-defined schemas)
        self._providers.append(VertexAISchemaProvider())

        # Google GenAI handler (no API token needed - uses pre-defined schemas)
        self._providers.append(GoogleGenAISchemaProvider())

        # Replicate handler (requires API token)
        if self.replicate_token:
            self._providers.append(ReplicateSchemaProvider(self.replicate_token))
        else:
            logger.warning(
                "REPLICATE_API_TOKEN not set - Replicate schema fetching disabled"
            )

        # Load cached schemas from disk
        self._load_disk_cache()

    def _load_disk_cache(self) -> None:
        """Load cached schemas from disk."""
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    schema = self._dict_to_schema(data)
                    self._schema_cache[schema.model_id] = schema
            except Exception as e:
                logger.warning(f"Failed to load cached schema {cache_file}: {e}")

    def _get_cache_path(self, model_id: str) -> Path:
        """Get cache file path for a model."""
        safe_name = hashlib.md5(model_id.encode()).hexdigest()
        return self.cache_dir / f"{safe_name}.json"

    def _dict_to_schema(self, data: Dict[str, Any]) -> ModelSchema:
        """Convert dict to ModelSchema."""
        controls = [
            ControlDefinition(
                name=c["name"],
                control_type=ControlType(c["control_type"]),
                label=c["label"],
                description=c.get("description", ""),
                required=c.get("required", False),
                default=c.get("default"),
                minimum=c.get("minimum"),
                maximum=c.get("maximum"),
                step=c.get("step"),
                options=c.get("options", []),
                accepted_types=c.get("accepted_types", []),
                max_duration=c.get("max_duration"),
                min_duration=c.get("min_duration"),
                order=c.get("order", 0),
            )
            for c in data.get("controls", [])
        ]

        requirements = [
            AssetRequirement(
                param_name=r["param_name"],
                asset_type=r["asset_type"],
                description=r.get("description", ""),
                required=r.get("required", True),
                accepted_formats=r.get("accepted_formats", []),
                min_duration=r.get("min_duration"),
                max_duration=r.get("max_duration"),
                content_type=r.get("content_type"),
            )
            for r in data.get("asset_requirements", [])
        ]

        return ModelSchema(
            model_id=data["model_id"],
            name=data["name"],
            description=data.get("description", ""),
            controls=controls,
            asset_requirements=requirements,
            output_type=data.get("output_type", "unknown"),
            raw_schema=data.get("raw_schema", {}),
            fetched_at=data.get("fetched_at", 0),
            version_id=data.get("version_id"),
            provider=data.get("provider", "replicate"),
        )

    def _schema_to_dict(self, schema: ModelSchema) -> Dict[str, Any]:
        """Convert ModelSchema to dict for caching."""
        return {
            "model_id": schema.model_id,
            "name": schema.name,
            "description": schema.description,
            "controls": [
                {
                    "name": c.name,
                    "control_type": c.control_type.value,
                    "label": c.label,
                    "description": c.description,
                    "required": c.required,
                    "default": c.default,
                    "minimum": c.minimum,
                    "maximum": c.maximum,
                    "step": c.step,
                    "options": c.options,
                    "accepted_types": c.accepted_types,
                    "max_duration": c.max_duration,
                    "min_duration": c.min_duration,
                    "order": c.order,
                }
                for c in schema.controls
            ],
            "asset_requirements": [
                {
                    "param_name": r.param_name,
                    "asset_type": r.asset_type,
                    "description": r.description,
                    "required": r.required,
                    "accepted_formats": r.accepted_formats,
                    "min_duration": r.min_duration,
                    "max_duration": r.max_duration,
                    "content_type": r.content_type,
                }
                for r in schema.asset_requirements
            ],
            "output_type": schema.output_type,
            "raw_schema": schema.raw_schema,
            "fetched_at": schema.fetched_at,
            "version_id": schema.version_id,
            "provider": schema.provider,
        }

    def _get_provider_for_model(
        self, model_id: str, provider_hint: Optional[str] = None
    ) -> Optional[SchemaProvider]:
        """
        Find the appropriate provider handler for a model.

        Args:
            model_id: Model identifier
            provider_hint: Optional provider name hint (from ModelRegistry)

        Returns:
            SchemaProvider that can handle this model, or None
        """
        for provider in self._providers:
            if provider.can_handle(model_id, provider_hint):
                return provider
        return None

    def _fetch_model_info(
        self, model_id: str, provider_hint: Optional[str] = None
    ) -> Tuple[Dict[str, Any], str]:
        """
        Fetch model info using the appropriate provider handler.

        Args:
            model_id: Model identifier (format depends on provider)
            provider_hint: Optional provider name from ModelRegistry

        Returns:
            Tuple of (model_info dict, provider_name)

        Raises:
            ValueError: If no provider can handle the model (Fail Fast)
        """
        # Find appropriate provider
        provider = self._get_provider_for_model(model_id, provider_hint)

        if provider is None:
            raise ValueError(
                f"No schema provider available for model: {model_id}. "
                f"Provider hint: {provider_hint}. "
                f"Available providers: {[p.get_provider_name() for p in self._providers]}"
            )

        logger.info(f"Using {provider.get_provider_name()} provider for: {model_id}")
        schema_data = provider.fetch_schema(model_id)
        return schema_data, provider.get_provider_name()

    def _infer_control_type(
        self, name: str, prop: Dict[str, Any]
    ) -> Tuple[ControlType, Optional[str]]:
        """
        Infer the UI control type from schema property.

        Returns:
            Tuple of (ControlType, asset_content_type or None)
        """
        prop_type = prop.get("type", "string")
        prop_format = prop.get("format", "")
        description = prop.get("description", "").lower()
        name_lower = name.lower()

        # Check if it should be hidden
        if name in self.HIDDEN_PARAMS:
            return ControlType.HIDDEN, None

        # Check for enum (select)
        if "enum" in prop or "allOf" in prop:
            return ControlType.SELECT, None

        # Check for file inputs
        is_file_param = any(kw in name_lower for kw in self.FILE_KEYWORDS)
        is_uri_format = (
            prop_format == "uri" or "url" in description or "file" in description
        )

        # Only string-typed (or untyped) properties and arrays of them can be
        # file inputs: the keyword heuristic used to run first and misrendered
        # this file's own schemas (Veo `generate_audio` boolean -> audio picker
        # + bogus asset requirement; Imagen `number_of_images` integer -> image
        # upload). Arrays keep their file treatment (Replicate list-of-uri params).
        if prop_type in ("string", "array") and (is_file_param or is_uri_format):
            # Determine content type from name/description
            content_type = None
            for keyword, ctype in self.AUDIO_CONTENT_KEYWORDS.items():
                if keyword in name_lower or keyword in description:
                    content_type = ctype
                    break

            # Determine file type
            if (
                "audio" in name_lower
                or "voice" in name_lower
                or "music" in name_lower
                or "song" in name_lower
            ):
                return ControlType.AUDIO_FILE, content_type
            elif "video" in name_lower:
                return ControlType.VIDEO_FILE, None
            elif "image" in name_lower or "photo" in name_lower:
                return ControlType.IMAGE_FILE, None
            else:
                return ControlType.FILE, content_type

        # Boolean
        if prop_type == "boolean":
            return ControlType.CHECKBOX, None

        # Numbers with range
        if prop_type in ("integer", "number"):
            has_range = "minimum" in prop or "maximum" in prop
            if has_range:
                return ControlType.SLIDER, None
            return ControlType.NUMBER, None

        # Strings
        if prop_type == "string":
            # Long text (prompts, lyrics)
            if any(
                kw in name_lower for kw in ["prompt", "lyrics", "text", "description"]
            ):
                return ControlType.TEXT_AREA, None
            return ControlType.TEXT, None

        return ControlType.TEXT, None

    def _parse_openapi_schema(
        self,
        model_id: str,
        model_info: Dict[str, Any],
        provider_name: str = "replicate",
    ) -> ModelSchema:
        """
        Parse OpenAPI schema into ModelSchema with controls.

        Args:
            model_id: Model identifier
            model_info: Full model info from provider
            provider_name: Name of the provider that supplied the schema

        Returns:
            Parsed ModelSchema
        """
        name = model_info.get("name", model_id.split("/")[-1])
        description = model_info.get("description", "")

        # Get latest version schema (may be directly in model_info for non-Replicate)
        latest_version = model_info.get("latest_version", {})
        version_id = latest_version.get("id")

        # Schema may be at different locations depending on provider
        openapi_schema = model_info.get("openapi_schema") or latest_version.get(
            "openapi_schema", {}
        )

        # Get input schema
        components = openapi_schema.get("components", {})
        schemas = components.get("schemas", {})
        input_schema = schemas.get("Input", {})
        output_schema = schemas.get("Output", {})

        properties = input_schema.get("properties", {})
        required_fields = set(input_schema.get("required", []))

        controls: List[ControlDefinition] = []
        asset_requirements: List[AssetRequirement] = []

        for idx, (param_name, prop) in enumerate(properties.items()):
            control_type, content_type = self._infer_control_type(param_name, prop)

            # Skip hidden controls from the public list
            if control_type == ControlType.HIDDEN:
                continue

            # Create label from param name
            label = param_name.replace("_", " ").title()

            # Build control definition
            control = ControlDefinition(
                name=param_name,
                control_type=control_type,
                label=label,
                description=prop.get("description", ""),
                required=param_name in required_fields,
                default=prop.get("default"),
                minimum=prop.get("minimum"),
                maximum=prop.get("maximum"),
                order=prop.get("x-order", idx),
            )

            # Handle enums
            if "enum" in prop:
                control.options = prop["enum"]
            elif "allOf" in prop:
                # Handle allOf references
                for ref in prop.get("allOf", []):
                    if "$ref" in ref:
                        ref_name = ref["$ref"].split("/")[-1]
                        ref_schema = schemas.get(ref_name, {})
                        if "enum" in ref_schema:
                            control.options = ref_schema["enum"]

            # Handle numeric ranges
            if control_type == ControlType.SLIDER:
                # Infer step from type
                if prop.get("type") == "integer":
                    control.step = 1
                else:
                    # Estimate step from range
                    if control.minimum is not None and control.maximum is not None:
                        range_size = control.maximum - control.minimum
                        control.step = range_size / 100  # 100 steps

            controls.append(control)

            # Check if this is an asset requirement
            if control_type in (
                ControlType.AUDIO_FILE,
                ControlType.VIDEO_FILE,
                ControlType.IMAGE_FILE,
                ControlType.FILE,
            ):
                asset_type_map = {
                    ControlType.AUDIO_FILE: "audio",
                    ControlType.VIDEO_FILE: "video",
                    ControlType.IMAGE_FILE: "image",
                    ControlType.FILE: "file",
                }

                asset_req = AssetRequirement(
                    param_name=param_name,
                    asset_type=asset_type_map[control_type],
                    description=prop.get("description", ""),
                    required=param_name in required_fields,
                    content_type=content_type,
                )

                # Try to extract duration constraints from description
                desc_lower = prop.get("description", "").lower()
                if "second" in desc_lower or "duration" in desc_lower:
                    # Try to parse duration hints
                    import re

                    duration_match = re.search(r"(\d+)\s*(?:second|sec|s)", desc_lower)
                    if duration_match:
                        duration_val = int(duration_match.group(1))
                        # Heuristic: if mentioned as max, set as max
                        if "max" in desc_lower or "up to" in desc_lower:
                            asset_req.max_duration = float(duration_val)
                        elif "min" in desc_lower or "at least" in desc_lower:
                            asset_req.min_duration = float(duration_val)
                        else:
                            # Default: treat as target/max
                            asset_req.max_duration = float(duration_val)

                asset_requirements.append(asset_req)

        # Sort controls by order
        controls.sort(key=lambda c: c.order)

        # Infer output type from output schema or model category
        output_type = "unknown"
        output_schema_type = output_schema.get("type", "")
        if "items" in output_schema:
            items_format = output_schema.get("items", {}).get("format", "")
            if items_format == "uri":
                # Could be audio, video, or image - infer from model name
                model_lower = model_id.lower()
                if any(
                    kw in model_lower
                    for kw in ["music", "audio", "song", "voice", "speech"]
                ):
                    output_type = "audio"
                elif any(kw in model_lower for kw in ["video", "film", "movie"]):
                    output_type = "video"
                elif any(
                    kw in model_lower
                    for kw in ["image", "picture", "photo", "flux", "sdxl", "stable"]
                ):
                    output_type = "image"

        return ModelSchema(
            model_id=model_id,
            name=name,
            description=description,
            controls=controls,
            asset_requirements=asset_requirements,
            output_type=output_type,
            raw_schema=openapi_schema,
            fetched_at=time.time(),
            version_id=version_id,
            provider=provider_name,
        )

    def get_schema(
        self,
        model_id: str,
        force_refresh: bool = False,
        cache_ttl: int = 86400,  # 24 hours
        provider_hint: Optional[str] = None,
    ) -> ModelSchema:
        """
        Get schema for a model, using cache if available.

        Supports multiple providers via strategy pattern:
        - Replicate models: Fetches from Replicate API
        - Vertex AI models: Uses pre-defined schemas
        - Google GenAI models: Uses pre-defined schemas

        Args:
            model_id: Model identifier (format depends on provider)
            force_refresh: If True, bypass cache
            cache_ttl: Cache time-to-live in seconds
            provider_hint: Optional provider name (from ModelRegistry)

        Returns:
            Parsed ModelSchema

        Raises:
            ValueError: If schema fetch fails (Fail Fast)
        """
        # Check memory cache
        if not force_refresh and model_id in self._schema_cache:
            cached = self._schema_cache[model_id]
            if time.time() - cached.fetched_at < cache_ttl:
                logger.debug(f"Schema cache hit: {model_id}")
                return cached

        # Fetch from appropriate provider
        logger.info(f"Fetching schema for: {model_id} (provider_hint: {provider_hint})")
        model_info, provider_name = self._fetch_model_info(model_id, provider_hint)
        schema = self._parse_openapi_schema(model_id, model_info, provider_name)

        # Cache to memory and disk
        self._schema_cache[model_id] = schema
        cache_path = self._get_cache_path(model_id)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(self._schema_to_dict(schema), f, indent=2)

        logger.info(
            f"Schema cached: {model_id} ({len(schema.controls)} controls, provider: {provider_name})"
        )
        return schema

    def get_schema_for_registry_model(self, model_id: str) -> ModelSchema:
        """
        Get schema for a model registered in ModelRegistry.

        Automatically detects the provider from the registry.

        Args:
            model_id: Model identifier as registered in ModelRegistry

        Returns:
            Parsed ModelSchema
        """
        # Import here to avoid circular dependency
        from DeepAgents.services.model_registry import get_model_registry

        registry = get_model_registry()
        model_info = registry.get(model_id)

        if model_info:
            provider_hint = model_info.provider.value if model_info.provider else None
            return self.get_schema(model_id, provider_hint=provider_hint)
        else:
            # Model not in registry, try to auto-detect provider
            return self.get_schema(model_id)

    def get_asset_requirements(self, model_id: str) -> List[AssetRequirement]:
        """Get asset requirements for a model."""
        schema = self.get_schema(model_id)
        return schema.asset_requirements

    def has_asset_requirements(self, model_id: str) -> bool:
        """Check if model requires any asset inputs."""
        requirements = self.get_asset_requirements(model_id)
        return any(r.required for r in requirements)

    def clear_cache(self, model_id: Optional[str] = None) -> None:
        """Clear cached schema(s)."""
        if model_id:
            self._schema_cache.pop(model_id, None)
            cache_path = self._get_cache_path(model_id)
            if cache_path.exists():
                cache_path.unlink()
        else:
            self._schema_cache.clear()
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()


# Singleton instance
_schema_service: Optional[SchemaService] = None


def get_schema_service() -> SchemaService:
    """Get singleton schema service instance."""
    global _schema_service
    if _schema_service is None:
        _schema_service = SchemaService()
    return _schema_service
