"""
Character Counter Components for Streamlit.

Provides text input and textarea widgets with:
- Live character counting
- Hard-blocking at max character limit
- Visual feedback (green/yellow/red)
- Min/max character validation
"""
from typing import Optional, Tuple

import streamlit as st


def get_char_status(
    current: int,
    max_chars: Optional[int] = None,
    min_chars: Optional[int] = None
) -> Tuple[str, str]:
    """
    Get status color and message for character count.

    Args:
        current: Current character count
        max_chars: Maximum allowed characters (None = unlimited)
        min_chars: Minimum required characters (None = no minimum)

    Returns:
        Tuple of (color, message)
        Colors: "green", "orange", "red"
    """
    if max_chars is None:
        # No limit
        if min_chars and current < min_chars:
            return "orange", f"{current} chars (min: {min_chars})"
        return "green", f"{current} chars"

    remaining = max_chars - current
    percentage = (current / max_chars) * 100 if max_chars > 0 else 0

    # Check minimum
    if min_chars and current < min_chars:
        return "orange", f"{current} / {max_chars} (need {min_chars - current} more)"

    # Check maximum
    if current > max_chars:
        return "red", f"{current} / {max_chars} ({-remaining} over limit!)"
    elif percentage >= 90:
        return "orange", f"{current} / {max_chars} ({remaining} remaining)"
    else:
        return "green", f"{current} / {max_chars}"


def text_input_with_counter(
    label: str,
    key: str,
    max_chars: Optional[int] = None,
    min_chars: Optional[int] = None,
    placeholder: str = "",
    default_value: str = "",
    help_text: Optional[str] = None,
    disabled: bool = False
) -> str:
    """
    Single-line text input with character counter and hard limit.

    Args:
        label: Label for the input
        key: Unique key for Streamlit state
        max_chars: Maximum characters (hard limit)
        min_chars: Minimum characters (soft validation)
        placeholder: Placeholder text
        default_value: Initial value
        help_text: Help tooltip
        disabled: Whether input is disabled

    Returns:
        The current input value (truncated to max_chars if exceeded)
    """
    # Get current value from session state or default
    state_key = f"_char_input_{key}"
    if state_key not in st.session_state:
        st.session_state[state_key] = default_value

    # Create the input
    value = st.text_input(
        label,
        value=st.session_state[state_key],
        key=f"{key}_widget",
        placeholder=placeholder,
        help=help_text,
        disabled=disabled,
        max_chars=max_chars  # Streamlit's built-in hard limit
    )

    # Handle None return (shouldn't happen but type-safe)
    if value is None:
        value = ""

    # Update state
    st.session_state[state_key] = value

    # Show character counter
    current_len = len(value)
    color, message = get_char_status(current_len, max_chars, min_chars)

    color_map = {"green": "#28a745", "orange": "#ffc107", "red": "#dc3545"}
    st.markdown(
        f"<span style='color: {color_map[color]}; font-size: 0.8em;'>{message}</span>",
        unsafe_allow_html=True
    )

    return value


def text_area_with_counter(
    label: str,
    key: str,
    max_chars: Optional[int] = None,
    min_chars: Optional[int] = None,
    placeholder: str = "",
    default_value: str = "",
    height: int = 150,
    help_text: Optional[str] = None,
    disabled: bool = False,
    show_remaining: bool = True
) -> str:
    """
    Multi-line textarea with character counter and hard blocking.

    Args:
        label: Label for the textarea
        key: Unique key for Streamlit state
        max_chars: Maximum characters (hard blocking via truncation)
        min_chars: Minimum characters (soft validation)
        placeholder: Placeholder text
        default_value: Initial value
        height: Height in pixels
        help_text: Help tooltip
        disabled: Whether input is disabled
        show_remaining: Show remaining chars in label

    Returns:
        The current textarea value (truncated to max_chars if exceeded)
    """
    # Get current value from session state or default
    state_key = f"_char_textarea_{key}"
    if state_key not in st.session_state:
        st.session_state[state_key] = default_value

    current_value = st.session_state[state_key]
    current_len = len(current_value)

    # Build label with counter if max_chars specified
    display_label = label
    if max_chars and show_remaining:
        remaining = max_chars - current_len
        if remaining < 0:
            display_label = f"{label} (⚠️ {-remaining} over limit!)"
        elif remaining <= 50:
            display_label = f"{label} ({remaining} chars left)"

    # Create the textarea
    # Note: Streamlit textarea doesn't have max_chars, so we handle it manually
    raw_value = st.text_area(
        display_label,
        value=current_value,
        key=f"{key}_widget",
        placeholder=placeholder,
        height=height,
        help=help_text,
        disabled=disabled
    )

    # Handle None return (shouldn't happen but type-safe)
    value: str = raw_value if raw_value is not None else ""

    # HARD BLOCKING: Truncate if over limit
    if max_chars and len(value) > max_chars:
        value = value[:max_chars]
        st.session_state[state_key] = value
        st.warning(f"Input truncated to {max_chars} characters (limit reached)")
    else:
        st.session_state[state_key] = value

    # Show character counter bar
    current_len = len(value)
    color, message = get_char_status(current_len, max_chars, min_chars)

    color_map = {"green": "#28a745", "orange": "#ffc107", "red": "#dc3545"}

    # Progress bar style counter
    if max_chars:
        percentage = min((current_len / max_chars) * 100, 100)
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 10px; margin-top: -10px;">
                <div style="flex-grow: 1; background: #333; border-radius: 4px; height: 6px; overflow: hidden;">
                    <div style="width: {percentage}%; background: {color_map[color]}; height: 100%;"></div>
                </div>
                <span style="color: {color_map[color]}; font-size: 0.8em; white-space: nowrap;">{message}</span>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"<span style='color: {color_map[color]}; font-size: 0.8em;'>{message}</span>",
            unsafe_allow_html=True
        )

    return value


def lyrics_input(
    key: str,
    max_chars: int = 600,
    default_value: str = "",
    help_text: str = "Use [Verse], [Chorus], [Bridge] markers for structure"
) -> str:
    """
    Specialized lyrics input for music generation.

    Pre-configured for Music-1.5 (600 char limit) with structure hints.

    Args:
        key: Unique key
        max_chars: Limit (default 600 for Music-1.5)
        default_value: Initial lyrics
        help_text: Help text

    Returns:
        Lyrics string
    """
    return text_area_with_counter(
        label="🎤 Lyrics",
        key=key,
        max_chars=max_chars,
        min_chars=10,
        placeholder="[Verse 1]\nYour lyrics here...\n\n[Chorus]\nCatchy hook...",
        default_value=default_value,
        height=200,
        help_text=help_text
    )


def prompt_input(
    key: str,
    label: str = "🎬 Prompt",
    max_chars: Optional[int] = 300,
    default_value: str = "",
    placeholder: str = "Describe the style, mood, and details...",
    height: int = 100
) -> str:
    """
    Specialized prompt input for AI generation.

    Args:
        key: Unique key
        label: Display label
        max_chars: Limit (default 300 for many APIs)
        default_value: Initial prompt
        placeholder: Placeholder text
        height: Textarea height

    Returns:
        Prompt string
    """
    return text_area_with_counter(
        label=label,
        key=key,
        max_chars=max_chars,
        placeholder=placeholder,
        default_value=default_value,
        height=height
    )
