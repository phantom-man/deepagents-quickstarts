"""DeepAgents GUI Components Package."""

from .char_counter import (
    text_input_with_counter,
    text_area_with_counter,
    get_char_status,
)

from .preset_selector import (
    render_preset_selector,
    lyrics_preset_selector,
    composer_preset_selector,
    get_preset_stats,
)

__all__ = [
    # Character Counter
    "text_input_with_counter",
    "text_area_with_counter",
    "get_char_status",
    # Preset Selector
    "render_preset_selector",
    "lyrics_preset_selector",
    "composer_preset_selector",
    "get_preset_stats",
]
