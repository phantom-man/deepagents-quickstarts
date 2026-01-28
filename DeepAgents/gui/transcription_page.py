"""
Streamlit Transcription Page.

Provides a UI for uploading audio files and viewing transcriptions
using Google Cloud Speech-to-Text.
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Optional

import streamlit as st

# Add parent directory to path for imports when running standalone
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load environment variables from DeepAgents .env
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Import the transcription service
from DeepAgents.services.transcription_service import (
    AudioEncoding,
    TranscriptionResponse,
    TranscriptionService,
)


def init_session_state():
    """Initialize session state variables."""
    if "transcription_result" not in st.session_state:
        st.session_state.transcription_result = None
    if "transcription_error" not in st.session_state:
        st.session_state.transcription_error = None
    if "is_transcribing" not in st.session_state:
        st.session_state.is_transcribing = False


def render_transcription_page():
    """Render the main transcription page."""
    init_session_state()

    st.title("🎤 Audio Transcription")
    st.markdown(
        "Upload an audio file to transcribe it using Google Cloud Speech-to-Text."
    )

    # Create two columns for layout
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📤 Upload Audio")
        render_upload_section()

    with col2:
        st.subheader("📝 Transcription Result")
        render_result_section()


def render_upload_section():
    """Render the file upload and settings section."""
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose an audio file",
        type=["wav", "mp3", "flac", "ogg", "webm", "m4a"],
        help="Supported formats: WAV, MP3, FLAC, OGG, WebM, M4A",
    )

    # Settings expander
    with st.expander("⚙️ Transcription Settings", expanded=False):
        # Language selection
        language_code = st.selectbox(
            "Language",
            options=[
                "en-US",
                "en-GB",
                "es-ES",
                "es-MX",
                "fr-FR",
                "de-DE",
                "it-IT",
                "pt-BR",
                "ja-JP",
                "ko-KR",
                "zh-CN",
                "zh-TW",
                "ru-RU",
                "ar-SA",
                "hi-IN",
            ],
            index=0,
            help="Select the language spoken in the audio",
        )

        # Check if project ID is available for V2 API
        project_id_available = bool(os.getenv("GOOGLE_CLOUD_PROJECT"))

        # API version
        use_v2 = st.checkbox(
            "Use V2 API (Chirp models)",
            value=False,
            disabled=not project_id_available,
            help="V2 API provides access to latest Chirp models. "
            + (
                ""
                if project_id_available
                else "⚠️ Requires GOOGLE_CLOUD_PROJECT env var to be set."
            ),
        )

        if not project_id_available:
            st.caption("ℹ️ V2 API disabled - set GOOGLE_CLOUD_PROJECT env var to enable")

        # Model selection based on API version
        if use_v2:
            model = st.selectbox(
                "Model",
                options=["long", "short", "chirp", "chirp_2", "chirp_3"],
                index=0,
                help="chirp_3 offers best quality but requires US region",
            )
        else:
            model = st.selectbox(
                "Model",
                options=["default", "phone_call", "video", "command_and_search"],
                index=0,
                help="Select model optimized for your audio type",
            )

        # Audio encoding (for V1 API)
        if not use_v2:
            encoding = st.selectbox(
                "Audio Encoding",
                options=["LINEAR16", "FLAC", "MP3", "OGG_OPUS", "WEBM_OPUS"],
                index=0,
                help="Audio encoding format. LINEAR16 for WAV, FLAC for FLAC files",
            )

            sample_rate = st.number_input(
                "Sample Rate (Hz)",
                min_value=8000,
                max_value=48000,
                value=16000,
                step=1000,
                help="Sample rate of the audio file",
            )
        else:
            encoding = "AUTO"
            sample_rate = 16000

    # Transcribe button
    if uploaded_file is not None:
        file_details = {
            "Filename": uploaded_file.name,
            "Size": f"{uploaded_file.size / 1024:.1f} KB",
            "Type": uploaded_file.type or "Unknown",
        }

        st.markdown("**File Details:**")
        for key, value in file_details.items():
            st.text(f"  {key}: {value}")

        # Audio preview
        st.audio(uploaded_file, format=uploaded_file.type)

        if st.button(
            "🚀 Transcribe",
            type="primary",
            disabled=st.session_state.is_transcribing,
            use_container_width=True,
        ):
            # Cast encoding string to AudioEncoding type
            encoding_typed: AudioEncoding = encoding  # type: ignore[assignment]
            transcribe_audio(
                uploaded_file,
                language_code,
                use_v2,
                model if model != "default" else None,
                encoding_typed,
                sample_rate,
            )
    else:
        st.info("👆 Upload an audio file to get started")


def transcribe_audio(
    uploaded_file,
    language_code: str,
    use_v2: bool,
    model: Optional[str],
    encoding: str,  # Will be cast to AudioEncoding
    sample_rate: int,
):
    """Perform the transcription."""
    st.session_state.is_transcribing = True
    st.session_state.transcription_error = None
    st.session_state.transcription_result = None

    try:
        # Save uploaded file to temp location
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=Path(uploaded_file.name).suffix
        ) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name

        with st.spinner("Transcribing... This may take a moment."):
            service = TranscriptionService()

            if use_v2:
                result = service.transcribe_file_v2(
                    tmp_path,
                    language_codes=[language_code],
                    model=model or "long",
                )
            else:
                # Cast encoding to AudioEncoding type
                encoding_cast: AudioEncoding = encoding  # type: ignore[assignment]
                result = service.transcribe_file(
                    tmp_path,
                    language_code=language_code,
                    encoding=encoding_cast,
                    sample_rate_hertz=sample_rate,
                    model=model,
                )

            st.session_state.transcription_result = result

        # Clean up temp file
        os.unlink(tmp_path)

    except Exception as e:
        st.session_state.transcription_error = str(e)
        # Clean up temp file on error too
        if "tmp_path" in locals():
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    finally:
        st.session_state.is_transcribing = False
        st.rerun()


def render_result_section():
    """Render the transcription result section."""
    if st.session_state.transcription_error:
        st.error(f"❌ Transcription failed: {st.session_state.transcription_error}")

        # Show troubleshooting tips
        with st.expander("🔧 Troubleshooting"):
            st.markdown("""
            **Common issues:**

            1. **Authentication Error**: Ensure `GOOGLE_APPLICATION_CREDENTIALS` 
               environment variable is set to your service account key path.

            2. **API Not Enabled**: Enable the Speech-to-Text API in your 
               Google Cloud Console.

            3. **Invalid Audio Format**: Try a different encoding setting or 
               convert your audio to WAV format.

            4. **Project ID Missing**: For V2 API, ensure `GOOGLE_CLOUD_PROJECT` 
               environment variable is set.
            """)

    elif st.session_state.transcription_result:
        result: TranscriptionResponse = st.session_state.transcription_result

        # Show full transcript
        st.text_area(
            "Full Transcript",
            value=result.full_transcript,
            height=300,
            help="The complete transcription of your audio",
        )

        # Copy button
        if st.button("📋 Copy to Clipboard"):
            st.write("Transcript copied!")
            st.toast("Copied to clipboard!", icon="✅")

        # Download button
        st.download_button(
            label="💾 Download as Text",
            data=result.full_transcript,
            file_name="transcription.txt",
            mime="text/plain",
        )

        # Show detailed results
        if result.results:
            with st.expander(f"📊 Detailed Results ({len(result.results)} segments)"):
                for i, segment in enumerate(result.results):
                    st.markdown(f"**Segment {i + 1}**")
                    st.text(segment.transcript)
                    if segment.confidence > 0:
                        st.progress(
                            segment.confidence,
                            text=f"Confidence: {segment.confidence:.1%}",
                        )
                    st.divider()

    else:
        st.markdown(
            """
            <div style="
                border: 2px dashed #555;
                border-radius: 10px;
                padding: 40px;
                text-align: center;
                color: #888;
            ">
                <p style="font-size: 1.2em;">Your transcription will appear here</p>
                <p>Upload an audio file and click Transcribe</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_standalone():
    """Render as a standalone Streamlit app."""
    st.set_page_config(
        page_title="Audio Transcription",
        page_icon="🎤",
        layout="wide",
    )

    # Custom CSS
    st.markdown(
        """
        <style>
        .stTextArea textarea {
            font-family: 'Segoe UI', sans-serif;
            font-size: 14px;
            line-height: 1.6;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    render_transcription_page()


# Allow running as standalone app
if __name__ == "__main__":
    render_standalone()
