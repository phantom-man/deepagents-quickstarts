"""
Agency Sections - Dynamic UI components for Cinematographer and Composer.

These sections provide schema-driven configuration panels with:
- Model selection from registry
- Dynamic parameter controls from schemas
- Asset dependency resolution
- Storyboard integration for video
"""
import os
import re
import time
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st

from DeepAgents.services.model_registry import (
    ModelRegistry,
    ModelInfo,
    ModelCategory,
    ModelProvider,
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

BASE_DIR = Path(__file__).resolve().parents[2]


def _get_artifact_path(*segments: str) -> Path:
    """Return an absolute path under Artifacts directory."""
    target = BASE_DIR.joinpath("Artifacts", *segments)
    target.mkdir(parents=True, exist_ok=True)
    return target


def _sanitize_filename(name: str) -> str:
    """Sanitize filenames to avoid problematic characters."""
    base = Path(name).name
    return re.sub(r"[^A-Za-z0-9_.-]", "_", base)


def _persist_uploaded_file(uploaded, subdir: str) -> str:
    """Persist an uploaded file to Artifacts and return the saved path."""
    target_dir = _get_artifact_path(*subdir.split("/"))
    sanitized = _sanitize_filename(getattr(uploaded, "name", "uploaded.bin"))
    unique = f"user_{int(time.time() * 1000)}_{sanitized}"
    dest_path = target_dir / unique

    uploaded.seek(0)
    dest_path.write_bytes(uploaded.read())
    uploaded.seek(0)
    return str(dest_path)


def _render_metadata_block(title: str, metadata: Dict[str, Any]) -> None:
    """Render metadata details in Streamlit."""
    if not metadata:
        st.info(f"{title}: Metadata unavailable")
        return

    rows = []
    for key, value in metadata.items():
        if value in (None, "", [], {}):
            continue
        label = key.replace("_", " ").title()
        rows.append(f"- **{label}:** {value}")

    if rows:
        st.markdown(f"**{title}**")
        st.markdown("\n".join(rows))
    else:
        st.info(f"{title}: Metadata unavailable")

logger = logging.getLogger(__name__)


def _init_section_state():
    """Initialize session state for agency sections."""
    defaults = {
        # Cinematographer
        "cinematographer_active": True,
        "cinematographer_model": None,
        "cinematographer_params": {},
        "cinematographer_schema": None,
        "cinematographer_source": "model",
        "cinematographer_files": [],
        "cinematographer_file_metadata": [],
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
        "composer_source": "model",
        "composer_files": [],
        "composer_file_metadata": [],
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
        "source": "model",
        "file_paths": [],
        "file_metadata": [],
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
    video_models = dict(get_video_model_options())
    file_option_label = "Uploaded Video File (Pass-through)"
    sentinel_video = "__video_file__"
    video_models[file_option_label] = sentinel_video
    model_names = list(video_models.keys())

    # Get current selection index
    current_model_id = st.session_state.cinematographer_model or next(iter(video_models.values()))
    current_idx = 0
    for i, name in enumerate(model_names):
        if video_models[name] == current_model_id:
            current_idx = i
            break

    selected_name = st.selectbox(
        "Video Source",
        options=model_names,
        index=current_idx,
        key="cinema_model_select",
        help="Select an AI model or upload an existing video"
    )

    model_id = video_models[selected_name]
    st.session_state.cinematographer_model = model_id
    config["model_id"] = model_id

    validator = get_asset_validator()

    if model_id == sentinel_video:
        st.session_state.cinematographer_source = "file"
        config["source"] = "file"
        st.info("Video generation disabled. Uploaded clips will be passed directly to the Editor.")

        uploaded_files = st.file_uploader(
            "Upload video clip(s)",
            type=["mp4", "mov", "m4v", "webm"],
            accept_multiple_files=True,
            key="cinema_uploaded_videos"
        )

        stored_entries: List[Dict[str, Any]] = []
        if uploaded_files:
            existing_entries = st.session_state.get("cinematographer_files", []) or []

            for uploaded in uploaded_files:
                file_size = getattr(uploaded, "size", None)
                existing = next(
                    (
                        entry for entry in existing_entries
                        if entry.get("name") == uploaded.name and entry.get("size") == file_size
                        and os.path.exists(entry.get("path", ""))
                    ),
                    None
                )

                if existing:
                    entry = existing
                else:
                    result = validate_upload(uploaded, "video")
                    uploaded.seek(0)
                    if not result.is_valid:
                        st.error(f"✗ {uploaded.name}: {result.message}")
                        continue

                    saved_path = _persist_uploaded_file(uploaded, "Video/Recovered")
                    metadata = validator.extract_metadata(saved_path, "video")
                    entry = {
                        "name": uploaded.name,
                        "size": file_size,
                        "path": saved_path,
                        "metadata": metadata
                    }

                stored_entries.append(entry)

            if stored_entries:
                st.session_state.cinematographer_files = stored_entries
                config["file_paths"] = [item["path"] for item in stored_entries]
                config["file_metadata"] = [item.get("metadata", {}) for item in stored_entries]

                for idx, entry in enumerate(stored_entries, start=1):
                    _render_metadata_block(f"Video {idx}: {Path(entry['path']).name}", entry.get("metadata", {}))
            else:
                st.session_state.cinematographer_files = []
                config["file_paths"] = []
                config["file_metadata"] = []
        else:
            st.warning("Upload at least one video clip to proceed.")
            st.session_state.cinematographer_files = []
            config["file_paths"] = []
            config["file_metadata"] = []

        # Storyboard and parameters are not applicable in file mode
        st.session_state.storyboard_active = False
        config["storyboard_active"] = False
        st.session_state.cinematographer_params = {}
        config["params"] = {}

    else:
        st.session_state.cinematographer_source = "model"
        config["source"] = "model"
        config["file_paths"] = []
        config["file_metadata"] = []
        st.session_state.cinematographer_files = []

        # Model info with cost
        model_info = registry.get(model_id)
        if model_info:
            cost_str = f"${model_info.cost_per_run:.3f}/run" if model_info.cost_per_run else "Cost N/A"
            st.caption(f"{model_info.description}")
            st.markdown(f"**Tier:** {model_info.tier.upper()} | **Cost:** {cost_str}")

    if st.session_state.cinematographer_source == "model":
        # Dynamic Parameters from Schema (works for all providers)
        with st.expander("⚙️ Video Model Parameters", expanded=False):
            try:
                schema = schema_service.get_schema_for_registry_model(model_id)
                st.session_state.cinematographer_schema = schema

                ui_generator = DynamicUIGenerator(key_prefix="cinema")
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
                st.session_state.cinematographer_params = {}
                config["params"] = {}
    else:
        st.info("Model parameters not required when using uploaded video files.")

    st.divider()

    if st.session_state.cinematographer_source == "model":
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
    else:
        st.markdown("#### 📸 Storyboard Generation")
        st.info("Storyboard generation is disabled while using uploaded video clips.")
        config["storyboard_active"] = False
        config["storyboard_model_id"] = None

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
        "source": "model",
        "file_paths": [],
        "file_metadata": [],
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
    music_models = dict(get_music_model_options())
    file_option_label = "Uploaded Audio File (Pass-through)"
    sentinel_audio = "__audio_file__"
    music_models[file_option_label] = sentinel_audio
    model_names = list(music_models.keys())

    current_model_id = st.session_state.composer_model or next(iter(music_models.values()))
    current_idx = 0
    for i, name in enumerate(model_names):
        if music_models[name] == current_model_id:
            current_idx = i
            break

    selected_name = st.selectbox(
        "Music Source",
        options=model_names,
        index=current_idx,
        key="composer_model_select",
        help="Select an AI music model or upload an existing track"
    )

    model_id = music_models[selected_name]
    st.session_state.composer_model = model_id
    config["model_id"] = model_id

    validator = get_asset_validator()

    if model_id == sentinel_audio:
        st.session_state.composer_source = "file"
        config["source"] = "file"
        st.info("Music generation disabled. Uploaded audio will be passed directly to the Editor.")

        uploaded_audio = st.file_uploader(
            "Upload audio track",
            type=["wav", "mp3", "flac", "m4a", "aac"],
            key="composer_uploaded_audio"
        )

        if uploaded_audio:
            file_size = getattr(uploaded_audio, "size", None)
            existing = None
            for entry in st.session_state.get("composer_files", []) or []:
                if entry.get("name") == uploaded_audio.name and entry.get("size") == file_size and os.path.exists(entry.get("path", "")):
                    existing = entry
                    break

            if existing:
                entry = existing
            else:
                result = validate_upload(uploaded_audio, "audio")
                uploaded_audio.seek(0)
                if not result.is_valid:
                    st.error(f"✗ {uploaded_audio.name}: {result.message}")
                    entry = None
                else:
                    saved_path = _persist_uploaded_file(uploaded_audio, "Audio/Recovered")
                    metadata = validator.extract_metadata(saved_path, "audio")
                    entry = {
                        "name": uploaded_audio.name,
                        "size": file_size,
                        "path": saved_path,
                        "metadata": metadata
                    }

            if entry:
                st.session_state.composer_files = [entry]
                config["file_paths"] = [entry["path"]]
                config["file_metadata"] = [entry.get("metadata", {})]
                _render_metadata_block(f"Audio: {Path(entry['path']).name}", entry.get("metadata", {}))
            else:
                st.session_state.composer_files = []
                config["file_paths"] = []
                config["file_metadata"] = []
        else:
            st.warning("Upload an audio file to continue.")
            st.session_state.composer_files = []
            config["file_paths"] = []
            config["file_metadata"] = []

        st.session_state.composer_params = {}
        config["params"] = {}
        st.session_state.composer_voice_source = None
        st.session_state.composer_voice_file = None
        st.session_state.composer_voice_model = None
        config["voice_source"] = None
        config["voice_file"] = None
        config["voice_model_id"] = None
        requires_voice = False

    else:
        st.session_state.composer_source = "model"
        config["source"] = "model"
        config["file_paths"] = []
        config["file_metadata"] = []
        st.session_state.composer_files = []

        model_info = registry.get(model_id)
        if model_info:
            caps = []
            if model_info.supports_lyrics:
                caps.append("🎤 Lyrics")
            if model_info.supports_instrumental:
                caps.append("🎸 Instrumental")
            if model_info.max_duration:
                caps.append(f"⏱️ Max {model_info.max_duration}s")

            cost_str = f"${model_info.cost_per_run:.3f}/run" if model_info.cost_per_run else "Cost N/A"
            st.caption(f"{model_info.description}")
            st.markdown(f"**Cost:** {cost_str}")
            if caps:
                st.markdown(" | ".join(caps))

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
                cost_str = f"${voice_info.cost_per_run:.3f}/run" if voice_info.cost_per_run else ""
                st.caption(f"{voice_info.description} {cost_str}")

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

    if st.session_state.composer_source == "model":
        # Dynamic Parameters from Schema (works for all providers)
        with st.expander("⚙️ Music Model Parameters", expanded=False):
            try:
                schema = schema_service.get_schema_for_registry_model(model_id)
                st.session_state.composer_schema = schema

                ui_generator = DynamicUIGenerator(key_prefix="composer")
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
                st.session_state.composer_params = {}
                config["params"] = {}
    else:
        st.info("Model parameters not required when using uploaded audio.")

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
            "source": st.session_state.get("cinematographer_source", "model"),
            "file_paths": [entry.get("path") for entry in st.session_state.get("cinematographer_files", []) or []],
            "file_metadata": [entry.get("metadata") for entry in st.session_state.get("cinematographer_files", []) or []],
            "storyboard_active": st.session_state.get("storyboard_active", False),
            "storyboard_model_id": st.session_state.get("storyboard_model"),
        },
        "composer": {
            "active": st.session_state.get("composer_active", True),
            "model_id": st.session_state.get("composer_model"),
            "params": st.session_state.get("composer_params", {}),
            "source": st.session_state.get("composer_source", "model"),
            "file_paths": [entry.get("path") for entry in st.session_state.get("composer_files", []) or []],
            "file_metadata": [entry.get("metadata") for entry in st.session_state.get("composer_files", []) or []],
            "voice_source": st.session_state.get("composer_voice_source"),
            "voice_file": st.session_state.get("composer_voice_file"),
            "voice_model_id": st.session_state.get("composer_voice_model"),
        }
    }


