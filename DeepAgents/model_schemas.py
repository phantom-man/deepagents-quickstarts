"""
Model Schemas Registry - Dynamic Model Schema Allocation
Zero-Touch LangSmith Hub Integration for Model-Specific Output Formats

This module provides a centralized registry for model output schemas,
enabling dynamic schema loading based on capability model selection.

Architecture:
    Hub Structure:
        {org}/
        ├── cinematographer-video-{model_id}-output-schema
        ├── cinematographer-image-{model_id}-output-schema
        ├── composer-music-{model_id}-output-schema
        └── composer-voice-{model_id}-output-schema

    Self-Healing Pattern:
        Pull from Hub → Use cached → Push default if missing
"""

import logging
from typing import Optional, Dict, Any
from DeepAgents.hub_manager import get_or_push_prompt

logger = logging.getLogger(__name__)

# =============================================================================
# CINEMATOGRAPHER MODEL SCHEMAS
# =============================================================================

# --- VIDEO GENERATION SCHEMAS ---

DEFAULT_ZEROSCOPE_SCHEMA = """
You are optimizing a prompt for the Zeroscope V2-XL Video Model.
The Director requests: "{input_text}"

MODEL CHARACTERISTICS:
- Resolution: 576x320 (low-res, SD quality)
- Duration: 2-4 seconds typical
- Strengths: Fast generation, cost-effective, single-subject consistency
- Weaknesses: Struggles with complex motion, text rendering, multiple subjects

PROMPT OPTIMIZATION RULES:
1. SIMPLIFY: Use direct, concrete descriptions (no abstract concepts)
2. SINGLE SUBJECT: Focus on ONE subject/action per prompt
3. STATIC BACKGROUNDS: Describe backgrounds as still/minimal movement
4. MOTION KEYWORDS: Include: "slow motion", "smooth movement", "cinematic"
5. AVOID: Complex interactions, fast action, text/logos, crowds

REQUIRED OUTPUT FORMAT:
VISUAL_PROMPT: <A single, optimized prompt string. 50-100 words max.>
NEGATIVE_PROMPT: <What to avoid. E.g., "blurry, distorted, low quality, fast motion">
"""

DEFAULT_WAN_SCHEMA = """
You are optimizing a prompt for the Wan 2.5 T2V (Text-to-Video) Model.
The Director requests: "{input_text}"

MODEL CHARACTERISTICS:
- Resolution: 480p (720x480)
- Duration: ~5 seconds (81 frames at 16fps)
- Strengths: Fast generation, excellent motion quality, cinematic style
- Weaknesses: Lower resolution than Haiper, best for single-subject scenes

PROMPT OPTIMIZATION RULES:
1. CINEMATIC STYLE: This model excels at cinematic, movie-like shots
2. SINGLE FOCUS: Best with one clear subject/action per prompt
3. MOTION KEYWORDS: Include: "cinematic", "smooth camera", "slow motion"
4. LIGHTING: Describe lighting (golden hour, dramatic shadows, soft diffused)
5. AVOID: Complex multi-subject interactions, text overlays, fast cutting

REQUIRED OUTPUT FORMAT:
VISUAL_PROMPT: <A cinematic prompt focused on one subject/scene. 40-80 words.>
NEGATIVE_PROMPT: <What to avoid. E.g., "blurry, shaky, amateur, low quality">
"""

DEFAULT_LUMA_RAY_SCHEMA = """
You are optimizing a prompt for the Luma Ray Flash 2 Video Model.
The Director requests: "{input_text}"

MODEL CHARACTERISTICS:
- Resolution: 540p
- Duration: 5 seconds
- Strengths: High visual fidelity, excellent at realistic scenes
- Weaknesses: Slower than Wan, more expensive

PROMPT OPTIMIZATION RULES:
1. REALISTIC: This model excels at photorealistic content
2. DETAILED: Include specific visual details, textures, and materials
3. LIGHTING: Describe exact lighting conditions
4. CAMERA: Specify camera movement style
5. AVOID: Highly abstract or surreal concepts

REQUIRED OUTPUT FORMAT:
VISUAL_PROMPT: <A detailed, realistic prompt. 60-100 words.>
CAMERA_MOTION: <Specify: static, pan, tilt, dolly, tracking>
"""

