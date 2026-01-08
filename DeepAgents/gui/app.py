import streamlit as st # type: ignore
import time
import os
import sys

# Add parent path to allow imports from DeepAgents
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from DeepAgents.gui.diagnostics_service import run_diagnostics
from DeepAgents.gui.history_manager import SessionManager, list_sessions
from DeepAgents.gui.agent_runner import AgentRunner
from DeepAgents.agent_brain import AgentConfig  # New Config Manager

# Initialize Config
config_manager = AgentConfig()

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
    .cinematographer { border-left: 5px solid #FFD600; background-color: #262730; } 
    .stSelectbox label { font-size: 0.9em; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def get_available_models():
    """
    Checks connections and returns available models for each provider.
    """
    models = {
        "Google": {"text": [], "image": [], "video": []},
        "Anthropic": {"text": []},
        "Other": {"image": [], "video": []}
    }
    
    # Check Google
    try:
        from google import genai
        # Try to use standard env var or fallback
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GOOGLE_PROJECT_ID")
        location = "us-central1"
        if project_id:
            client = genai.Client(vertexai=True, project=project_id, location=location)
            
            # Simple list
            g_models = list(client.models.list())
            for m in g_models:
                # Ensure name exists
                if not m.name: continue
                name = m.name.split('/')[-1] # simplified name
                # Categorize
                if "gemini" in name.lower():
                    models["Google"]["text"].append(name)
                elif "imagen" in name.lower():
                     models["Google"]["image"].append(name)
                elif "veo" in name.lower():
                     models["Google"]["video"].append(name)
            
            # Fallbacks if list is empty or specific models known
            if not models["Google"]["image"]:
                models["Google"]["image"] = ["imagen-3.0-generate-001", "imagen-2.0"]
            if not models["Google"]["video"]:
                models["Google"]["video"] = ["veo-2.0-generate-001"] # Future/Preview

        else:
             # Fallback if no project ID but maybe API key
             models["Google"]["text"] = ["gemini-1.5-pro", "gemini-1.5-flash"]
             models["Google"]["image"] = ["imagen-3.0-generate-001"]
             models["Google"]["video"] = ["veo-2.0-generate-001"]
                 
    except Exception as e:
        # st.toast(f"Google Connection Failed: {e}", icon="⚠️")
        # Fallback defaults
        models["Google"]["text"] = ["gemini-1.5-pro", "gemini-1.5-flash"]
        models["Google"]["image"] = ["imagen-3.0-generate-001"]
        models["Google"]["video"] = ["veo-2.0-generate-001"]

    # Check Anthropic
    try:
        # Anthropic doesn't have a simple "list models" API in the same way, using standard list
        models["Anthropic"]["text"] = [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-3-5-sonnet-20240620"
        ]
    except Exception as e:
        pass

    return models

# --- SIDEBAR: CONTROLS & DIAGNOSTICS ---
st.sidebar.title("🎛️ Control Center")

# 1. Diagnostics & Pre-flight
st.sidebar.subheader("System Status")

if "connection_checked" not in st.session_state:
    st.session_state.connection_checked = False
if "available_models" not in st.session_state:
    st.session_state.available_models = {}

col_chk1, col_chk2 = st.sidebar.columns([2,1])
with col_chk1:
    if st.button("🚀 Check Connections", type="primary"):
        with st.sidebar.status("Running Pre-flight Checks...", expanded=True):
            # 1. Run Diagnostics
            results = run_diagnostics()
            all_ok = True
            for sys_name, res in results.items():
                if res["status"]:
                    st.write(f"✅ {sys_name}")
                else:
                    st.write(f"❌ {sys_name}: {res.get('message')}")
                    all_ok = False
            
            # 2. Fetch Models
            st.write("📡 Querying Providers...")
            st.session_state.available_models = get_available_models()
            st.write(f"Found {len(st.session_state.available_models['Google']['text'])} Google Models")
            
            st.session_state.connection_checked = True
            st.success("Ready for Launch!")

# 2. Configuration (Selectors)
st.sidebar.divider()
st.sidebar.subheader("Agent Configuration")

agents = ["Director", "Researcher", "Confidence", "Cinematographer"]
# Load current config
current_conf = config_manager.config 

if not st.session_state.connection_checked:
    st.sidebar.info("👋 Click 'Check Connections' to unlock configuration.")
    for agent in agents:
        with st.sidebar.expander(f"{agent} Settings", expanded=False):
            st.caption("🔒 Locked")
else:
    # Render Selectors
    for agent in agents:
        with st.sidebar.expander(f"⚙️ {agent} Settings", expanded=False):
            # Load saved values
            saved_provider = current_conf.get(agent, {}).get("provider", "Google")
            saved_model = current_conf.get(agent, {}).get("model", "gemini-1.5-flash")
            
            # 1. Provider Selector
            # Cinematographer has different providers for now (Video/Image)
            providers = ["Google", "Anthropic"]
                
            try: 
                prov_idx = providers.index(saved_provider) 
            except ValueError: 
                prov_idx = 0
                
            provider = st.selectbox(f"Provider ({agent})", providers, index=prov_idx, key=f"prov_{agent}")
            
            # 2. Model Selector
            model_list = st.session_state.available_models.get(provider, {}).get("text", [])
            
            if not model_list:
                model_list = [saved_model] # Fallback
                
            try:
                mod_idx = model_list.index(saved_model)
            except ValueError:
                if saved_model not in model_list:
                    model_list.append(saved_model)
                mod_idx = model_list.index(saved_model)
            
            model = st.selectbox(f"Model ({agent})", model_list, index=mod_idx, key=f"mod_{agent}")

            # 3. Extra Selectors for Cinematographer (Image/Video)
            extras = {}
            needs_save = False

            # Check basic Text Model changes
            if provider != saved_provider or model != saved_model:
                needs_save = True

            if agent == "Cinematographer":
                st.markdown("---")
                
                # --- Image Generation ---
                st.caption("🎨 Image Generation")
                saved_img_prov = current_conf.get(agent, {}).get("image_provider", "Google")
                saved_img_mod = current_conf.get(agent, {}).get("image_model", "imagen-3.0-generate-001")
                
                img_providers = ["Google", "Other"]
                img_provider_val = st.selectbox("Image Provider", img_providers, index=0 if saved_img_prov=="Google" else 1, key="cine_img_prov")
                
                img_models = st.session_state.available_models.get(img_provider_val, {}).get("image", ["imagen-3.0"])
                # Handle fallback logic
                if saved_img_mod not in img_models: img_models.append(saved_img_mod)
                img_model_val = st.selectbox("Image Model", img_models, index=img_models.index(saved_img_mod) if saved_img_mod in img_models else 0, key="cine_img_mod")

                # --- Video Generation ---
                st.caption("🎥 Video Generation")
                saved_vid_prov = current_conf.get(agent, {}).get("video_provider", "Google")
                saved_vid_mod = current_conf.get(agent, {}).get("video_model", "veo-2.0-generate-001")
                
                vid_providers = ["Google", "Other"]
                vid_provider_val = st.selectbox("Video Provider", vid_providers, index=0 if saved_vid_prov=="Google" else 1, key="cine_vid_prov")
                
                vid_models = st.session_state.available_models.get(vid_provider_val, {}).get("video", ["veo-2.0"])
                if saved_vid_mod not in vid_models: vid_models.append(saved_vid_mod)
                vid_model_val = st.selectbox("Video Model", vid_models, index=vid_models.index(saved_vid_mod) if saved_vid_mod in vid_models else 0, key="cine_vid_mod")

                # Populate Extras and Check for Changes
                extras["image_provider"] = img_provider_val
                extras["image_model"] = img_model_val
                extras["video_provider"] = vid_provider_val
                extras["video_model"] = vid_model_val

                if img_provider_val != saved_img_prov or img_model_val != saved_img_mod: needs_save = True
                if vid_provider_val != saved_vid_prov or vid_model_val != saved_vid_mod: needs_save = True

            
            if needs_save:
                config_manager.set_agent_config(agent, provider, model, **extras)
                st.toast(f"Saved {agent} Configuration")


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
tab_director, tab_research, tab_confidence, tab_cinematographer, tab_comms, tab_properties = st.tabs([
    "🎬 Director (Creative)", 
    "🔎 Research (Truth)", 
    "⚖️ Confidence (Audit)",
    "🎥 Cinematographer (Vision)", 
    "📡 Inter-Agent Comms",
    "⚙️ Canons"
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
        # Re-init runner with manager
        runner = AgentRunner(manager)
        
        with output_container:
            st.info(f"Session started: {manager.session_id}")
            # Stream events
            for agent, type_, content in runner.stream_director(directive): 
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

# --- TAB 2: RESEARCH ---
with tab_research:
    st.header("Research Agent")
    st.info("The Researcher verifies facts and finds references.")
    if session_id or st.session_state.current_session_id:
        logs = manager.load_history()
        for log in logs:
            if log['agent'] == "Researcher":
                with st.expander(f"📚 Research Report ({log['timestamp']})"):
                    st.markdown(log['content'])

# --- TAB 3: CONFIDENCE ---
with tab_confidence:
    st.header("Confidence / Audit Agent")
    st.info("The Audit Agent critiques the plan for feasibility.")
    if session_id or st.session_state.current_session_id:
        logs = manager.load_history()
        for log in logs:
            if log['agent'] == "Confidence":
                st.markdown(f"### 🛡️ Audit Report")
                st.markdown(log['content'])

# --- TAB 4: CINEMATOGRAPHER (New) ---
with tab_cinematographer:
    st.header("Cinematographer Agent")
    st.info("Translates the Director's vision into visual descriptions and video.")
    
    if session_id or st.session_state.current_session_id:
        logs = manager.load_history()
        found_cinema = False
        for log in logs:
            if log['agent'] == "Cinematographer":
                found_cinema = True
                if log['type'] == 'output':
                    st.markdown(f"### 🎥 Visual Treatment")
                    st.markdown(log['content'])
        
        if not found_cinema:
            st.write("Waiting for Director's instructions...")

# --- TAB 5: AGENT COMMS (The Mesh) ---
with tab_comms:
    st.header("Agent Neural Link")
    st.write("Visualizing messages passed between agents.")
    
    logs = manager.load_history()
    for log in logs:
        if log.get("tool_calls"):
            st.markdown(f"**{log['timestamp']}** | {log['agent']} ➡️ System: `{log['content']}`")

# --- TAB 6: PROPERTIES ---
with tab_properties:
    st.header("Agent Constitutions (Ontologies)")
    try:
        # Dynamically load ontologies
        ontologies = {
            "Director": "DeepAgents/Canon/Director_Ontology.md",
            "Research": "DeepAgents/Canon/Research_Agent_Ontology.md",
            "Cinematographer": "DeepAgents/Canon/Cinematographer_Ontology.md",
            "Confidence": "DeepAgents/Canon/Confidence_Agent_Ontology.md"
        }
        
        cols = st.columns(2)
        idx = 0
        for name, path in ontologies.items():
            content = "Not found"
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
            
            with cols[idx % 2]:
                with st.expander(f"📜 {name} Ontology"):
                    st.markdown(content)
            idx += 1
                
    except Exception as e:
        st.error(f"Could not load ontologies: {e}")

st.sidebar.text(f"Session: {manager.session_id}")
