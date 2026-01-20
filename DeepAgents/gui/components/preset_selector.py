"""
Preset Selector Component - UI for selecting presets in Streamlit.

Features:
- Dropdown selector with genre/mood/category filtering
- Preview of preset content with char count
- Model compatibility badges
- Apply button to fill input fields
"""
from typing import Callable, Optional, Union

import streamlit as st

from DeepAgents.gui.presets.lyrics_presets import (
    LYRICS_PRESETS,
    LyricsPreset,
    get_lyrics_for_model,
    get_all_genres as get_lyrics_genres
)
from DeepAgents.gui.presets.composer_presets import (
    COMPOSER_PRESETS,
    ComposerPreset,
    get_composer_for_model,
    get_all_genres as get_composer_genres
)
from DeepAgents.gui.presets.video_presets import (
    VIDEO_PRESETS,
    VideoPreset,
    get_video_for_model,
    get_all_categories as get_video_categories
)
from DeepAgents.gui.presets.director_presets import (
    DIRECTOR_PRESETS,
    DirectorPreset,
    get_director_for_model,
    get_all_genres as get_director_genres
)


PresetType = Union[LyricsPreset, ComposerPreset, VideoPreset, DirectorPreset]


def render_preset_selector(
    preset_type: str,
    key_prefix: str,
    model_id: str = "",
    on_select: Optional[Callable[[str], None]] = None,
    show_preview: bool = True,
    max_chars: Optional[int] = None
) -> Optional[str]:
    """
    Render a preset selector with filtering and preview.

    Args:
        preset_type: "lyrics", "composer", "video", or "director"
        key_prefix: Unique key prefix for Streamlit widgets
        model_id: Model ID for compatibility filtering
        on_select: Callback when preset is selected
        show_preview: Show preview of selected preset
        max_chars: Override max chars for filtering

    Returns:
        Selected preset content or None
    """
    # Get appropriate presets
    if preset_type == "lyrics":
        if model_id:
            all_presets = get_lyrics_for_model(model_id)
        else:
            all_presets = LYRICS_PRESETS
        filter_options = get_lyrics_genres()
        filter_label = "Filter by Genre"
        label = "Lyrics Preset"
        char_limit = max_chars or 600
    elif preset_type == "video":
        if model_id:
            all_presets = get_video_for_model(model_id)
        else:
            all_presets = VIDEO_PRESETS
        filter_options = get_video_categories()
        filter_label = "Filter by Category"
        label = "Video Preset"
        char_limit = max_chars or 500
    elif preset_type == "director":
        if model_id:
            all_presets = get_director_for_model(model_id)
        else:
            all_presets = DIRECTOR_PRESETS
        filter_options = get_director_genres()
        filter_label = "Filter by Genre"
        label = "Story Preset"
        char_limit = max_chars or 1000
    else:  # composer
        if model_id:
            all_presets = get_composer_for_model(model_id)
        else:
            all_presets = COMPOSER_PRESETS
        filter_options = get_composer_genres()
        filter_label = "Filter by Genre"
        label = "Style Preset"
        char_limit = max_chars or 300

    # Filter by char limit if specified
    if max_chars:
        all_presets = [p for p in all_presets if p.char_count <= max_chars]

    # Container for the selector
    with st.container():
        col1, col2 = st.columns([3, 1])

        with col1:
            # Filter dropdown (genre/category based on preset type)
            filter_value = st.selectbox(
                filter_label,
                options=["All"] + filter_options,
                key=f"{key_prefix}_filter"
            )

        with col2:
            # Show count
            filtered_presets = all_presets
            if filter_value != "All":
                # Filter by genre or category depending on preset type
                filter_attr = "category" if preset_type == "video" else "genre"
                filtered_presets = [
                    p for p in all_presets
                    if getattr(p, filter_attr, None) == filter_value
                ]
            st.metric("Available", len(filtered_presets))

        # Apply filter
        if filter_value != "All":
            filter_attr = "category" if preset_type == "video" else "genre"
            all_presets = [
                p for p in all_presets
                if getattr(p, filter_attr, None) == filter_value
            ]

        # Build options list (video uses category, others use genre)
        if preset_type == "video":
            options = ["-- Select a Preset --"] + [
                f"{p.name} ({getattr(p, 'category', '')}) [{p.char_count} chars]"
                for p in all_presets
            ]
        else:
            options = ["-- Select a Preset --"] + [
                f"{p.name} ({getattr(p, 'genre', '')}) [{p.char_count} chars]"
                for p in all_presets
            ]

        # Main selector
        selected_idx = st.selectbox(
            label,
            options=range(len(options)),
            format_func=lambda x: options[x],
            key=f"{key_prefix}_selector"
        )

        # Get selected preset
        selected_content = None
        if selected_idx > 0:
            selected_preset = all_presets[selected_idx - 1]
            selected_content = selected_preset.content

            # Show preview
            if show_preview:
                with st.expander("Preview", expanded=False):
                    # Char count with status
                    char_pct = (selected_preset.char_count / char_limit) * 100
                    if char_pct <= 80:
                        status_color = "green"
                    elif char_pct <= 95:
                        status_color = "orange"
                    else:
                        status_color = "red"

                    st.markdown(f"**{selected_preset.char_count}** / {char_limit} chars "
                               f"(:{status_color}[{char_pct:.0f}%])")

                    # Tags
                    if selected_preset.tags:
                        st.markdown("**Tags:** " + ", ".join(selected_preset.tags))

                    # Content preview
                    st.text_area(
                        "Content",
                        value=selected_preset.content,
                        height=150,
                        disabled=True,
                        key=f"{key_prefix}_preview"
                    )

            # Apply button - show it whenever a preset is selected
            if st.button("Apply Preset", key=f"{key_prefix}_apply", type="primary"):
                # Set the external_update key that char_counter will pick up
                st.session_state[f"{key_prefix}_external_update"] = selected_content
                if on_select:
                    on_select(selected_content)
                st.rerun()

        return None


