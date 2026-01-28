"""
System Configuration Module.
Central configuration management for DeepAgents.
"""

import json
import logging
from typing import Any, Dict, Optional

# Default System Configuration (The Truth)
DEFAULT_SYSTEM_CONFIG = {
    "version": "1.1.0",
    "description": "DeepAgents Global Configuration Matrix",
    "provider_settings": {
        "google": {
            "strategy": "native",
            "package": "langchain_google_genai",
            "class_name": "ChatGoogleGenerativeAI",
            "description": "Uses Google GenAI SDK with Vertex Adapter (High Performance).",
            "default_region": "us-central1",
        },
        "anthropic": {
            "strategy": "native",
            "package": "langchain_anthropic",
            "class_name": "ChatAnthropic",
            "description": "Native Anthropic Integration.",
        },
        "openai": {
            "strategy": "native",
            "package": "langchain_openai",
            "class_name": "ChatOpenAI",
        },
        "replicate": {
            "strategy": "api_proxy",
            "package": "replicate",
            "description": "Direct API calls via Replicate Python Client.",
        },
    },
    "agents": {
        "Director": {
            "intelligence_model": "google/gemini-2.0-flash-001",
            "provider": "Google",
        },
        "Composer": {
            "intelligence_model": "google/gemini-2.0-flash-001",
            "provider": "Google",
            "capabilities": [
                {
                    "type": "music_generation",
                    "models": [
                        {
                            "id": "replicate/minimax/music-1.5",
                            "priority": 120,
                            "description": (
                                "Minimax Music-1.5 (Replicate). Primary Music Engine. Full songs with vocals."
                            ),
                            "strengths": (
                                "High fidelity full songs with lyrics, "
                                "consistent structure, fast generation."
                            ),
                            "weaknesses": (
                                "600 char lyric limit, length determined by lyrics volume."
                            ),
                            "supports_lyrics": True,
                            "supports_duration": False,
                            "max_duration_seconds": 240,
                        },
                        {
                            "id": "replicate/meta/musicgen",
                            "priority": 110,
                            "description": (
                                "Meta MusicGen (Replicate). Instrumental only."
                            ),
                            "strengths": (
                                "Fast, cheap, excellent instrumental quality, "
                                "explicit duration control."
                            ),
                            "weaknesses": ("No lyrics support, max 30s clips."),
                            "supports_lyrics": False,
                            "supports_duration": True,
                            "max_duration_seconds": 30,
                        },
                        {
                            "id": "replicate/lucataco/ace-step",
                            "priority": 100,
                            "description": (
                                "ACE-Step (Replicate). Text-to-music with lyric alignment."
                            ),
                            "strengths": (
                                "Excellent lyric synchronization, supports explicit "
                                "duration constraints."
                            ),
                            "weaknesses": (
                                "Can be expensive, occasionally hallucinates phantom vocals."
                            ),
                            "supports_lyrics": True,
                            "supports_duration": True,
                            "max_duration_seconds": 240,
                        },
                        {
                            "id": "vertex/publishers/google/models/lyria-002",
                            "priority": 10,
                            "description": (
                                "Google Lyria-002 (Vertex AI - Restricted Quota)."
                            ),
                            "supports_lyrics": False,
                            "max_duration_seconds": 60,
                        },
                    ],
                },
                {
                    "type": "voice_generation",
                    "models": [
                        {
                            "id": "google/en-US-Studio-O",
                            "priority": 110,
                            "description": "Google Cloud TTS - Studio O (Female)",
                            "provider": "Google",
                        },
                        {
                            "id": "google/en-US-Studio-M",
                            "priority": 105,
                            "description": "Google Cloud TTS - Studio M (Male)",
                            "provider": "Google",
                        },
                        {
                            "id": "lucataco/xtts-v2",
                            "priority": 100,
                            "description": "XTTS v2 (Replicate). Good cloning.",
                        },
                        {
                            "id": "minimax/speech-01",
                            "priority": 90,
                            "description": "Minimax Speech 01 (Replicate).",
                        },
                    ],
                    "asset_paths": {"voice_clones": "Artifacts/Audio/Voices"},
                },
            ],
        },
        "Researcher": {
            "intelligence_model": "google/gemini-2.0-flash-exp",
            "provider": "Google",
        },
        "Confidence": {
            "intelligence_model": "google/gemini-2.0-flash-exp",
            "provider": "Google",
        },
        "Cinematographer": {
            "intelligence_model": "google/gemini-2.0-flash-001",
            "provider": "Google",
            "capabilities": [
                {
                    "type": "video_generation",
                    "models": [
                        {
                            "id": "replicate/wan-video/wan-2.5-t2v-fast",
                            "priority": 100,
                            "description": "Alibaba Wan 2.5 fast text-to-video.",
                            "strengths": "Fast, cheap, good motion quality, 480p-720p.",
                            "weaknesses": (
                                "Lower resolution than premium models, 5-10s duration."
                            ),
                            "best_practices": (
                                "Use descriptive prompts, specify camera movements."
                            ),
                        },
                        {
                            "id": "replicate/luma/ray-flash-2-540p",
                            "priority": 90,
                            "description": "Luma Ray Flash - fast high quality.",
                            "strengths": "High quality, good prompt adherence.",
                            "weaknesses": "540p resolution, moderate cost.",
                            "best_practices": (
                                "Detailed prompts with specific lighting/camera angles."
                            ),
                        },
                        {
                            "id": "replicate/kwaivgi/kling-v2.5-turbo-pro",
                            "priority": 85,
                            "description": "Kuaishou Kling v2.5 Turbo Pro - fast premium video.",
                            "strengths": "Excellent motion, fast generation, 10s duration.",
                            "weaknesses": "Newer model, less community examples.",
                            "best_practices": (
                                "Use cinematic prompts, specify camera movements explicitly."
                            ),
                        },
                        {
                            "id": "replicate/openai/sora-2-pro",
                            "priority": 95,
                            "description": "OpenAI Sora 2 Pro - premium video generation.",
                            "strengths": "Best-in-class quality, 20s duration, excellent physics.",
                            "weaknesses": "Higher cost, slower generation.",
                            "best_practices": (
                                "Detailed scene descriptions, specify temporal progression."
                            ),
                        },
                        {
                            "id": "replicate/bytedance/seedance-1-pro-fast",
                            "priority": 80,
                            "description": "ByteDance Seedance - fast video generation.",
                            "strengths": "Fast generation, good value, 8s duration.",
                            "weaknesses": "Less consistent than premium models.",
                            "best_practices": (
                                "Simple prompts work best, avoid complex multi-subject scenes."
                            ),
                        },
                        {
                            "id": "replicate/minimax/hailuo-2.3",
                            "priority": 82,
                            "description": "Minimax Hailuo 2.3 - balanced video generation.",
                            "strengths": "Good quality-to-cost ratio, consistent output.",
                            "weaknesses": "6s max duration.",
                            "best_practices": (
                                "Works well with character-focused prompts."
                            ),
                        },
                        {
                            "id": "replicate/minimax/hailuo-2.3-fast",
                            "priority": 78,
                            "description": "Minimax Hailuo 2.3 Fast - quick iterations.",
                            "strengths": "Very fast, cheap, good for prototyping.",
                            "weaknesses": "Lower quality than standard Hailuo.",
                            "best_practices": (
                                "Use for quick previews before premium generation."
                            ),
                        },
                    ],
                },
                {
                    "type": "image_generation",
                    "models": [
                        {
                            "id": "google/imagen-3.0-generate-001",
                            "priority": 100,
                            "description": "Google Vertex AI Imagen 3",
                            "strengths": (
                                "Excellent text rendering, photorealism, distinct styles."
                            ),
                            "weaknesses": "Strict safety filters.",
                            "best_practices": (
                                "Use negative prompts for exclusions, specify aspect ratio clearly."
                            ),
                        },
                        {
                            "id": "replicate/flux-schnell",
                            "priority": 90,
                            "description": "Black Forest Labs Flux Model",
                            "strengths": "Fastest SOTA model, great prompt adherence.",
                            "weaknesses": "Less detail than Pro version.",
                            "best_practices": "Use 'cinematic' keywords, avoid vague terms.",
                        },
                    ],
                },
            ],
        },
    },
    "global_assets": {
        "audio": "Artifacts/Audio",
        "video": "Artifacts/Video",
        "images": "Artifacts/Images",
        "data": "Artifacts/Data",
    },
}


