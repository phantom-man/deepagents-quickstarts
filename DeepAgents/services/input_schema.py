"""
Input Schema Service - Dynamic Input Field Generation.

This service extends the Schema Service to provide:
1. Input-specific control definitions with character limits
2. Model-aware input constraints
3. Preset filtering based on character limits
4. Input validation before API submission

Works with char_counter.py for UI rendering.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class InputType(Enum):
    """Types of user inputs for AI models."""

    TEXT = "text"  # Short text (< 200 chars typically)
    TEXTAREA = "textarea"  # Long text (prompts, descriptions)
    LYRICS = "lyrics"  # Music lyrics with structure markers
    PROMPT = "prompt"  # Generation prompt
    NEGATIVE_PROMPT = "negative_prompt"  # What to avoid
    TAGS = "tags"  # Comma-separated keywords
    FILE_AUDIO = "file_audio"  # Audio file upload
    FILE_VIDEO = "file_video"  # Video file upload
    FILE_IMAGE = "file_image"  # Image file upload
    SELECT = "select"  # Dropdown selection
    NUMBER = "number"  # Numeric input


@dataclass
class InputFieldDefinition:
    """
    Definition for a dynamic input field.

    Used by UI components to render appropriate controls
    with validation and character counting.
    """

    name: str  # API parameter name
    input_type: InputType  # Type of input
    label: str  # Display label
    description: str = ""  # Help text

    # Character limits
    max_chars: Optional[int] = None  # Hard limit
    min_chars: Optional[int] = None  # Soft minimum

    # Validation
    required: bool = False
    pattern: Optional[str] = None  # Regex pattern

    # Default/placeholder
    default: Any = None
    placeholder: str = ""

    # For SELECT type
    options: List[Dict[str, Any]] = field(default_factory=list)

    # For FILE types
    accepted_types: List[str] = field(default_factory=list)
    max_file_size_mb: Optional[float] = None
    max_duration_seconds: Optional[float] = None
    min_duration_seconds: Optional[float] = None

    # UI hints
    height: int = 100  # For textareas
    order: int = 0  # Display order
    collapsible: bool = False  # Can be collapsed
    advanced: bool = False  # Show in advanced section

    # Preset support
    supports_presets: bool = False  # Can load from presets
    preset_category: Optional[str] = None  # Which preset category


# =============================================================================
# MODEL-SPECIFIC INPUT DEFINITIONS
# =============================================================================

# Minimax Music-1.5 inputs
MINIMAX_MUSIC_INPUTS: List[InputFieldDefinition] = [
    InputFieldDefinition(
        name="prompt",
        input_type=InputType.PROMPT,
        label="Music Style Prompt",
        description="Describe the genre, mood, tempo, and instruments",
        max_chars=300,
        min_chars=10,
        required=True,
        placeholder="90s rock anthem, power chords, driving drums at 120 BPM, arena rock energy",
        height=100,
        order=1,
        supports_presets=True,
        preset_category="composer_prompt",
    ),
    InputFieldDefinition(
        name="lyrics",
        input_type=InputType.LYRICS,
        label="Lyrics",
        description="Song lyrics with [Verse], [Chorus], [Bridge] markers. 600 char max.",
        max_chars=600,
        min_chars=10,
        required=False,
        placeholder="[Verse 1]\nYour opening lines...\n\n[Chorus]\nThe catchy hook...",
        height=200,
        order=2,
        supports_presets=True,
        preset_category="lyrics",
    ),
]

# ACE-Step inputs
ACE_STEP_INPUTS: List[InputFieldDefinition] = [
    InputFieldDefinition(
        name="prompt",
        input_type=InputType.TAGS,
        label="Style Tags",
        description="Comma-separated style tags (genre, mood, instruments)",
        max_chars=500,
        required=True,
        placeholder="Rock, 1980s, Power Ballad, Electric Guitar, Male Vocals",
        height=80,
        order=1,
        supports_presets=True,
        preset_category="composer_tags",
    ),
    InputFieldDefinition(
        name="lyrics",
        input_type=InputType.LYRICS,
        label="Lyrics",
        description="Full song lyrics with structure markers",
        max_chars=3000,  # ACE-Step supports longer lyrics
        min_chars=20,
        required=True,
        placeholder="[Verse]\nThe world outside is cold tonight...\n\n[Chorus]\nBut we'll make it through together...",
        height=250,
        order=2,
        supports_presets=True,
        preset_category="lyrics",
    ),
]

# Lyria-2 inputs (instrumental only)
LYRIA_INPUTS: List[InputFieldDefinition] = [
    InputFieldDefinition(
        name="prompt",
        input_type=InputType.PROMPT,
        label="Instrumental Prompt",
        description="Describe the instrumental style (no lyrics supported)",
        max_chars=500,
        min_chars=10,
        required=True,
        placeholder="Orchestral epic, sweeping strings, brass fanfare, cinematic tension building to triumphant resolution",
        height=120,
        order=1,
        supports_presets=True,
        preset_category="instrumental_prompt",
    ),
]

# MusicGen inputs
MUSICGEN_INPUTS: List[InputFieldDefinition] = [
    InputFieldDefinition(
        name="prompt",
        input_type=InputType.PROMPT,
        label="Music Description",
        description="Describe the instrumental music you want to generate",
        max_chars=500,
        required=True,
        placeholder="Upbeat electronic dance music with synthesizers, heavy bass, and energetic drums",
        height=100,
        order=1,
        supports_presets=True,
        preset_category="instrumental_prompt",
    ),
]

# Cinematographer/Video inputs
WAN_VIDEO_INPUTS: List[InputFieldDefinition] = [
    InputFieldDefinition(
        name="prompt",
        input_type=InputType.PROMPT,
        label="Visual Prompt",
        description="Describe the scene, camera movement, lighting, and style",
        max_chars=500,
        min_chars=20,
        required=True,
        placeholder="Cinematic aerial shot of a neon-lit cyberpunk city at night, flying through rain, camera slowly descending",
        height=120,
        order=1,
        supports_presets=True,
        preset_category="video_prompt",
    ),
    InputFieldDefinition(
        name="negative_prompt",
        input_type=InputType.NEGATIVE_PROMPT,
        label="Negative Prompt",
        description="What to avoid in the generation",
        max_chars=300,
        required=False,
        placeholder="blurry, low quality, distorted faces, text, watermark",
        height=80,
        order=2,
        advanced=True,
    ),
]

LUMA_VIDEO_INPUTS: List[InputFieldDefinition] = [
    InputFieldDefinition(
        name="prompt",
        input_type=InputType.PROMPT,
        label="Scene Description",
        description="Describe the visual scene for Luma Ray",
        max_chars=1000,
        min_chars=20,
        required=True,
        placeholder="A majestic dragon soaring through clouds at sunset, scales glistening with golden light, cinematic wide shot",
        height=150,
        order=1,
        supports_presets=True,
        preset_category="video_prompt",
    ),
]

VEO_VIDEO_INPUTS: List[InputFieldDefinition] = [
    InputFieldDefinition(
        name="prompt",
        input_type=InputType.PROMPT,
        label="Video Prompt",
        description="Describe the video for Google Veo",
        max_chars=1500,
        min_chars=20,
        required=True,
        placeholder="Photorealistic shot of a coffee being poured into a cup, steam rising, warm morning light through window",
        height=150,
        order=1,
        supports_presets=True,
        preset_category="video_prompt",
    ),
]


# =============================================================================
# MODEL INPUT REGISTRY
# =============================================================================

MODEL_INPUT_REGISTRY: Dict[str, List[InputFieldDefinition]] = {
    # Composer models
    "minimax/music-1.5": MINIMAX_MUSIC_INPUTS,
    "minimax/music-01": MINIMAX_MUSIC_INPUTS,  # Legacy alias
    "lucataco/ace-step": ACE_STEP_INPUTS,
    "google/lyria-2": LYRIA_INPUTS,
    "meta/musicgen": MUSICGEN_INPUTS,
    # Video models
    "wan-video/wan-2.5-t2v-fast": WAN_VIDEO_INPUTS,
    "luma/ray-flash-2-540p": LUMA_VIDEO_INPUTS,
    "veo-3.1-fast-generate-001": VEO_VIDEO_INPUTS,
    "veo-3.1-generate-001": VEO_VIDEO_INPUTS,
}


def get_input_fields_for_model(model_id: str) -> List[InputFieldDefinition]:
    """
    Get input field definitions for a specific model.

    Args:
        model_id: The model identifier (e.g., "minimax/music-1.5")

    Returns:
        List of InputFieldDefinition for the model's inputs
    """
    # Direct match
    if model_id in MODEL_INPUT_REGISTRY:
        return MODEL_INPUT_REGISTRY[model_id]

    # Try partial match (for version suffixes)
    for key, inputs in MODEL_INPUT_REGISTRY.items():
        if model_id.startswith(key) or key.startswith(model_id):
            return inputs

    # Default: generic prompt input
    logger.warning(f"No input schema for {model_id}, using generic prompt")
    return [
        InputFieldDefinition(
            name="prompt",
            input_type=InputType.PROMPT,
            label="Prompt",
            description="Describe what you want to generate",
            max_chars=1000,
            required=True,
            placeholder="Enter your generation prompt...",
            height=120,
            order=1,
        )
    ]


def get_max_chars_for_field(model_id: str, field_name: str) -> Optional[int]:
    """
    Get the maximum character limit for a specific field.

    Args:
        model_id: Model identifier
        field_name: Input field name (e.g., "lyrics", "prompt")

    Returns:
        Max chars or None if unlimited
    """
    fields = get_input_fields_for_model(model_id)
    for field in fields:
        if field.name == field_name:
            return field.max_chars
    return None


def validate_input(
    model_id: str, field_name: str, value: str
) -> Tuple[bool, Optional[str]]:
    """
    Validate an input value against model constraints.

    Args:
        model_id: Model identifier
        field_name: Input field name
        value: The value to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    fields = get_input_fields_for_model(model_id)

    for field in fields:
        if field.name == field_name:
            # Check required
            if field.required and not value.strip():
                return False, f"{field.label} is required"

            # Check max chars
            if field.max_chars and len(value) > field.max_chars:
                return (
                    False,
                    f"{field.label} exceeds {field.max_chars} character limit ({len(value)} chars)",
                )

            # Check min chars
            if field.min_chars and value.strip() and len(value) < field.min_chars:
                return (
                    False,
                    f"{field.label} needs at least {field.min_chars} characters",
                )

            return True, None

    # Field not found, assume valid
    return True, None


def filter_presets_by_char_limit(
    presets: List[Dict[str, Any]], max_chars: int, content_field: str = "content"
) -> List[Dict[str, Any]]:
    """
    Filter presets to only those that fit within a character limit.

    Args:
        presets: List of preset dictionaries
        max_chars: Maximum allowed characters
        content_field: Key in preset dict containing the text content

    Returns:
        Filtered list of presets that fit within limit
    """
    return [p for p in presets if len(p.get(content_field, "")) <= max_chars]


def get_fields_supporting_presets(model_id: str) -> List[InputFieldDefinition]:
    """Get only the input fields that support presets for a model."""
    fields = get_input_fields_for_model(model_id)
    return [f for f in fields if f.supports_presets]
