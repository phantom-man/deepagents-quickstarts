"""
Agency Sections - Dynamic UI components for Cinematographer and Composer.

These sections provide schema-driven configuration panels with:
- Model selection from registry
- Dynamic parameter controls from schemas
- Asset dependency resolution
- Storyboard integration for video
"""
import os
import logging
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st

from DeepAgents.services.model_registry import (
    ModelRegistry,
    ModelInfo,
    ModelCategory,
    InputRequirement,
    get_model_registry,
    get_video_model_options,
    get_music_model_options,
    get_voice_model_options,
    get_image_model_options,
    model_requires_voice
)
from DeepAgents.services.schema_service import (
    SchemaService,
    ModelSchema,
    AssetRequirement,
    get_schema_service
)
from DeepAgents.services.ui_generator import DynamicUIGenerator
from DeepAgents.services.asset_validator import (
    AssetValidator,
    ValidationResult,
    validate_upload,
    get_asset_validator
)

logger = logging.getLogger(__name__)


def _init_section_state():
    """Initialize session state for agency sections."""
    defaults = {
        # Cinematographer
        "cinematographer_active": True,
        "cinematographer_model": None,
        "cinematographer_params": {},
        "cinematographer_schema": None,
        "storyboard_active": False,
        "storyboard_model": None,
        "storyboard_params": {},

        # Composer
        "composer_active": True,
        "composer_model": None,
        "composer_params": {},
        "composer_schema": None,
        "composer_voice_source": None,
        "composer_voice_file": None,
        "composer_voice_model": None,
    }

    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default


def render_cinematographer_section() -> Dict[str, Any]:
    """
    Render the Cinematographer configuration section.

    Returns:
        Dict with cinematographer configuration:
        - active: bool
        - model_id: str
        - params: dict
        - storyboard_active: bool
        - storyboard_model_id: str
        - storyboard_params: dict
    """
    _init_section_state()
    registry = get_model_registry()
    schema_service = get_schema_service()

    config = {
        "active": False,
        "model_id": None,
        "params": {},
        "storyboard_active": False,
        "storyboard_model_id": None,
        "storyboard_params": {}
    }

    # Active checkbox
    st.markdown("### 🎬 Cinematographer")
    col_active, col_info = st.columns([1, 3])

    with col_active:
        active = st.checkbox(
            "Enable",
            value=st.session_state.cinematographer_active,
            key="cinema_active_check",
            help="Enable video generation"
        )
        st.session_state.cinematographer_active = active
        config["active"] = active

    with col_info:
        if active:
            st.markdown("<span style='color: green;'>✓ Video generation enabled</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span style='color: gray;'>○ Video generation disabled</span>", unsafe_allow_html=True)

    if not active:
        return config

    # Model Selection
    video_models = get_video_model_options()
    model_names = list(video_models.keys())

    # Get current selection index
    current_model_id = st.session_state.cinematographer_model
    current_idx = 0
    if current_model_id:
        for i, name in enumerate(model_names):
            if video_models[name] == current_model_id:
                current_idx = i
                break

    selected_name = st.selectbox(
        "Video Model",
        options=model_names,
        index=current_idx,
        key="cinema_model_select",
        help="Select the AI model for video generation"
    )

    model_id = video_models[selected_name]
    st.session_state.cinematographer_model = model_id
    config["model_id"] = model_id

    # Model info
    model_info = registry.get(model_id)
    if model_info:
        st.caption(f"{model_info.description} | Tier: {model_info.tier.upper()}")

    # Dynamic Parameters from Schema
    with st.expander("⚙️ Video Model Parameters", expanded=False):
        try:
            schema = schema_service.get_schema(model_id)
            st.session_state.cinematographer_schema = schema

            # Generate UI controls
            ui_generator = DynamicUIGenerator(key_prefix="cinema")

            # Exclude prompt since Director provides it
            exclude = ["prompt", "text", "caption", "input"]

            params = ui_generator.render_controls(
                schema,
                current_values=st.session_state.cinematographer_params,
                exclude_params=exclude,
                columns=2
            )

            st.session_state.cinematographer_params = params
            config["params"] = params

        except ValueError as e:
            st.warning(f"Could not load schema: {e}")
            st.info("Using default parameters. The model may still work.")

    st.divider()

    # Storyboard Section
    st.markdown("#### 📸 Storyboard Generation")

    col_sb_active, col_sb_info = st.columns([1, 3])

    with col_sb_active:
        sb_active = st.checkbox(
            "Enable Storyboard",
            value=st.session_state.storyboard_active,
            key="storyboard_active_check",
            help="Generate storyboard images before video"
        )
        st.session_state.storyboard_active = sb_active
        config["storyboard_active"] = sb_active

    with col_sb_info:
        if sb_active:
            st.markdown("<span style='color: green;'>✓ Storyboard will be generated first</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span style='color: gray;'>○ Direct video generation</span>", unsafe_allow_html=True)

    if sb_active:
        image_models = get_image_model_options()
        image_names = list(image_models.keys())

        # Get current selection
        current_sb_model = st.session_state.storyboard_model
        current_sb_idx = 0
        if current_sb_model:
            for i, name in enumerate(image_names):
                if image_models[name] == current_sb_model:
                    current_sb_idx = i
                    break

        selected_sb_name = st.selectbox(
            "Storyboard Image Model",
            options=image_names,
            index=current_sb_idx,
            key="storyboard_model_select",
            help="Model for generating storyboard frames"
        )

        sb_model_id = image_models[selected_sb_name]
        st.session_state.storyboard_model = sb_model_id
        config["storyboard_model_id"] = sb_model_id

        # Storyboard model info
        sb_info = registry.get(sb_model_id)
        if sb_info:
            st.caption(f"{sb_info.description}")

    return config