def lyrics_preset_selector(
    key: str = "lyrics",
    model_id: str = "minimax/music-1.5",
    on_select: Optional[Callable[[str], None]] = None
) -> Optional[str]:
    """
    Simplified lyrics preset selector.

    Args:
        key: Unique key for widgets
        model_id: Music model for char limit filtering
        on_select: Callback when preset is applied

    Returns:
        Selected lyrics content or None
    """
    st.markdown("#### Load Lyrics Preset")
    return render_preset_selector(
        preset_type="lyrics",
        key_prefix=key,
        model_id=model_id,
        on_select=on_select,
        max_chars=600 if "music-1.5" in model_id else 3000
    )


def composer_preset_selector(
    key: str = "composer",
    model_id: str = "minimax/music-1.5",
    on_select: Optional[Callable[[str], None]] = None
) -> Optional[str]:
    """
    Simplified composer prompt preset selector.

    Args:
        key: Unique key for widgets
        model_id: Music model for char limit filtering
        on_select: Callback when preset is applied

    Returns:
        Selected prompt content or None
    """
    st.markdown("#### Load Style Preset")
    return render_preset_selector(
        preset_type="composer",
        key_prefix=key,
        model_id=model_id,
        on_select=on_select,
        max_chars=300 if "music-1.5" in model_id else 500
    )


def video_preset_selector(
    key: str = "video",
    model_id: str = "wan-video/wan-2.5-t2v-fast",
    on_select: Optional[Callable[[str], None]] = None
) -> Optional[str]:
    """
    Simplified video prompt preset selector.

    Args:
        key: Unique key for widgets
        model_id: Video model for char limit filtering
        on_select: Callback when preset is applied

    Returns:
        Selected prompt content or None
    """
    st.markdown("#### Load Video Preset")
    # Wan models ~500 chars, Veo ~1000 chars
    if "wan" in model_id.lower():
        max_chars = 500
    elif "veo" in model_id.lower():
        max_chars = 1000
    else:
        max_chars = 500  # Conservative default
    return render_preset_selector(
        preset_type="video",
        key_prefix=key,
        model_id=model_id,
        on_select=on_select,
        max_chars=max_chars
    )


def director_preset_selector(
    key: str = "director",
    model_id: str = "",
    on_select: Optional[Callable[[str], None]] = None
) -> Optional[str]:
    """
    Simplified director story concept preset selector.

    Args:
        key: Unique key for widgets
        model_id: Optional model ID (not typically used for Director)
        on_select: Callback when preset is applied

    Returns:
        Selected story concept content or None
    """
    st.markdown("#### Load Story Concept")
    return render_preset_selector(
        preset_type="director",
        key_prefix=key,
        model_id=model_id,
        on_select=on_select,
        max_chars=1000  # Director prompts can be longer
    )


def get_preset_stats() -> dict:
    """Get statistics about available presets."""
    lyrics_chars = [p.char_count for p in LYRICS_PRESETS]
    composer_chars = [p.char_count for p in COMPOSER_PRESETS]
    video_chars = [p.char_count for p in VIDEO_PRESETS]
    director_chars = [p.char_count for p in DIRECTOR_PRESETS]

    return {
        "lyrics": {
            "total": len(LYRICS_PRESETS),
            "fits_music15": len([p for p in LYRICS_PRESETS if p.fits_music15]),
            "genres": len(get_lyrics_genres()),
            "avg_chars": sum(lyrics_chars) // len(lyrics_chars) if lyrics_chars else 0,
            "min_chars": min(lyrics_chars) if lyrics_chars else 0,
            "max_chars": max(lyrics_chars) if lyrics_chars else 0,
        },
        "composer": {
            "total": len(COMPOSER_PRESETS),
            "fits_music15": len([p for p in COMPOSER_PRESETS if p.fits_music15]),
            "genres": len(get_composer_genres()),
            "avg_chars": sum(composer_chars) // len(composer_chars) if composer_chars else 0,
            "min_chars": min(composer_chars) if composer_chars else 0,
            "max_chars": max(composer_chars) if composer_chars else 0,
        },
        "video": {
            "total": len(VIDEO_PRESETS),
            "fits_wan": len([p for p in VIDEO_PRESETS if p.fits_wan]),
            "fits_veo": len([p for p in VIDEO_PRESETS if p.fits_veo]),
            "categories": len(get_video_categories()),
            "avg_chars": sum(video_chars) // len(video_chars) if video_chars else 0,
            "min_chars": min(video_chars) if video_chars else 0,
            "max_chars": max(video_chars) if video_chars else 0,
        },
        "director": {
            "total": len(DIRECTOR_PRESETS),
            "genres": len(get_director_genres()),
            "avg_chars": sum(director_chars) // len(director_chars) if director_chars else 0,
            "min_chars": min(director_chars) if director_chars else 0,
            "max_chars": max(director_chars) if director_chars else 0,
        }
    }
