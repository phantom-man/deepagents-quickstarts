"""
Model Registry - Curated catalog of AI models for media generation.

This module provides a centralized registry of known models with their
capabilities, output types, and compatible dependencies.

Philosophy: Single Source of Truth for model metadata.
"""
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class ModelCategory(Enum):
    """Categories of generative models."""
    VIDEO = "video"
    AUDIO_MUSIC = "audio_music"
    AUDIO_VOICE = "audio_voice"
    AUDIO_SFX = "audio_sfx"
    IMAGE = "image"
    TEXT = "text"


class OutputType(Enum):
    """Types of model outputs."""
    VIDEO_FILE = "video_file"
    AUDIO_FILE = "audio_file"
    IMAGE_FILE = "image_file"
    TEXT = "text"
    URL = "url"


class InputRequirement(Enum):
    """Types of input a model may require."""
    TEXT_PROMPT = "text_prompt"
    AUDIO_VOICE = "audio_voice"
    AUDIO_MUSIC = "audio_music"
    IMAGE = "image"
    VIDEO = "video"


@dataclass
class ModelInfo:
    """Information about a specific model."""
    id: str  # Replicate model ID (owner/name)
    name: str  # Display name
    category: ModelCategory
    output_type: OutputType
    description: str = ""

    # Input requirements
    required_inputs: List[InputRequirement] = field(default_factory=list)
    optional_inputs: List[InputRequirement] = field(default_factory=list)

    # Capabilities
    max_duration: Optional[float] = None  # Max output duration in seconds
    supports_lyrics: bool = False  # For music models
    supports_instrumental: bool = True  # For music models

    # Quality/Speed tier
    tier: str = "standard"  # fast, standard, premium

    # Additional metadata
    tags: Set[str] = field(default_factory=set)
    deprecated: bool = False

    @property
    def replicate_url(self) -> str:
        """Get Replicate model URL."""
        return f"https://replicate.com/{self.id}"

    def requires_asset(self, asset_type: InputRequirement) -> bool:
        """Check if model requires specific asset type."""
        return asset_type in self.required_inputs


