"""
DeepAgents Preset System.

This package provides curated presets for:
- Lyrics (100 presets with structure markers)
- Composer prompts (50 music style descriptions)
- Video prompts (50 cinematographer visuals)
- Director prompts (30 story concepts)

Each preset includes:
- Character count for model compatibility filtering
- Genre/mood tags for categorization
- Model compatibility flags
"""

from DeepAgents.gui.presets.composer_presets import (
    COMPOSER_PRESETS,
    ComposerPreset,
    get_composer_by_genre,
    get_composer_by_mood,
    get_composer_for_model,
)
from DeepAgents.gui.presets.composer_presets import (
    get_all_genres as get_composer_genres,
)
from DeepAgents.gui.presets.composer_presets import (
    get_all_moods as get_composer_moods,
)
from DeepAgents.gui.presets.director_presets import (
    DIRECTOR_PRESETS,
    DirectorPreset,
    get_director_by_genre,
    get_director_by_tone,
)
from DeepAgents.gui.presets.director_presets import (
    get_all_genres as get_director_genres,
)
from DeepAgents.gui.presets.director_presets import (
    get_all_tones as get_director_tones,
)
from DeepAgents.gui.presets.lyrics_presets import (
    LYRICS_PRESETS,
    LyricsPreset,
    get_lyrics_by_genre,
    get_lyrics_by_mood,
    get_lyrics_for_model,
)
from DeepAgents.gui.presets.lyrics_presets import (
    get_all_genres as get_lyrics_genres,
)
from DeepAgents.gui.presets.lyrics_presets import (
    get_all_moods as get_lyrics_moods,
)
from DeepAgents.gui.presets.video_presets import (
    VIDEO_PRESETS,
    VideoPreset,
    get_video_by_category,
    get_video_by_mood,
    get_video_for_model,
)
from DeepAgents.gui.presets.video_presets import (
    get_all_categories as get_video_categories,
)
from DeepAgents.gui.presets.video_presets import (
    get_all_moods as get_video_moods,
)

__all__ = [
    # Lyrics (100 presets)
    "LYRICS_PRESETS",
    "get_lyrics_by_genre",
    "get_lyrics_by_mood",
    "get_lyrics_for_model",
    "get_lyrics_genres",
    "get_lyrics_moods",
    "LyricsPreset",
    # Composer (50 presets)
    "COMPOSER_PRESETS",
    "get_composer_by_genre",
    "get_composer_by_mood",
    "get_composer_for_model",
    "get_composer_genres",
    "get_composer_moods",
    "ComposerPreset",
    # Video (50 presets)
    "VIDEO_PRESETS",
    "get_video_by_category",
    "get_video_by_mood",
    "get_video_for_model",
    "get_video_categories",
    "get_video_moods",
    "VideoPreset",
    # Director (30 presets)
    "DIRECTOR_PRESETS",
    "get_director_by_genre",
    "get_director_by_tone",
    "get_director_genres",
    "get_director_tones",
    "DirectorPreset",
]
