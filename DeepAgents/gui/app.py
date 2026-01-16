"""
DeepAgents Streamlit GUI - Simplified Agency Interface.
Exposes only the core Agency orchestration, Research Agent, and Agent Communications.
Follows LangChain/LangSmith Gold Standard with Zero-Touch Configuration.
"""

# pylint: disable=line-too-long, import-error, wrong-import-position
# pylint: disable=import-outside-toplevel, broad-exception-caught, missing-function-docstring
# pylint: disable=too-many-statements, too-many-locals, too-many-branches

import os
import sys
import logging
import time
from datetime import datetime

import streamlit as st

# Add parent directory for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from gui.agent_runner import AgentRunner
from gui.history_manager import SessionManager
from agent_brain import AgentComms, AgentConfig

# Configure logging (ASCII-safe for Windows cp1252)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DeepAgentsGUI")

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG & STYLING
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="DeepAgents Agency",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    /* Clean dark theme overrides */
    .stApp { background-color: #0e1117; }
    .block-container { padding: 2rem; max-width: 1200px; margin: auto; }
    
    /* Event log styling */
    .event-log {
        background: #1a1a2e;
        border-radius: 8px;
        padding: 1rem;
        max-height: 500px;
        overflow-y: auto;
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 0.85rem;
        border: 1px solid #333;
    }
    .event-info { color: #58a6ff; }
    .event-output { color: #7ee787; }
    .event-error { color: #f85149; }
    .event-thinking { color: #d29922; font-style: italic; }
    
    /* Message bubbles for AgentComms */
    .msg-sender { color: #58a6ff; font-weight: bold; }
    .msg-recipient { color: #a371f7; }
    .msg-content { 
        background: #21262d;
        padding: 0.75rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 3px solid #58a6ff;
    }
    .msg-timestamp { color: #8b949e; font-size: 0.75rem; }
    
    /* Status indicators */
    .status-connected { color: #3fb950; }
    .status-disconnected { color: #f85149; }
</style>
""", unsafe_allow_html=True)

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
        st.markdown("**LangSmith:** <span class='status-connected'>Connected</span>", unsafe_allow_html=True)
    else:
        st.markdown("**LangSmith:** <span class='status-disconnected'>Not Configured</span>", unsafe_allow_html=True)

with col_status2:
    if st.session_state.comms_connected:
        st.markdown("**Postgres:** <span class='status-connected'>Connected</span>", unsafe_allow_html=True)
    else:
        st.markdown("**Postgres:** <span class='status-disconnected'>Disconnected</span>", unsafe_allow_html=True)

with col_status3:
    try:
        config = AgentConfig()
        dir_config = config.get_agent_config("Director")
        model = dir_config.get("model", "Unknown")
        st.markdown(f"**Model:** `{model}`")
    except Exception:
        st.markdown("**Model:** <span class='status-disconnected'>Config Error</span>", unsafe_allow_html=True)

st.divider()

# ═══════════════════════════════════════════════════════════════════════════════
# TAB LAYOUT - SIMPLIFIED TO 3 CORE FEATURES
# ═══════════════════════════════════════════════════════════════════════════════

tab_agency, tab_research, tab_comms = st.tabs([
    "🎬 Agency",
    "🔬 Research Agent",
    "📡 Agent Comms"
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: AGENCY - FULL LANGGRAPH ORCHESTRATION
# ═══════════════════════════════════════════════════════════════════════════════

with tab_agency:
    st.header("Agency Orchestration")
    st.markdown("""
    **Zero-Touch AI Production Pipeline**
    
    Enter a creative directive and the Agency will orchestrate the full production:
    - **Director (Apollo)** - Plans and coordinates the project
    - **Researcher (Delphi)** - Gathers facts and context
    - **Confidence (Validator)** - Quality assurance and validation
    - **Cinematographer (Lumiere)** - Video generation
    - **Composer (Orpheus)** - Music and audio generation
    - **Editor** - Final assembly and delivery
    """)
    
    st.divider()
    
    # Directive Input
    directive = st.text_area(
        "Creative Directive",
        placeholder="Example: Create a 15-second promotional video for an AI startup with inspiring music",
        height=100,
        key="agency_directive"
    )
    
    col_run, col_stop = st.columns([1, 1])
    
    with col_run:
        run_button = st.button(
            "🚀 Run Agency",
            disabled=st.session_state.agency_running or not directive,
            use_container_width=True,
            type="primary"
        )
    
    with col_stop:
        stop_button = st.button(
            "⏹️ Stop",
            disabled=not st.session_state.agency_running,
            use_container_width=True
        )
    
    # Event Log Container
    event_container = st.container()
    
    # Execution Logic
    if run_button and directive:
        st.session_state.agency_running = True
        
        with event_container:
            st.markdown("<div class='event-log'>", unsafe_allow_html=True)
            event_placeholder = st.empty()
            events_html = []
            
            try:
                runner = st.session_state.agent_runner
                
                for event in runner.stream_agency_graph(directive):
                    if event is None:
                        break
                    
                    agent_name, event_type, content = event
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    
                    # Format event
                    css_class = "event-info"
                    if event_type == "output":
                        css_class = "event-output"
                    elif event_type == "error":
                        css_class = "event-error"
                    elif event_type == "thinking":
                        css_class = "event-thinking"
                    
                    event_html = f"<div class='{css_class}'>[{timestamp}] <b>{agent_name}</b>: {content}</div>"
                    events_html.append(event_html)
                    
                    # Update display (show last 50 events)
                    event_placeholder.markdown("\n".join(events_html[-50:]), unsafe_allow_html=True)
                
                st.success("Agency pipeline completed!")
                
            except Exception as e:
                st.error(f"Agency Error: {str(e)}")
                logger.exception("Agency execution failed")
            finally:
                st.session_state.agency_running = False
            
            st.markdown("</div>", unsafe_allow_html=True)
    
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
        key="research_query"
    )
    
    research_button = st.button(
        "🔬 Run Research",
        disabled=st.session_state.research_running or not research_query,
        use_container_width=True,
        type="primary"
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
        st.error("❌ Postgres not connected. Check your POSTGRES_* environment variables.")
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
                options=["Director", "Researcher", "Confidence", "Cinematographer", "Composer", "Editor", "Human"],
                index=6,  # Default to Human
                key="msg_sender"
            )
        
        with col_recipient:
            recipient = st.selectbox(
                "To Agent",
                options=["All", "Director", "Researcher", "Confidence", "Cinematographer", "Composer", "Editor"],
                key="msg_recipient"
            )
        
        message_content = st.text_area(
            "Message Content",
            placeholder="Enter your message or directive here...",
            height=100,
            key="msg_content"
        )
        
        send_button = st.button("📨 Send Message", disabled=not message_content, use_container_width=True)
        
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
                options=["All", "Director", "Researcher", "Confidence", "Cinematographer", "Composer", "Editor", "Human"],
                key="msg_filter"
            )
        
        # Fetch and display messages
        try:
            messages = st.session_state.comms.get_all_recent_messages(limit=50)
            
            if not messages:
                st.info("No messages yet. Send a message to get started!")
            else:
                # Filter if needed
                if filter_agent != "All":
                    messages = [m for m in messages if m["sender"] == filter_agent or m["recipient"] == filter_agent]
                
                for msg in messages:
                    timestamp = msg["timestamp"]
                    if hasattr(timestamp, "strftime"):
                        ts_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        ts_str = str(timestamp)
                    
                    status_icon = "📨" if msg["status"] == "unread" else "✅"
                    
                    st.markdown(f"""
                    <div class='msg-content'>
                        <span class='msg-sender'>{msg['sender']}</span> → 
                        <span class='msg-recipient'>{msg['recipient']}</span>
                        <span class='msg-timestamp'> | {ts_str} {status_icon}</span>
                        <br>{msg['content']}
                    </div>
                    """, unsafe_allow_html=True)
                    
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
        ("REPLICATE_API_TOKEN", "Set" if os.getenv("REPLICATE_API_TOKEN") else "Not Set"),
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
    st.text(f"Session ID: {session.session_id[:8]}...")
    history = session.load_history()
    st.text(f"Events: {len(history)}")