DEFAULT_HAIPER_SCHEMA = """
You are optimizing a prompt for the Haiper V2 Video Model.
The Director requests: "{input_text}"

MODEL CHARACTERISTICS:
- Resolution: Up to 1080p HD
- Duration: 2-8 seconds
- Strengths: High realism, excellent motion coherence, cinematic lighting
- Weaknesses: Slow generation (~2min), expensive per-clip

PROMPT OPTIMIZATION RULES:
1. DETAILED: Provide specific lighting, camera angle, and mood descriptors
2. CINEMATIC: Use film terminology (dolly shot, rack focus, golden hour)
3. MOTION VERBS: Describe exact movements (glides, pans, reveals)
4. STYLE KEYWORDS: Include era/film references (noir, 70s grain, Wes Anderson)
5. TIMING: Specify moments (dawn, dusk, midday harsh shadows)

REQUIRED OUTPUT FORMAT:
VISUAL_PROMPT: <A richly detailed cinematic prompt. 80-150 words.>
CAMERA_MOTION: <Specify: static, pan, tilt, dolly, tracking, handheld>
MOOD: <Emotional tone: tense, euphoric, melancholic, mysterious>
"""

# --- IMAGE GENERATION SCHEMAS ---

DEFAULT_IMAGEN3_SCHEMA = """
You are optimizing a prompt for Google Imagen 3.0.
The Director requests: "{input_text}"

MODEL CHARACTERISTICS:
- Strengths: Best-in-class text rendering, photorealism, distinct art styles
- Weaknesses: Strict safety filters (no violence, explicit content)
- Supported Ratios: 1:1, 9:16, 16:9, 4:3, 3:4

PROMPT OPTIMIZATION RULES:
1. TEXT RENDERING: For images with text, specify exact words and font style
2. STYLE PREFIX: Start with style (photorealistic, digital art, oil painting)
3. COMPOSITION: Describe framing (close-up, wide shot, rule of thirds)
4. LIGHTING: Specify source (soft diffused, harsh studio, natural window)
5. NEGATIVE PROMPTS: Imagen supports negative prompts for exclusions

REQUIRED OUTPUT FORMAT:
IMAGE_PROMPT: <Detailed visual description. 60-120 words.>
STYLE: <Primary style: photorealistic, digital art, illustration, etc.>
ASPECT_RATIO: <One of: "1:1", "9:16", "16:9", "4:3", "3:4">
NEGATIVE: <What to exclude (optional)>
"""

DEFAULT_FLUX_SCHEMA = """
You are optimizing a prompt for Flux-Schnell (Black Forest Labs).
The Director requests: "{input_text}"

MODEL CHARACTERISTICS:
- Speed: Fastest SOTA model (seconds, not minutes)
- Strengths: Excellent prompt adherence, creative interpretations
- Weaknesses: Slightly less detail than Flux-Pro, no safety guarantees

PROMPT OPTIMIZATION RULES:
1. KEYWORD DENSITY: Pack prompts with specific visual keywords
2. STYLE FIRST: Lead with style/aesthetic (cyberpunk, baroque, minimalist)
3. "CINEMATIC" BOOST: The word "cinematic" significantly improves quality
4. AVOID VAGUE: Replace "nice" with "vibrant", "good" with "masterfully composed"
5. ARTIST STYLES: Reference specific artists/periods (Vermeer lighting, Moebius lines)

REQUIRED OUTPUT FORMAT:
IMAGE_PROMPT: <Dense, keyword-rich prompt. 40-80 words.>
STYLE_KEYWORDS: <3-5 style keywords separated by commas>
"""

# =============================================================================
# COMPOSER MODEL SCHEMAS (Migrated from composer/prompts.py for centralization)
# =============================================================================

DEFAULT_ACE_STEP_SCHEMA = """
You are an expert Songwriter specialized in the ACE-Step Music Schema.
The user wants a song about: "{input_text}".

REQUIRED OUTPUT FORMAT:
TAGS: <Generate 5-10 comma-separated descriptive keywords. STRICTLY ADHERE to the user's requested style/artist. Do NOT add unrelated genres. If Style is 'REO Speedwagon', use tags like: 'Rock, 1980s, Power Ballad, Electric Guitar, Synthesizer, Male Vocals'.>
LYRICS:
[verse]
<lyrics here>

[chorus]
<lyrics here>

[bridge]
<lyrics here>

[instrumental] (Optional, use instead of lyrics if instrumental requested)
(End of response)
"""