def calculate_cost_estimate(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate estimated cost based on current model selections.

    Args:
        config: Agency config from get_agency_config()

    Returns:
        Dict with cost breakdown and total
    """
    registry = get_model_registry()
    costs = {
        "video": None,
        "storyboard": None,
        "music": None,
        "voice": None,
        "total": 0.0,
        "details": []
    }

    cinema = config.get("cinematographer", {})
    composer = config.get("composer", {})

    # Video cost
    if cinema.get("active") and cinema.get("source", "model") != "file" and cinema.get("model_id"):
        model = registry.get(cinema["model_id"])
        if model and model.cost_per_run:
            costs["video"] = model.cost_per_run
            costs["total"] += model.cost_per_run
            costs["details"].append(f"Video ({model.name}): ${model.cost_per_run:.3f}")

    # Storyboard cost (image model)
    if cinema.get("storyboard_active") and cinema.get("storyboard_model_id"):
        model = registry.get(cinema["storyboard_model_id"])
        if model and model.cost_per_run:
            costs["storyboard"] = model.cost_per_run
            costs["total"] += model.cost_per_run
            costs["details"].append(f"Storyboard ({model.name}): ${model.cost_per_run:.3f}")

    # Music cost
    if composer.get("active") and composer.get("source", "model") != "file" and composer.get("model_id"):
        model = registry.get(composer["model_id"])
        if model and model.cost_per_run:
            costs["music"] = model.cost_per_run
            costs["total"] += model.cost_per_run
            costs["details"].append(f"Music ({model.name}): ${model.cost_per_run:.3f}")

    # Voice generation cost
    if composer.get("voice_source") == "generate" and composer.get("voice_model_id"):
        model = registry.get(composer["voice_model_id"])
        if model and model.cost_per_run:
            costs["voice"] = model.cost_per_run
            costs["total"] += model.cost_per_run
            costs["details"].append(f"Voice ({model.name}): ${model.cost_per_run:.3f}")

    return costs


def render_cost_estimate():
    """
    Render a cost estimate panel in the sidebar or main area.
    Updates dynamically as selections change.
    """
    config = get_agency_config()
    costs = calculate_cost_estimate(config)

    st.markdown("### 💰 Estimated Cost")

    if costs["total"] == 0:
        st.info("Enable agents and select models to see cost estimate")
        return

    # Cost breakdown
    for detail in costs["details"]:
        st.text(detail)

    st.markdown("---")
    st.markdown(f"**Total: ${costs['total']:.3f}**")

    # Tier note
    st.caption("💡 Costs are estimates and may vary based on duration and complexity")


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
        if cinema.get("source") == "file":
            files = cinema.get("file_paths") or []
            if not files:
                errors.append("Cinematographer: Upload at least one video file for pass-through mode")
            else:
                for path in files:
                    if not path or not os.path.exists(path):
                        errors.append("Cinematographer: Uploaded video file missing on disk")
                        break

    # Composer validation
    if composer.get("active"):
        if not composer.get("model_id"):
            errors.append("Composer: No music model selected")
        if composer.get("source") == "file":
            files = composer.get("file_paths") or []
            if not files:
                errors.append("Composer: Upload an audio file for pass-through mode")
            else:
                for path in files:
                    if not path or not os.path.exists(path):
                        errors.append("Composer: Uploaded audio file missing on disk")
                        break

        # Check voice requirement
        model_id = composer.get("model_id")
        if model_id and model_requires_voice(model_id):
            voice_source = composer.get("voice_source")
            if voice_source == "generate" and not composer.get("voice_model_id"):
                errors.append("Composer: Voice model selected but no generator chosen")
            elif voice_source in ("upload", "local") and not composer.get("voice_file"):
                errors.append("Composer: Voice file required but not provided")

    return len(errors) == 0, errors
