import streamlit as st
import time
import os
import sys

# Add parent path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from DeepAgents.gui.diagnostics_service import run_diagnostics
from DeepAgents.gui.history_manager import SessionManager, list_sessions
from DeepAgents.gui.agent_runner import AgentRunner

st.set_page_config(page_title="DeepAgents HQ", layout="wide", page_icon="🎬")

# --- CSS / STYLING ---
st.markdown("""
<style>
    .agent-box {
        border: 1px solid #ddd;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .director { border-left: 5px solid #FF4B4B; background-color: #262730; }
    .researcher { border-left: 5px solid #1E88E5; background-color: #262730; }
    .confidence { border-left: 5px solid #00C853; background-color: #262730; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR: CONTROLS & DIAGNOSTICS ---
st.sidebar.title("🎛️ Control Center")

# 1. Diagnostics
st.sidebar.subheader("System Status")
if st.sidebar.button("Run Pre-flight Checks"):
    with st.sidebar.status("Checking Systems..."):
        results = run_diagnostics()
        for sys_name, res in results.items():
            if res["status"]:
                st.sidebar.success(f"{sys_name}: OK")
            else:
                st.sidebar.error(f"{sys_name}: {res.get('message')}")

# 2. Configuration
st.sidebar.divider()
st.sidebar.subheader("Configuration")
selected_model = st.sidebar.selectbox(
    "AI Model", 
    ["gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-experimental"],
    index=0
)

# 3. History / Session
st.sidebar.divider()
st.sidebar.subheader("Time Travel")
mode = st.sidebar.radio("Mode", ["Live Operation", "Review History"])

session_id = None
if mode == "Review History":
    sessions = list_sessions()
    if sessions:
        selected_session = st.sidebar.selectbox("Select Past Directive", sessions)
        session_id = selected_session
    else:
        st.sidebar.warning("No history found.")

# Initialize Manager
if not "current_session_id" in st.session_state:
    st.session_state.current_session_id = None

manager = SessionManager(session_id if mode == "Review History" else st.session_state.current_session_id)
runner = AgentRunner(manager)

# --- MAIN INTERFACE ---
st.title("🤖 DeepAgents Orchestrator")

# Tabs for Agents
tab_director, tab_research, tab_confidence, tab_comms, tab_properties = st.tabs([
    "🎬 Director (Creative)", 
    "🔎 Research (Truth)", 
    "⚖️ Confidence (Audit)",
    "📡 Inter-Agent Comms",
    "⚙️ Properties & Ontologies"
])

# --- TAB 1: DIRECTOR ---
with tab_director:
    st.header("Creative Direction")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        directive = st.text_area("Enter Commercial Concept / Directive", height=100)
    with col2:
        st.write("## ")
        run_btn = st.button("ACTION!", type="primary", use_container_width=True, disabled=(mode == "Review History"))

    # Output Containter
    output_container = st.container()

    if run_btn and directive:
        # Create new session if needed
        st.session_state.current_session_id = SessionManager().session_id
        manager = SessionManager(st.session_state.current_session_id)
        runner = AgentRunner(manager)
        
        with output_container:
            st.info(f"Session started: {manager.session_id}")
            # Stream events
            for agent, type_, content in runner.stream_director(directive, model=selected_model):
                if type_ == "thinking":
                    with st.expander(f"💭 {agent} Thinking...", expanded=False):
                        st.markdown(content)
                elif type_ == "output":
                     st.markdown(f"### 🎬 {agent} Output")
                     st.markdown(content)
                elif type_ == "error":
                    st.error(content)

    elif mode == "Review History" and session_id:
        # Replay Log
        logs = manager.load_history()
        for log in logs:
            if log['agent'] == "Director":
                with output_container:
                    if log['type'] == 'thinking':
                        with st.expander(f"💭 Director Thinking ({log['timestamp']})"):
                            st.write(log['content'])
                    elif log['type'] == 'output':
                        st.markdown("### 🎬 Director Output")
                        st.markdown(log['content'])


# --- TAB 4: AGENT COMMS (The Mesh) ---
with tab_comms:
    st.header("Agent Neural Link")
    st.write("Visualizing messages passed between agents.")
    
    # Load logs and filter for cross-agent calls
    logs = manager.load_history()
    for log in logs:
        # Heuristic for inter-agent comms (Tool Calls)
        if log.get("tool_calls"):
            # This logic depends on how we structured the tool call logging in agent_runner
            # Currently it logs raw thinking. Ideally we parse it better.
            st.markdown(f"**{log['timestamp']}** | {log['agent']} ➡️ System: `{log['content']}`")

# --- TAB 5: PROPERTIES ---
with tab_properties:
    st.header("Agent Constitutions (Ontologies)")
    
    # Read files
    try:
        with open("DeepAgents/Canon/Director_Ontology.md", "r", encoding="utf-8") as f:
            director_ont = f.read()
        with open("DeepAgents/Canon/Research_Agent_Ontology.md", "r", encoding="utf-8") as f:
            research_ont = f.read()
            
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            with st.expander("🎬 Director Ontology"):
                st.markdown(director_ont)
        with col_p2:
            with st.expander("🔎 Research Ontology"):
                st.markdown(research_ont)
                
    except Exception as e:
        st.error(f"Could not load ontologies: {e}")

st.sidebar.text(f"Session: {manager.session_id}")
