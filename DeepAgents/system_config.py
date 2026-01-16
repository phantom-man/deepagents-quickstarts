"""
System Configuration Module.
Central configuration management for DeepAgents.
"""

import json
import logging
from typing import Dict, Any, Optional

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
                            "id": "publishers/google/models/lyria-002",
                            "priority": 120,
                            "description": (
                                "Google Lyria Native (Vertex AI). Primary Music Engine."
                            ),
                            "strengths": (
                                "Fast generation, high fidelity instrumental, "
                                "consistent structure."
                            ),
                            "weaknesses": (
                                "No lyrics support, max 60s clips, strict instrumental focus."
                            ),
                            "supports_lyrics": False,
                            "supports_duration": False,
                            "max_duration_seconds": 60,
                        },
                        {
                            "id": "lucataco/ace-step",
                            "priority": 110,
                            "description": (
                                "State-of-the-art text-to-music with lyric alignment."
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
                            "id": "minimax/music-1.5",
                            "priority": 100,
                            "description": (
                                "High fidelity instrumental and lyrical music generation."
                            ),
                            "strengths": (
                                "Best-in-class full song structure, emotional range."
                            ),
                            "weaknesses": (
                                "Ignores explicit duration constraints "
                                "(length determined by lyrics/text volume)."
                            ),
                            "supports_lyrics": True,
                            "supports_duration": False,
                            "max_duration_seconds": 240,
                        },
                        {
                            "id": "google/lyria-2",
                            "priority": 10,
                            "description": (
                                "Google DeepMind MusicLM v2 (Replicate - Deprecated/Missing)."
                            ),
                            "supports_lyrics": False,
                            "max_duration_seconds": 60,
                        },
                        {
                            "id": "meta/musicgen",
                            "priority": 50,
                            "description": "Instrumental only music generation.",
                            "supports_lyrics": False,
                            "max_duration_seconds": 30,
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