class SystemConfiguration:
    """
    Singleton class handling the loading and access of global system configuration.
    Synchronizes with the LangSmith Hub for remote configuration management.
    """

    _instance = None
    _config: Optional[Dict[str, Any]] = None
    logger: logging.Logger

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SystemConfiguration, cls).__new__(cls)
            cls._instance.logger = logging.getLogger("SystemConfig")
        return cls._instance

    def load_config(self) -> Dict[str, Any]:
        """
        Loads the configuration. Ideally from Hub, falling back to local default.
        In this implementation, it relies on HubManager to handle the sync.
        """
        if self._config:
            return self._config

        # Import here to avoid circular dependencies
        from DeepAgents.hub_manager import get_or_push_configuration

        try:
            self.logger.info("Initializing System Configuration from Hub...")
            config_json = get_or_push_configuration(
                "deepagents-system-config", json.dumps(DEFAULT_SYSTEM_CONFIG, indent=2)
            )
            self._config = json.loads(config_json)
            self.logger.info("Configuration loaded successfully.")
        except Exception as e:
            self.logger.critical(f"FATAL: Failed to load configuration from Hub: {e}")
            raise e  # FAIL FAST - Do not use local default

        if self._config is None:
            raise ValueError("Configuration failed to load (None).")
        return self._config

    def get_provider_strategy(self, provider_name: str) -> Dict[str, Any]:
        """
        Returns the implementation strategy for a given provider.
        (e.g., Which package/class to use).
        """
        cfg = self.load_config()
        return cfg.get("provider_settings", {}).get(provider_name.lower(), {})

    def get_agent_intelligence(self, agent_name: str):
        """
        Retrieves the configured intelligence model (LLM) for a specific agent.
        Defaults to Google Gemini if not found.
        """
        cfg = self.load_config()
        return (
            cfg.get("agents", {})
            .get(agent_name, {})
            .get("intelligence_model", "google/gemini-2.0-flash-001")
        )

    def get_agent_params(self, agent_name: str) -> tuple[str, str]:
        """
        Helper: Returns (provider, model_name) for a given agent.
        Parses 'provider/model' format.
        """
        model_str = self.get_agent_intelligence(agent_name)
        if "/" in model_str:
            parts = model_str.split("/", 1)
            # Capitalize provider (google -> Google) for compatibility
            return parts[0].capitalize(), parts[1]

        # Heuristic fallback if just model name provided
        if "gemini" in model_str.lower():
            return "Google", model_str
        if "claude" in model_str.lower():
            return "Anthropic", model_str

        return "Google", model_str

    def get_capability_model(self, agent_name: str, capability_type: str):
        """
        Implements the 'Overloaded Function' logic.
        Returns the highest priority model for the requested capability.
        """
        cfg = self.load_config()
        capabilities = cfg.get("agents", {}).get(agent_name, {}).get("capabilities", [])

        target_cap = next(
            (c for c in capabilities if c.get("type") == capability_type), None
        )

        if not target_cap:
            return None

        models = target_cap.get("models", [])
        # Sort by priority desc
        models.sort(key=lambda x: x.get("priority", 0), reverse=True)

        if models:
            return models[0]  # Return highest priority
        return None