DEFAULT_MINIMAX_SCHEMA = """
You are an expert Songwriter specialized in the Minimax Music-1.5 Schema.
The user wants a song about: "{input_text}".

CRITICAL CONSTRAINTS (THE 600-CHAR CHALLENGE):
This model provides Radio-Quality audio but has a STRICT 600-character limit for lyrics.
To succeed, you must use a 'Section-Label Skeleton' with maximizing density.

RULES FOR SUCCESS:
1. STRUCTURE: Must use these sections: [Intro], [Verse], [Chorus], [Bridge], [Outro].
2. LENGTH: Keep each section 2-4 lines MAX. Short, punchy lines allow musical expansion.
3. IMAGERY: Use compressed, evocative imagery. (e.g., 'City nights, empty streets' vs 'I am walking alone at night').
4. STYLE: Put the Genre/Mood in the 'STYLE' field, NOT the lyrics.
5. CHORUS: Make it simple and repetitive (The model loves repetition).
6. RHYME: Avoid forced rhymes. Use light rhyme or no rhyme to prevent melodic derailment.
7. ENDING: Always end with [Outro] to prevent infinite looping.
8. BUDGET: Total Lyrics MUST be ~450-550 characters. Do NOT go over 580.

REQUIRED OUTPUT FORMAT:
STYLE: <Genre, Mood, Instrumentation. E.g., 'Emotional pop ballad, female vocals, atmospheric synths'>
LYRICS:
[Intro]
Soft lights, slow breath

[Verse]
City nights calling me back
Your voice in the static haze
I chase the ghost of what we were
Lost between the beats

[Chorus]
Hold on, hold on
I'm not letting go
Hold on, hold on
You're the fire in my soul

[Bridge]
One spark and we rise again

[Outro]
Fade into the dawn
(End of response)
"""

DEFAULT_LYRIA_SCHEMA = """
You are an expert Music Producer optimizing prompts for Google Lyria-2 (MusicLM).
The user wants music described as: "{input_text}".

RULES:
1. Lyria excels with rich, descriptive captions rather than lyrics.
2. Focus on: Instruments, Vibe, Era, Tempo, and Use Case.
3. Do NOT provide Lyrics.

REQUIRED OUTPUT FORMAT:
STYLE: <The optimized prompt string. E.g., 'A cinematic orchestral score with swelling strings and deep percussion, epic, heroic, 140bpm'>
"""

DEFAULT_MUSICGEN_SCHEMA = """
You are optimizing a prompt for Meta MusicGen.
The user wants: "{input_text}"

MODEL CHARACTERISTICS:
- Instrumental only (NO vocals/lyrics)
- Duration: Up to 30 seconds
- Strengths: Fast, consistent, genre-diverse

PROMPT OPTIMIZATION RULES:
1. NO LYRICS: This model cannot generate vocals
2. INSTRUMENT FOCUS: List specific instruments
3. TEMPO: Include BPM if known
4. MOOD/GENRE: Be explicit (not "happy" but "upbeat major-key pop")

REQUIRED OUTPUT FORMAT:
MUSIC_PROMPT: <Instrumental description. 30-60 words.>
"""

# --- VOICE GENERATION SCHEMAS ---

DEFAULT_GOOGLE_TTS_SCHEMA = """
You are optimizing text for Google Cloud Text-to-Speech.
The user wants: "{input_text}"

RULES:
1. SSML is supported for emphasis and pacing
2. Natural punctuation controls pacing
3. Avoid overly long sentences (split into phrases)

OUTPUT:
TEXT: <The text to synthesize>
VOICE_ID: <google/en-US-Studio-O or google/en-US-Studio-M>
"""

