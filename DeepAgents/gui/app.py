"""
DeepAgents Streamlit GUI - Simplified Agency Interface.
Exposes only the core Agency orchestration, Research Agent, and Agent Communications.
Follows LangChain/LangSmith Gold Standard with Zero-Touch Configuration.
"""

# pylint: disable=line-too-long, import-error, wrong-import-position
# pylint: disable=import-outside-toplevel, broad-exception-caught, missing-function-docstring
# pylint: disable=too-many-statements, too-many-locals, too-many-branches

import logging
import os
import sys
import time
from datetime import datetime

import streamlit as st

# Add parent directory for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from agent_brain import AgentComms, AgentConfig
from gui.agent_runner import AgentRunner
from gui.history_manager import SessionManager
from gui.presets import DIRECTOR_PRESETS

# Configure logging (ASCII-safe for Windows cp1252)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("DeepAgentsGUI")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG & STYLING
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="DeepAgents Agency",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
    /* Light theme for better readability - scoped to Streamlit elements only */
    .stApp { background-color: #f8f9fa; }
    .block-container { padding: 2rem; max-width: 1200px; margin: auto; }
    
    /* Main content text */
    .stApp .stMarkdown, .stApp p, .stApp span, .stApp label { color: #212529; }
    .stApp h1, .stApp h2, .stApp h3, .stApp h4 { color: #212529; }
    
    /* FIX: Button cursor states - ensure enabled buttons have pointer cursor */
    .stButton > button {
        cursor: pointer !important;
    }
    .stButton > button:disabled {
        cursor: not-allowed !important;
        opacity: 0.6;
    }
    .stButton > button:not(:disabled):hover {
        cursor: pointer !important;
    }
    
    /* Event log styling */
    .event-log {
        background: #ffffff;
        border-radius: 8px;
        padding: 1rem;
        max-height: 500px;
        overflow-y: auto;
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 0.85rem;
        border: 1px solid #dee2e6;
        color: #212529;
    }
    .event-info { color: #0d6efd; }
    .event-output { color: #198754; }
    .event-error { color: #dc3545; }
    .event-thinking { color: #fd7e14; font-style: italic; }
    .event-progress { color: #0d6efd; font-weight: 500; }
    
    /* Message bubbles for AgentComms */
    .msg-sender { color: #0d6efd; font-weight: bold; }
    .msg-recipient { color: #6f42c1; }
    .msg-content { 
        background: #ffffff;
        padding: 0.75rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 3px solid #0d6efd;
        color: #212529;
        border: 1px solid #dee2e6;
    }
    .msg-timestamp { color: #6c757d; font-size: 0.75rem; }
    
    /* Status indicators */
    .status-connected { color: #198754; font-weight: bold; }
    .status-disconnected { color: #dc3545; font-weight: bold; }
</style>
""",
    unsafe_allow_html=True,
)

# ═══════════════════════════════════════════════════════════════════════════════
# SESSION STATE INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

if "session_manager" not in st.session_state:
    st.session_state.session_manager = SessionManager()

if "agent_runner" not in st.session_state:
    st.session_state.agent_runner = AgentRunner(st.session_state.session_manager)

if "comms" not in st.session_state:
    st.session_state.comms = AgentComms()
    st.session_state.comms_connected = st.session_state.comms.connect()
    if st.session_state.comms_connected:
        st.session_state.comms.setup_tables()

if "agency_running" not in st.session_state:
    st.session_state.agency_running = False

if "agency_session_start" not in st.session_state:
    st.session_state.agency_session_start = None

if "research_running" not in st.session_state:
    st.session_state.research_running = False

# ═══════════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════════

st.title("🎬 DeepAgents Agency")
st.caption("AI-Powered Content Production Pipeline | LangGraph Studio Integration")

# Connection status indicators
col_status1, col_status2, col_status3 = st.columns(3)

with col_status1:
    if os.getenv("LANGCHAIN_TRACING_V2", "").lower() == "true":
        st.markdown(
            "**LangSmith:** <span class='status-connected'>Connected</span>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "**LangSmith:** <span class='status-disconnected'>Not Configured</span>",
            unsafe_allow_html=True,
        )

with col_status2:
    if st.session_state.comms_connected:
        st.markdown(
            "**Postgres:** <span class='status-connected'>Connected</span>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "**Postgres:** <span class='status-disconnected'>Disconnected</span>",
            unsafe_allow_html=True,
        )

with col_status3:
    try:
        config = AgentConfig()
        dir_config = config.get_agent_config("Director")
        model = dir_config.get("model", "Unknown")
        st.markdown(f"**Model:** `{model}`")
    except Exception:
        st.markdown(
            "**Model:** <span class='status-disconnected'>Config Error</span>",
            unsafe_allow_html=True,
        )

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# TAB LAYOUT - SIMPLIFIED TO 3 CORE FEATURES
# ═══════════════════════════════════════════════════════════════════════════════

tab_agency, tab_research, tab_comms = st.tabs(
    ["🎬 Agency", "🔬 Research Agent", "📡 Agent Comms"]
)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: AGENCY - FULL LANGGRAPH ORCHESTRATION
# ═══════════════════════════════════════════════════════════════════════════════

# Import agency sections for dynamic UI
try:
    from gui.agency_sections import (
        get_agency_config,
        render_cinematographer_section,
        render_composer_section,
        validate_agency_config,
    )

    AGENCY_SECTIONS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Agency sections not available: {e}")
    AGENCY_SECTIONS_AVAILABLE = False

with tab_agency:
    st.header("Agency Orchestration")
    st.markdown("""
    **Schema-Driven AI Production Pipeline**
    
    Configure your agents below, enter a creative directive, and run the Agency.
    """)

    st.divider()

    # ─────────────────────────────────────────────────────────────────────────
    # AGENT CONFIGURATION SECTIONS
    # ─────────────────────────────────────────────────────────────────────────

    if AGENCY_SECTIONS_AVAILABLE:
        # Two-column layout for Cinematographer and Composer
        col_cinema, col_composer = st.columns(2)

        with col_cinema:
            cinema_config = render_cinematographer_section()

        with col_composer:
            composer_config = render_composer_section()

        # Cost estimate panel
        st.divider()
        from DeepAgents.gui.agency_sections import render_cost_estimate

        render_cost_estimate()

        st.divider()

    # ─────────────────────────────────────────────────────────────────────────
    # DIRECTIVE INPUT
    # ─────────────────────────────────────────────────────────────────────────

    preset_prompt_lookup = {}
    preset_display_options = ["Select a director preset"]
    for preset in DIRECTOR_PRESETS:
        # DirectorPreset has: name, description, genre, tone, content
        display_label = (
            f"{preset.name} - {preset.description} ({preset.genre}/{preset.tone})"
        )
        preset_display_options.append(display_label)
        preset_prompt_lookup[display_label] = preset

    selected_preset_label = st.selectbox(
        "Director Prompt Presets", preset_display_options, key="director_prompt_select"
    )

    if selected_preset_label != preset_display_options[0]:
        selected_preset = preset_prompt_lookup[selected_preset_label]
        # Show preset details
        st.caption(f"Genre: {selected_preset.genre} | Tone: {selected_preset.tone}")
        if selected_preset.music_style_hint:
            st.caption(f"Music: {selected_preset.music_style_hint}")
        if st.button("Use This Preset", key=f"use_preset_{selected_preset.id}"):
            st.session_state.agency_directive = selected_preset.content
            st.session_state.selected_director_preset = selected_preset.id
            st.session_state.director_preset_feedback = (
                f"Loaded preset: {selected_preset.name}"
            )

    if st.session_state.get("director_preset_feedback"):
        st.info(st.session_state.director_preset_feedback)
        st.session_state.director_preset_feedback = ""

    # Directive Input
    directive = st.text_area(
        "Creative Directive",
        placeholder="Example: Create a 15-second promotional video for an AI startup with inspiring music",
        height=100,
        key="agency_directive",
    )

    # Validation before run
    # Always validate to enable/disable button, but only show errors if user attempted to run
    if AGENCY_SECTIONS_AVAILABLE:
        agency_cfg = get_agency_config()
        is_valid, validation_errors = validate_agency_config(agency_cfg)

        # Only show warnings if user tried to run
        show_validation_warnings = st.session_state.get(
            "show_validation_warnings", False
        )
        if not is_valid and show_validation_warnings:
            for err in validation_errors:
                st.warning(f"⚠️ {err}")
    else:
        is_valid = True
        agency_cfg = None

    col_run, col_stop = st.columns([1, 1])

    with col_run:
        # Run Agency - disabled if running, no directive, or invalid config
        run_disabled = (
            st.session_state.agency_running
            or not directive
            or (AGENCY_SECTIONS_AVAILABLE and not is_valid)
        )
        run_button = st.button(
            "🚀 Run Agency",
            disabled=run_disabled,
            use_container_width=True,
            type="primary",
        )

    with col_stop:
        # Stop - only enabled while agency is running
        stop_button = st.button(
            "⏹️ Stop",
            disabled=not st.session_state.agency_running,
            use_container_width=True,
        )

    # Initialize session state for generated assets
    if "generated_video" not in st.session_state:
        st.session_state.generated_video = None
    if "generated_audio" not in st.session_state:
        st.session_state.generated_audio = None
    if "generated_final" not in st.session_state:
        st.session_state.generated_final = None

    # Progress and Status Display
    progress_container = st.container()
    event_container = st.container()
    download_container = st.container()

    # Helper function to extract file paths from content
    def extract_file_path(content):
        """Extract file paths from content string and normalize them."""
        import re

        # Match common file patterns - prioritize cloud URLs
        patterns = [
            r"(https://storage\.googleapis\.com/[^\s\)\"\']+)",  # GCS public URLs (highest priority)
            r"(https?://[^\s\)\"\']+\.(mp4|mp3|wav|png|jpg|webm))",  # Other URLs with media extensions
            r"(gs://[^\s\)\"\']+ )",  # GCS paths
            r"([A-Za-z]:\\[^\s\)\"\']+\.(mp4|mp3|wav|png|jpg|webm))",  # Windows paths
            r"(/[^\s\)\"\']+\.(mp4|mp3|wav|png|jpg|webm))",  # Unix paths
            r"(Artifacts[/\\][^\s\)\"\']+\.(mp4|mp3|wav|png|jpg|webm))",  # Relative Artifacts paths
        ]
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                path = match.group(1)
                # If it's a URL, return as-is
                if path.startswith("http"):
                    return path
                # Normalize local path - fix mixed slashes
                path = path.replace("/", os.sep).replace("\\", os.sep)
                # Convert relative Artifacts paths to absolute
                if path.startswith("Artifacts"):
                    base_dir = os.path.abspath(
                        os.path.join(os.path.dirname(__file__), "../..")
                    )
                    path = os.path.join(base_dir, path)
                return os.path.normpath(path)
        return None

    def extract_cloud_url(content):
        """Extract cloud/public URL from content string."""
        import re

        # Look specifically for GCS public URLs
        match = re.search(r"(https://storage\.googleapis\.com/[^\s\)\"\']+)", content)
        if match:
            return match.group(1)
        # Also check for generic HTTPS media URLs
        match = re.search(
            r"(https://[^\s\)\"\']+\.(mp4|mp3|wav|webm))", content, re.IGNORECASE
        )
        if match:
            return match.group(1)
        return None

    def make_content_clickable(content):
        """Convert file paths in content to clickable links."""
        import re

        # Replace GCS paths
        content = re.sub(
            r"(gs://[^\s\)\"\'<>]+)",
            r'<a href="https://console.cloud.google.com/storage/browser/\1" target="_blank" style="color: #0d6efd;">\1</a>',
            content,
        )
        # Replace HTTP URLs
        content = re.sub(
            r"(https?://[^\s\)\"\'<>]+)",
            r'<a href="\1" target="_blank" style="color: #0d6efd;">\1</a>',
            content,
        )
        # Replace local file paths (make them visible but note they're local)
        content = re.sub(
            r"([A-Za-z]:\\[^\s\)\"\'<>]+\.(mp4|mp3|wav|png|jpg|webm))",
            r'<span style="color: #0d6efd; text-decoration: underline;" title="Local file path">\1</span>',
            content,
            flags=re.IGNORECASE,
        )
        return content

    # Execution Logic
    if run_button:
        # User attempted to run - now show validation errors if any
        st.session_state.show_validation_warnings = True

        if not directive:
            st.warning("⚠️ Please enter a creative directive before running the agency.")
        elif AGENCY_SECTIONS_AVAILABLE and not is_valid:
            # Rerun to show validation warnings
            st.rerun()
        else:
            st.session_state.agency_running = True
            st.session_state.agency_session_start = datetime.now()
            st.session_state.generated_video = None
            st.session_state.generated_audio = None
            st.session_state.generated_final = None

            with progress_container:
                progress_bar = st.progress(0, text="Initializing Agency...")
                status_text = st.empty()

            with event_container:
                st.subheader("📋 Event Log")
                event_placeholder = st.empty()
                events_html = []

                # Agent progress mapping
                agent_progress = {
                    "System": 5,
                    "Director": 15,
                    "Researcher": 30,
                    "Confidence": 45,
                    "Cinematographer": 60,
                    "Composer": 75,
                    "Editor": 90,
                }

                try:
                    runner = st.session_state.agent_runner
                    current_agent = "System"

                    # Pass agency config if available
                    stream_config = agency_cfg if AGENCY_SECTIONS_AVAILABLE else None

                    for event in runner.stream_agency_graph(
                        directive, agency_config=stream_config  # type: ignore[arg-type]
                    ):
                        if event is None:
                            break

                        agent_name, event_type, content = event
                        timestamp = datetime.now().strftime("%H:%M:%S")

                        # Update progress bar immediately on ANY event from an agent
                        current_agent = agent_name
                        progress_pct = agent_progress.get(agent_name, 50)

                        # For progress events, use the content as the status text
                        if event_type == "progress":
                            progress_bar.progress(
                                progress_pct / 100,
                                text=f"🔄 {agent_name}: {content[:60]}...",
                            )
                            status_text.markdown(
                                f"**Current Agent:** {agent_name} | **Status:** Processing"
                            )
                            # KEEP progress events in log - don't skip them
                        else:
                            progress_bar.progress(
                                progress_pct / 100,
                                text=f"🔄 {agent_name}: Processing...",
                            )
                            status_text.markdown(
                                f"**Current Agent:** {agent_name} | **Status:** {event_type.title()}"
                            )

                        # Track generated assets - prioritize cloud URLs over local paths
                        content_lower = content.lower()
                        cloud_url = extract_cloud_url(content)
                        local_path = extract_file_path(content)
                        # Use cloud URL if available, otherwise local path
                        path = cloud_url if cloud_url else local_path

                        # Cinematographer outputs video
                        if agent_name == "Cinematographer" and path:
                            if path.startswith("http") or (
                                path and path.endswith((".mp4", ".webm"))
                            ):
                                st.session_state.generated_video = path
                        # Composer outputs audio
                        elif agent_name == "Composer" and path:
                            if path.startswith("http") or (
                                path and path.endswith((".wav", ".mp3", ".m4a"))
                            ):
                                st.session_state.generated_audio = path
                        # Editor outputs final merged video
                        elif agent_name == "Editor" and path:
                            if path.startswith("http") or (
                                path and path.endswith(".mp4")
                            ):
                                st.session_state.generated_final = path
                        # Fallback: generic detection
                        elif path:
                            if "video" in content_lower and (
                                "created" in content_lower
                                or "generated" in content_lower
                                or "success" in content_lower
                            ):
                                if path.startswith("http") or path.endswith(
                                    (".mp4", ".webm")
                                ):
                                    st.session_state.generated_video = path
                            if "audio" in content_lower and (
                                "created" in content_lower
                                or "generated" in content_lower
                                or "success" in content_lower
                            ):
                                if path.startswith("http") or path.endswith(
                                    (".wav", ".mp3", ".m4a")
                                ):
                                    st.session_state.generated_audio = path
                            if "final" in content_lower and (
                                "merge" in content_lower
                                or "output" in content_lower
                                or "cut" in content_lower
                            ):
                                if path.startswith("http") or path.endswith(".mp4"):
                                    st.session_state.generated_final = path

                        # Format event with clickable links
                        css_class = "event-info"
                        if event_type == "output":
                            css_class = "event-output"
                        elif event_type == "error":
                            css_class = "event-error"
                        elif event_type == "thinking":
                            css_class = "event-thinking"
                        elif event_type == "progress":
                            css_class = "event-progress"

                        clickable_content = make_content_clickable(content)
                        event_html = f"<div class='{css_class}' style='padding: 4px 0; border-bottom: 1px solid #eee;'>[{timestamp}] <b>{agent_name}</b>: {clickable_content}</div>"
                        events_html.append(event_html)

                        # Update display (show last 50 events)
                        event_placeholder.markdown(
                            f"<div class='event-log'>{''.join(events_html[-50:])}</div>",
                            unsafe_allow_html=True,
                        )

                    progress_bar.progress(100, text="✅ Pipeline Complete!")
                    status_text.markdown("**Status:** Complete")
                    st.success("Agency pipeline completed!")

                except Exception as e:
                    progress_bar.progress(100, text="❌ Pipeline Failed")
                    status_text.markdown(f"**Status:** Error - {str(e)[:50]}")
                    st.error(f"Agency Error: {str(e)}")
                    logger.exception("Agency execution failed")
                finally:
                    st.session_state.agency_running = False

    # Download Section - Always visible if assets exist
    with download_container:
        has_video = st.session_state.generated_video is not None
        has_audio = st.session_state.generated_audio is not None
        has_final = st.session_state.generated_final is not None

        if has_video or has_audio or has_final:
            st.divider()
            st.subheader("📥 Download Generated Media")

            col_final, col_video, col_audio = st.columns(3)

            with col_final:
                if has_final:
                    final_path = st.session_state.generated_final
                    st.markdown("**Combined Video**")
                    if final_path and final_path.startswith("gs://"):
                        st.markdown(
                            f"[🎬 Download Final Video]({final_path.replace('gs://', 'https://storage.googleapis.com/')})"
                        )
                    elif final_path and final_path.startswith("http"):
                        st.markdown(f"[🎬 Download Final Video]({final_path})")
                    elif final_path:
                        # Local file - try to provide download
                        if os.path.exists(final_path):
                            with open(final_path, "rb") as f:
                                st.download_button(
                                    "🎬 Download Final Video",
                                    data=f.read(),
                                    file_name=os.path.basename(final_path),
                                    mime="video/mp4",
                                )
                        else:
                            st.info(f"Local: {final_path}")
                    else:
                        st.info("Final video path not set")
                else:
                    st.markdown("*No combined video*")

            with col_video:
                if has_video:
                    video_path = st.session_state.generated_video
                    st.markdown("**Video Only**")
                    if video_path and video_path.startswith("gs://"):
                        st.markdown(
                            f"[🎥 Download Video]({video_path.replace('gs://', 'https://storage.googleapis.com/')})"
                        )
                    elif video_path and video_path.startswith("http"):
                        st.markdown(f"[🎥 Download Video]({video_path})")
                    elif video_path:
                        if os.path.exists(video_path):
                            with open(video_path, "rb") as f:
                                st.download_button(
                                    "🎥 Download Video",
                                    data=f.read(),
                                    file_name=os.path.basename(video_path),
                                    mime="video/mp4",
                                )
                        else:
                            st.info(f"Local: {video_path}")
                    else:
                        st.info("Video path not set")
                else:
                    st.markdown("*No video generated*")

            with col_audio:
                if has_audio:
                    audio_path = st.session_state.generated_audio
                    st.markdown("**Audio Only**")
                    if audio_path and audio_path.startswith("gs://"):
                        st.markdown(
                            f"[🎵 Download Audio]({audio_path.replace('gs://', 'https://storage.googleapis.com/')})"
                        )
                    elif audio_path and audio_path.startswith("http"):
                        st.markdown(f"[🎵 Download Audio]({audio_path})")
                    elif audio_path:
                        if os.path.exists(audio_path):
                            with open(audio_path, "rb") as f:
                                # Detect mime type based on extension
                                audio_mime = (
                                    "audio/wav"
                                    if audio_path.lower().endswith(".wav")
                                    else "audio/mpeg"
                                )
                                st.download_button(
                                    "🎵 Download Audio",
                                    data=f.read(),
                                    file_name=os.path.basename(audio_path),
                                    mime=audio_mime,
                                )
                        else:
                            st.info(f"Local: {audio_path}")
                    else:
                        st.info("Audio path not set")
                else:
                    st.markdown("*No audio generated*")

    if stop_button:
        st.session_state.agency_running = False
        st.warning("Stop requested. Pipeline will halt at next checkpoint.")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: RESEARCH AGENT - STANDALONE RESEARCH
# ═══════════════════════════════════════════════════════════════════════════════

with tab_research:
    st.header("Research Agent (Delphi)")
    st.markdown("""
    **Standalone Research Capability**
    
    Uses Native Google Search Grounding for live web research.
    Results are stored in the Agent Memory (LanceDB) for future reference.
    """)

    st.divider()

    research_query = st.text_area(
        "Research Query",
        placeholder="Example: What are the latest developments in AI video generation technology?",
        height=100,
        key="research_query",
    )

    research_button = st.button(
        "🔬 Run Research",
        disabled=st.session_state.research_running or not research_query,
        use_container_width=True,
        type="primary",
    )

    research_output = st.container()

    if research_button and research_query:
        st.session_state.research_running = True

        with research_output:
            with st.spinner("Researching..."):
                try:
                    runner = st.session_state.agent_runner

                    # Stream research events
                    result_text = []
                    for event in runner.run_research_direct(research_query):
                        if event is None:
                            break

                        agent_name, event_type, content = event

                        if event_type == "output":
                            result_text.append(content)
                        elif event_type == "error":
                            st.error(content)

                    if result_text:
                        st.markdown("### Research Results")
                        st.markdown("\n\n".join(result_text))

                    st.success("Research complete!")

                except Exception as e:
                    st.error(f"Research Error: {str(e)}")
                    logger.exception("Research execution failed")
                finally:
                    st.session_state.research_running = False

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: AGENT COMMS - INTER-AGENT MESSAGING
# ═══════════════════════════════════════════════════════════════════════════════

with tab_comms:
    st.header("Agent Communications")
    st.markdown("""
    **Inter-Agent Messaging System**
    
    Monitor and interact with the Agent Neural Fabric (Postgres).
    Send manual directives to specific agents or broadcast to all.
    """)

    st.divider()

    # Connection Status
    if not st.session_state.comms_connected:
        st.error(
            "❌ Postgres not connected. Check your POSTGRES_* environment variables."
        )
        st.code("""
# Required environment variables:
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
        """)

        if st.button("🔄 Retry Connection"):
            st.session_state.comms = AgentComms()
            st.session_state.comms_connected = st.session_state.comms.connect()
            if st.session_state.comms_connected:
                st.session_state.comms.setup_tables()
                st.rerun()
    else:
        # Message Composer
        st.subheader("📤 Send Message")

        col_sender, col_recipient = st.columns(2)

        with col_sender:
            sender = st.selectbox(
                "From Agent",
                options=[
                    "Director",
                    "Researcher",
                    "Confidence",
                    "Cinematographer",
                    "Composer",
                    "Editor",
                    "Human",
                ],
                index=6,  # Default to Human
                key="msg_sender",
            )

        with col_recipient:
            recipient = st.selectbox(
                "To Agent",
                options=[
                    "All",
                    "Director",
                    "Researcher",
                    "Confidence",
                    "Cinematographer",
                    "Composer",
                    "Editor",
                ],
                key="msg_recipient",
            )

        message_content = st.text_area(
            "Message Content",
            placeholder="Enter your message or directive here...",
            height=100,
            key="msg_content",
        )

        send_button = st.button(
            "📨 Send Message", disabled=not message_content, use_container_width=True
        )

        if send_button and message_content:
            try:
                st.session_state.comms.send_message(sender, recipient, message_content)
                st.success(f"Message sent: {sender} → {recipient}")
                # Force refresh
                time.sleep(0.5)
                st.rerun()
            except Exception as e:
                st.error(f"Failed to send message: {str(e)}")

        st.divider()

        # Message History
        st.subheader("📬 Message History")

        col_refresh, col_filter = st.columns([1, 2])

        with col_refresh:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()

        with col_filter:
            filter_agent = st.selectbox(
                "Filter by Agent",
                options=[
                    "All",
                    "Director",
                    "Researcher",
                    "Confidence",
                    "Cinematographer",
                    "Composer",
                    "Editor",
                    "Human",
                ],
                key="msg_filter",
            )

        # Fetch and display messages
        try:
            # Use session start time for filtering if available
            session_filter = st.session_state.get("agency_session_start", None)
            messages = st.session_state.comms.get_all_recent_messages(
                limit=50, since=session_filter
            )

            if not messages:
                if session_filter:
                    st.info(
                        f"No messages in current session (started {session_filter.strftime('%H:%M:%S')}). Messages will appear when agents communicate."
                    )
                else:
                    st.info(
                        "No messages yet. Start an agency run to see agent communications."
                    )
            else:
                # Filter if needed
                if filter_agent != "All":
                    messages = [
                        m
                        for m in messages
                        if m["sender"] == filter_agent or m["recipient"] == filter_agent
                    ]

                for msg in messages:
                    timestamp = msg["timestamp"]
                    if hasattr(timestamp, "strftime"):
                        ts_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        ts_str = str(timestamp)

                    status_icon = "📨" if msg["status"] == "unread" else "✅"

                    st.markdown(
                        f"""
                    <div class='msg-content'>
                        <span class='msg-sender'>{msg["sender"]}</span> → 
                        <span class='msg-recipient'>{msg["recipient"]}</span>
                        <span class='msg-timestamp'> | {ts_str} {status_icon}</span>
                        <br>{msg["content"]}
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

        except Exception as e:
            st.error(f"Failed to fetch messages: {str(e)}")
            logger.exception("Message fetch failed")

# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR - DIAGNOSTICS & SYSTEM INFO
# ═══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.header("🔧 System Diagnostics")

    # Environment Status
    st.subheader("Environment")

    env_vars = [
        ("LANGCHAIN_TRACING_V2", os.getenv("LANGCHAIN_TRACING_V2", "Not Set")),
        ("LANGCHAIN_API_KEY", "Set" if os.getenv("LANGCHAIN_API_KEY") else "Not Set"),
        ("GOOGLE_CLOUD_PROJECT", os.getenv("GOOGLE_CLOUD_PROJECT", "Not Set")),
        (
            "REPLICATE_API_TOKEN",
            "Set" if os.getenv("REPLICATE_API_TOKEN") else "Not Set",
        ),
        ("POSTGRES_HOST", os.getenv("POSTGRES_HOST", "localhost")),
    ]

    for var_name, var_value in env_vars:
        st.text(f"{var_name}: {var_value}")

    st.divider()

    # Quick Actions
    st.subheader("Quick Actions")

    if st.button("🧹 New Session", use_container_width=True):
        new_id = st.session_state.session_manager.create_session("Manual reset")
        st.session_state.session_manager = SessionManager(new_id)
        st.success(f"New session: {new_id[:8]}...")

    if st.button("🔗 Open LangSmith", use_container_width=True):
        st.markdown("[LangSmith Dashboard](https://smith.langchain.com/)")

    st.divider()

    # Session Info
    st.subheader("Session Info")
    session = st.session_state.session_manager
    st.code(f"{session.session_id}", language=None)
    history = session.load_history()
    st.text(f"Events: {len(history)}")
