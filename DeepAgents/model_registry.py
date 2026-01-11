"""
Registry of Supported External Models (Replicate, etc.)
Defines ID, Inputs, and Display Options for dynamic GUI generation.
"""

REPLICATE_MODELS = {
    # === AUDIO / MUSIC ===
    "audio": {
        "minimax/music-01": {
            "id": "minimax/music-01",
            "name": "Minimax Music 01 (Songs with Lyrics)",
            "provider": "Replicate",
            "cost_type": "high",
            "pricing": {"type": "run", "cost": 0.10},  # Estimate
            "inputs": [
                {
                    "name": "prompt",
                    "type": "text",
                    "label": "Song Description/Style",
                    "default": "A synthwave song about robots"
                },
                {
                    "name": "lyrics",
                    "type": "textarea",
                    "label": "Lyrics (Optional - Generated if empty)",
                    "default": ""
                }
            ]
        },
        "meta/musicgen:fast": {
            "id": "meta/musicgen:b05b1dff1d8c6dc63d14b0cdb42135378dcb87f6373b0d3d341ede46e59e2b38",
            "name": "Meta MusicGen (Instrumental)",
            "provider": "Replicate",
            "cost_type": "low",
            "pricing": {"type": "second", "cost": 0.0005},  # T4 GPU time approx
            "inputs": [
                {
                    "name": "prompt",
                    "type": "text",
                    "label": "Music Description",
                    "default": "Lo-fi hip hop beat"
                },
                {
                    "name": "duration",
                    "type": "number",
                    "label": "Duration (sec)",
                    "min": 1,
                    "max": 60,
                    "default": 20
                },
                {
                    "name": "model_version",
                    "type": "select",
                    "options": ["stereo-large", "stereo-melody", "large", "melody"],
                    "default": "stereo-large"
                }
            ]
        },
        "riffusion/riffusion": {
            "id": ("riffusion/riffusion:"
                   "8cf61ea6c56afd61d8f5b9ffd14d7c216c0a93844ce2d82ac1c9ecc9c7f24e05"),
            "name": "Riffusion (Spectrogram Audio)",
            "provider": "Replicate",
            "cost_type": "low",
            "pricing": {"type": "run", "cost": 0.02},
            "inputs": [
                {
                    "name": "prompt_a",
                    "type": "text",
                    "label": "Prompt",
                    "default": "church bells"
                },
                {
                    "name": "denoising",
                    "type": "number",
                    "label": "Denoising",
                    "min": 0.0,
                    "max": 1.0,
                    "default": 0.75
                }
            ]
        },
        "suno-ai/bark": {
            "id": "suno-ai/bark:b76242b40d67c76ab6742e987628a2a9ac019e11d56ab96c4e91ce03b79b2787",
            "name": "Suno Bark (Speech + FX)",
            "provider": "Replicate",
            "cost_type": "medium",
            "pricing": {"type": "second", "cost": 0.001},
            "inputs": [
                {
                    "name": "prompt",
                    "type": "text",
                    "label": "Text to Speak",
                    "default": "Hello World [laughter]"
                },
                {
                    "name": "history_prompt",
                    "type": "select",
                    "options": [
                        "en_speaker_0", "en_speaker_1", "fr_speaker_0", "announcer"
                    ],
                    "default": "en_speaker_0"
                }
            ]
        }
    },

    # === LLM (TEXT) ===
    "llm": {
        "meta/meta-llama-3-70b-instruct": {
            "id": "meta/meta-llama-3-70b-instruct",
            "name": "Meta Llama 3 70B Instruct",
            "provider": "Replicate",
            "cost_type": "low",
            "pricing": {"type": "token", "cost": 0.00065}, 
            "inputs": [] 
        },
    },

    # === VIDEO ===
    "video": {
        "zeroscope/v2-xl": {
            "id": ("anotherjesse/zeroscope-v2-xl:"
                   "9f747673945c62801b13b84701c783929c0ee784e4748ec062204894dda1a351"),
            "name": "Zeroscope v2 XL (Budget Friendly)",
            "provider": "Replicate",
            "cost_type": "very_low",
            "pricing": {"type": "second", "cost": 0.0023},
            "inputs": [
                {
                    "name": "prompt",
                    "type": "text",
                    "label": "Prompt",
                    "default": "A futuristic city in neon rain"
                },
                {"name": "num_frames", "type": "number", "label": "Frames", "default": 24},
                {"name": "fps", "type": "number", "label": "FPS", "default": 24},
                {"name": "width", "type": "number", "label": "Width", "default": 1024},
                {"name": "height", "type": "number", "label": "Height", "default": 576}
            ]
        },
        "lucataco/animate-diff": {
            "id": ("lucataco/animate-diff:"
                   "beecf59c50aa2333b9341236894575ec7f742fab79fc9af38d81373595f93998"),
            "name": "AnimateDiff (Stylized Loops)",
            "provider": "Replicate",
            "cost_type": "low",
            "pricing": {"type": "second", "cost": 0.005},
            "inputs": [
                {
                    "name": "prompt",
                    "type": "text",
                    "label": "Prompt",
                    "default": (
                        "masterpiece, best quality, 1girl, solo, cherry blossoms, "
                        "hanami, pink flower, white flower, spring season, wisteria, "
                        "petals, flower, outdoors, falling petals, white hair, blue eyes"
                    )
                },
                {
                    "name": "motion_module",
                    "type": "select",
                    "options": ["mm_sd_v14", "mm_sd_v15_v2"],
                    "default": "mm_sd_v15_v2"
                },
                {
                    "name": "steps",
                    "type": "number",
                    "label": "Steps",
                    "min": 10,
                    "max": 50,
                    "default": 25
                },
                {"name": "guidance_scale", "type": "number", "label": "Guidance", "default": 7.5}
            ]
        }
    }
}

def get_model_options(category):
    """Returns list of (friendly_name, id) tuples for a category."""
    if category not in REPLICATE_MODELS:
        return []
    return [(v["name"], k) for k, v in REPLICATE_MODELS[category].items()]

def get_model_info(category, model_key):
    """Returns the dictionary info for a specific model key."""
    return REPLICATE_MODELS.get(category, {}).get(model_key, {})