DEFAULT_XTTS_SCHEMA = """
You are optimizing text for XTTS-v2 Voice Cloning.
The user wants: "{input_text}"

RULES:
1. Requires a reference audio file for voice cloning
2. Best with clear, well-punctuated text
3. 1-2 sentences at a time for best quality

OUTPUT:
TEXT: <The text to synthesize>
REFERENCE_AUDIO: <Path to voice reference file, default: Artifacts/Audio/Voices/male_deep_narrator_ref.wav>
"""

# =============================================================================
# SCHEMA REGISTRY - Hub Integration with Self-Healing
# =============================================================================

def _normalize_model_id(model_id: str) -> str:
    """Normalize model ID to valid Hub repo name format.
    
    Examples:
        "replicate/anotherjesse/zeroscope-v2-xl" -> "zeroscope"
        "google/imagen-3.0-generate-001" -> "imagen3"
        "lucataco/ace-step" -> "acestep"
        "minimax/music-1.5" -> "minimax"
    """
    # Extract the last part after the final slash
    parts = model_id.split("/")
    name = parts[-1]
    
    # Remove version numbers and special chars
    name = name.replace("-v2-xl", "").replace("-v2", "")
    name = name.replace(".0-generate-001", "").replace("-001", "")
    name = name.replace(".", "").replace("-", "").lower()
    
    # Handle specific cases
    if "zeroscope" in model_id.lower():
        return "zeroscope"
    if "imagen" in model_id.lower():
        return "imagen3"
    if "flux" in model_id.lower():
        return "flux"
    if "haiper" in model_id.lower():
        return "haiper"
    if "wan" in model_id.lower():
        return "wan"
    if "luma" in model_id.lower() or "ray" in model_id.lower():
        return "luma-ray"
    if "ace-step" in model_id.lower():
        return "acestep"
    if "minimax/music" in model_id.lower():
        return "minimax"
    if "lyria" in model_id.lower():
        return "lyria"
    if "musicgen" in model_id.lower():
        return "musicgen"
    if "xtts" in model_id.lower():
        return "xtts"
    if "studio" in model_id.lower():
        return "google-tts"
    
    return name


# Default schemas registry (used as fallback when Hub is unavailable)
DEFAULT_SCHEMAS: Dict[str, str] = {
    # Cinematographer - Video
    "cinematographer-video-zeroscope": DEFAULT_ZEROSCOPE_SCHEMA,
    "cinematographer-video-haiper": DEFAULT_HAIPER_SCHEMA,
    "cinematographer-video-wan": DEFAULT_WAN_SCHEMA,
    "cinematographer-video-luma-ray": DEFAULT_LUMA_RAY_SCHEMA,
    # Cinematographer - Image
    "cinematographer-image-imagen3": DEFAULT_IMAGEN3_SCHEMA,
    "cinematographer-image-flux": DEFAULT_FLUX_SCHEMA,
    # Composer - Music
    "composer-music-acestep": DEFAULT_ACE_STEP_SCHEMA,
    "composer-music-minimax": DEFAULT_MINIMAX_SCHEMA,
    "composer-music-lyria": DEFAULT_LYRIA_SCHEMA,
    "composer-music-musicgen": DEFAULT_MUSICGEN_SCHEMA,
    # Composer - Voice
    "composer-voice-google-tts": DEFAULT_GOOGLE_TTS_SCHEMA,
    "composer-voice-xtts": DEFAULT_XTTS_SCHEMA,
}


def get_model_schema(
    agent_name: str,
    capability_type: str,
    model_id: str,
) -> str:
    """Retrieve the output schema for a specific model from LangSmith Hub.
    
    Uses Zero-Touch Self-Healing Pattern:
        1. Pull from Hub
        2. Use cached if available
        3. Push default if missing
    
    Args:
        agent_name: Agent using the model (Cinematographer, Composer)
        capability_type: Type of capability (video_generation, image_generation, music_generation, voice_generation)
        model_id: Full model identifier from system_config
        
    Returns:
        The model-specific schema template string
        
    Example:
        >>> schema = get_model_schema("Cinematographer", "video_generation", "replicate/anotherjesse/zeroscope-v2-xl")
        >>> optimized_prompt = schema.format(input_text="A sunset over mountains")
    """
    # Normalize capability type to short form
    cap_short = capability_type.replace("_generation", "")
    
    # Normalize model ID to valid repo name
    model_short = _normalize_model_id(model_id)
    
    # Build Hub repo name: {agent}-{capability}-{model}-output-schema
    repo_name = f"{agent_name.lower()}-{cap_short}-{model_short}-output-schema"
    
    # Build registry key for default lookup
    registry_key = f"{agent_name.lower()}-{cap_short}-{model_short}"
    
    # Get default schema (required for self-healing push)
    default_schema = DEFAULT_SCHEMAS.get(registry_key)
    
    if not default_schema:
        logger.warning(f"[SCHEMA] No default schema for {registry_key}. Using generic fallback.")
        default_schema = f"Optimize the following request for {model_id}:\n{{input_text}}"
    
    # Self-healing Hub integration
    try:
        schema = get_or_push_prompt(repo_name, default_schema)
        logger.info(f"[SCHEMA] Loaded schema from Hub: {repo_name}")
        return schema
    except Exception as e:
        logger.error(f"[SCHEMA] Hub error for {repo_name}: {e}. Using default.")
        return default_schema