class ModelRegistry:
    """
    Registry of known AI models for media generation.

    Provides lookup, filtering, and dependency resolution.
    """

    def __init__(self):
        self._models: Dict[str, ModelInfo] = {}
        self._load_default_models()

    def _load_default_models(self):
        """Load curated list of known models."""

        # ===================
        # VIDEO MODELS
        # ===================

        self.register(ModelInfo(
            id="wan-video/wan-2.5-t2v-fast",
            name="Wan 2.5 Fast (T2V)",
            category=ModelCategory.VIDEO,
            output_type=OutputType.VIDEO_FILE,
            description="Fast text-to-video generation at 480p. Good for quick iterations.",
            max_duration=5.0,
            tier="fast",
            tags={"text-to-video", "480p"}
        ))

        self.register(ModelInfo(
            id="luma/ray-flash-2-540p",
            name="Luma Ray Flash 2",
            category=ModelCategory.VIDEO,
            output_type=OutputType.VIDEO_FILE,
            description="High-quality video generation at 540p from Luma AI.",
            max_duration=5.0,
            tier="standard",
            tags={"text-to-video", "540p"}
        ))

        self.register(ModelInfo(
            id="minimax/video-01-live",
            name="Minimax Video-01 Live",
            category=ModelCategory.VIDEO,
            output_type=OutputType.URL,
            description="Premium video generation from Minimax.",
            max_duration=6.0,
            tier="premium",
            tags={"text-to-video", "premium"}
        ))

        # ===================
        # MUSIC/AUDIO MODELS
        # ===================

        self.register(ModelInfo(
            id="google-deepmind/lyria-2",
            name="Lyria-002 (Google)",
            category=ModelCategory.AUDIO_MUSIC,
            output_type=OutputType.AUDIO_FILE,
            description="Google DeepMind's music generation model. High-fidelity music with optional lyrics.",
            supports_lyrics=True,
            supports_instrumental=True,
            max_duration=60.0,
            tier="premium",
            tags={"music", "lyrics", "instrumental", "google"}
        ))

        self.register(ModelInfo(
            id="minimax/music-01",
            name="Minimax Music-01",
            category=ModelCategory.AUDIO_MUSIC,
            output_type=OutputType.AUDIO_FILE,
            description="Full songs with lyrics. Requires voice reference for best results.",
            required_inputs=[InputRequirement.AUDIO_VOICE],
            supports_lyrics=True,
            supports_instrumental=False,
            max_duration=300.0,
            tier="premium",
            tags={"music", "lyrics", "voice-clone"}
        ))

        self.register(ModelInfo(
            id="facebookresearch/musicgen",
            name="MusicGen (Meta)",
            category=ModelCategory.AUDIO_MUSIC,
            output_type=OutputType.AUDIO_FILE,
            description="Instrumental music generation. Good for background tracks.",
            supports_lyrics=False,
            supports_instrumental=True,
            max_duration=30.0,
            tier="standard",
            tags={"music", "instrumental", "meta"}
        ))

        self.register(ModelInfo(
            id="ace-step/ace-step-v1-3-5b",
            name="ACE-Step v1.3",
            category=ModelCategory.AUDIO_MUSIC,
            output_type=OutputType.AUDIO_FILE,
            description="Advanced music generation with fine control. Supports lyrics and instrumental.",
            supports_lyrics=True,
            supports_instrumental=True,
            max_duration=120.0,
            tier="premium",
            tags={"music", "lyrics", "instrumental", "advanced"}
        ))

        # ===================
        # VOICE MODELS
        # ===================

        self.register(ModelInfo(
            id="minimax/speech-01",
            name="Minimax Speech-01",
            category=ModelCategory.AUDIO_VOICE,
            output_type=OutputType.AUDIO_FILE,
            description="High-fidelity text-to-speech with voice cloning.",
            optional_inputs=[InputRequirement.AUDIO_VOICE],
            max_duration=60.0,
            tier="premium",
            tags={"tts", "voice-clone"}
        ))

        self.register(ModelInfo(
            id="lucataco/xtts-v2",
            name="XTTS-v2",
            category=ModelCategory.AUDIO_VOICE,
            output_type=OutputType.AUDIO_FILE,
            description="Coqui TTS with voice cloning. Robust fallback option.",
            optional_inputs=[InputRequirement.AUDIO_VOICE],
            max_duration=30.0,
            tier="standard",
            tags={"tts", "voice-clone", "coqui"}
        ))

        self.register(ModelInfo(
            id="jaaari/kokoro-82m",
            name="Kokoro 82M",
            category=ModelCategory.AUDIO_VOICE,
            output_type=OutputType.AUDIO_FILE,
            description="Lightweight TTS model. Fast and efficient.",
            max_duration=30.0,
            tier="fast",
            tags={"tts", "lightweight"}
        ))

        # ===================
        # IMAGE MODELS
        # ===================

        self.register(ModelInfo(
            id="black-forest-labs/flux-schnell",
            name="FLUX Schnell",
            category=ModelCategory.IMAGE,
            output_type=OutputType.IMAGE_FILE,
            description="Fast image generation from Black Forest Labs.",
            tier="fast",
            tags={"image", "fast", "flux"}
        ))

        self.register(ModelInfo(
            id="black-forest-labs/flux-1.1-pro",
            name="FLUX 1.1 Pro",
            category=ModelCategory.IMAGE,
            output_type=OutputType.IMAGE_FILE,
            description="Premium image generation with high detail.",
            tier="premium",
            tags={"image", "premium", "flux"}
        ))

        self.register(ModelInfo(
            id="stability-ai/sdxl",
            name="Stable Diffusion XL",
            category=ModelCategory.IMAGE,
            output_type=OutputType.IMAGE_FILE,
            description="Stable Diffusion XL for high-quality images.",
            tier="standard",
            tags={"image", "sdxl", "stability"}
        ))

        self.register(ModelInfo(
            id="bytedance/sdxl-lightning-4step",
            name="SDXL Lightning 4-Step",
            category=ModelCategory.IMAGE,
            output_type=OutputType.IMAGE_FILE,
            description="Extremely fast SDXL variant with 4-step inference.",
            tier="fast",
            tags={"image", "sdxl", "fast", "bytedance"}
        ))

        self.register(ModelInfo(
            id="google/imagen-3",
            name="Imagen 3 (Google)",
            category=ModelCategory.IMAGE,
            output_type=OutputType.IMAGE_FILE,
            description="Google's Imagen 3 for premium image generation.",
            tier="premium",
            tags={"image", "google", "premium"}
        ))

    def register(self, model: ModelInfo):
        """Register a model in the registry."""
        self._models[model.id] = model
        logger.debug(f"Registered model: {model.id}")

    def get(self, model_id: str) -> Optional[ModelInfo]:
        """Get model by ID."""
        return self._models.get(model_id)

    def get_by_category(
        self,
        category: ModelCategory,
        exclude_deprecated: bool = True
    ) -> List[ModelInfo]:
        """Get all models in a category."""
        models = [
            m for m in self._models.values()
            if m.category == category
        ]
        if exclude_deprecated:
            models = [m for m in models if not m.deprecated]
        return sorted(models, key=lambda m: (m.tier != "fast", m.name))

    def get_video_models(self) -> List[ModelInfo]:
        """Get all video generation models."""
        return self.get_by_category(ModelCategory.VIDEO)

    def get_music_models(self) -> List[ModelInfo]:
        """Get all music generation models."""
        return self.get_by_category(ModelCategory.AUDIO_MUSIC)

    def get_voice_models(self) -> List[ModelInfo]:
        """Get all voice/TTS models."""
        return self.get_by_category(ModelCategory.AUDIO_VOICE)

    def get_image_models(self) -> List[ModelInfo]:
        """Get all image generation models."""
        return self.get_by_category(ModelCategory.IMAGE)

    def get_compatible_generators(
        self,
        requirement: InputRequirement
    ) -> List[ModelInfo]:
        """
        Get models that can generate assets for a given requirement.

        Example: If a music model requires AUDIO_VOICE, this returns
        all voice models that can generate that asset.
        """
        category_map = {
            InputRequirement.AUDIO_VOICE: ModelCategory.AUDIO_VOICE,
            InputRequirement.AUDIO_MUSIC: ModelCategory.AUDIO_MUSIC,
            InputRequirement.IMAGE: ModelCategory.IMAGE,
            InputRequirement.VIDEO: ModelCategory.VIDEO,
        }

        target_category = category_map.get(requirement)
        if not target_category:
            return []

        return self.get_by_category(target_category)

    def get_models_for_dropdown(
        self,
        category: ModelCategory
    ) -> Dict[str, str]:
        """
        Get models formatted for Streamlit dropdown.

        Returns:
            Dict of display_name -> model_id
        """
        models = self.get_by_category(category)
        return {m.name: m.id for m in models}

    def find_by_tags(self, *tags: str) -> List[ModelInfo]:
        """Find models that have all specified tags."""
        tags_set = set(tags)
        return [
            m for m in self._models.values()
            if tags_set.issubset(m.tags) and not m.deprecated
        ]

    def get_all_models(self) -> List[ModelInfo]:
        """Get all registered models."""
        return list(self._models.values())


# Singleton instance
_registry_instance: Optional[ModelRegistry] = None


def get_model_registry() -> ModelRegistry:
    """Get singleton ModelRegistry instance."""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ModelRegistry()
    return _registry_instance


# Convenience functions

def get_video_model_options() -> Dict[str, str]:
    """Get video models for dropdown selection."""
    return get_model_registry().get_models_for_dropdown(ModelCategory.VIDEO)


def get_music_model_options() -> Dict[str, str]:
    """Get music models for dropdown selection."""
    return get_model_registry().get_models_for_dropdown(ModelCategory.AUDIO_MUSIC)


def get_voice_model_options() -> Dict[str, str]:
    """Get voice models for dropdown selection."""
    return get_model_registry().get_models_for_dropdown(ModelCategory.AUDIO_VOICE)


def get_image_model_options() -> Dict[str, str]:
    """Get image models for dropdown selection."""
    return get_model_registry().get_models_for_dropdown(ModelCategory.IMAGE)


def model_requires_voice(model_id: str) -> bool:
    """Check if a model requires voice input."""
    model = get_model_registry().get(model_id)
    if model:
        return model.requires_asset(InputRequirement.AUDIO_VOICE)
    return False
