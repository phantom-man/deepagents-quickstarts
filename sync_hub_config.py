"""
Sync ModelRegistry models to LangSmith Hub deepagents-system-config.
This script pushes a comprehensive config including ALL registered models.
"""
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client

# Load .env from DeepAgents folder
env_path = Path(__file__).parent / "DeepAgents" / ".env"
load_dotenv(env_path)

# Comprehensive system config with ALL models from ModelRegistry
UPDATED_SYSTEM_CONFIG = {
    "version": "1.2.0",
    "description": "DeepAgents Global Configuration Matrix - Full Model Sync",
    "provider_settings": {
        "google": {
            "strategy": "native",
            "package": "langchain_google_genai",
            "class_name": "ChatGoogleGenerativeAI",
            "description": "Uses Google GenAI SDK with Vertex Adapter (High Performance).",
            "default_region": "us-central1"
        },
        "anthropic": {
            "strategy": "native",
            "package": "langchain_anthropic",
            "class_name": "ChatAnthropic",
            "description": "Native Anthropic Integration."
        },
        "openai": {
            "strategy": "native",
            "package": "langchain_openai",
            "class_name": "ChatOpenAI"
        },
        "replicate": {
            "strategy": "api_proxy",
            "package": "replicate",
            "description": "Direct API calls via Replicate Python Client."
        }
    },
    "agents": {
        "Director": {
            "intelligence_model": "google/gemini-2.0-flash-001",
            "provider": "Google"
        },
        "Composer": {
            "intelligence_model": "google/gemini-2.0-flash-001",
            "provider": "Google",
            "capabilities": [
                {
                    "type": "music_generation",
                    "models": [
                        {
                            "id": "google/lyria-2",
                            "priority": 120,
                            "description": "Google Lyria 2 - High fidelity instrumental music generation.",
                            "provider": "google-genai",
                            "strengths": "Fast generation, high fidelity instrumental, consistent structure.",
                            "weaknesses": "No lyrics support, max 30s clips, strictly instrumental.",
                            "supports_lyrics": False,
                            "supports_duration": True,
                            "max_duration_seconds": 30
                        },
                        {
                            "id": "lucataco/ace-step",
                            "priority": 110,
                            "description": "State-of-the-art text-to-music with lyric alignment.",
                            "provider": "replicate",
                            "strengths": "Excellent lyric synchronization, supports explicit duration constraints.",
                            "weaknesses": "Can be expensive, occasionally hallucinates phantom vocals.",
                            "supports_lyrics": True,
                            "supports_duration": True,
                            "max_duration_seconds": 240
                        },
                        {
                            "id": "minimax/music-01",
                            "priority": 100,
                            "description": "Minimax Music 01 - High fidelity music with lyrics support.",
                            "provider": "replicate",
                            "strengths": "Best-in-class full song structure, emotional range, lyrics.",
                            "weaknesses": "Ignores explicit duration constraints.",
                            "supports_lyrics": True,
                            "supports_duration": False,
                            "max_duration_seconds": 240
                        },
                        {
                            "id": "meta/musicgen",
                            "priority": 50,
                            "description": "Meta MusicGen - Instrumental only music generation.",
                            "provider": "replicate",
                            "supports_lyrics": False,
                            "supports_duration": True,
                            "max_duration_seconds": 30
                        }
                    ]
                },
                {
                    "type": "voice_generation",
                    "models": [
                        {
                            "id": "gemini-2.5-flash-lite-tts",
                            "priority": 120,
                            "description": "Google Gemini 2.5 Flash Lite TTS - Fast multilingual voices.",
                            "provider": "google-genai"
                        },
                        {
                            "id": "google/en-US-Studio-O",
                            "priority": 115,
                            "description": "Google Cloud TTS Studio O - Premium female voice.",
                            "provider": "vertex-ai"
                        },
                        {
                            "id": "google/en-US-Studio-M",
                            "priority": 110,
                            "description": "Google Cloud TTS Studio M - Premium male voice.",
                            "provider": "vertex-ai"
                        },
                        {
                            "id": "minimax/speech-01",
                            "priority": 100,
                            "description": "Minimax Speech 01 - High quality TTS.",
                            "provider": "replicate"
                        },
                        {
                            "id": "lucataco/xtts-v2",
                            "priority": 90,
                            "description": "XTTS-v2 - Voice cloning support.",
                            "provider": "replicate"
                        },
                        {
                            "id": "jaaari/kokoro-82m",
                            "priority": 80,
                            "description": "Kokoro 82M - Lightweight fast TTS.",
                            "provider": "replicate"
                        }
                    ],
                    "asset_paths": {
                        "voice_clones": "Artifacts/Audio/Voices"
                    }
                }
            ]
        },
        "Researcher": {
            "intelligence_model": "google/gemini-2.0-flash-exp",
            "provider": "Google"
        },
        "Confidence": {
            "intelligence_model": "google/gemini-2.0-flash-exp",
            "provider": "Google"
        },
        "Cinematographer": {
            "intelligence_model": "google/gemini-2.0-flash-001",
            "provider": "Google",
            "capabilities": [
                {
                    "type": "video_generation",
                    "models": [
                        {
                            "id": "veo-3.1-fast-generate-001",
                            "priority": 130,
                            "description": "Google Veo 3.1 Fast - Premium AI video generation.",
                            "provider": "vertex-ai",
                            "strengths": "Highest quality, 720p/1080p, best prompt adherence.",
                            "weaknesses": "Most expensive, requires Vertex AI access.",
                            "best_practices": "Use detailed cinematic prompts with camera movements."
                        },
                        {
                            "id": "veo-3.1-generate-001",
                            "priority": 125,
                            "description": "Google Veo 3.1 - High quality video generation.",
                            "provider": "vertex-ai",
                            "strengths": "Best quality, longer clips possible.",
                            "weaknesses": "Expensive, slower than fast variant."
                        },
                        {
                            "id": "wan-video/wan-2.5-t2v-fast",
                            "priority": 100,
                            "description": "Alibaba Wan 2.5 Fast - Fast text-to-video.",
                            "provider": "replicate",
                            "strengths": "Fast, cheap, good motion quality, 480p-720p.",
                            "weaknesses": "Lower resolution than premium models, 5-10s duration.",
                            "best_practices": "Use descriptive prompts, specify camera movements."
                        },
                        {
                            "id": "luma/ray-flash-2-540p",
                            "priority": 95,
                            "description": "Luma Ray Flash 2 - Fast high quality video.",
                            "provider": "replicate",
                            "strengths": "High quality, good prompt adherence.",
                            "weaknesses": "540p resolution, moderate cost."
                        },
                        {
                            "id": "minimax/video-01-live",
                            "priority": 90,
                            "description": "Minimax Video 01 Live - Real-time video generation.",
                            "provider": "replicate"
                        },
                        {
                            "id": "minimax/hailuo-2.3",
                            "priority": 85,
                            "description": "Minimax Hailuo 2.3 - High quality video.",
                            "provider": "replicate"
                        },
                        {
                            "id": "minimax/hailuo-2.3-fast",
                            "priority": 80,
                            "description": "Minimax Hailuo 2.3 Fast - Quick video generation.",
                            "provider": "replicate"
                        },
                        {
                            "id": "kwaivgi/kling-v2.5-turbo-pro",
                            "priority": 75,
                            "description": "Kling V2.5 Turbo Pro - Fast high quality video.",
                            "provider": "replicate"
                        },
                        {
                            "id": "bytedance/seedance-1-pro-fast",
                            "priority": 70,
                            "description": "ByteDance Seedance 1 Pro Fast - Dance/motion specialized.",
                            "provider": "replicate"
                        },
                        {
                            "id": "openai/sora-2-pro",
                            "priority": 65,
                            "description": "OpenAI Sora 2 Pro - Premium video generation.",
                            "provider": "replicate"
                        }
                    ]
                },
                {
                    "type": "image_generation",
                    "models": [
                        {
                            "id": "google/imagen-3",
                            "priority": 120,
                            "description": "Google Imagen 3 - Premium image generation.",
                            "provider": "vertex-ai",
                            "strengths": "Excellent text rendering, photorealism, distinct styles.",
                            "weaknesses": "Strict safety filters.",
                            "best_practices": "Use negative prompts for exclusions, specify aspect ratio."
                        },
                        {
                            "id": "black-forest-labs/flux-schnell",
                            "priority": 100,
                            "description": "FLUX Schnell - Fastest SOTA image model.",
                            "provider": "replicate",
                            "strengths": "Fastest SOTA model, great prompt adherence.",
                            "weaknesses": "Less detail than Pro version."
                        },
                        {
                            "id": "black-forest-labs/flux-1.1-pro",
                            "priority": 95,
                            "description": "FLUX 1.1 Pro - High detail image generation.",
                            "provider": "replicate",
                            "strengths": "Best detail, excellent for complex scenes.",
                            "weaknesses": "Slower than Schnell, higher cost."
                        },
                        {
                            "id": "stability-ai/sdxl",
                            "priority": 85,
                            "description": "Stability AI SDXL - Versatile image generation.",
                            "provider": "replicate"
                        },
                        {
                            "id": "bytedance/sdxl-lightning-4step",
                            "priority": 80,
                            "description": "SDXL Lightning 4-Step - Ultra fast image generation.",
                            "provider": "replicate",
                            "strengths": "Extremely fast (4 steps), good quality.",
                            "weaknesses": "Less refined than full SDXL."
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


def main():
    """Push updated config to LangSmith Hub."""
    client = Client()
    
    # Get user handle
    try:
        # Try to get from API key info
        api_key = os.getenv("LANGCHAIN_API_KEY", "")
        # For personal workspaces, we need the handle
        handle = os.getenv("LANGCHAIN_HUB_HANDLE")
        
        if not handle:
            print("LANGCHAIN_HUB_HANDLE not set, attempting to detect...")
            # Could try to get from workspace info, but for now require it
            print("ERROR: Please set LANGCHAIN_HUB_HANDLE in .env")
            print("You can find this in LangSmith under Settings > Account")
            return
    except Exception as e:
        print(f"Error getting user info: {e}")
        return
    
    repo_name = "deepagents-system-config"
    full_repo = f"{handle}/{repo_name}"
    
    print(f"Pushing config to: {full_repo}")
    print(f"Config version: {UPDATED_SYSTEM_CONFIG['version']}")
    print(f"Total video models: {len(UPDATED_SYSTEM_CONFIG['agents']['Cinematographer']['capabilities'][0]['models'])}")
    print(f"Total image models: {len(UPDATED_SYSTEM_CONFIG['agents']['Cinematographer']['capabilities'][1]['models'])}")
    print(f"Total music models: {len(UPDATED_SYSTEM_CONFIG['agents']['Composer']['capabilities'][0]['models'])}")
    print(f"Total voice models: {len(UPDATED_SYSTEM_CONFIG['agents']['Composer']['capabilities'][1]['models'])}")
    
    # Format as ChatPromptTemplate for Hub
    config_content = json.dumps(UPDATED_SYSTEM_CONFIG, indent=2)
    
    from langchain_core.prompts import ChatPromptTemplate
    
    # Create a prompt template that contains the config as a system message
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", config_content)
    ])
    
    try:
        # Push to hub
        url = client.push_prompt(
            repo_name,
            object=prompt_template,
            description="DeepAgents System Configuration - Full Model Registry Sync",
            is_public=False
        )
        print(f"\n✓ Successfully pushed to Hub!")
        print(f"  URL: {url}")
        
        # Also update local cache
        cache_dir = os.path.join(os.path.dirname(__file__), "DeepAgents/.cache/prompts")
        os.makedirs(cache_dir, exist_ok=True)
        cache_file = os.path.join(cache_dir, "deepagents-system-config.txt")
        
        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(f"```plaintext\n{config_content}\n```")
        
        print(f"  Local cache updated: {cache_file}")
        
    except Exception as e:
        print(f"\n✗ Error pushing to Hub: {e}")
        print("\nTrying to create new prompt...")
        try:
            url = client.push_prompt(
                repo_name,
                object=config_content,
                description="DeepAgents System Configuration - Full Model Registry Sync",
                is_public=False
            )
            print(f"✓ Created new prompt: {url}")
        except Exception as e2:
            print(f"✗ Failed to create: {e2}")


if __name__ == "__main__":
    main()