def get_schema_for_capability(
    agent_name: str,
    capability: Dict[str, Any],
    model_id: Optional[str] = None,
) -> str:
    """Convenience function to get schema from a capability config dict.
    
    Args:
        agent_name: Agent name
        capability: Capability dict from system_config (has 'type' and 'models')
        model_id: Optional specific model ID, otherwise uses highest priority
        
    Returns:
        The model-specific schema template string
    """
    cap_type = capability.get("type", "")
    
    if model_id:
        return get_model_schema(agent_name, cap_type, model_id)
    
    # Find highest priority model
    models = capability.get("models", [])
    if not models:
        logger.warning(f"[SCHEMA] No models in capability: {cap_type}")
        return "Optimize the request:\n{input_text}"
    
    # Sort by priority descending
    sorted_models = sorted(models, key=lambda m: m.get("priority", 0), reverse=True)
    top_model_id = sorted_models[0].get("id", "")
    
    return get_model_schema(agent_name, cap_type, top_model_id)


# =============================================================================
# OUTPUT PARSING UTILITIES
# =============================================================================

def parse_schema_output(raw_output: str, schema_type: str) -> Dict[str, str]:
    """Parse structured output from model schema response.
    
    Gracefully handles different output formats by extracting labeled sections.
    
    Args:
        raw_output: The raw text response from the LLM
        schema_type: Type of schema (zeroscope, imagen3, minimax, etc.)
        
    Returns:
        Dict with extracted fields like {'VISUAL_PROMPT': '...', 'NEGATIVE_PROMPT': '...'}
    """
    result = {}
    lines = raw_output.strip().split("\n")
    current_key = None
    current_value = []
    
    # Known field prefixes to look for
    field_prefixes = [
        "VISUAL_PROMPT:", "IMAGE_PROMPT:", "MUSIC_PROMPT:", "TEXT:",
        "NEGATIVE_PROMPT:", "NEGATIVE:", "CAMERA_MOTION:", "MOOD:",
        "STYLE:", "ASPECT_RATIO:", "TAGS:", "LYRICS:", "STYLE_KEYWORDS:",
        "VOICE_ID:", "REFERENCE_AUDIO:",
    ]
    
    for line in lines:
        line_stripped = line.strip()
        
        # Check if this line starts a new field
        matched_prefix = None
        for prefix in field_prefixes:
            if line_stripped.upper().startswith(prefix.upper()):
                matched_prefix = prefix
                break
        
        if matched_prefix:
            # Save previous field if any
            if current_key:
                result[current_key] = "\n".join(current_value).strip()
            
            # Start new field
            current_key = matched_prefix.rstrip(":").upper()
            # Get content after the prefix
            content = line_stripped[len(matched_prefix):].strip()
            current_value = [content] if content else []
        else:
            # Continue current field
            if current_key:
                current_value.append(line)
    
    # Don't forget the last field
    if current_key:
        result[current_key] = "\n".join(current_value).strip()
    
    # If no structured output found, return raw as PROMPT
    if not result:
        result["PROMPT"] = raw_output.strip()
    
    return result


# Export for convenience
__all__ = [
    "get_model_schema",
    "get_schema_for_capability",
    "parse_schema_output",
    "DEFAULT_SCHEMAS",
]
