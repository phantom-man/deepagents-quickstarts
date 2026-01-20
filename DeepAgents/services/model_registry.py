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


class ModelProvider(Enum):
    """Provider/host for the model."""
    REPLICATE = "replicate"
    VERTEX_AI = "vertex-ai"
    GOOGLE_GENAI = "google-genai"


@dataclass
class ModelInfo:
    """Information about a specific model."""
    id: str  # Model ID (format depends on provider)
    name: str  # Display name
    category: ModelCategory
    output_type: OutputType
    description: str = ""

    # Provider (determines how to fetch schema and call API)
    provider: ModelProvider = ModelProvider.REPLICATE

    # Input requirements
    required_inputs: List[InputRequirement] = field(default_factory=list)
    optional_inputs: List[InputRequirement] = field(default_factory=list)

    # Capabilities
    max_duration: Optional[float] = None  # Max output duration in seconds
    supports_lyrics: bool = False  # For music models
    supports_instrumental: bool = True  # For music models

    # Quality/Speed tier
    tier: str = "standard"  # fast, standard, premium

    # Cost information
    cost_per_run: Optional[float] = None  # Estimated cost in USD per run
    cost_unit: str = "run"  # "run", "second", "minute"

    # Additional metadata
    tags: Set[str] = field(default_factory=set)
    deprecated: bool = False

    @property
    def replicate_url(self) -> Optional[str]:
        """Get Replicate model URL (only for Replicate models)."""
        if self.provider == ModelProvider.REPLICATE:
            return f"https://replicate.com/{self.id}"
        return None

    @property
    def is_replicate(self) -> bool:
        """Check if this is a Replicate-hosted model."""
        return self.provider == ModelProvider.REPLICATE

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
            tags={"text-to-video", "480p"},
            cost_per_run=0.035
        ))

        self.register(ModelInfo(
            id="luma/ray-flash-2-540p",
            name="Luma Ray Flash 2",
            category=ModelCategory.VIDEO,
            output_type=OutputType.VIDEO_FILE,
            description="High-quality video generation at 540p from Luma AI.",
            max_duration=5.0,
            tier="standard",
            tags={"text-to-video", "540p"},
            cost_per_run=0.25
        ))

        self.register(ModelInfo(
            id="minimax/video-01-live",
            name="Minimax Video-01 Live",
            category=ModelCategory.VIDEO,
            output_type=OutputType.URL,
            description="Premium video generation from Minimax.",
            max_duration=6.0,
            tier="premium",
            tags={"text-to-video", "premium"},
            cost_per_run=0.50
        ))

        self.register(ModelInfo(
            id="veo-3.1-fast-generate-001",
            name="Veo 3.1 Fast (Google)",
            category=ModelCategory.VIDEO,
            output_type=OutputType.VIDEO_FILE,
            description="Google Vertex AI video generation. Fast mode, 720p/1080p. $0.10/sec.",
            provider=ModelProvider.VERTEX_AI,
            max_duration=8.0,
            tier="fast",
            tags={"text-to-video", "google", "vertex-ai", "720p", "1080p"},
            cost_per_run=0.80,  # ~8 sec * $0.10/sec
            cost_unit="second"
        ))

        self.register(ModelInfo(
            id="veo-3.1-generate-001",
            name="Veo 3.1 (Google)",
            category=ModelCategory.VIDEO,
            output_type=OutputType.VIDEO_FILE,
            description="Google Vertex AI premium video. 720p/1080p/4K. $0.20-$0.40/sec.",
            provider=ModelProvider.VERTEX_AI,
            max_duration=8.0,
            tier="premium",
            tags={"text-to-video", "google", "vertex-ai", "4k"},
            cost_per_run=1.60,  # ~8 sec * $0.20/sec
            cost_unit="second"
        ))

        self.register(ModelInfo(
            id="kwaivgi/kling-v2.5-turbo-pro",
            name="Kling v2.5 Turbo Pro",
            category=ModelCategory.VIDEO,
            output_type=OutputType.VIDEO_FILE,
            description="Kuaishou Kling video generation. Fast turbo mode with pro quality.",
            max_duration=10.0,
            tier="fast",
            tags={"text-to-video", "kling", "kuaishou"},
            cost_per_run=0.20
        ))

        self.register(ModelInfo(
            id="openai/sora-2-pro",
            name="Sora 2 Pro (OpenAI)",
            category=ModelCategory.VIDEO,
            output_type=OutputType.VIDEO_FILE,
            description="OpenAI's Sora 2 Pro video generation. Premium quality.",
            max_duration=20.0,
            tier="premium",
            tags={"text-to-video", "openai", "sora"},
            cost_per_run=0.80
        ))

        self.register(ModelInfo(
            id="bytedance/seedance-1-pro-fast",
            name="Seedance 1 Pro Fast",
            category=ModelCategory.VIDEO,
            output_type=OutputType.VIDEO_FILE,
            description="ByteDance Seedance video generation. Fast mode.",
            max_duration=8.0,
            tier="fast",
            tags={"text-to-video", "bytedance", "seedance"},
            cost_per_run=0.15
        ))

        self.register(ModelInfo(
            id="minimax/hailuo-2.3",
            name="Hailuo 2.3 (Minimax)",
            category=ModelCategory.VIDEO,
            output_type=OutputType.VIDEO_FILE,
            description="Minimax Hailuo 2.3 video generation. Standard quality.",
            max_duration=6.0,
            tier="standard",
            tags={"text-to-video", "minimax", "hailuo"},
            cost_per_run=0.30
        ))

        self.register(ModelInfo(
            id="minimax/hailuo-2.3-fast",
            name="Hailuo 2.3 Fast (Minimax)",
            category=ModelCategory.VIDEO,
            output_type=OutputType.VIDEO_FILE,
            description="Minimax Hailuo 2.3 fast mode. Quick iterations.",
            max_duration=6.0,
            tier="fast",
            tags={"text-to-video", "minimax", "hailuo", "fast"},
            cost_per_run=0.15
        ))

        # ===================
        # MUSIC/AUDIO MODELS
        # ===================

        self.register(ModelInfo(
            id="google/lyria-2",
            name="Lyria-2 (Google)",
            category=ModelCategory.AUDIO_MUSIC,
            output_type=OutputType.AUDIO_FILE,
            description="Google's music generation model. 30-sec instrumental clips, supports genres from classical to electronic. NO VOCALS/LYRICS.",
            provider=ModelProvider.GOOGLE_GENAI,
            supports_lyrics=False,
            supports_instrumental=True,
            max_duration=30.0,
            tier="premium",
            tags={"music", "instrumental", "google", "genai"},
            cost_per_run=0.05
        ))

        self.register(ModelInfo(
            id="minimax/music-1.5",
            name="Minimax Music-1.5",
            category=ModelCategory.AUDIO_MUSIC,
            output_type=OutputType.AUDIO_FILE,
            description="Full songs with vocals from lyrics + text prompt. No reference required. Up to 4 mins. $0.03/song.",
            required_inputs=[InputRequirement.TEXT_PROMPT],  # Just needs lyrics + prompt
            supports_lyrics=True,
            supports_instrumental=True,  # Can do both
            max_duration=240.0,  # 4 minutes max
            tier="premium",
            tags={"music", "lyrics", "vocals", "minimax"},
            cost_per_run=0.03
        ))

        self.register(ModelInfo(
            id="meta/musicgen",
            name="MusicGen (Meta)",
            category=ModelCategory.AUDIO_MUSIC,
            output_type=OutputType.AUDIO_FILE,
            description="Instrumental music generation from text prompts. Good for background tracks.",
            supports_lyrics=False,
            supports_instrumental=True,
            max_duration=60.0,
            tier="standard",
            tags={"music", "instrumental", "meta"},
            cost_per_run=0.097
        ))

        self.register(ModelInfo(
            id="lucataco/ace-step",
            name="ACE-Step",
            category=ModelCategory.AUDIO_MUSIC,
            output_type=OutputType.AUDIO_FILE,
            description="Music+vocals from text tags and lyrics. Supports [verse], [chorus], [bridge] structure.",
            supports_lyrics=True,
            supports_instrumental=True,
            max_duration=240.0,
            tier="standard",
            tags={"music", "lyrics", "instrumental", "vocals"},
            cost_per_run=0.10
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
            tags={"tts", "voice-clone"},
            cost_per_run=0.02
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
            tags={"tts", "voice-clone", "coqui"},
            cost_per_run=0.01
        ))

        self.register(ModelInfo(
            id="jaaari/kokoro-82m",
            name="Kokoro 82M",
            category=ModelCategory.AUDIO_VOICE,
            output_type=OutputType.AUDIO_FILE,
            description="Lightweight TTS model. Fast and efficient.",
            max_duration=30.0,
            tier="fast",
            tags={"tts", "lightweight"},
            cost_per_run=0.005
        ))

        self.register(ModelInfo(
            id="gemini-2.5-flash-lite-tts",
            name="Gemini 2.5 Flash Lite TTS",
            category=ModelCategory.AUDIO_VOICE,
            output_type=OutputType.AUDIO_FILE,
            description="Google's Gemini 2.5 Flash Lite for text-to-speech. Fast, multilingual, natural voices.",
            provider=ModelProvider.GOOGLE_GENAI,
            max_duration=300.0,
            tier="fast",
            tags={"tts", "google", "genai", "multilingual"},
            cost_per_run=0.001
        ))

        self.register(ModelInfo(
            id="google/en-US-Studio-O",
            name="Google Cloud TTS Studio O",
            category=ModelCategory.AUDIO_VOICE,
            output_type=OutputType.AUDIO_FILE,
            description="Google Cloud Text-to-Speech Studio O voice. Premium female voice with natural intonation.",
            provider=ModelProvider.VERTEX_AI,
            max_duration=300.0,
            tier="standard",
            tags={"tts", "google", "cloud-tts", "female", "studio"},
            cost_per_run=0.016
        ))

        self.register(ModelInfo(
            id="google/en-US-Studio-M",
            name="Google Cloud TTS Studio M",
            category=ModelCategory.AUDIO_VOICE,
            output_type=OutputType.AUDIO_FILE,
            description="Google Cloud Text-to-Speech Studio M voice. Premium male voice with natural intonation.",
            provider=ModelProvider.VERTEX_AI,
            max_duration=300.0,
            tier="standard",
            tags={"tts", "google", "cloud-tts", "male", "studio"},
            cost_per_run=0.016
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
            provider=ModelProvider.VERTEX_AI,
            tier="premium",
            tags={"image", "google", "premium", "vertex-ai"}
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
