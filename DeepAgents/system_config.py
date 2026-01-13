import json
import logging
from typing import Dict, Any, List

# Default System Configuration (The Truth)
DEFAULT_SYSTEM_CONFIG = {
    "version": "1.0.0",
    "description": "DeepAgents Global Configuration Matrix",
    "agents": {
        "Director": {
            "intelligence_model": "anthropic/claude-3-haiku-20240307",
            "provider": "Anthropic"
        },
        "Composer": {
            "intelligence_model": "anthropic/claude-3-haiku-20240307",
            "capabilities": [
                {
                    "type": "music_generation",
                    "models": [
                        { 
                            "id": "minimax/music-1.5", 
                            "priority": 100, 
                            "description": "High fidelity instrumental and lyrical music generation.",
                            "supports_lyrics": True,
                            "max_duration_seconds": 240
                        },
                        { 
                            "id": "meta/musicgen", 
                            "priority": 50, 
                            "description": "Instrumental only music generation.",
                            "supports_lyrics": False,
                            "max_duration_seconds": 30
                        }
                    ]
                },
                {
                    "type": "voice_generation",
                    "models": [
                        {
                            "id": "elevenlabs/multilingual-v2",
                            "priority": 100
                        },
                         {
                            "id": "lucataco/xtts-v2",
                            "priority": 80
                        }
                    ],
                    "asset_paths": {
                        "voice_clones": "Artifacts/Audio/Voices"
                    }
                }
            ]
        },
        "Cinematographer": {
             "intelligence_model": "anthropic/claude-3-haiku-20240307",
             "capabilities": [
                {
                    "type": "video_generation",
                    "models": [
                        {
                            "id": "haiper/v2",
                            "priority": 100,
                            "description": "High quality video generation.",
                        },
                        {
                            "id": "minimax/video-01",
                            "priority": 90,
                             "description": "Fast video generation.",
                        }
                    ]
                }
            ]
        }
    },
    "global_assets": {
        "audio": "Artifacts/Audio",
        "video": "Artifacts/Video",
        "images": "Artifacts/Images",
        "data": "Artifacts/Data"
    }
}

class SystemConfiguration:
    _instance = None
    _config: Dict[str, Any] = None

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
            config_json = get_or_push_configuration("deepagents-system-config", json.dumps(DEFAULT_SYSTEM_CONFIG, indent=2))
            self._config = json.loads(config_json)
            self.logger.info("Configuration loaded successfully.")
        except Exception as e:
            self.logger.error(f"Failed to load from Hub, using local default. Error: {e}")
            self._config = DEFAULT_SYSTEM_CONFIG
            
        return self._config

    def get_agent_intelligence(self, agent_name: str):
        cfg = self.load_config()
        return cfg.get("agents", {}).get(agent_name, {}).get("intelligence_model", "anthropic/claude-3-haiku-20240307")

    def get_capability_model(self, agent_name: str, capability_type: str):
        """
        Implements the 'Overloaded Function' logic.
        Returns the highest priority model for the requested capability.
        """
        cfg = self.load_config()
        capabilities = cfg.get("agents", {}).get(agent_name, {}).get("capabilities", [])
        
        target_cap = next((c for c in capabilities if c.get("type") == capability_type), None)
        
        if not target_cap:
            return None
            
        models = target_cap.get("models", [])
        # Sort by priority desc
        models.sort(key=lambda x: x.get("priority", 0), reverse=True)
        
        if models:
            return models[0] # Return highest priority
        return None