def render_composer_section() -> Dict[str, Any]:
    """
    Render the Composer configuration section.

    Returns:
        Dict with composer configuration:
        - active: bool
        - model_id: str
        - params: dict
        - voice_source: 'generate' | 'upload' | 'local' | None
        - voice_file: uploaded file or path
        - voice_model_id: str (if generating)
    """
    _init_section_state()
    registry = get_model_registry()
    schema_service = get_schema_service()
    validator = get_asset_validator()

    config = {
        "active": False,
        "model_id": None,
        "params": {},
        "voice_source": None,
        "voice_file": None,
        "voice_model_id": None
    }

    # Active checkbox
    st.markdown("### 🎵 Composer")
    col_active, col_info = st.columns([1, 3])

    with col_active:
        active = st.checkbox(
            "Enable",
            value=st.session_state.composer_active,
            key="composer_active_check",
            help="Enable music/audio generation"
        )
        st.session_state.composer_active = active
        config["active"] = active

    with col_info:
        if active:
            st.markdown("<span style='color: green;'>✓ Music generation enabled</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span style='color: gray;'>○ Music generation disabled</span>", unsafe_allow_html=True)

    if not active:
        return config

    # Model Selection
    music_models = get_music_model_options()
    model_names = list(music_models.keys())

    # Get current selection
    current_model_id = st.session_state.composer_model
    current_idx = 0
    if current_model_id:
        for i, name in enumerate(model_names):
            if music_models[name] == current_model_id:
                current_idx = i
                break

    selected_name = st.selectbox(
        "Music Model",
        options=model_names,
        index=current_idx,
        key="composer_model_select",
        help="Select the AI model for music generation"
    )

    model_id = music_models[selected_name]
    st.session_state.composer_model = model_id
    config["model_id"] = model_id

    # Model info and capabilities
    model_info = registry.get(model_id)
    if model_info:
        caps = []
        if model_info.supports_lyrics:
            caps.append("🎤 Lyrics")
        if model_info.supports_instrumental:
            caps.append("🎸 Instrumental")
        if model_info.max_duration:
            caps.append(f"⏱️ Max {model_info.max_duration}s")

        st.caption(f"{model_info.description}")
        if caps:
            st.markdown(" | ".join(caps))

    # Check if model requires voice input
    requires_voice = model_requires_voice(model_id)

    if requires_voice:
        st.markdown("---")
        st.markdown("**🎤 Voice Reference Required**")
        st.info("This model requires a voice reference file for best results.")

        # Voice source selection
        voice_source = st.radio(
            "Voice Source",
            options=["Generate with AI", "Upload File", "Select from Library"],
            key="composer_voice_source_radio",
            horizontal=True
        )

        if voice_source == "Generate with AI":
            config["voice_source"] = "generate"
            st.session_state.composer_voice_source = "generate"

            voice_models = get_voice_model_options()
            voice_names = list(voice_models.keys())

            selected_voice = st.selectbox(
                "Voice Generator",
                options=voice_names,
                key="composer_voice_model_select"
            )

            voice_model_id = voice_models[selected_voice]
            st.session_state.composer_voice_model = voice_model_id
            config["voice_model_id"] = voice_model_id

            voice_info = registry.get(voice_model_id)
            if voice_info:
                st.caption(voice_info.description)

            st.success("✓ Voice will be generated before music")

        elif voice_source == "Upload File":
            config["voice_source"] = "upload"
            st.session_state.composer_voice_source = "upload"

            uploaded = st.file_uploader(
                "Upload Voice Reference",
                type=["wav", "mp3", "flac", "m4a"],
                key="composer_voice_upload"
            )

            if uploaded:
                # Validate
                result = validate_upload(uploaded, "audio", max_duration=60)

                if result.is_valid:
                    st.success(f"✓ {result.message}")
                    st.session_state.composer_voice_file = uploaded
                    config["voice_file"] = uploaded
                else:
                    st.error(f"✗ {result.message}")
            else:
                st.warning("⚠ Voice reference required for this model")

        else:  # Select from Library
            config["voice_source"] = "local"
            st.session_state.composer_voice_source = "local"

            # Look for voice files in Artifacts
            voice_dir = os.path.join(
                os.path.dirname(__file__),
                "..", "..", "Artifacts", "Audio", "Voices"
            )
            voice_dir = os.path.normpath(voice_dir)

            local_files = []
            if os.path.exists(voice_dir):
                for f in os.listdir(voice_dir):
                    if f.endswith(('.wav', '.mp3', '.flac', '.m4a')):
                        local_files.append(f)

            if local_files:
                selected_file = st.selectbox(
                    "Select Voice File",
                    options=[""] + local_files,
                    key="composer_voice_local_select"
                )

                if selected_file:
                    full_path = os.path.join(voice_dir, selected_file)
                    st.session_state.composer_voice_file = full_path
                    config["voice_file"] = full_path
                    st.success(f"✓ Selected: {selected_file}")
                else:
                    st.warning("⚠ Please select a voice file")
            else:
                st.info(f"No voice files found in {voice_dir}")
                st.markdown("Upload a voice file instead.")

    # Dynamic Parameters from Schema
    with st.expander("⚙️ Music Model Parameters", expanded=False):
        try:
            schema = schema_service.get_schema(model_id)
            st.session_state.composer_schema = schema

            # Generate UI controls
            ui_generator = DynamicUIGenerator(key_prefix="composer")

            # Exclude prompt and voice (handled separately)
            exclude = ["prompt", "text", "lyrics", "voice", "voice_file", "reference_audio"]

            params = ui_generator.render_controls(
                schema,
                current_values=st.session_state.composer_params,
                exclude_params=exclude,
                columns=2
            )

            st.session_state.composer_params = params
            config["params"] = params

        except ValueError as e:
            st.warning(f"Could not load schema: {e}")
            st.info("Using default parameters.")

    return config


def get_agency_config() -> Dict[str, Any]:
    """
    Get the full agency configuration from current UI state.

    Returns:
        Dict with:
        - cinematographer: cinematographer config
        - composer: composer config
    """
    return {
        "cinematographer": {
            "active": st.session_state.get("cinematographer_active", True),
            "model_id": st.session_state.get("cinematographer_model"),
            "params": st.session_state.get("cinematographer_params", {}),
            "storyboard_active": st.session_state.get("storyboard_active", False),
            "storyboard_model_id": st.session_state.get("storyboard_model"),
        },
        "composer": {
            "active": st.session_state.get("composer_active", True),
            "model_id": st.session_state.get("composer_model"),
            "params": st.session_state.get("composer_params", {}),
            "voice_source": st.session_state.get("composer_voice_source"),
            "voice_file": st.session_state.get("composer_voice_file"),
            "voice_model_id": st.session_state.get("composer_voice_model"),
        }
    }


def validate_agency_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate the agency configuration before running.

    Args:
        config: Agency config from get_agency_config()

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []

    cinema = config.get("cinematographer", {})
    composer = config.get("composer", {})

    # At least one must be active
    if not cinema.get("active") and not composer.get("active"):
        errors.append("At least one of Cinematographer or Composer must be enabled")

    # Cinematographer validation
    if cinema.get("active"):
        if not cinema.get("model_id"):
            errors.append("Cinematographer: No video model selected")

    # Composer validation
    if composer.get("active"):
        if not composer.get("model_id"):
            errors.append("Composer: No music model selected")

        # Check voice requirement
        model_id = composer.get("model_id")
        if model_id and model_requires_voice(model_id):
            voice_source = composer.get("voice_source")
            if voice_source == "generate" and not composer.get("voice_model_id"):
                errors.append("Composer: Voice model selected but no generator chosen")
            elif voice_source in ("upload", "local") and not composer.get("voice_file"):
                errors.append("Composer: Voice file required but not provided")

    return len(errors) == 0, errors
